"""
Transition engine: single authority for state changes. Idempotent per assistant_message_id.
"""
import hashlib
import json
import time

import sqlite3

from db import (
    get_conn,
    get_system_state,
    get_stage_methods,
    get_current_run,
    update_system_state,
    update_system_state_with_version,
    upsert_method,
    lock_method,
    promote_mastery,
    insert_state_event,
    update_state_event_result,
)
from state_schema import ProposedTransition

STAGE_NAMES = {
    "S0": "SETUP", "S1": "LOAD", "S2": "INSPECT", "S3": "CLEAN",
    "S4": "SELECT", "S5": "TRANSFORM (Core Facts)",
    "S6": "TRANSFORM (Task Mechanics)", "S7A": "AGGREGATE (Pandas)",
    "S7B": "AGGREGATE (SQL)", "S8": "SLA ENGINE",
    "S9": "INTELLIGENCE ENGINE", "S10": "VALIDATE",
    "S11": "PRESENT", "S12": "AUTOMATE",
}

MAX_RETRIES = 5
RETRY_BACKOFF = 0.05


def _state_hash(state: dict) -> str:
    """Stable hash of relevant system_state fields."""
    key_fields = {k: state.get(k) for k in ("version", "stage", "stage_name", "last_hardened") if k in state}
    return hashlib.sha256(json.dumps(key_fields, sort_keys=True).encode()).hexdigest()[:16]


def apply_transitions(
    assistant_message_id: int,
    proposals: list[ProposedTransition],
    current_state: dict,
    prompt_version: str | None = None,
) -> bool:
    """
    Apply proposed transitions in one transaction. Idempotent: if state_events
    already has a row for this assistant_message_id, return True without re-applying.
    Returns True if applied (or already applied), False if rejected.
    """
    conn = get_conn()
    try:
        # Idempotency: already applied?
        row = conn.execute(
            "SELECT applied FROM state_events WHERE assistant_message_id = ?",
            (assistant_message_id,),
        ).fetchone()
        if row is not None:
            return bool(row["applied"])

        prior_hash = _state_hash(current_state)
        proposed_json = json.dumps([{"action": p.action, "method_number": p.method_number, "method_name": p.method_name, "stage": p.stage} for p in proposals])

        for attempt in range(MAX_RETRIES):
            try:
                insert_state_event(
                    conn,
                    assistant_message_id,
                    prior_hash,
                    proposed_json,
                    parser_mode="regex",
                    prompt_version=prompt_version,
                )
                break
            except sqlite3.IntegrityError:
                # UNIQUE(assistant_message_id) — already applied by another path
                conn.rollback()
                conn.close()
                return True
            except sqlite3.OperationalError as e:
                if "locked" in str(e).lower() or "BUSY" in str(e).upper():
                    conn.rollback()
                    time.sleep(RETRY_BACKOFF * (2 ** attempt))
                    continue
                raise
        else:
            conn.rollback()
            conn.close()
            return False

        # Validate all proposals first
        rejection_reasons: list[str] = []
        state = dict(current_state)
        for p in proposals:
            if p.action == "none":
                continue
            if p.action == "method_lock":
                stage = state.get("stage")
                if not stage:
                    rejection_reasons.append("method_lock: no current stage")
                    continue
                methods = get_stage_methods(stage, conn=conn)
                if any(m["method_name"] == p.method_name and m["locked"] for m in methods):
                    rejection_reasons.append(f"method_lock: {p.method_name} already locked")
            elif p.action == "stage_transition":
                if p.stage not in STAGE_NAMES:
                    rejection_reasons.append(f"stage_transition: {p.stage} not in STAGE_NAMES")

        if rejection_reasons:
            update_state_event_result(conn, assistant_message_id, applied=False, rejection_reason="; ".join(rejection_reasons))
            conn.commit()
            conn.close()
            return False

        # Apply all in same txn
        expected_version = current_state.get("version", 1)
        for p in proposals:
            if p.action == "none":
                continue
            if p.action == "method_lock":
                stage = current_state.get("stage")
                upsert_method(stage, p.method_number or 0, p.method_name or "", conn=conn)
                lock_method(stage, p.method_name or "", conn=conn)
                update_system_state(conn=conn, last_hardened=p.method_name or "")
                run = get_current_run(conn=conn)
                if run:
                    promote_mastery(run["run_number"], stage, p.method_name or "", conn=conn)
                current_state = dict(get_system_state(conn))
            elif p.action == "stage_transition":
                ok = update_system_state_with_version(
                    conn,
                    expected_version,
                    stage=p.stage,
                    stage_name=STAGE_NAMES[p.stage],
                )
                if not ok:
                    update_state_event_result(conn, assistant_message_id, applied=False, rejection_reason="stage_transition: version mismatch")
                    conn.commit()
                    conn.close()
                    return False
                current_state = dict(get_system_state(conn))
                expected_version = current_state.get("version", 1)

        applied = True
        update_state_event_result(
            conn,
            assistant_message_id,
            applied=applied,
            rejection_reason="; ".join(rejection_reasons) if rejection_reasons else None,
        )
        conn.commit()
        return applied
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
