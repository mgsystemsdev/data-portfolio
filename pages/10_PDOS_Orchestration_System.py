"""
Personal Developer Operating System (PDOS) — portfolio showcase page.
Local-first AI orchestration: idea → contract → tasks → routing → execution → validation → PR.
"""

import time
from pathlib import Path

import streamlit as st

st.title("Personal Developer Operating System (PDOS)")

st.markdown(
    "**Local-first AI orchestration system that turns raw ideas into validated code changes "
    "through structured execution.**"
)

# Optional hero image (add assets/pdos_control_plane.png when you have a screenshot)
_repo_root = Path(__file__).resolve().parent.parent
_hero = _repo_root / "assets" / "pdos_control_plane.png"
if _hero.is_file():
    st.image(str(_hero), caption="PDOS control plane (dashboard)")
else:
    st.caption(
        "_Tip: add `assets/pdos_control_plane.png` for a control-plane screenshot above the metrics._"
    )

# --- Top metrics ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Session startup", "30+ min → <2 min")
col2.metric("Token efficiency", "3 days → 7 days")
col3.metric("State failures", "0 (full cycles)")
col4.metric("Traceability", "1:1 task → commit")

st.divider()

# --- System flow ---
st.subheader("System flow")
st.info(
    "Idea → Requirement Contract → Task Decomposition → Tool Routing → "
    "Execution → Validation → PR Output"
)

st.divider()

# --- What it replaces ---
st.subheader("What it replaces")
st.markdown(
    """
- **Context loss** between sessions and tools  
- **Re-explaining** project state to every new AI session  
- **Manual task planning** and fragmented tracking across notes  
- **Coordination overhead** between design (thinking) and implementation (terminal)  
"""
)

st.divider()

# --- What it does ---
st.subheader("What it does")
st.markdown(
    """
- Converts raw intent into **5-element Requirement Contracts** (Trigger, Input, Output, Constraints, Failure Path)  
- Decomposes work into **atomic tasks** (≈30–90 min) in machine-readable `tasks.json`  
- **Routes** each unit of work to the most cost-capable tool  
- Runs **analyze → plan → execute** so tools do not touch code blind  
- **Validates** against defined Done Conditions before state moves forward  
"""
)

st.divider()

# --- Orchestration layer ---
st.subheader("Orchestration layer")

c1, c2 = st.columns(2)

with c1:
    st.markdown("**Thinking layer**")
    st.markdown(
        "- GPT-4o agents: Architect, Spec Gate, Strategist, Operator (design + verification outside premium execution tokens)"
    )
    st.markdown("**Execution layer**")
    st.markdown("- Claude Code — multi-file reasoning, complex builds")
    st.markdown("- Cursor / Codex — surgical file-level edits and tests")

with c2:
    st.markdown("**Analysis layer**")
    st.markdown("- Gemini CLI — large-context “Step 0” repo analysis → baton files")
    st.markdown("**System control**")
    st.markdown("- `agents` CLI — disk ↔ SQLite sync, execution hooks")
    st.markdown("- SQLite — operational mirror for dashboard and runs")

st.divider()

# --- Validation + control ---
st.subheader("Validation + control")
st.markdown(
    """
- No task completes without evidence against a **Done Condition**  
- Failed verification → **correction loop** (diagnostic + fix prompt), not silent retry  
- **Human gate**: state mutations go through explicit approval (e.g. Actions tab)  
- **Git discipline**: isolated branches, merges via PR; **1:1** completed task ↔ atomic commit  
"""
)

st.divider()

# --- Local-first ---
st.subheader("Local-first architecture")

l1, l2 = st.columns(2)

with l1:
    st.markdown("**Source of truth**")
    st.markdown("- Git-tracked Markdown + JSON (e.g. `.claude/context/`)")
    st.markdown("- Project “brain”: PRD, tasks, decisions, session logs")

with l2:
    st.markdown("**Operational mirror**")
    st.markdown("- SQLite — queryable tasks, runs, health")
    st.markdown("- **Baton files** (`analysis.md`, `plan.md`, `handoff.md`) — hand context between tools")

st.divider()

# --- Not a wrapper ---
st.subheader("Why this is not a wrapper")
st.markdown(
    """
- **Custom task system** — work is queued and governed, not chat-thread execution  
- **Propose → approve → execute** lifecycle instead of blind agent writes  
- **Unidirectional sync** — disk-authored truth wins; DB does not overwrite project files  
- **Explicit routing logic** — cheapest capable tool per task type and context size  
"""
)

st.divider()

# --- Live artifacts (samples) ---
st.subheader("Live artifacts (examples)")
st.caption("Replace these samples with snippets from your real repo when publishing.")

with st.expander("Sample `tasks.json` structure", expanded=False):
    st.code(
        """{
  "version": 1,
  "tasks": [
    {
      "id": "TASK-001",
      "title": "Add notification schema + migration",
      "estimate_min": 45,
      "status": "blocked",
      "done_condition": "alembic upgrade passes; pytest tests/db/test_notifications.py green",
      "branch": "feature/TASK-001-notification-schema"
    },
    {
      "id": "TASK-002",
      "title": "Notification API + validation",
      "estimate_min": 60,
      "status": "queued",
      "done_condition": "OpenAPI contract + integration tests for POST /notifications"
    }
  ]
}""",
        language="json",
    )

with st.expander("Sample `plan.md` excerpt (plan-before-code)", expanded=False):
    st.code(
        """# Plan: TASK-001 — Notification schema

## Scope
- New tables: notifications, notification_preferences
- No behavior change to existing auth paths

## Steps
1. Add SQLAlchemy models + Alembic revision
2. Add migration test + rollback check
3. Hand off baton: handoff.md with file touch list

## Out of scope
- Email delivery workers (TASK-003)
""",
        language="markdown",
    )

with st.expander("Sample validation / PR outcome", expanded=False):
    st.code(
        """$ pytest -q tests/db/test_notifications.py
..                                                                      [100%]

$ git log -1 --oneline
a4f9c21 TASK-001: notification schema + migration

PR: https://github.com/<org>/<repo>/pull/42
- Diff constrained to models/, alembic/versions/, tests/db/
""",
        language="text",
    )

st.divider()

# --- Interactive demo ---
st.subheader("Interactive demo: PDOS execution pipeline")
st.caption("Simulation: shows state transitions and routing—no live LLM calls.")

user_input = st.text_area("Enter a feature request or idea", height=100, key="pdos_demo_input")

if st.button("Run PDOS", type="primary"):
    if not user_input.strip():
        st.warning("Enter an idea to run the pipeline.")
    else:
        progress = st.progress(0)
        status = st.empty()

        status.info("Step 1: Generating Requirement Contract…")
        time.sleep(0.6)
        progress.progress(20)
        st.markdown("### Requirement Contract")
        st.code(
            f"""Trigger: User request
Input: {user_input[:500]}{"…" if len(user_input) > 500 else ""}
Output: Implementation plan + scoped task list
Constraints: Minimal diff, testable Done Conditions
Failure: Refine contract; retry planning""",
            language="text",
        )

        status.info("Step 2: Decomposing into tasks…")
        time.sleep(0.6)
        progress.progress(40)
        st.markdown("### Task decomposition")
        st.json(
            {
                "tasks": [
                    {"id": 1, "task": "Analyze request + repo touchpoints", "tool_hint": "Gemini"},
                    {"id": 2, "task": "Generate implementation plan", "tool_hint": "Claude"},
                    {"id": 3, "task": "Execute code changes", "tool_hint": "Cursor"},
                    {"id": 4, "task": "Validate (tests / logs / diff)", "tool_hint": "Operator"},
                ]
            }
        )

        status.info("Step 3: Routing tools…")
        time.sleep(0.6)
        progress.progress(60)
        st.markdown("### Tool routing")
        r1, r2, r3 = st.columns(3)
        r1.success("Gemini → analysis")
        r2.success("Claude → planning")
        r3.success("Cursor → execution")

        status.info("Step 4: Executing changes…")
        time.sleep(0.6)
        progress.progress(80)
        st.markdown("### Execution output (illustrative)")
        st.code(
            """- Feature logic updated with validation layer
- Tests added for edge cases surfaced in contract
- Branch: feature/TASK-XXX (isolated from main)""",
            language="text",
        )

        status.info("Step 5: Validating against Done Conditions…")
        time.sleep(0.6)
        progress.progress(100)
        st.markdown("### Validation")
        st.success("Checks passed. Ready for Pull Request.")
        status.success("PDOS pipeline complete (demo).")

st.divider()

# --- Deep dive ---
st.subheader("System architecture (deep dive)")

with st.expander("View full PDOS architecture", expanded=False):
    st.markdown("### Architecture layers")
    st.markdown(
        """
- **Global memory** — operator identity, preferences, durable decisions  
- **Project context** — PRD, `tasks.json`, decisions, session logs  
- **Control plane** — SQLite + API + dashboard (health, actions, runs)  
- **Execution interfaces** — Claude Code, Gemini CLI, Cursor / Codex  
"""
    )

    st.markdown("### State management")
    st.markdown(
        """
- **Files** = authoritative authored truth  
- **SQLite** = operational mirror for visibility and agents  
- **Unidirectional sync** — disk → DB only; no DB overwrite of source files  
- **`session.md`** — fast context restoration at session start  
"""
    )

    st.markdown("### Execution lifecycle")
    st.markdown(
        """
- PRD → `tasks.json` → **approval** → **branch** → analysis → plan → execute → **validate** → PR  
- **One task → one branch → one commit** (traceability)  
- No execution without analysis + plan baton files  
"""
    )

    st.markdown("### Failure handling")
    st.markdown(
        """
- **Fail loudly** — errors surface in dashboard / logs, not silent retries  
- **Correction loop** — Operator issues fix prompts with evidence gaps  
- **Fallback routing** — e.g. Claude budget → Gemini analysis + Cursor execution  
- **Atomic ingestion** — bad `tasks.json` batches fail whole ingest (no partial corrupt state)  
"""
    )

    st.markdown("### Validation system")
    st.markdown(
        """
- **Done Condition** tied to Requirement Contract success criteria  
- **Evidence required** — tests, logs, diffs; no “trust me” completions  
- Completion **blocked** until proof matches contract  
"""
    )

    st.markdown("### Observability")
    st.markdown(
        """
- Worker + dashboard logs  
- **Runs** table — attempts, outputs, pass/fail  
- **Health** endpoint — DB, worker, key presence  
"""
    )

    st.markdown("### Security + local-first")
    st.markdown(
        """
- **Local-first** — code + SQLite + context bundle stay on machine (or your VPS)  
- **Keys** — environment / `.env`, never committed  
- **Minimal cloud exposure** — send only task-necessary context to LLM APIs  
"""
    )

    st.markdown("### Real execution trace (summary)")
    st.markdown(
        """
**Idea** → Architect (PRD + contracts) → Spec Gate (`tasks.json`) → `agents push` →
dashboard → branch + Gemini analysis → Claude plan → Cursor/Codex edits →
Operator verification → **GitHub PR** → merge.
"""
    )

st.divider()

st.subheader("Deep dive links (optional)")
st.caption(
    "Use these as **supporting** material only. The system should read clearly without opening chat logs."
)
st.markdown(
    """
- Design / spec sessions (ChatGPT projects) — *link when you publish*  
- Cursor / IDE traces — *link to a sample PR or gist*  
- Execution logs — *paste redacted excerpt or attach in repo `docs/`*  
"""
)
