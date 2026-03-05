"""
Transition engine (FSM): validates and applies proposed state transitions.
Only the engine mutates system state; parser never touches the DB.
"""

import hashlib
import json
import sqlite3
import time
from typing import List, Optional

from state_schema import ProposedTransition
from topics import TOPIC_MENU
import db

# Version constants for state_events (observability)
PROMPT_VERSION = "7"
PARSER_VERSION = "1"
TOPICS_SCHEMA_VERSION = "1"
MASTERY_SCHEMA_VERSION = "1"

MAX_RETRIES = 5
INITIAL_BACKOFF_S = 0.05


def _hash_state(state: dict) -> str:
    """Canonical hash of system_state (sorted keys, JSON)."""
    # Exclude 'updated_at' for reproducibility if desired, or include for full fingerprint
    canonical = {k: state[k] for k in sorted(state.keys())}
    return hashlib.sha256(json.dumps(canonical, sort_keys=True).encode()).hexdigest()


def _guard_lock(conn, proposal: ProposedTransition, state: dict) -> Optional[str]:
    """Returns None if allowed, else rejection reason."""
    topic = state.get("topic", "None")
    category = state.get("category", "general")
    concepts = db.get_topic_concepts(topic, category, conn=conn)
    concept_names = {c["concept_name"] for c in concepts}
    if proposal.concept_name and proposal.concept_name not in concept_names:
        # Concept might not exist yet; allow if in decomposition or we'll create via upsert
        decomp = state.get("decomposition") or "[]"
        try:
            decomp_list = json.loads(decomp) if isinstance(decomp, str) else decomp
        except (json.JSONDecodeError, TypeError):
            decomp_list = []
        if proposal.concept_name not in decomp_list and proposal.concept_name not in concept_names:
            return f"concept {proposal.concept_name!r} not in topic decomposition or concept list"
    # Check not already locked
    for c in concepts:
        if c["concept_name"] == proposal.concept_name and c.get("locked"):
            return f"concept {proposal.concept_name!r} already locked"
    return None


def _guard_announce(conn, proposal: ProposedTransition, state: dict) -> Optional[str]:
    """Optional: concept exists in topic. Allow if in decomposition or concept list."""
    topic = state.get("topic", "None")
    category = state.get("category", "general")
    concepts = db.get_topic_concepts(topic, category, conn=conn)
    concept_names = {c["concept_name"] for c in concepts}
    decomp = state.get("decomposition") or "[]"
    try:
        decomp_list = json.loads(decomp) if isinstance(decomp, str) else decomp
    except (json.JSONDecodeError, TypeError):
        decomp_list = []
    if proposal.concept_name in concept_names or proposal.concept_name in decomp_list:
        return None
    return None  # Allow announce even if new (engine may allow)


def _guard_decompose(proposal: ProposedTransition, state: dict) -> Optional[str]:
    """Reject if already decomposed (non-empty). Spec says 'not already decomposed'."""
    decomp = state.get("decomposition") or "[]"
    try:
        decomp_list = json.loads(decomp) if isinstance(decomp, str) else decomp
    except (json.JSONDecodeError, TypeError):
        decomp_list = []
    if decomp_list:
        return "topic already has decomposition; overwrite not allowed"
    return None


def _guard_topic_change(proposal: ProposedTransition) -> Optional[str]:
    """Topic must be in TOPIC_MENU."""
    if proposal.topic not in TOPIC_MENU:
        return f"topic {proposal.topic!r} not in allowed topic list"
    return None


def _apply_one(conn, proposal: ProposedTransition, state: dict, updates: dict) -> Optional[str]:
    """
    Apply a single transition into `updates` (for system_state) and run side effects (upsert_concept, lock_concept).
    Returns None on success, or rejection reason.
    """
    topic = state.get("topic", "None")
    category = state.get("category", "general")

    if proposal.rejection_reason:
        return proposal.rejection_reason

    if proposal.action == "lock":
        if proposal.parser_mode == "regex":
            return "regex fallback cannot perform lock (destructive action not allowed)"
        err = _guard_lock(conn, proposal, state)
        if err:
            return err
        db.upsert_concept(
            topic,
            proposal.concept_number or 0,
            proposal.concept_name or "",
            category,
            conn=conn,
        )
        db.lock_concept(topic, proposal.concept_name, conn=conn)
        updates["last_locked"] = proposal.concept_name
        # Mastery derived from accumulated data only (not from model)
        run = db.get_current_run(conn=conn)
        run_number = run["run_number"] if run else 1
        db.promote_mastery(run_number, topic, proposal.concept_name or "", conn=conn)
        return None

    if proposal.action == "announce":
        err = _guard_announce(conn, proposal, state)
        if err:
            return err
        updates["current_concept"] = proposal.concept_name or ""
        return None

    if proposal.action == "decompose":
        err = _guard_decompose(proposal, state)
        if err:
            return err
        updates["decomposition"] = json.dumps(proposal.decomposition or [])
        return None

    if proposal.action == "topic_change":
        err = _guard_topic_change(proposal)
        if err:
            return err
        updates["topic"] = proposal.topic or "None"
        updates["current_concept"] = "None"
        return None

    return f"unknown action: {proposal.action}"


def apply_transitions(
    assistant_message_id: int,
    proposals: List[ProposedTransition],
    current_state: dict,
    prompt_version: Optional[str] = None,
) -> tuple[bool, Optional[str]]:
    """
    Validate and apply proposed transitions for one assistant message.
    Idempotent: if assistant_message_id already in state_events, returns (True, "idempotent") without applying.
    Returns (success, rejection_reason). rejection_reason set only on failure.
    """
    prompt_version = prompt_version or PROMPT_VERSION
    proposed_state_json = json.dumps([p.to_dict() for p in proposals])
    prior_state_hash = _hash_state(current_state)
    expected_version = current_state.get("version", 1)

    for attempt in range(MAX_RETRIES):
        conn = db.get_conn()
        try:
            conn.execute("BEGIN")
            # Idempotency: insert state_events; if UNIQUE violation, already processed
            parser_mode = proposals[0].parser_mode if proposals else "json"
            try:
                event_id = db.insert_state_event(
                    conn,
                    assistant_message_id,
                    prior_state_hash,
                    proposed_state_json,
                    parser_mode,
                    prompt_version,
                    parser_version=PARSER_VERSION,
                    topics_schema_version=TOPICS_SCHEMA_VERSION,
                    mastery_schema_version=MASTERY_SCHEMA_VERSION,
                )
            except sqlite3.IntegrityError:
                conn.rollback()
                conn.close()
                return True, None  # idempotent: already applied

            # Skip proposals that are already rejected by parser (e.g. schema validation failed)
            updates = {}
            for p in proposals:
                if p.rejection_reason:
                    db.update_state_event_result(conn, event_id, applied=0, rejection_reason=p.rejection_reason)
                    conn.rollback()
                    conn.close()
                    return False, p.rejection_reason
                reason = _apply_one(conn, p, current_state, updates)
                if reason:
                    db.update_state_event_result(conn, event_id, applied=0, rejection_reason=reason)
                    conn.rollback()
                    conn.close()
                    return False, reason

            # Apply accumulated system_state update with version check (only if we have changes)
            if updates:
                ok = db.update_system_state_with_version(conn, expected_version, **updates)
                if not ok:
                    db.update_state_event_result(conn, event_id, applied=0, rejection_reason="state version mismatch")
                    conn.rollback()
                    conn.close()
                    return False, "state version mismatch"

            db.update_state_event_result(conn, event_id, applied=1)
            conn.commit()
            conn.close()
            return True, None

        except sqlite3.OperationalError as e:
            conn.rollback()
            conn.close()
            if "SQLITE_BUSY" in str(e) or "locked" in str(e).lower():
                if attempt < MAX_RETRIES - 1:
                    time.sleep(INITIAL_BACKOFF_S * (2 ** attempt))
                    continue
            return False, str(e)

    return False, "max retries exceeded"
