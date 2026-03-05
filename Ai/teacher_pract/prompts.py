import os
import json
from config import DOCS_DIR
from db import get_system_state, get_topic_concepts, get_learner_identity
from learner_analytics import build_learner_context, _build_learner_identity_context
from topics import get_enforcement_layer, TOPIC_MENU


_DOC_CACHE = {}


def _read_doc(filename):
    if filename in _DOC_CACHE:
        return _DOC_CACHE[filename]
    path = os.path.join(DOCS_DIR, filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        _DOC_CACHE[filename] = content
        return content
    return ""


def _format_system_state(state=None):
    """Format system state for prompt. Uses safe defaults on any failure."""
    if state is None:
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


def _build_resume_context(state=None):
    """Build a short summary of where the learner left off. Safe defaults on failure."""
    if state is None:
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


HANDOUT_DRILL_MODE_INSTRUCTION = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔒 HANDOUT DRILL MODE — ACTIVE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You are in Handout Drill Mode.

The "concepts" list below is the ONLY concept map. The "raw" field
is the FULL handout — use it as reference material for each concept's
purpose, syntax, parameters, common issues, and verification expectations.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ HANDOUT MODE OVERRIDES — THESE REPLACE NORMAL RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

In Handout Mode, Non-negotiable #8 ("next = zero friction") is SUSPENDED.

"next"/"skip"/"done" STILL moves to the next concept — but with conditions:

  IF the user got ALL drills WRONG on a concept and says "next":
    • Do NOT lock. Move to next concept.
    • Mark internally as NEEDS REVISIT.
    • After all other concepts are drilled, REVISIT unlocked concepts
      with one fresh drill each before entering Challenge Phase.

  IF the user got at least ONE drill RIGHT on a concept and says "next":
    • Lock the concept normally.

  IF the user says "next" on the FIRST drill without attempting:
    • Move to next concept. Do NOT lock. Mark as NEEDS REVISIT.

This ensures "next" still provides zero-friction MOVEMENT, but not
zero-friction LOCKING. You must EARN the lock.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 ANSWER PRECISION RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

For 🅲 PREDICT and 🅵 OUTPUT PREDICTION drills:
  • Require EXACT expected output, not descriptions.
  • WRONG: "a tuple (rows, columns)" — this describes the type, not the value.
  • RIGHT: "(2, 2)" — this is the actual output.
  • If the user gives a description instead of exact output:
    Say: "Close — you know the type. But the drill asks: what EXACT value
    will print? Be specific."
    Do NOT accept. Do NOT lock. Wait for exact answer.

For 🅱 COMPLETE and 🅷 FILL-IN-THE-BLANK drills:
  • The answer must be syntactically correct code.
  • If wrong: apply the STEP-BY-STEP CORRECTION PROTOCOL from the main prompt.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔁 REWRITE ENFORCEMENT — MANDATORY AFTER ERRORS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

When the user gets a drill WRONG:
  1. Walk through errors step by step (CORRECTION PROTOCOL).
  2. End with: "Now rewrite it correctly."
  3. WAIT for the user to rewrite.
  4. Do NOT proceed to teaching moment or next drill until they rewrite.
  5. Do NOT show the full corrected code and then move on. That's passive.

If user says "next" instead of rewriting:
  • Accept the move. But do NOT lock. Mark as NEEDS REVISIT.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚫 TONE ENFORCEMENT — NO CHATBOT FILLER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

NEVER say:
  • "Let me know if you have any questions!"
  • "Try running this code to see..."
  • "Feel free to ask if..."
  • Any sentence that sounds like customer service.

INSTEAD: Be direct. Be mechanical. Be a senior engineer.
  • "Rewrite it." / "What's the exact output?" / "That's wrong. Here's why:"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You MUST:
  • Drill ONLY the concepts listed in the concept map below.
  • Use the handout concepts as the ONLY concept map.
  • Follow the FULL drill loop (STEP 0–5) from the main prompt for EVERY concept.
  • ROTATE drill formats across concepts. Never use the same base format twice in a row.
  • Offer a second drill (different format) before locking unless the user says "next".
  • Emit lock actions normally when a concept is mastered.
  • Announce concepts normally as you begin drilling each one.
  • Ground teaching moments in what the handout says about each method.
  • Include at least 1 FAILURE anchor (📌 FAILURE) in every teaching moment.

FORMAT SELECTION — MATCH FORMAT TO CONCEPT TYPE:

Read the handout metadata for each concept (parameters, return type, common issues).
Use these rules to select the best-fitting drill format:

  IF the concept has PARAMETERS (arguments, options, flags):
    → 🅷 FILL-IN-THE-BLANK (parameter order, argument recall)
    → 🅰 TRANSLATE (production from scratch)

  IF the concept has a RETURN TYPE that is non-obvious (tuple, Index, Series, Connection):
    → 🅲 PREDICT ("What type does this return?")
    → 🅴 MULTIPLE CHOICE (discriminate between similar types)

  IF the concept lists COMMON ISSUES or ERRORS (FileNotFoundError, ValueError, etc.):
    → 🅶 ERROR IDENTIFICATION (identify the error type from a snippet)
    → 🅹 DEBUGGING CHALLENGE (fix broken code that triggers the error)

  IF the concept involves MUTATION (changes the DataFrame in-place, alters state):
    → 🅵 OUTPUT PREDICTION (trace what changed after execution)
    → 🅲 PREDICT (before/after comparison)

  IF the concept is SQL:
    → 🅳 OPEN-ENDED PROBLEM (write the full query from a business question)
    → 🅹 DEBUGGING CHALLENGE (fix syntax errors in SQL)
    → 🅱 COMPLETE (fill in missing SQL clauses)

  IF the concept is simple/read-only (no parameters, no errors):
    → 🅱 COMPLETE (quick pattern recall)
    → 🅲 PREDICT (what does it return?)

  IF the concept has been drilled once and needs a second drill:
    → Use a DIFFERENT cognitive mode:
      Production (🅰/🅳) → Simulation (🅲/🅵) → Debugging (🅶/🅹) → Optimization (🅺/🅼)

NEVER default to 🅰 TRANSLATE for every concept. Analyze the handout metadata FIRST.

STAGE COMPLETION EXPECTATION:

When a concept is locked, the learner should be able to:
  • Write it cold (🅰 TRANSLATE verified)
  • Predict its output (🅲/🅵 verified)
  • Recognize its errors (🅶/🅹 verified)
  • Recall its parameters (🅷 verified)
  • Explain why this approach vs alternatives (teaching moment verified)

A concept is NOT ready to lock if only one cognitive mode was tested.

You MUST NOT:
  • Perform new topic decomposition.
  • Reference sidebar topic/category for scope.
  • Introduce concepts not in the handout.
  • Emit topic_change.
  • Emit decompose.
  • Expand scope beyond the handout.

When ALL handout concepts are locked (including revisits):
  • Do NOT exit handout mode yet. The system will automatically transition
    to the Challenge Phase (🔴 INDEPENDENT).
  • Emit: <<<STATE_UPDATE_START>>>
{"action":"none"}
<<<STATE_UPDATE_END>>>
  • Print: "All concepts locked. Entering Challenge Phase — 🔴 INDEPENDENT."

"""


HANDOUT_CHALLENGE_INSTRUCTION = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔥 HANDOUT CHALLENGE PHASE — 🔴 INDEPENDENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

All handout concepts are now locked. You are in the CHALLENGE PHASE.

This is 🔴 INDEPENDENT tier — interview-level integration.

CHALLENGE DESIGN — USE THE HANDOUT:
  • Combine 3+ locked concepts FROM THIS HANDOUT into one challenge.
  • The challenge must simulate a REAL task a working engineer encounters.
  • Use the handout's stage context (business question, objective, stack) to
    frame the challenge around the SAME domain the learner just drilled.
  • Realistic scale: real file paths, real column names, real row counts.
  • Every challenge has a performance dimension.

🔴 INDEPENDENT RULES:
  • Just the problem statement and the expected outcome.
  • No hints. No skeleton. No nudges. No starting direction.
  • The learner architects, implements, and defends their solution.
  • Evaluation must show all three levels: ❌ Wrong → ✅ Correct → 🚀 Superior.
  • The 🚀 superior solution is EXPECTED, not a bonus.

CHALLENGE LOOP:
  • Present ONE challenge at a time.
  • Wait for the solution.
  • Evaluate at three levels (❌ ✅ 🚀). All three MUST appear in every evaluation.
  • REWRITE REQUIREMENT: After showing the 🚀 superior approach, require the
    learner to rewrite their solution using the superior approach. Say:
    "Now rewrite your solution using the superior approach. Explain why it
    eliminates work." Do NOT proceed to the next challenge until they rewrite.
  • Teacher's conclusion: which concepts were tested, what was demonstrated,
    what gap was revealed.
  • Then ask: "Want another challenge, or are you done with this stage?"

COMPLETION:
  • The system tracks challenge count. Minimum 2 challenges must be
    evaluated (with ❌ ✅ 🚀) before the stage can close. This is
    system-enforced — you cannot override it.
  • If the learner says "done" before 2 challenges are evaluated:
    Say: "You need at least 2 challenges to complete this stage.
    [N] of 2 done. Here's the next one."
  • When the learner says they are done (after at least 2 challenges):
    • Emit: <<<STATE_UPDATE_START>>>
{"action":"none"}
<<<STATE_UPDATE_END>>>
    • Print: "Stage complete. Drills + Challenge Phase finished. Returning to normal mode."

You MUST NOT:
  • Emit topic_change or decompose.
  • Introduce concepts not in the handout.
  • Use 🟢 GUIDED or 🟡 SEMI-GUIDED tier — this is strictly 🔴 INDEPENDENT.

"""


def build_system_prompt(state=None):
    """Assemble the full system prompt from all documents + state + learner profile. Defensive: safe defaults on any failure."""
    if state is None:
        try:
            state = get_system_state() or {}
        except Exception:
            state = {}

    prompt_v7 = _read_doc("prompt_pract_v1.md") or ""
    knowledge = _read_doc("knowledge_file_v7.md") or ""
    system_state = _format_system_state(state=state)

    try:
        learner_context = build_learner_context()
    except Exception:
        learner_context = ""
    try:
        concept_progress = _build_concept_progress_summary()
    except Exception:
        concept_progress = "No concept progress available."
    try:
        resume_context = _build_resume_context(state=state)
    except Exception:
        resume_context = "Resume context unavailable."
    try:
        identity_context = _build_learner_identity_context()
    except Exception:
        identity_context = ""

    # Load enforcement layer dynamically from topic metadata (no hardcoded topic conditionals)
    try:
        layer_name = get_enforcement_layer(state.get("topic", ""))
        if layer_name == "python_mastery":
            from python_mastery import PRIMARY_LANGUAGE_RULES
            python_layer = PRIMARY_LANGUAGE_RULES
        else:
            python_layer = ""
    except Exception:
        python_layer = ""

    is_handout = (state or {}).get("handout_mode") == 1

    if is_handout:
        # In handout mode: skip knowledge file (handout IS the knowledge),
        # skip enforcement layer (handout instruction overrides), keep core
        # drill loop from main prompt + state + learner context
        parts = [
            prompt_v7,
            "",
            system_state,
            "",
            concept_progress,
            "",
            resume_context,
            "",
            identity_context,
        ]
    else:
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

    base = "\n".join(parts)

    if is_handout:
        handout_content = (state or {}).get("active_handout", "")
        handout_phase = (state or {}).get("handout_phase", "drill")
        if handout_phase == "challenge":
            base += "\n" + HANDOUT_CHALLENGE_INSTRUCTION
        else:
            base += "\n" + HANDOUT_DRILL_MODE_INSTRUCTION
        if handout_content:
            base += "\n── HANDOUT CONTENT ──\n" + handout_content + "\n── END HANDOUT ──\n"

    return base
