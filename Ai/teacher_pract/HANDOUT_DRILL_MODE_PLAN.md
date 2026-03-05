# Handout Drill Mode — Architectural Plan (teacher_pract only)

**Scope:** teacher_pract only. Do NOT modify teacher/. Do NOT modify transition_engine, state_parser, or existing drill loop / resume / topic decomposition behavior. System behaves exactly as before unless Handout Drill Mode is activated.

---

## Objective

- **Sidebar:** Add "Run Stage Handout" plus a way to provide handout content (paste/upload).
- **On activation:** Practice drills ONLY from the provided handout: no topic decomposition, no sidebar topic/category scope, no `topic_change`, no `decompose`. Lock actions and drill-loop rules unchanged. When all handout concepts are locked, exit Handout Drill Mode automatically.

---

## 1. Safest injection point in `build_system_prompt()`

**Location:** End of [prompts.py](prompts.py), after the existing `parts` are built and before the single return. Keep the prompt builder **state-fed**: orchestration passes `state` in (e.g. `build_system_prompt(state=state)`); prompts do not call `get_system_state()` for this.

**Approach:**

- Add parameter `state=None` to `build_system_prompt(state=None)`.
- After `base = "\n".join(parts)` (replace current `return "\n".join(parts)` with this):
  - If `(state or {}).get("handout_mode") == 1`:
    - Append a fixed **Handout Drill Mode instruction block** (no decomposition, no topic/category scope, no topic_change/decompose, use handout as concept map, standard drill loop, on completion emit `{"action":"none"}` and print "Handout practice complete. Returning to normal mode.").
    - Append the handout content: `(state or {}).get("active_handout")` (raw text or a formatted snippet—if stored as JSON, include a clear “Handout concepts: …” section for the model).
  - Return `base`.

**Why this is safest:** One append at the very end; no reordering of existing sections. Handout mode is purely additive and last in the prompt, so it overrides normal “use topic/decomposition” behavior only when active. No DB read inside the prompt builder if state is passed from orchestration.

---

## 2. How to override decomposition safely (without touching transition_engine)

**Constraint:** Do not modify transition_engine or state_parser. So we do **not** block `decompose` or `topic_change` in the engine.

**Safe override: prompt-only**

- When `handout_mode == 1`, the appended instruction block must tell the model explicitly:
  - Do NOT perform new topic decomposition.
  - Do NOT reference sidebar topic/category for scope.
  - Do NOT emit `topic_change`.
  - Do NOT emit `decompose`.
  - Use the handout concepts as the only concept map and drill only those.
- The engine still *would* apply decompose/topic_change if the model emitted them; we rely on the model not doing so when in Handout Drill Mode. No new guards or engine logic.

**Optional hardening (still no engine/parser changes):** In orchestration, after `parse_state_updates` and before `apply_transitions`, if `handout_mode == 1` and any proposal has `action in ("decompose", "topic_change")`, drop those proposals or replace with `action: "none"` so they are never applied. That keeps the contract “handout mode never changes topic or decomposition” even if the model misbehaves. This is an orchestration-layer filter only.

---

## 3. How to track handout concept completion without altering topic logic

**Goal:** Know when “all handout concepts are locked” so we can call `update_system_state(handout_mode=0, active_handout=None)` and exit Handout Drill Mode. Do not change how topic/decomposition/concept_progress work for normal mode.

**Data:**

- `active_handout` (TEXT) stores a serialized handout. Use a minimal JSON shape so completion can be computed, e.g. `{"concepts": ["Concept A", "Concept B", "Concept C"]}`. When the user pastes/uploades, the UI (or a thin helper) parses or builds this list and saves it as `active_handout`.
- Locks still go through the existing transition_engine path: `lock` → `upsert_concept` + `lock_concept` for `(topic, category, concept_number, concept_name)` from **current** `system_state` (topic/category are not changed when entering handout mode). So handout concepts are drilled under the **current** topic/category; concept_progress rows are the same as today.

**Completion check (orchestration only):**

- After `apply_transitions(...)` in orchestration, if `state.get("handout_mode") == 1` and `state.get("active_handout")`:
  - Parse `active_handout` (JSON) and get the list of concept names (e.g. `concepts = data.get("concepts", [])`).
  - For `topic = state.get("topic")`, `category = state.get("category")`, query `concept_progress` (existing DB helpers) for those concept names and check that every one has `locked == 1`.
  - If all handout concepts are locked: call `update_system_state(handout_mode=0, active_handout=None)` (and optionally clear or leave `current_concept`; spec says exit mode, so resetting the two handout flags is enough).
- No new tables, no change to topic/decomposition or to transition_engine. A small helper (e.g. `all_handout_concepts_locked(state)`) in db or orchestration can encapsulate the parse + query + check.

**Edge case:** If the handout lists a concept that doesn’t exist in `concept_progress` yet, the first lock for it will create it via existing `upsert_concept` in the engine. So completion = “all names in handout’s concept list are locked for current topic/category.”

---

## 4. Minimal code diff summary

| File | Change |
|------|--------|
| **db.py** | In `init_db()`, add migrations: `handout_mode INTEGER NOT NULL DEFAULT 0`, `active_handout TEXT NULL` on `system_state` (try/except like existing ALTERs). Optional: add helper `all_handout_concepts_locked(state)` that parses `state.get("active_handout")`, gets concept names, checks `concept_progress` for `state["topic"]`/`state["category"]` and returns True iff all are locked. |
| **prompts.py** | Add constant `HANDOUT_DRILL_MODE_INSTRUCTION` (full instruction block per spec). Add parameter `state=None` to `build_system_prompt(state=None)`. After building `parts`, set `base = "\n".join(parts)`; if `(state or {}).get("handout_mode") == 1`: append instruction block + handout content from `state.get("active_handout")`. Return `base`. No DB call in prompt builder. |
| **orchestration.py** | (1) Keep `state = get_system_state()` at start; call `build_system_prompt(state=state)`. (2) **Safety:** If `state.get("handout_mode") == 1` and not `state.get("active_handout")`: do not call LLM; save user message + analytics; save assistant message with "No active handout found." and `<<<STATE_UPDATE_START>>>\n{\"action\":\"none\"}\n<<<STATE_UPDATE_END>>>`; call `update_system_state(handout_mode=0)`; return. (3) Optional: after `parse_state_updates`, if `handout_mode == 1`, filter out any proposal with `action in ("decompose", "topic_change")` so they are not passed to `apply_transitions`. (4) After `apply_transitions`, if `state.get("handout_mode") == 1` and `all_handout_concepts_locked(state)` (or equivalent): call `update_system_state(handout_mode=0, active_handout=None)`. |
| **desktop.py** | Add sidebar: input for handout (e.g. multiline paste or file upload) and button "Run Stage Handout". On click: build handout JSON (e.g. extract or parse concept list into `{"concepts": [...]}`); call `update_system_state(handout_mode=1, active_handout=handout_json)`; do not change topic/category/current_concept/decomposition/run. Optionally trigger a first assistant message or leave for user to send next message to start drilling. |
| **streamlit_app.py** | Same idea: sidebar control to paste/upload handout + "Run Stage Handout" button; on click set `handout_mode=1` and `active_handout=<serialized>`; no other state changes. |

**Not modified:** teacher/, transition_engine.py, state_parser.py, existing drill loop behavior, resume logic, normal topic-based decomposition behavior.

---

## 5. Safety (no active handout)

- **Condition:** `handout_mode == 1` and `active_handout` is NULL or empty.
- **Action:** Do not call the LLM. Save user message and run analytics as usual. Save one assistant message with "No active handout found." and the state block `<<<STATE_UPDATE_START>>>\n{"action":"none"}\n<<<STATE_UPDATE_END>>>`. Call `update_system_state(handout_mode=0)`. Return that content so the UI can display it.

---

## 6. Mode exit (automatic)

- When `handout_mode == 1` and the completion check (all handout concepts locked) is True after a response: in orchestration, call `update_system_state(handout_mode=0, active_handout=None)`.
- No parser changes; no new action types. Lock and mastery behavior unchanged. Handout Drill Mode is isolated and does not affect normal behavior outside activation.

---

## 7. Contract

- **Teacher_pract** remains independent: no coupling to teacher/, no cross-awareness, no state contamination.
- **Producer (teacher/)** is out of scope: this plan is only for the consumer side (teacher_pract: run handout, drill only that, exit when done).
