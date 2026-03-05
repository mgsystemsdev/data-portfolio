import os
import json
from config import DOCS_DIR
from db import get_system_state, get_topic_concepts, get_learner_identity
from learner_analytics import build_learner_context, _build_learner_identity_context
from topics import get_enforcement_layer, TOPIC_MENU


def _read_doc(filename):
    path = os.path.join(DOCS_DIR, filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def _format_system_state():
    """Format system state for prompt. Uses safe defaults on any failure."""
    try:
        state = get_system_state()
    except Exception:
        state = {}
    if not state:
        state = {"topic": "None", "category": "general", "current_concept": "None", "last_locked": "None", "run_number": 1}

    topic = state.get("topic", "None")
    category = state.get("category", "general")
    current_concept = state.get("current_concept", "None")
    last_locked = state.get("last_locked", "None")
    run_number = state.get("run_number", 1)

    try:
        concepts = get_topic_concepts(topic, category)
    except Exception:
        concepts = []
    locked = [c.get("concept_name", "") for c in concepts if c.get("locked")]
    remaining = [c.get("concept_name", "") for c in concepts if not c.get("locked")]

    try:
        decomposition = json.loads(state.get("decomposition", "[]"))
    except (json.JSONDecodeError, TypeError):
        decomposition = []
    if not isinstance(decomposition, list):
        decomposition = []

    category_display = "All categories" if category in ("general", "None") else category
    lines = [
        "",
        "━━━━━━━━━━━━━━━━━━━━",
        "📌 CURRENT SYSTEM STATE",
        "━━━━━━━━━━━━━━━━━━━━",
        f"📚 Topic:           {topic}",
        f"📂 Category:        {category_display}",
        f"🎯 Current Concept: {current_concept}",
        f"🔒 Last Locked:     {last_locked}",
        f"🔁 Run:             {run_number}",
        "━━━━━━━━━━━━━━━━━━━━",
    ]

    if category in ("general", "None") and topic and topic != "None":
        cats = TOPIC_MENU.get(topic, [])
        if cats:
            lines.append(f"Categories for this topic (in sequence): {', '.join(cats)}")

    if decomposition:
        lines.append(f"Full decomposition map: {', '.join(str(x) for x in decomposition)}")
    if locked:
        lines.append(f"Locked concepts: {', '.join(locked)}")
    if remaining:
        lines.append(f"Remaining concepts: {', '.join(remaining)}")
        lines.append(f"Next concept: {remaining[0]}")

    return "\n".join(lines)


def _build_concept_progress_summary():
    """Build a summary of ALL locked concepts across ALL topics for cross-session memory. Safe defaults on failure."""
    try:
        from db import get_conn
        conn = get_conn()
        rows = conn.execute("""
            SELECT topic, category, concept_name, locked, attempts, locked_at
            FROM concept_progress
            ORDER BY topic, category, concept_number
        """).fetchall()
        conn.close()
    except Exception:
        return "No concepts have been started yet."

    if not rows:
        return "No concepts have been started yet."

    lines = ["── CONCEPT PROGRESS (ALL TOPICS) ──"]
    current_topic = None
    current_category = None
    for r in rows:
        if r["topic"] != current_topic:
            current_topic = r["topic"]
            current_category = None
            lines.append(f"\n{current_topic}:")
        if r["category"] != current_category:
            current_category = r["category"]
            if current_category != "general":
                lines.append(f"  [{current_category}]")
        icon = "✅" if r["locked"] else "⬜"
        extra = f" (locked {r['locked_at']})" if r["locked"] else f" (attempts: {r['attempts']})"
        indent = "    " if current_category != "general" else "  "
        lines.append(f"{indent}{icon} {r['concept_name']}{extra}")

    return "\n".join(lines)


def _build_resume_context():
    """Build a short summary of where the learner left off. Safe defaults on failure."""
    try:
        state = get_system_state() or {}
    except Exception:
        state = {}
    try:
        from db import get_conn
        conn = get_conn()
        total_locked = conn.execute(
            "SELECT COUNT(*) as c FROM concept_progress WHERE locked = 1"
        ).fetchone()["c"]

        last_concept = conn.execute(
            "SELECT topic, concept_name, locked_at FROM concept_progress WHERE locked = 1 ORDER BY locked_at DESC LIMIT 1"
        ).fetchone()

        next_concept = conn.execute(
            "SELECT topic, concept_name FROM concept_progress WHERE locked = 0 ORDER BY topic, concept_number LIMIT 1"
        ).fetchone()

        session_count = conn.execute("SELECT COUNT(*) as c FROM sessions").fetchone()["c"]
        conn.close()
    except Exception:
        total_locked = 0
        last_concept = None
        next_concept = None
        session_count = 0

    lines = ["── RESUME CONTEXT ──"]
    lines.append(f"Session number: {session_count}")
    lines.append(f"Current topic: {state.get('topic', 'None')} / {state.get('category', 'None')}")
    lines.append(f"Current concept: {state.get('current_concept', 'None')}")
    lines.append(f"Total concepts locked: {total_locked}")

    if last_concept:
        lines.append(
            f"Last locked concept: {last_concept['concept_name']} "
            f"in {last_concept['topic']} (at {last_concept['locked_at']})"
        )

    if next_concept:
        lines.append(
            f"Next concept to teach: {next_concept['concept_name']} in {next_concept['topic']}"
        )
    elif total_locked > 0:
        lines.append("All tracked concepts are locked. Start a new topic.")

    return "\n".join(lines)


def build_system_prompt():
    """Assemble the full system prompt from all documents + state + learner profile. Defensive: safe defaults on any failure."""
    prompt_v7 = _read_doc("prompt_v7.md") or ""
    knowledge = _read_doc("knowledge_file_v7.md") or ""
    system_state = _format_system_state()

    try:
        learner_context = build_learner_context()
    except Exception:
        learner_context = ""
    try:
        concept_progress = _build_concept_progress_summary()
    except Exception:
        concept_progress = "No concept progress available."
    try:
        resume_context = _build_resume_context()
    except Exception:
        resume_context = "Resume context unavailable."
    try:
        identity_context = _build_learner_identity_context()
    except Exception:
        identity_context = ""

    # Load enforcement layer dynamically from topic metadata (no hardcoded topic conditionals)
    try:
        state = get_system_state() or {}
        layer_name = get_enforcement_layer(state.get("topic", ""))
        if layer_name == "python_mastery":
            from python_mastery import PRIMARY_LANGUAGE_RULES
            python_layer = PRIMARY_LANGUAGE_RULES
        else:
            python_layer = ""
    except Exception:
        python_layer = ""

    parts = [
        prompt_v7,
        "",
        python_layer,
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "📚 KNOWLEDGE FILE — REFERENCE THROUGHOUT SESSION",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        knowledge,
        "",
        system_state,
        "",
        concept_progress,
        "",
        learner_context,
        "",
        resume_context,
        "",
        identity_context,
    ]

    return "\n".join(parts)
