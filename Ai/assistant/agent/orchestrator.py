"""Two-phase orchestrator: conversation first, extraction second."""
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from openai import OpenAI

from config import OPENAI_API_KEY, MODEL
from db.database import get_connection
from events.event_store import append_event
from events.projector import project_event

PROMPTS_DIR = Path(__file__).parent / "prompts"

ALLOWED_EVENT_TYPES = {
    "TASK_CREATED", "TASK_UPDATED", "TASK_COMPLETED",
    "GOAL_CREATED", "GOAL_UPDATED",
    "TIME_LOGGED", "NOTE_RECORDED",
}

ISO = lambda: datetime.now(timezone.utc).isoformat()


# --------------------------------------------------
# DB helpers
# --------------------------------------------------

def ensure_conversation(conversation_id: Optional[str] = None) -> str:
    """Create or verify a conversation row. Does NOT update last_active_at —
    that happens after day-context detection so gap detection sees the real gap."""
    conv_id = conversation_id or str(uuid.uuid4())
    now = ISO()
    conn = get_connection()
    try:
        row = conn.execute("SELECT id FROM conversations WHERE id = ?", (conv_id,)).fetchone()
        if not row:
            conn.execute(
                "INSERT INTO conversations (id, summary, started_at, last_active_at) VALUES (?, '', ?, ?)",
                (conv_id, now, now),
            )
            conn.commit()
    finally:
        conn.close()
    return conv_id


def touch_conversation(conversation_id: str):
    """Update last_active_at AFTER day-context has been read."""
    conn = get_connection()
    try:
        conn.execute("UPDATE conversations SET last_active_at = ? WHERE id = ?", (ISO(), conversation_id))
        conn.commit()
    finally:
        conn.close()


def save_message(conversation_id: str, role: str, content: str) -> str:
    msg_id = str(uuid.uuid4())
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO messages (id, conversation_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
            (msg_id, conversation_id, role, content, ISO()),
        )
        conn.commit()
    finally:
        conn.close()
    return msg_id


def load_history(conversation_id: str, limit: int = 20) -> List[Dict[str, str]]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY created_at DESC LIMIT ?",
            (conversation_id, limit),
        ).fetchall()
    finally:
        conn.close()
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]


def load_summary(conversation_id: str) -> str:
    conn = get_connection()
    try:
        row = conn.execute("SELECT summary FROM conversations WHERE id = ?", (conversation_id,)).fetchone()
    finally:
        conn.close()
    return row[0] if row else ""


def save_summary(conversation_id: str, summary: str):
    conn = get_connection()
    try:
        conn.execute("UPDATE conversations SET summary = ? WHERE id = ?", (summary, conversation_id))
        conn.commit()
    finally:
        conn.close()


def count_messages(conversation_id: str) -> int:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT COUNT(*) FROM messages WHERE conversation_id = ?", (conversation_id,)
        ).fetchone()
    finally:
        conn.close()
    return row[0] if row else 0


def fetch_state_context() -> Dict[str, Any]:
    conn = get_connection()
    try:
        goals = [
            {"goal_id": r[0], "title": r[1]}
            for r in conn.execute("SELECT goal_id, title FROM goals ORDER BY updated_at DESC LIMIT 10").fetchall()
        ]
        tasks = [
            {"task_id": r[0], "title": r[1], "status": r[2]}
            for r in conn.execute(
                "SELECT task_id, title, status FROM tasks WHERE status NOT IN ('done','completed','canceled') ORDER BY updated_at DESC LIMIT 25"
            ).fetchall()
        ]
        time_logs = [
            {"duration_minutes": r[0], "logged_at": r[1]}
            for r in conn.execute("SELECT duration_minutes, logged_at FROM time_logs ORDER BY logged_at DESC LIMIT 10").fetchall()
        ]
        return {"goals": goals, "tasks": tasks, "recent_time_logs": time_logs}
    finally:
        conn.close()


# --------------------------------------------------
# Context loaders
# --------------------------------------------------

def _load_prompt(name: str) -> str:
    path = PROMPTS_DIR / name
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def load_profile() -> str:
    path = Path(__file__).parent / "profile.txt"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def detect_day_context(conversation_id: str) -> str:
    """Check last_active_at, compute overdue tasks, gap days."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT last_active_at FROM conversations WHERE id = ?",
            (conversation_id,)
        ).fetchone()

        if not row or not row[0]:
            return ""

        last = datetime.fromisoformat(row[0])
        now = datetime.now(timezone.utc)
        gap_days = (now - last).days

        # Overdue tasks (created > 7 days ago, still todo)
        overdue = conn.execute(
            "SELECT title FROM tasks WHERE status = 'todo' "
            "AND julianday('now') - julianday(created_at) > 7"
        ).fetchall()

        # Week metrics
        tasks_created = conn.execute(
            "SELECT COUNT(*) FROM events WHERE event_type = 'TASK_CREATED' "
            "AND created_at > datetime('now', '-7 days')"
        ).fetchone()[0]
        tasks_completed = conn.execute(
            "SELECT COUNT(*) FROM events WHERE event_type = 'TASK_COMPLETED' "
            "AND created_at > datetime('now', '-7 days')"
        ).fetchone()[0]
        time_this_week = conn.execute(
            "SELECT COALESCE(SUM(duration_minutes), 0) FROM time_logs "
            "WHERE logged_at > datetime('now', '-7 days')"
        ).fetchone()[0]

        parts = []
        if gap_days >= 2:
            parts.append(f"INACTIVITY GAP: {gap_days} days since last conversation.")
        if overdue:
            titles = [r[0] for r in overdue]
            parts.append(f"OVERDUE TASKS (open >7 days): {', '.join(titles)}")
        parts.append(
            f"WEEK METRICS: {tasks_created} tasks created, "
            f"{tasks_completed} completed, "
            f"{int(time_this_week)} min logged"
        )
        return "\n".join(parts) if parts else ""
    finally:
        conn.close()


def load_known_facts(limit: int = 15) -> str:
    """Pull recent NOTE_RECORDED events with identity/preference/constraint categories."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT payload FROM events WHERE event_type = 'NOTE_RECORDED' "
            "ORDER BY created_at DESC LIMIT ?", (limit * 3,)
        ).fetchall()

        facts = []
        for r in rows:
            try:
                p = json.loads(r[0])
                cat = p.get("category", "")
                if cat in ("identity", "preference", "constraint", "commitment", "reflection", "progress"):
                    facts.append(f"[{cat}] {p.get('content', '')}")
            except Exception:
                pass
        return "\n".join(facts[:limit]) if facts else ""
    finally:
        conn.close()


# --------------------------------------------------
# Phase 1: Conversational reply (always works)
# --------------------------------------------------

def phase1_reply(
    user_text: str,
    history: List[Dict[str, str]],
    summary: str,
    state: Dict[str, Any],
    profile: str,
    day_context: str,
    known_facts: str,
) -> str:
    client = OpenAI(api_key=OPENAI_API_KEY)
    system_prompt = _load_prompt("chat.txt")

    context_parts = []
    if profile:
        context_parts.append(f"USER PROFILE:\n{profile}")
    if summary:
        context_parts.append(f"CONVERSATION SUMMARY:\n{summary}")
    if known_facts:
        context_parts.append(f"KNOWN FACTS & PREFERENCES:\n{known_facts}")
    if state["tasks"] or state["goals"]:
        context_parts.append(f"CURRENT STATE:\n{json.dumps(state, ensure_ascii=False)}")
    if day_context:
        context_parts.append(f"DAY CONTEXT:\n{day_context}")

    messages = [{"role": "system", "content": system_prompt}]
    if context_parts:
        messages.append({"role": "system", "content": "\n\n".join(context_parts)})
    messages.extend(history)
    messages.append({"role": "user", "content": user_text})

    resp = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.7,
    )
    return resp.choices[0].message.content


# --------------------------------------------------
# Phase 2: Silent extraction (best effort)
# --------------------------------------------------

def phase2_extract(user_text: str, assistant_reply: str, state: Dict[str, Any], source_message_id: str):
    client = OpenAI(api_key=OPENAI_API_KEY)
    system_prompt = _load_prompt("extract.txt")

    extract_input = f"USER MESSAGE:\n{user_text}\n\nASSISTANT REPLY:\n{assistant_reply}"
    if state["tasks"] or state["goals"]:
        extract_input += f"\n\nCURRENT STATE:\n{json.dumps(state, ensure_ascii=False)}"

    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": extract_input},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        obj = json.loads(resp.choices[0].message.content)
        events = obj.get("events", [])
        if not isinstance(events, list):
            return

        for ev in events:
            if not isinstance(ev, dict):
                continue
            event_type = ev.get("event_type")
            payload = ev.get("payload")
            if not isinstance(event_type, str) or event_type not in ALLOWED_EVENT_TYPES:
                continue
            if not isinstance(payload, dict):
                continue

            # Auto-generate IDs
            if event_type == "TASK_CREATED":
                payload.setdefault("task_id", str(uuid.uuid4()))
            elif event_type == "GOAL_CREATED":
                payload.setdefault("goal_id", str(uuid.uuid4()))

            now = ISO()
            eid = append_event(event_type, payload, source_message_id)
            project_event(event_type, payload, now)

    except Exception:
        pass


# --------------------------------------------------
# Summary update (every ~10 turns)
# --------------------------------------------------

def maybe_update_summary(conversation_id: str):
    msg_count = count_messages(conversation_id)
    if msg_count < 20 or msg_count % 20 != 0:
        return

    history = load_history(conversation_id, limit=40)
    current_summary = load_summary(conversation_id)

    client = OpenAI(api_key=OPENAI_API_KEY)
    prompt = "Update the rolling summary of this conversation. Keep it under 300 words. Focus on: who the user is, their goals, preferences, ongoing tasks, and key facts they've shared."
    messages = [
        {"role": "system", "content": prompt},
    ]
    if current_summary:
        messages.append({"role": "system", "content": f"PREVIOUS SUMMARY:\n{current_summary}"})
    messages.append({"role": "user", "content": "\n".join(f"{m['role']}: {m['content']}" for m in history)})

    try:
        resp = client.chat.completions.create(model=MODEL, messages=messages, temperature=0.3)
        save_summary(conversation_id, resp.choices[0].message.content)
    except Exception:
        pass


# --------------------------------------------------
# Orchestrator entrypoint
# --------------------------------------------------

def run_turn(conversation_id: Optional[str], user_text: str) -> Tuple[str, str]:
    conv_id = ensure_conversation(conversation_id)

    # Day boundary check BEFORE updating last_active_at
    day_context = detect_day_context(conv_id) if conversation_id else ""

    # Now update last_active_at
    touch_conversation(conv_id)

    user_msg_id = save_message(conv_id, "user", user_text)
    history = load_history(conv_id, limit=20)
    summary = load_summary(conv_id)
    state = fetch_state_context()
    profile = load_profile()
    known_facts = load_known_facts()

    # Phase 1: always respond conversationally
    try:
        reply = phase1_reply(user_text, history, summary, state, profile, day_context, known_facts)
    except Exception:
        reply = "Hey, I'm having trouble connecting right now. Your message is saved — I'll be back shortly!"

    save_message(conv_id, "assistant", reply)

    # Phase 2: silently extract structured data
    phase2_extract(user_text, reply, state, user_msg_id)

    # Periodically update rolling summary
    maybe_update_summary(conv_id)

    return conv_id, reply


def chat(user_message: str, conversation_id: Optional[str] = None) -> Tuple[str, str]:
    """Returns (conversation_id, assistant_reply)."""
    return run_turn(conversation_id, user_message)
