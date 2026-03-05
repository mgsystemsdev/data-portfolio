# Generate Handout — Architectural Plan (teacher/ only)

**Scope:** teacher/ (Learning app) only. Do NOT modify teacher_pract/. Do NOT modify transition_engine, state_parser, lock behavior, or progression logic. System behaves exactly as before unless the button is pressed.

---

## Objective

- **Sidebar:** Add "Generate Handout" button.
- **On click:** Set `handoff_mode=1`, then trigger one LLM response that generates a structured handout for the **last locked stage** only. No advance, no lock, no announce, no topic_change. Model outputs the handout, then exactly "Handout generated. Enter Practice Mode." and the state block `<<<STATE_UPDATE_START>>>\n{"action":"none"}\n<<<STATE_UPDATE_END>>>`. After the response is sent, orchestration resets `handoff_mode=0`. Single-response override; normal mode resumes immediately after.

---

## 1. Safest injection point in `build_system_prompt()`

**Location:** End of [teacher/app/prompts.py](app/prompts.py), after the existing `parts` are built and before `return "\n".join(parts)`.

**Approach:** Keep the prompt builder **state-fed**. Orchestration already has `state = get_system_state()`; pass it in as `build_system_prompt(state=state)`.

- In **orchestration:** Call `build_system_prompt(state=state)` (pass state; no extra DB read in prompts).
- In **prompts.py:** Add parameter `state=None` to `build_system_prompt(state=None)`. After building `parts`, set `base = "\n".join(parts)`. If `(state or {}).get("handoff_mode") == 1`: append the **Handout Mode instruction block** (generate handout for last locked stage only; do not advance/lock/announce/change topic/modify state; required handout sections; then output exact phrase and emit the state block). Append nothing else (e.g. "last locked stage" can be stated in the instruction block using the state already in the prompt, or you can pass it as part of the block). Return `base`.

**Why this is safest:** One append at the very end of the system prompt. No reordering of existing sections. Handout mode overrides normal teaching only for that one response. No DB call inside the prompt builder if state is passed from orchestration.

**Concrete spot:** Replace the current `return "\n".join(parts)"` at the end of `build_system_prompt()` with:

- `base = "\n".join(parts)`
- If `(state or {}).get("handoff_mode") == 1`: `base += "\n\n" + HANDOUT_MODE_INSTRUCTION` (constant with the full spec text; the instruction should say "Generate a structured handout for the LAST LOCKED STAGE" and can reference that the current system state / resume context already shows last locked method/stage).
- `return base`

---

## 2. Where to reset `handoff_mode` safely

**Location:** [teacher/app/orchestration.py](app/orchestration.py), inside `handle_user_message()`.

**Two reset points:**

1. **Safety guard (no stage locked yet):**  
   Right after `state = get_system_state()`, if `state.get("handoff_mode") == 1`:  
   - Determine "last locked stage" by querying the DB (e.g. `SELECT stage FROM method_progress WHERE locked = 1 ORDER BY locked_at DESC LIMIT 1`). If there is no such row, **do not call the LLM.** Save the user message and run analytics as usual. Save one assistant message with content: "Stage must be completed before generating a handout." plus the state block `<<<STATE_UPDATE_START>>>\n{"action":"none"}\n<<<STATE_UPDATE_END>>>`. Call `update_system_state(handoff_mode=0)` and return that content. Reset happens before any LLM call.

2. **After normal handout response:**  
   When the LLM was called with `handoff_mode == 1` (guard did not run), after the stream completes and the assistant message is written: **do not** run `parse_state_updates` or `apply_transitions` for this response (so no lock/stage transition is applied). Then call `update_system_state(handoff_mode=0)` and return. Reset happens in orchestration immediately after the response is persisted, in the same `handle_user_message` run.

**Why orchestration:** So `handoff_mode` never persists beyond one cycle; the model does not clear it. Single responsibility: one response, then reset.

---

## 3. Confirmation: does NOT interfere with resume logic

**Resume is unaffected:**

- **Data:** Resume uses `get_system_state()`, `get_stage_methods()`, `build_resume_block()` ([teacher/app/db.py](app/db.py)), and sidebar actions in [teacher/app/desktop.py](app/desktop.py) and [teacher/app/teacher.py](app/teacher.py). None of these read or display `handoff_mode`. `build_resume_block()` does not use `handoff_mode`.
- **Lifecycle:** `handoff_mode` is set to 1 only when the user clicks "Generate Handout" and is set back to 0 in the same `handle_user_message` run (either after the guard response or after the handout response). It is never persisted across sessions.
- **Sidebar:** New Session, New Run, Resume, Practice This Stage do not touch `handoff_mode`. Adding "Generate Handout" only sets `handoff_mode=1` and triggers one send; it does not change how resume or session state are computed.

So resume and normal flow remain unchanged unless the user actually clicks "Generate Handout".

---

## 4. Minimal code diff summary

| File | Change |
|------|--------|
| **db.py** | In `init_db()` (or `_migrate_schema()` if that runs for existing DBs), add migration: `ALTER TABLE system_state ADD COLUMN handoff_mode INTEGER NOT NULL DEFAULT 0` in a try/except. No change to `get_system_state` (SELECT * already returns the new column). Optional: add helper `get_last_locked_stage(conn=None)` that returns the stage of the most recently locked method (e.g. `SELECT stage FROM method_progress WHERE locked = 1 ORDER BY locked_at DESC LIMIT 1`), or None if no method is locked. |
| **prompts.py** | Define constant `HANDOUT_MODE_INSTRUCTION` (full instruction block per spec: handout for last locked stage only; no advance/lock/announce/topic_change; required sections; exact closing phrase and state block). Add parameter `state=None` to `build_system_prompt(state=None)`. After building `parts`, set `base = "\n".join(parts)`; if `(state or {}).get("handoff_mode") == 1`: `base += "\n\n" + HANDOUT_MODE_INSTRUCTION`. Return `base`. No DB call in prompt builder. |
| **orchestration.py** | (1) Import `update_system_state`. (2) Keep `state = get_system_state()` at start; call `build_system_prompt(state=state)`. (3) **Safety guard:** If `state.get("handoff_mode") == 1`, compute last locked stage (e.g. via `get_last_locked_stage()` or inline query). If none: save user message, run `analyze_user_message`, save assistant message with "Stage must be completed before generating a handout." and state block, call `update_system_state(handoff_mode=0)`, return. (4) After streaming and setting assistant content complete, if `state.get("handoff_mode") == 1`: **skip** `parse_state_updates` and `apply_transitions`; call `update_system_state(handoff_mode=0)`; return `full_response`. |
| **desktop.py** | Add sidebar button "Generate Handout". On click: call `update_system_state(handoff_mode=1)`, then trigger one send (e.g. call `handle_user_message(session_id, "Generate handout.", client, ...)` in a thread, or inject a synthetic user message and run the same send path). Do not modify stage, mastery, topic, or current_concept. Place button in state panel (e.g. near "Practice This Stage" / "Resume"). |
| **teacher.py** | Same idea: add "Generate Handout" in sidebar; on click set `handoff_mode=1` and trigger one request (e.g. with a fixed user message so one response is generated). |

**Not modified:** teacher_pract/, transition_engine.py, state_parser.py, lock behavior, progression logic.

---

## 5. Safety guard (no stage locked)

- **Condition:** `handoff_mode == 1` and there is no locked method (query returns no row for "last locked stage").
- **Action:** Do not call the LLM. Save user message and run analytics. Save one assistant message with "Stage must be completed before generating a handout." and the state block `<<<STATE_UPDATE_START>>>\n{"action":"none"}\n<<<STATE_UPDATE_END>>>`. Call `update_system_state(handoff_mode=0)`. Return that content.

---

## 6. Handout instruction block (spec)

Append when `handoff_mode == 1`:

- You are in Handout Mode.
- Generate a structured handout for the **LAST LOCKED STAGE** only.
- Do NOT: advance stage, lock stage, announce next stage, change topic, modify state.
- Handout must contain: Topic, Stage Name, Core Concepts (max 10 bullets), Required Syntax Templates, 3 Minimal Code Examples, 3 Common Failure Cases, Verification Expectations, Exit Criteria. Keep concise; no motivational language; no scope expansion.
- After the handout, output exactly: "Handout generated. Enter Practice Mode."
- Then emit: `<<<STATE_UPDATE_START>>>\n{"action":"none"}\n<<<STATE_UPDATE_END>>>`.
- This overrides normal stage teaching only for this response.

(Teacher’s state_parser is regex-only and does not parse this block; skipping parse/apply when `handoff_mode==1` ensures no transitions are applied.)

---

## 7. Contract

- **Teacher** remains independent; no coupling to teacher_pract.
- **handoff_mode** is reset in orchestration after one response and does not persist beyond one cycle.
