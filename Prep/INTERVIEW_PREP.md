**How to use this doc**  
Explain your systems in your own words; use the **technical terms** in bold when you want to sound precise in an interview. Plain-English versions are there so you get it; recruiter terms are there so they hear what they need.

---

## 1. Portfolio Overview

AI Systems: 4  
Data Projects: 2 (plus placeholder stubs)

**Primary Technologies**
- Python
- Streamlit
- SQLite
- Pandas
- OpenAI API (via `openai` client)
- Flet (desktop variants for some AI apps)

**Architecture Patterns**
- **Event sourcing + projections** for the Personal Task & Goal Assistant (`Ai/assistant`)
- **State machines with transition engines** for the apprenticeship and practice engines (`Ai/teacher`, `Ai/teacher_pract`, `Ai/metacode`)
- **Two-phase LLM workflow** (conversation first, extraction second) for the assistant
- **Strict JSON schema validation + regex fallback** for practice / apprenticeship state updates
- **Guard conditions and idempotent updates** to keep AI-driven state transitions safe
- **ETL and enrichment pipelines** for the Operational Turnover Intelligence (OTI) project and Operational Turnover Intelligence — Make-Ready (`career txt/the-dmrb`)

**Implemented AI Systems**
- **Personal Task & Goal Assistant** (`Ai/assistant`)
- **Data Analytics Apprenticeship** (`Ai/teacher/app/teacher.py`)
- **Concept Practice Engine** (`Ai/teacher_pract/streamlit_app.py`)
- **Code & Analytics Apprenticeship** (`Ai/metacode/streamlit_app.py`)

**Implemented Data / Analytics Projects**
- **Operational Turnover Intelligence** (OTI) case study (`pages/1_Operational_Turnover_Intelligence.py` + `pipeline/`)
- **Operational Turnover Intelligence — Make-Ready (the-dmrb)** operational app (`career txt/the-dmrb`)

**Not Implemented in Code**
- **Nightwing Engine** only appears in career planning notes as a prompt-only “skill forge” / interview conditioning concept. There is no Nightwing code in this repository; the implemented systems are the four listed above.

---

## Concepts You Need to Own

Understand these four ideas deeply so you can explain your systems and apply them to new problems in an interview.

**State**  
- **Plain English:** What the system "knows" right now—current tasks, current stage, current topic. It's the current view you get when you read from the database or derive it from a log of what happened.  
- **Technical one-liner:** State is the current view of the system; it can be stored in DB tables or derived from events.  
- **Where you use it:** Assistant → tasks/goals/time_logs tables; apprenticeship engines → current stage + locked concepts; make-ready app → units, turnovers, tasks.

**Validation**  
- **Plain English:** Checking that incoming data or AI output is allowed and well-formed before we trust it. We never let raw AI or user input change the system until it passes these checks.  
- **Technical one-liner:** Validation (e.g. **schema checks**, **guard conditions**) ensures only valid transitions or events update state.  
- **Where you use it:** Assistant → **allowed event types**; practice engine → **validate_state_update()** + **guard functions**.

**Event sourcing**  
- **Plain English:** Instead of overwriting "current state," we append things that happened; current state is computed from that log. So we have a full history and can replay or fix logic later.  
- **Technical one-liner:** **Append-only event log** plus **projections**; state is derived, not overwritten.  
- **Where you use it:** Assistant → **events** table + **projector** → tasks/goals/time_logs.

**Schemas**  
- **Plain English:** A fixed shape for data—which fields exist, what type, what values are allowed. That makes AI or API output machine-checkable.  
- **Technical one-liner:** **Schema enforcement** (e.g. JSON schema, allowed event types) makes outputs deterministic and safe to apply.  
- **Where you use it:** Practice engine → **STATE_UPDATE** JSON with allowed keys and enums; DB → tables and **foreign keys**.

**One-line transfer summary:**  
I think in terms of **state**, **validation**, **event sourcing**, and **schemas**; my systems are examples of those building blocks, and I'd use the same ideas for something new.

---

## Pattern Recognition: When You See X, Think Y

When someone describes a new problem, classify it so you can reuse the same building blocks.

| If the problem sounds like… | Think… |
|-----------------------------|--------|
| User actions change what we remember over time | **State** (and maybe **event sourcing**) |
| We must trust external or AI output before changing anything | **Validation** + **schema** |
| Strict step-by-step flow (stages, phases) | **State machine** + **guards** |
| Raw input must become clean, structured data | **ETL** + **normalization** |
| Several reports describing the same real-world thing | **Domain model** + **reconciliation** |

---

## Apply to Something New (practice prompts)

Practice using **state**, **validation**, **event sourcing**, and **schemas** on scenarios you didn't build.

1. **"Design a system where users suggest changes that only apply after review."**  
   Use: **state** (e.g. pending vs applied), **validation** (review step), optional **event log** for audit.

2. **"Chatbot that updates a database from conversation."**  
   Use: **two-phase LLM** (reply vs extraction), **schema** for extracted events, **validation**, then **event store** or controlled writes.

3. **"Three CSV feeds all describe 'orders' differently; we need one source of truth."**  
   Use: **domain model**, **normalization**, **ETL**, **reconciliation** (same ideas as OTI and the make-ready app).

---

## 2. AI Systems Architecture

This section walks through each AI system using an interview-friendly structure.

### Personal Task & Goal Assistant (`Ai/assistant`)

**System Name**  
Personal Task & Goal Assistant

**Purpose**  
A Streamlit-based personal assistant that turns free-form chat into structured tasks, goals, time logs, and notes. It maintains long-term state about your work, study, and life goals using an event-sourced architecture backed by SQLite.

**In plain English**  
You talk; the app answers and, in the background, turns what you said into structured tasks and goals it can store and show later. Nothing from the AI touches your data until it’s been checked and written as an event.

**Terms recruiters listen for:** **event sourcing**, **two-phase LLM**, **projection**, **allowed event types**, **append-only event log**, **SQLite**.

**Key Components**
- **UI**: Streamlit app (`assistant.py`, described in `docs/README.md`)
- **Orchestrator**: `agent/orchestrator.py` (two-phase LLM workflow)
- **Prompts**: `agent/prompts/chat.txt` and `agent/prompts/extract.txt`, plus `agent/profile.txt`
- **Event Store**: `events/event_store.py` (append-only events)
- **Projector**: `events/projector.py` (turns events into current tasks/goals/time_logs)
- **Database**: `db/database.py` + `db/schema.sql` + `db/snapshot.py` (SQLite + snapshots)
- **Config**: `config/config.py` (API keys, model, DB path)
- **Docs**: `docs/ARCHITECTURE_AND_PRODUCTION.md`, `docs/EXPLORATORY_24H.md`, `docs/STANDARDS.md`

**Workflow**
1. **User sends a message** in the Streamlit chat UI.
2. The orchestrator calls **Phase 1** (`phase1_reply`):
   - Loads profile, recent conversation summary, known facts, and task/goal/time context.
   - Builds a system prompt from `chat.txt` and these contexts.
   - Calls the LLM (via `openai` client) to generate a conversational reply.
3. The user message and assistant reply are saved into the `messages` table (`save_message`).
4. The orchestrator then runs **Phase 2** (`phase2_extract_events`):
   - Calls a second LLM prompt (`extract.txt`) with the full turn (user + assistant).
   - Asks the model to emit **structured JSON events** representing changes (tasks, goals, time logs, notes).
   - Parses the JSON and filters event types against a whitelist (`ALLOWED_EVENT_TYPES`).
5. For each valid event, the system:
   - Calls `append_event` in `events/event_store.py` to persist an append-only row in the `events` table.
   - Calls `project_event` in `events/projector.py` to apply the event to **current-state tables** (`tasks`, `goals`, `time_logs`, etc.).
6. The conversation metadata (`conversations.last_active_at`, summaries, metrics) is updated for later context (gap detection, weekly stats, etc.).

**State Management**
- Conversation history stored in `messages` and `conversations` tables.
- Long-lived state (tasks, goals, time logs) stored in normalized tables.
- All **mutations** come from the **event log**:
  - Events are immutable, append-only rows in `events` (e.g. `TASK_CREATED`, `TASK_COMPLETED`, `GOAL_UPDATED`, `TIME_LOGGED`, `NOTE_RECORDED`).
  - Projectors compute the current state by applying events in order.
- Snapshots (`db/snapshot.py`) allow saving serialized state for faster reloads or backups.

**Validation / Guardrails**
- **Event type whitelist**: `ALLOWED_EVENT_TYPES` ensures only known event types are accepted.
- **Best-effort extraction**: If JSON parsing fails or events are invalid, the conversational reply still succeeds; state updates are simply skipped for that turn.
- **Separation of concerns**:
  - LLM never writes directly to DB tables.
  - Only the orchestrator and projector mutate persistent state based on validated events.
- **Context shaping**: `detect_day_context` summarizes gaps, overdue tasks, and weekly metrics so the LLM’s decisions are grounded in real data instead of hallucinated structure.

**Persistence**
- SQLite database initialized from `db/schema.sql`.
- Connection helper in `db/database.py` with WAL mode for reliability.
- Events and state tables live in a single-file DB, suitable for local personal use.

**Why This Architecture**
- **Event sourcing + projections** (documented in `docs/ARCHITECTURE_AND_PRODUCTION.md`) provide:
  - A full audit trail of how the assistant changed your state.
  - Ability to **replay** events if you improve the projector logic later.
  - Safer evolution of the schema over time.
- The **two-phase LLM design** separates “talk to the user” from “update the system,” which:
  - Avoids hard failures when extraction breaks.
  - Makes it easier to iterate on extraction prompts and JSON formats.
  - Aligns with production reliability expectations for AI systems.

---

### Data Analytics Apprenticeship (`Ai/teacher`)

**System Name**  
Data Analytics Apprenticeship

**Purpose**  
A stage-based learning engine for SQL and pandas that walks a learner through a structured curriculum (stages S0–S12) one concept and one method at a time. It is presented as a Streamlit (and Flet) app for interactive apprenticeships.

**In plain English**  
The app teaches you analytics step by step. It knows which stage you're in and which steps you've "locked"; it only moves you forward when the AI's reply matches patterns we recognize and allow.

**Terms recruiters listen for:** **state machine**, **stage progression**, **regex parsing**, **transition engine**, **idempotent** (per message), **method_lock**, **stage_transition**.

**Key Components**
- **UI**: `app/teacher.py` (Streamlit) and `app/desktop.py` (Flet desktop)
- **Orchestration**: `app/orchestration.py` (conversation loop + state updates)
- **State Parser**: `app/state_parser.py` (regex-based parsing of stage/method locks)
- **State Schema**: `app/state_schema.py` (dataclass + enums for transitions)
- **Transition Engine**: `app/transition_engine.py` (FSM that validates and applies transitions)
- **Prompts and Docs**:
  - `docs/layer1_why_v2.md`–`layer4_complete_v2.md`
  - `docs/prompt_v6.md` (main system prompt)
  - `docs/knowledge_file.md` (domain reference)
- **Database**: `app/db.py` (SQLite schema, state_events table, migrations)

**Workflow**
1. Learner opens `teacher.py` and starts a session (Streamlit sets up session state and DB connection).
2. The orchestration layer:
   - Loads current system state (current stage, locked methods, handoff status, etc.).
   - Builds a **system prompt** using stage docs, the method map, and active state.
   - Streams an LLM response back to the UI.
3. At the end of the LLM reply, the system runs the **state parser**:
   - It uses regex patterns to detect:
     - Newly locked methods (e.g. “Method 3 — Join two tables — LOCKED”).
     - Stage transitions (e.g. “Proceeding to Stage S3B”).
4. Parsed “proposed transitions” are mapped into `ProposedTransition` dataclasses (`state_schema.ProposedTransition` with `action` = `method_lock` or `stage_transition`).
5. The **transition engine** validates and applies these transitions:
   - Uses guard logic to ensure transitions are legal given the current stage.
   - Writes a `state_events` row keyed by `assistant_message_id` and containing the proposed state update.
   - Updates persistent state (e.g. which methods are locked, which stage is active).

**State Management**
- SQLite DB via `app/db.py`.
- `state_events` table stores one event per assistant message; this is the **source of truth** for state transitions.
- Session-specific state (current stage, list of methods, remaining/locked methods) is materialized from DB when building prompts.

**Validation / Guardrails**
- Only **recognized phrases** in the LLM output (via regex) can cause state changes.
- `state_schema` restricts actions to a small enum: `none`, `method_lock`, `stage_transition`.
- Handoff behavior (to practice engine) is guarded: `handoff_mode` requires at least one locked stage before allowing a “handout” to be generated.
- The transition engine treats `assistant_message_id` as an idempotency key so an LLM retry cannot accidentally re-apply a transition.

**Persistence**
- SQLite schema initialized and migrated via `_migrate_schema()` in `app/db.py`.
- `state_events`, `messages`, and content tables are stored in a single DB file.

**Why This Architecture**
- A **stage-based FSM** is a natural fit for a curriculum that must progress in a specific order.
- Regex-based parsing keeps the system simple and inspectable while still leveraging the LLM for pedagogy.
- Idempotent `state_events` makes the system robust to network/streaming glitches and UI refreshes.

---

### Concept Practice Engine (`Ai/teacher_pract`)

**System Name**  
Concept Practice Engine (Practice-First Apprenticeship Engine)

**Purpose**  
A practice engine that drills specific topics and concepts, often using “handouts” generated from the Data Analytics Apprenticeship. It focuses on practicing exactly what was previously taught, one concept and one challenge at a time.

**In plain English**  
You pick a topic and the app drills you one concept at a time. The AI can only change your progress when it outputs a strict JSON block that passes our checks; otherwise we ignore or fall back safely so the learning path stays correct.

**Terms recruiters listen for:** **schema validation**, **guard conditions**, **STATE_UPDATE** JSON, **validate_state_update**, **idempotent**, **regex fallback** (no destructive actions).

**Key Components**
- **UI**: `streamlit_app.py` (Streamlit) and `desktop.py` (Flet)
- **Orchestration**: `orchestration.py` (conversation loop + state updates)
- **State Parser**: `state_parser.py`
  - Parses a strict `STATE_UPDATE` JSON block between markers.
  - Provides a regex fallback when the strict format is missing.
- **State Schema**: `state_schema.py`
  - `ProposedTransition` dataclass with fields for `action`, `concept_number`, `concept_name`, `decomposition`, `topic`.
  - `validate_state_update()` function that enforces a strict schema.
- **Transition Engine**: `transition_engine.py` (FSM with guards)
- **Knowledge / Prompt Files**:
  - `prompt_pract_v1.md`
  - `knowledge_file_v7.md`
- **Database**: `db.py` (SQLite schema, state_events logging, parser metrics)

**Workflow**
1. User selects a topic or loads a handout (topics and handouts are stored in the DB).
2. Orchestration loads current state:
   - Current topic and category.
   - List of decomposed concepts.
   - Which concept is currently locked and being drilled.
3. It builds a system prompt using `prompt_pract_v1.md`, the current concept, and learner context, then streams the LLM reply.
4. At the end of the reply, the system looks for a `STATE_UPDATE` block:

   ```text
   <<<STATE_UPDATE_START>>>
   {"action": "...", ...}
   <<<STATE_UPDATE_END>>>
   ```

5. The JSON inside is parsed and passed to `validate_state_update()`:
   - Ensures only allowed keys (`action`, `concept_number`, `concept_name`, `decomposition`, `topic`) are present.
   - Verifies types (e.g. `concept_number` must be an `int`, `decomposition` a list of strings).
   - Restricts `action` to a fixed enum: `none`, `lock`, `announce`, `decompose`, `topic_change`.
6. If validation passes, the resulting `ProposedTransition` is passed to `transition_engine.apply_transitions()`, which:
   - Runs guard functions (`_guard_lock`, `_guard_announce`, `_guard_decompose`, `_guard_topic_change`).
   - Writes a `state_events` row tied to `assistant_message_id` along with parser version/topic schema version.
   - Applies the state mutation (lock a concept, update decomposition, change topic) if allowed.
7. If validation fails:
   - The parser may fall back to regex to recover some non-destructive updates.
   - The engine explicitly **disallows lock actions** when using regex fallback for safety.
   - Parser metrics (`json_success`, `regex_fallback`, `failed`) are recorded.

**State Management**
- SQLite DB with:
  - Topic/handout tables.
  - `state_events` table keyed by `assistant_message_id` (idempotency).
  - Parser and schema version fields (for tracking evolution).
- Runtime state reconstructed from `state_events` and topic metadata at each turn.

**Validation / Guardrails**
- **Strict JSON schema** for `STATE_UPDATE`.
- **Unknown fields are rejected** to prevent prompt drift from silently changing behavior.
- **Guard functions** enforce logical correctness:
  - Only lock valid concept numbers.
  - Decomposition length and concept name constraints.
  - Topic changes must be well-formed.
- **Regex fallback** is allowed for non-destructive actions, but explicitly blocked from performing locks.
- **Idempotent application** of transitions based on `assistant_message_id`.

**Persistence**
- SQLite DB via `db.py` with migrations and metrics columns.

**Why This Architecture**
- Practice flows are highly sensitive to incorrect state changes; a bad lock or topic change can derail the entire apprenticeship.
- The combination of **strict JSON schema**, **guards**, and **idempotent events** allows the system to use a non-deterministic LLM safely while maintaining a predictable learning progression.

---

### Code & Analytics Apprenticeship (`Ai/metacode`)

**System Name**  
Code & Analytics Apprenticeship (Stateful Apprenticeship Engine for Programming and Technology)

**Purpose**  
A topic-based apprenticeship engine that teaches programming and analytics concepts (e.g. Python, SQL, analytics topics). It uses the same core pattern as the Concept Practice Engine but is oriented around teaching rather than purely drilling.

**In plain English**  
Same idea as the Concept Practice Engine: the AI teaches you a topic step by step, and we only update your progress when the AI’s structured output passes validation and guards.

**Terms recruiters listen for:** **state machine**, **schema validation**, **guard conditions**, **topic decomposition**, **idempotent** state updates.

**Key Components**
- **UI**: `streamlit_app.py` (Streamlit) and `desktop.py` (Flet)
- **Orchestration**: `orchestration.py` (conversation + state loop)
- **Transition Engine**: `transition_engine.py` (same FSM pattern as teacher_pract)
- **State Schema**: `state_schema.py` (same structure and `validate_state_update()` as practice engine)
- **State Parser**: `state_parser.py` (shared JSON+regex parsing logic)
- **Prompts / Knowledge**:
  - `prompt_v7.md` (“Stateful Apprenticeship Engine for Programming and Technology”)
  - `knowledge_file_v7.md`
- **Database**: `db.py` (topics, state_events, parser metrics, schema versions)

**Workflow**
- Very similar to Concept Practice Engine:
  1. User selects or provides a topic (e.g. “window functions in SQL” or “pandas joins”).
  2. Orchestration loads topic concepts and current mastery state.
  3. Builds a system prompt (`prompt_v7.md`) describing:
     - The apprenticeship contract.
     - The topic’s decomposed concept list.
     - Current locked/announced concepts.
  4. Streams the LLM reply to the user.
  5. Parses a `STATE_UPDATE` block using the same JSON+regex strategy.
  6. Validates and applies transitions via the shared `transition_engine`.

**State Management**
- Same as Concept Practice Engine: `state_events` table with parser and schema versions, topics stored in DB, runtime state reconstructed at each turn.

**Validation / Guardrails**
- Identical pattern to teacher_pract:
  - `validate_state_update()` enforces schema and enums.
  - Guard functions restrict invalid actions.
  - Regex fallback cannot perform destructive actions.
  - Idempotent updates via `assistant_message_id`.

**Persistence**
- SQLite DB with topic and mastery schema version tracking in `db.py`.

**Why This Architecture**
- Reuses the proven practice-engine state machine and validation stack.
- Keeps “what to teach” (prompts and knowledge files) separate from “how to move through states,” which lives in the FSM and DB schema.

---

## 3. AI Workflow Diagrams (ASCII)

These diagrams reflect the actual flows implemented in the code.

### Personal Task & Goal Assistant

```text
User Input
  ↓
Phase 1 LLM (chat.txt)
  ↓
Save user + assistant messages (SQLite)
  ↓
Phase 2 LLM (extract.txt)
  ↓
Parse JSON events
  ↓
Filter allowed event types
  ↓
Append events to events table
  ↓
Project events into tasks/goals/time_logs
  ↓
Updated state available for next turn
```

### Data Analytics Apprenticeship

```text
User Input
  ↓
Load current stage + locked methods (DB)
  ↓
Build system prompt from docs + state
  ↓
LLM response (teaching + instructions)
  ↓
Regex-based state parsing (method locks, stage transitions)
  ↓
Map to ProposedTransition (action, method_number, stage)
  ↓
Transition engine guards + apply
  ↓
Write state_events row (idempotent per assistant_message_id)
  ↓
Updated stage/method state
```

### Concept Practice Engine / Code & Analytics Apprenticeship

```text
User Input
  ↓
Load topic, concepts, mastery state (DB)
  ↓
Build system prompt from topic + state
  ↓
LLM response (practice dialogue)
  ↓
Extract STATE_UPDATE JSON block (or regex fallback)
  ↓
validate_state_update (schema + enum checks)
  ↓
Transition engine guards (lock, announce, decompose, topic_change)
  ↓
Write state_events row (with parser + schema versions)
  ↓
Updated concept/topic state
```

---

## 4. Key Engineering Decisions

Each of these decisions is visible in the code and documentation.

- **SQLite as the primary database**
  - Used across `Ai/assistant`, `Ai/teacher`, `Ai/teacher_pract`, `Ai/metacode`, and `career txt/the-dmrb`.
  - Chosen because it is file-based, requires no external infrastructure, and is sufficient for single-user and small-team workloads.
  - Implemented via helpers like `db/database.py`, `app/db.py`, and `career txt/the-dmrb/db/connection.py` with migrations and integrity checks.

- **Two-phase LLM workflow for the assistant**
  - Defined in `Ai/assistant/agent/orchestrator.py` and described in `docs/ARCHITECTURE_AND_PRODUCTION.md`.
  - Phase 1 focuses on conversation and user-facing value.
  - Phase 2 focuses on extracting structured events for state updates.
  - Impact: The user always receives a response even if extraction fails; state mutations are decoupled from conversation reliability.

- **Structured JSON outputs and schema validation**
  - Practice and apprenticeship engines (`Ai/teacher_pract`, `Ai/metacode`) require a `STATE_UPDATE` JSON object.
  - `state_schema.validate_state_update()` rejects unknown fields and invalid types, ensuring state transitions are machine-checkable.
  - Impact: Prevents prompt drift and malformed outputs from silently corrupting learning state.

- **Regex fallback with restricted actions**
  - When the strict JSON block is missing or invalid, `state_parser.py` falls back to regex to salvage non-destructive information.
  - `transition_engine` explicitly blocks destructive actions (like `lock`) when the parser is in regex mode.
  - Impact: Improves robustness to imperfect LLM behavior while keeping critical actions safe.

- **Event sourcing for the assistant**
  - Every change (task, goal, time log, note) is represented as an event in the `events` table.
  - `project_event` computes the current state from events.
  - Impact: Adds auditability, supports replay if projector logic evolves, and decouples write history from read models.

- **Idempotent state updates in apprenticeship engines**
  - `state_events` tables in teacher, teacher_pract, and metacode are keyed by `assistant_message_id`.
  - Transition engines return early if a given message has already been applied.
  - Impact: Safe to retry or reprocess messages without double-applying transitions.

- **Domain-driven decomposition in the-dmrb**
  - `career txt/the-dmrb` separates layers into `db/`, `domain/`, and `services/`.
  - Domain contains pure enrichment, lifecycle, risk, SLA, and identity logic.
  - Services orchestrate imports, reconciliations, and board queries; UI layer is kept thin.
  - Impact: Makes the Operational Turnover Intelligence (Make-Ready) app maintainable and testable, with domain logic independent from UI and persistence.

---

## 5. Reliability and Guardrails

### Personal Task & Goal Assistant

- **Whitelisted event types** (`ALLOWED_EVENT_TYPES`) ensure only recognized mutations are applied.
- **Best-effort extraction**: If the extraction LLM output cannot be parsed or validated, the system skips state updates but still returns a reply.
- **Projector encapsulation**: All changes to `tasks`, `goals`, and `time_logs` flow through projector functions, not direct LLM writes.
- **Context-based prompts** (`detect_day_context`, `load_known_facts`) keep suggestions grounded in actual logged behavior.

### Data Analytics Apprenticeship

- **Regex-based parsing** ensures only explicit, human-readable signals in the LLM output affect state.
- **Limited action space**: `state_schema` allows only `none`, `method_lock`, and `stage_transition`.
- **Handoff guard**: Handoff to practice/handout mode is only allowed when sufficient progress (locked stages) exists.
- **Idempotent state_events**: Each assistant message can produce at most one applied transition set.

### Concept Practice Engine and Code & Analytics Apprenticeship

- **Strict schema validation** via `validate_state_update()`:
  - Rejects extra keys.
  - Enforces types and length constraints.
  - Restricts `action` to a small enum.
- **Guard functions in `transition_engine`**:
  - Confirm that concept numbers and topics are valid for the current state.
  - Block illegal transitions (e.g. locking a non-existent concept).
- **Regex fallback safety**:
  - Fallback parsing mode cannot perform locks.
  - Fallback is used for softer updates, like announcements.
- **Parser metrics and schema versions**:
  - DB columns track parser outcomes and versions, making it easier to debug parsing issues.

### Operational Turnover Intelligence — Make-Ready (the-dmrb)

- **Strict boundaries** (from its README): UI has no business logic; domain layer is pure; services orchestrate transactions and write audit logs; DB layer handles persistence only.
- **Migrations and integrity checks**: `db/connection.py` and `db/migrations` ensure schema evolution is explicit and recoverable.
- **Domain invariants**: Tests such as `test_legal_confirmation_invariant`, `test_manual_availability`, and `test_sla_effective_anchor` enforce business rules around legal confirmation, manual availability, and SLA behavior.

---

## 6. Data Projects

### Operational Turnover Intelligence (OTI)

**Problem**  
Coordinating make-ready work across apartment units and vendors, understanding which units are on track vs stalled, and reconciling “board dates” with official property reconciliation reports.

**Dataset**
- Primary source: `data/raw/DMRB_board.csv` (exported from a DMRB board sheet).
- Contains:
  - Unit identifier and status columns.
  - Move-out, ready, and move-in dates.
  - Task status dropdowns (inspection, paint, make-ready, housekeeping, CC).
  - Assignment, W/D, QC, and notes columns.
- Computed columns like DV (days vacant) and detailed task dates are removed from the raw CSV and recomputed in the pipeline.

**Pipeline**
- Implemented in `pipeline/` and wired in `pages/1_Operational_Turnover_Intelligence.py`:
  - `load_data(DATA_ROOT)`:
    - Reads `DMRB_board.csv`.
    - Normalizes column names.
    - Parses dates as datetime.
  - `clean_data(data)`:
    - Normalizes unit codes (extracts phase, building, and unit components).
    - Filters to operationally relevant phases (e.g. phases 5/7/8).
    - Ensures date columns are consistently typed.
  - `transform(cleaned)`:
    - Shapes the data into an operational “board” model aligned with unit/turnover/task entities.
  - `enrich(board_df)`:
    - Computes DV (days vacant), task aging, task pipeline status, stall flags, and SLA-like signals.
  - `compute_metrics(board_df)`:
    - Produces high-level metrics and crosstabs (e.g. counts by phase and status, task state distributions).

**Cleaning Steps**
- Strip unit identifiers down to a canonical `phase-building-unit` pattern.
- Filter down to active turnover phases only.
- Remove Excel-derived formula columns to ensure all metrics are computed reproducibly in Python.
- Normalize date and status fields for consistent downstream logic.

**Transformations**
- Map raw board columns into a schema aligned with a conceptual `unit`, `turnover`, and `task` model.
- Compute task pipeline states (e.g. which task is current vs next).
- Derive stall indicators and readiness flags.

**Metrics**
- Volume of units by phase and readiness state.
- Task pipeline counts and aging.
- Indicators of stalled units and SLA-type breaches.

**Business Insight**
- Shows how to go from a messy operations spreadsheet to a structured analytics pipeline.
- Highlights where units are stalled, how tasks progress, and how board-level data can be reconciled with canonical unit/turnover/task structures.

**Terms recruiters listen for:** **ETL**, **load → clean → transform → enrich**, **normalization**, **derived metrics**, **pandas**, **unit/turnover/task model**.

---

### Data Playground / Analytics Playground

**Problem**  
You needed a controlled, repeatable environment to build **muscle memory** in SQL and pandas: creating schemas, inserting data, joining tables, and writing analytical queries. Instead of ad-hoc examples, you created a small but realistic schema for customers, orders, products, employees, and payments and turned it into a portable lab you can reuse and extend.

**Dataset & Schema**
- Defined in `pages/5_Data_Playground.py` as reference code.
- Tables:
  - `departments` → parent of `employees`
  - `customers` → parent of `orders`
  - `employees` → references `departments`
  - `products`
  - `orders` → references `customers`
  - `order_items` → bridge between `orders` and `products`
  - `projects`
  - `payments` → references `orders`
- Domain shape: a **mini operational warehouse** for:
  - HR data (departments, employees)
  - Customer & order data (customers, orders, order_items, payments)
  - Projects and budgets

**Pipeline / Structure**
- The Streamlit page is organized as a teaching pipeline:
  - **SQL Setup**
    - `sqlite3` with `DB_PATH = "practice.db"`.
    - A reusable `execute(sql, params=None, fetch=False)` helper that:
      - Opens a connection with a `with` block.
      - Turns `PRAGMA foreign_keys = ON;` for referential integrity.
  - **Create Tables**
    - Full DDL for all eight tables using `CREATE TABLE IF NOT EXISTS`.
    - Demonstrates primary keys and foreign-key relationships.
  - **Insert Data**
    - Seed data arrays (e.g. `departments_data`, `customers_data`, `employees_data`).
    - Uses `executemany()` with **parameterized INSERTs**, not string concatenation.
  - **Schema Reference**
    - Narrative description of table roles and relationships.
  - **Pandas Lab & SQL Queries**
    - Mirrors your notebooks: “Basics”, “AND/OR”, “Group/Aggregation”, “Join/Merge”.
    - Shows how to:
      - Read from SQLite into DataFrames.
      - Filter, group, aggregate, and merge.
      - Express the same logic in SQL and in pandas.

**Cleaning Steps / Safety**
- “Clean slate” block drops all tables in a safe order (`order_items` and `payments` first, then parents).
- Foreign keys are enforced explicitly via `PRAGMA foreign_keys = ON;`.
- Parameterized queries (`?` placeholders) prevent SQL-injection patterns, even in a learning context.

**Transformations and Metrics**
- Within this lab, the “transformations” are about **query design patterns**:
  - Basic selects and filters.
  - Multi-condition filters (AND/OR).
  - Grouped aggregates (e.g. revenue by customer, orders by city).
  - Joins across the schema (e.g. customers → orders → order_items → products).
- The focus is less on a single business metric and more on:
  - Translating real-world questions into joins and aggregates.
  - Seeing the same logic in **SQL vs pandas** and understanding how they align.

**Business Insight**
- Even though it’s a practice environment, the schema is shaped like real analytics work:
  - Customers, orders, payments, and projects.
- This lab underpins your other projects:
  - It’s where you built query discipline that shows up later in OTI and the-dmrb.
  - It demonstrates that you understand **DDL, DML, foreign keys, parameterized queries, and pandas joins**, not just high-level AI concepts.

**Terms recruiters listen for:** **DDL**, **DML**, **foreign keys**, **parameterized queries**, **executemany**, **SQLite**, **pandas** (read, filter, group, merge).

---

### Operational Turnover Intelligence — Make-Ready (the-dmrb)

**Problem**
Provide an operational app for apartment turnover lifecycle and make-ready management, with a focus on making the lifecycle observable, reconcilable, and auditable across multiple input reports.

**Dataset**
- Multiple CSV inputs representing:
  - Move-outs.
  - Pending move-ins.
  - Available units.
  - Pending financial approvals (FAs).
  - DMRB board exports.
- These are imported via `services/import_service.py` into a SQLite-backed `cockpit.db`.

**Pipeline**
- **Import layer** (`services/import_service.py`):
  - Parses each report type.
  - Ensures units and related entities exist (via `db/repository.py`).
  - Creates or updates `turnover` and `task` rows as needed.
  - Writes `import_batch` and `import_row` records for traceability.
- **Domain enrichment layer** (`domain/enrichment.py`):
  - When building board views, computes:
    - DV and DTBR.
    - Phase and N/V/M states.
    - Operational state (e.g. stalled, active, ready).
    - W/D summary and assignee display.
    - SLA and risk flags.
- **SLA and risk engines** (`domain/sla_engine.py`, `domain/risk_engine.py` + `services/sla_service.py`, `services/risk_service.py`):
  - Evaluate SLA breaches and risk flags for each turnover.
  - Persist `sla_event` and `risk_flag` rows to capture time-based and rule-based risk.
- **Board query service** (`services/board_query_service.py`):
  - Joins core tables into flat “board” and “flag bridge” row sets.
  - Calls `domain.enrichment.enrich_row()` per row to compute derived metrics.
  - Feeds the UI with enriched, readable data.

**Cleaning Steps**
- Normalize unit identifiers using `domain/unit_identity.py`.
- Enforce referential integrity via foreign keys in `db/schema.sql`.
- Use migrations in `db/migrations/` to evolve the schema safely.

**Transformations**
- Convert raw import rows into canonical `unit`, `turnover`, `task`, `phase`, and `building` entities.
- Enrich these with lifecycle phase, DV, and SLA status.
- Build derived views that align with operator mental models (boards, bridges, detail views).

**Metrics / Outputs**
- Turnover board table (`get_dmrb_board_rows`).
- Flag bridge view for risk and SLA exceptions.
- Turnover detail views with tasks, notes, and risk/SLA context.

**Business Insight**
- Encodes domain rules around apartment turnover into deterministic functions.
- Provides a foundation for reliable make-ready operations and reporting.

**Terms recruiters listen for:** **domain model**, **domain layer**, **services layer**, **enrichment**, **lifecycle**, **SLA**, **risk engine**, **migrations**, **reconciliation**.

---

## 7. Technology Map

**Languages**
- Python

**Frameworks / UI**
- Streamlit (portfolio app, OTI page, AI apps, the-dmrb prototype)
- Flet (desktop variants for apprenticeship and practice engines)

**Databases and Storage**
- SQLite (assistant, apprenticeship/practice engines, the-dmrb)
- CSV files as input sources for OTI and the-dmrb imports

**AI / LLM APIs**
- OpenAI API (via `openai` Python client)

**Data Processing / Analytics**
- Pandas
- NumPy (in some enrichment functions)

**Visualization**
- Streamlit tables and charts
- Custom charts under `visuals/` (for analytics playground)

**Not Present**
- No FastAPI or other web frameworks in the codebase.
- No external cloud databases (e.g. Postgres) wired into these projects.

---

## 8. Interview Explanation Scripts

These are short scripts you can almost memorize and adapt.

### Personal Task & Goal Assistant

**Explain this system in 60 seconds**  
“I built a personal task and goal assistant that turns conversation into structured operational data. The architecture uses a two-phase LLM workflow: the first phase generates the assistant’s reply, and the second phase extracts structured JSON events like `TASK_CREATED` or `GOAL_UPDATED`. Those events are appended to an event log in SQLite and then projected into current-state tables for tasks, goals, and time logs. This gives me a conversational interface on top of an event-sourced system that I can audit, replay, and evolve over time.”

**Explain the architecture**  
“The system has three layers. The Streamlit UI handles chat and displays state. The orchestrator layer manages the two-phase LLM process and is the only part that talks to the model. The data layer is an event log plus projections: events are stored in an append-only table, and projector functions update normalized tables for tasks, goals, and time logs. All state changes are driven by validated events, never by raw LLM output.”

**Explain reliability safeguards**  
“The assistant only accepts a small set of whitelisted event types, and all events are validated before being applied. The extraction phase is best-effort—if parsing fails, the user still gets a reply and the system simply skips state updates for that turn. Because state is driven by an event log and projections, I can debug or replay behavior and improve projector logic later without losing history.”

**Explain how AI integrates with workflows**  
“The LLM handles the natural language side—understanding what I’m asking for and generating helpful responses. The workflows themselves are encoded in the event types and projector functions. For example, asking to ‘finish this task and log 45 minutes’ results in a conversational reply plus structured events that close the task and insert a time entry. The AI is embedded inside a system that enforces how tasks, goals, and time are represented and updated.”

---

### Concept Practice Engine / Code & Analytics Apprenticeship

**Explain this system in 60 seconds**  
“I built a practice engine that uses an LLM to drill programming and analytics concepts one at a time, but with a strict state machine behind it. Each LLM response can include a `STATE_UPDATE` JSON block describing actions like locking a concept, decomposing a topic, or changing topics. That JSON is validated against a schema and then passed into a transition engine that enforces guardrails and applies idempotent state transitions in SQLite. The result is a conversational tutor with a reliable, inspectable notion of learner state.”

**Explain the architecture**  
“The architecture is UI → orchestration → state machine. Streamlit or Flet handles the user interface. Orchestration builds system prompts from the current topic and learner state, streams the LLM response, and then extracts any `STATE_UPDATE` block. The state machine layer consists of a strict JSON schema (`validate_state_update`), a transition engine with guard functions, and a `state_events` table that records proposed and applied transitions keyed by message ID.”

**Explain reliability safeguards**  
“I never let raw LLM output mutate the learner’s state. The `STATE_UPDATE` JSON has to pass schema validation first—unknown fields are rejected and actions are restricted to an enum. Guard functions check that concept numbers and topics are valid for the current state. If the strict JSON block is missing, the parser can fall back to regex, but in that mode destructive actions like locking concepts are disabled. All transitions are idempotent per assistant message, so retries cannot double-apply updates.”

**Explain how AI integrates with workflows**  
“The LLM provides the explanations, questions, and feedback. The workflow of what gets practiced, in what order, and how progress is recorded is driven by the state machine and database. This separation means I can treat the LLM as a noisy but useful generator, while keeping the progression of topics and concepts deterministic and auditable.”

---

### Turnover Intelligence and the-dmrb

**Explain this system in 60 seconds**  
“On the data side I built a turnover intelligence pipeline and an operational cockpit for apartment make-ready workflows. The pipeline takes a DMRB board export, cleans and transforms it into a canonical unit/turnover/task model, and enriches it with DV, aging, task pipeline status, and stall flags. The cockpit goes further: it imports multiple report types into a normalized SQLite schema, runs deterministic domain logic for lifecycle, SLA, and risk, and then drives Streamlit dashboards that show board views, flag bridges, and detailed turnover timelines.”

**Explain the architecture**  
“For the portfolio pipeline, the architecture is classic ETL: load raw CSV, clean and normalize fields, transform into a modeled table, enrich with derived metrics, and then feed a Streamlit case study. For the-dmrb, the architecture is layered: a DB layer with migrations and schema, a domain layer with pure enrichment, lifecycle, risk, and SLA logic, a services layer for imports and reconciliations, and a UI layer that only reads enriched data. That separation keeps the operational rules testable and independent from the interface.”

---

## 9. Whiteboard Diagrams (ASCII)

### 1. AI Workflow Pipeline (Assistant / Practice Engines)

```text
User
  ↓
LLM Response
  ↓
Structured Extraction (JSON / regex)
  ↓
Schema Validation
  ↓
Guarded State Transitions
  ↓
SQLite State (events + tables)
  ↓
Next Turn Context
```

### 2. System Architecture (Assistant Example)

```text
Streamlit UI
  ↓
Orchestrator (phase1 + phase2)
  ↓
OpenAI LLM
  ↓
Event Store (append-only events)
  ↓
Projector (tasks/goals/time_logs)
  ↓
SQLite Database
  ↓
Dashboards / Context Loaders
```

### 3. Guardrail Validation Layer (Practice Engines)

```text
LLM Output
  ↓
Extract STATE_UPDATE Block
  ↓
validate_state_update (schema, enums, lengths)
  ↓
Guard Functions (lock, announce, decompose, topic_change)
  ↓
Idempotent state_events Write (assistant_message_id)
  ↓
Apply State Mutation (if allowed)
```

---

## 10. Likely Interview Questions (with Model Answers)

**Q1. Walk me through the architecture of your task and goal assistant.**  
**A.** “The assistant is a Streamlit app on top of an event-sourced core. The UI sends user messages to an orchestrator that runs a two-phase LLM process: phase one generates the reply, phase two extracts structured events. Those events are appended to an `events` table in SQLite and projected into normalized tables for tasks, goals, and time logs. All state changes come from these events, not directly from the model, which gives me auditability and the ability to replay or change projection logic later.”

**Q2. How does your system prevent unreliable AI output from corrupting state?**  
**A.** “I never let raw LLM text write to the database. In the assistant, only whitelisted event types are allowed and extraction is best-effort—if parsing fails, the state is left unchanged. In the practice engines, the LLM must produce a `STATE_UPDATE` JSON object that passes schema validation; unknown fields or wrong types cause the update to be rejected. Guard functions in the transition engine enforce additional invariants, and destructive actions are disabled when the parser falls back to regex. Together, that means the AI can be creative in explanations but constrained in how it can change state.”

**Q3. How does state persistence work in your apprenticeship and practice engines?**  
**A.** “Each assistant message can propose a state transition—for example, locking a concept or advancing a stage. Those proposals are recorded in a `state_events` table keyed by `assistant_message_id`, which makes them idempotent. At runtime, the system reconstructs current state by reading from that table and joining in topic and concept metadata. Because events are recorded separately from the current view of state, I can debug or adjust transition logic without losing a history of what happened.”

**Q4. Why did you choose SQLite instead of a cloud database?**  
**A.** “These systems are designed as offline-first or single-user tools and portfolio projects, so a file-based database is a good fit. SQLite gives me transactions, indexes, foreign keys, and WAL mode without needing to run a separate service. It keeps deployment and development friction low while still allowing me to design realistic schemas, migrations, and domain logic. The same pattern shows up in my make-ready app, where SQLite backs a full domain model for units, turnovers, tasks, SLA events, and risk flags in my make-ready app.”

**Q5. What happens if the extraction phase in your assistant fails?**  
**A.** “If the extraction LLM fails or returns invalid JSON, the user still receives the conversational reply from phase one. The system logs the failure, skips event creation and projection for that turn, and continues. That’s intentional: conversation reliability and state updates are decoupled, so a parsing issue never crashes the UI or corrupts state.”

**Q6. How would you identify where AI automation can help in a new operational workflow?**  
**A.** “I start by mapping the workflow as a sequence of states and events: where data is created, where it’s transformed, and where decisions happen. Then I look for steps that rely on interpreting unstructured inputs—emails, notes, board comments—or where humans convert natural language into structured updates. Those are good candidates for an AI layer similar to my assistant and practice engines, where the model sits behind a state machine or event-sourced interface instead of directly controlling the system.”

**Q7. What is the difference between using AI and building AI systems?**  
**A.** “Using AI means prompting a model and accepting its response. Building AI systems means designing the architecture around the model: orchestration, state machines, validation layers, persistence, and integration with real workflows. In my projects the model is one component inside a larger system that enforces how data flows, how state changes are validated, and how results are stored and surfaced.”

**Q8. How do your turnover analytics projects demonstrate engineering thinking, not just dashboards?**  
**A.** “In the OTI project, I start from a raw operational spreadsheet and build a full ETL pipeline: loading, cleaning, transforming, and enriching the data before visualizing it. In the-dmrb, I go further by encoding lifecycle, SLA, and risk rules as deterministic domain functions and wiring them to a normalized schema with migrations and tests. The focus is on designing the data model and logic that make dashboards trustworthy, not just drawing charts.”

**Q9. What is event sourcing and why did you use it?**  
**A. (Clear language)** "Instead of overwriting current state every time something changes, we append each change as an event to a log. Current state is computed by replaying those events. That gives us a full history and we can fix or improve logic later." **Terms to include:** append-only event log, projections, auditability, replay.

**Q10. How would you design a system where AI suggests actions but a human approves them?**  
**A. (Clear language)** "I'd have AI propose structured actions (e.g. JSON), validate them against a schema, and store them as pending. Only after human approval would we apply them to real state. That's state (pending vs applied), validation, and optionally an event log for audit." **Terms to include:** state, validation, schema, event log.

**Q11. Explain your ETL pipeline in 60 seconds.**  
**A. (Clear language)** "We load the raw board CSV, clean and normalize unit codes and dates, transform into a canonical unit/turnover/task shape, enrich with days vacant and stall flags, then compute metrics and feed the Streamlit case study." **Terms to include:** load, clean, transform, enrich, normalization, derived metrics, pandas.

**Q12. What is the role of guard conditions in your practice engine?**  
**A. (Clear language)** "Even when the AI outputs valid JSON, we check that the proposed change is allowed—e.g. the concept number exists. Those checks are guard conditions; they keep the learning path correct." **Terms to include:** guard conditions, validation, state machine, invariants.

**Q13. How would you make a chatbot that updates a database from conversation?**  
**A. (Clear language)** "I'd use a two-phase design: one phase for the reply, a second that extracts structured events from the turn. Events pass schema validation and then get appended to an event log or applied through a controlled write path. The chatbot never writes directly to the DB." **Terms to include:** two-phase LLM, extraction, schema validation, event store.

**Q14. What is idempotency and where do you use it?**  
**A. (Clear language)** "Idempotency means doing the same thing twice has the same effect as once. In my apprenticeship engines, each assistant message can apply its state update only once; we key by message ID so retries don't double-apply." **Terms to include:** idempotent, assistant_message_id, state_events.

**Q15. How do you handle it when the AI outputs something you didn't expect?**  
**A. (Clear language)** "We don't trust raw output. In the assistant we only accept a fixed set of event types; anything else is ignored. In the practice engine the JSON must pass schema validation and guards. If it doesn't, we skip the state update—and in the assistant the user still got their reply." **Terms to include:** whitelist, schema validation, guard conditions, best-effort extraction.

**Q16. What is the difference between the Data Analytics Apprenticeship and the Concept Practice Engine?**  
**A. (Clear language)** "The apprenticeship teaches a fixed curriculum in stages (S0–S12) and uses regex to detect method locks and stage moves. The practice engine is topic-based and uses a strict JSON block with schema validation and guards. Both use state machines and idempotent updates." **Terms to include:** stage-based vs topic-based, regex vs JSON schema, state machine, idempotent.

**Q17. Why use SQLite instead of Postgres or a cloud DB?**  
**A. (Clear language)** "For these projects I wanted a single file, no external infra, and realistic schema design—foreign keys, migrations, transactions. SQLite gives that for single-user and portfolio use. The same architecture would carry over to Postgres if we needed scale." **Terms to include:** SQLite, transactions, foreign keys, migrations.

**Q18. How do you know your AI system is reliable enough for production?**  
**A. (Clear language)** "I add validation layers—allowed event types, schema checks, guard conditions—and make state updates idempotent. The AI can fail or output junk; the system only applies changes that pass those checks. I also use an event log where possible for audit and replay." **Terms to include:** validation, schema, guards, idempotent, event log, auditability.

**Q19. Describe your make-ready app in one minute.**  
**A. (Clear language)** "It's an operational app for apartment turnover and make-ready. We import CSV reports into SQLite with a domain model—units, turnovers, tasks. A domain layer computes enrichment, lifecycle, SLA, and risk. Services handle imports and reconciliations; the UI displays enriched data. Clean separation: DB, domain, services, UI." **Terms to include:** domain model, domain layer, services, enrichment, SLA, risk, migrations.

**Q20. What would you improve in your assistant if you had more time?**  
**A. (Clear language)** "I'd add observability—logging when extraction fails, metrics on event types. I might add a review step for certain events before they're applied. The core design—two-phase, event sourcing, validation—would stay; I'd harden monitoring and optional human-in-the-loop." **Terms to include:** observability, logging, event types, human-in-the-loop, two-phase, event sourcing.

---

## 11. Portfolio Strengths

- **Event-sourced AI assistant** with a clear separation between conversation and state updates.
- **State machine–driven apprenticeship engines** with explicit transition engines and guards.
- **Strict schema validation and guardrail layers** around all AI-driven state changes.
- **Idempotent, versioned state events** that allow safe retries and evolution over time.
- **Layered architecture in the-dmrb** (DB, domain, services, UI) with migrations and tests.
- **End-to-end ETL and enrichment pipelines** for turnover analytics, demonstrating SQL and pandas skills grounded in real operations.
- **Consistent focus on reliability over raw model power**, visible in event logs, schema checks, and tests.

---

## 12. Portfolio Weaknesses

- **No FastAPI or HTTP APIs** are implemented in this repository; API integration experience would need to be supplemented separately.
- **Nightwing engine is conceptual only** and not represented as code, so interview conversations about it should be framed as design ideas, not implemented systems.
- **Inventory and revenue analytics** are present as stubs (SQL files and pages) without full pipelines or dashboards.
- **Observability is local**: there is basic parser and schema version logging in the apprenticeship engines and tests in the-dmrb, but no centralized logging, metrics collection, or distributed monitoring.
- **AI apps have limited test coverage** visible in the repo compared to the-dmrb, which has a richer test suite for its domain invariants.

---

## 2026 Hiring Lens

**Five signals hiring managers use when evaluating candidates**

1. **Build real systems** – Evidence of architecture, state, persistence, workflows (not just tutorials or toy apps).  
2. **Understand system architecture** – You can describe layers, workflow, state transitions, tradeoffs.  
3. **Control AI, not just use it** – LLM output → structured extraction → schema validation → guard conditions → state transition.  
4. **Understand data** – Relational schemas, ETL, normalization, analytics queries.  
5. **Explain clearly** – Problem → architecture → workflow → reliability → impact.

**One sentence to internalize**

My projects focus on building **reliable systems around AI**. The LLM is one component—its outputs are **validated**, **structured**, and converted into **deterministic state transitions** before affecting system state.

**How your systems map to the five signals**

| System | Real systems | Architecture | Control AI | Data | Explain |
|--------|--------------|--------------|------------|------|---------|
| Personal Task & Goal Assistant | ✓ | ✓ (event sourcing, two-phase) | ✓ (events, validation) | ✓ (SQLite, events) | ✓ |
| Data Analytics Apprenticeship | ✓ | ✓ (state machine) | ✓ (regex, guards) | ✓ (state_events) | ✓ |
| Concept Practice Engine | ✓ | ✓ (FSM, guards) | ✓ (schema, guards) | ✓ | ✓ |
| Code & Analytics Apprenticeship | ✓ | ✓ | ✓ | ✓ | ✓ |
| OTI | ✓ | ✓ (ETL pipeline) | — | ✓ (pandas, metrics) | ✓ |
| Data Playground | ✓ | ✓ (DDL, DML, labs) | — | ✓ (SQL, pandas) | ✓ |
| Operational Turnover Intelligence — Make-Ready | ✓ | ✓ (domain, services) | — | ✓ (domain model) | ✓ |

---

## 13. Key Talking Points

These are ten bullets you can keep in mind when describing your portfolio.

1. **Event-Sourced Assistant** – You designed a personal assistant where every task, goal, and time log is driven by events in SQLite, not raw LLM output.
2. **Two-Phase LLM Workflow** – You separate user-facing conversation from structured extraction, so the app stays usable even when extraction fails.
3. **State Machines for Learning** – Your apprenticeship and practice engines use explicit state machines and transition engines to control progression through concepts and stages.
4. **Strict Schema and Guards** – You wrap AI outputs in JSON schemas, guard functions, and idempotent updates to prevent unreliable behavior.
5. **SQLite with Real Schemas and Migrations** – Across projects, you design realistic schemas, migrations, and integrity checks while keeping deployment simple.
6. **Operational Turnover Intelligence** – You built a full ETL and enrichment pipeline that turns messy board data into actionable turnover metrics.
7. **Operational Turnover Intelligence (Make-Ready) domain model** – You implemented a layered domain model for apartment turnovers, with enrichment, lifecycle, SLA, and risk engines wired into a SQLite DB.
8. **Reliability over Hype** – Your systems treat the LLM as one component in a larger architecture that enforces structure, validation, and auditability.
9. **Operations-to-Systems Story** – You bring domain experience from property operations directly into your data and AI system designs, which is rare for junior engineers.
10. **Interview-Ready Explanations** – You can explain each system in terms of problem → architecture → workflow → reliability, which is exactly how CTOs evaluate AI workflow engineers.

