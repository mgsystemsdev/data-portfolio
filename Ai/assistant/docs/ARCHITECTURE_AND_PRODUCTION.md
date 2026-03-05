# Architecture and Production Documentation

This document describes the full vision, principles, production schema, module boundaries, and how the system is meant to evolve. It is the reference for the long-term, production-ready assistant. For a minimal version you can run in 24 hours and use daily, see **[EXPLORATORY_24H.md](EXPLORATORY_24H.md)**.

---

## Vision and goals

I am building a Streamlit application that includes a chat interface connected to an AI agent using my OpenAI API key. The system will use an SQLite database composed of well-structured, modular tables designed to capture and organize a wide range of personal data, activity records, and long-term behavioral patterns.

This AI agent will function as a highly intelligent personal assistant. It must maintain structured knowledge about my academic background, professional responsibilities, personal goals, daily schedule, study hours, milestones, and long-term objectives. During conversations, the agent should continuously track completed tasks, monitor time spent on activities, log study hours, and ensure that I am progressing toward defined milestones in a coherent, measurable, and optimized manner.

The agent must be capable of holding intelligent, context-aware conversations tailored to education, work, life management, scheduling, productivity optimization, and personal development. Its responses should not be generic; they must be adaptive, analytical, and strategically aligned with improving my overall performance and quality of life.

The system must also support continuous learning. As new information about me emerges, the agent should update the SQLite database dynamically. This includes modifying existing records, creating new tables when necessary, and restructuring data models to accommodate new categories of information. The database architecture should therefore be modular, extensible, and capable of evolving over time.

The primary objective of this project is to research, design, and implement the architecture required for such an adaptive agent. This includes:

- Defining what categories of personal data the agent needs to store.
- Designing modular scripts that handle specialized responsibilities (e.g., scheduling, progress tracking, habit analysis, study monitoring).
- Establishing how each module processes, updates, and retrieves contextual knowledge.
- Structuring an optimized and extensible SQLite schema that supports long-term tracking and dynamic expansion.
- Determining how the agent learns incrementally from conversations.
- Ensuring the entire system remains scalable, logically consistent, and maintainable.

The goal is to create a structured, modular, evolving AI assistant that continuously analyzes my progress, adapts to new information, and actively supports my academic, professional, and personal development in a systematic and intelligent manner.

---

## System decomposition (what you're really building)

### A. Streamlit app layer

- Chat UI (messages, tool traces, "what got logged" confirmations)
- Dashboards (today's plan, weekly progress, habits, milestones, time budget)
- Admin tools (data corrections, merges, "forget this", exports)

### B. Agent runtime layer (stateless compute, stateful memory)

- **Orchestrator:** decides what to do each turn (answer, ask clarifying question, log, schedule, analyze)
- **Tools/Modules:** narrow responsibilities (schedule, task tracking, study tracking, habit analytics, goal planning)
- **Memory subsystem:** short-term (last N turns, active plan for the day/week); long-term (SQLite records + derived summaries)
- **Policy/Guardrails:**
  - "don't silently mutate important facts"
  - "always show a diff for changes to identity/goals"
  - "never create new tables without migration metadata + version bump"

### C. Data layer (SQLite + migrations + event log)

- Canonical tables for identity, goals, tasks, time logs, schedules, and "facts"
- Immutable event log (critical for debugging + recovery)
- A small "schema registry" for controlled evolution (even if you do dynamic extension)

---

## Core design principle: event-sourcing + projections

If the agent "updates rows directly" from chat, you'll eventually get:

- contradictory facts ("I study 2 hrs/day" vs "I study 4 hrs/day")
- unreproducible states ("why did my milestone change?")
- corrupted progress metrics after model mistakes

**Fix:**

- Every turn produces proposed actions.
- Persist actions as events (append-only).
- Update "current state" tables via deterministic projection logic.

This gives you:

- audit trail
- rollback/replay
- ability to improve extractors later and recompute state

---

## SQLite schema (modular, extensible, evolution-safe)

### 3.1 Foundation tables

**users** — user_id (PK), preferred_name, timezone, created_at, updated_at

**conversations** — conversation_id (PK), started_at, ended_at, app_version, model_version

**messages** — message_id (PK), conversation_id (FK), role (user/assistant/system), content, created_at, token_count (optional)

### 3.2 Memory as structured "facts" with provenance

**facts** — fact_id (PK), user_id (FK), key (e.g., education.major, work.role, study.preference), value_json (JSON as TEXT), confidence (0–1), source (conversation_id/message_id, or manual), valid_from, valid_to (supports history), updated_at

Why this works: you can add new fact keys forever without schema changes, while still having structure.

### 3.3 Goals, milestones, tasks: separate intent from execution

**goals** — goal_id (PK), user_id, title, description, category (education/work/health/life/etc), horizon (weekly/quarterly/annual), status (active/paused/completed), start_date, target_date, success_metrics_json (measurable definitions), created_at, updated_at

**milestones** — milestone_id (PK), goal_id (FK), title, target_date, status, completion_criteria_json, created_at, updated_at

**tasks** — task_id (PK), user_id, goal_id (nullable), milestone_id (nullable), title, status (todo/doing/done/canceled), priority, due_at, estimated_minutes, created_at, updated_at

### 3.4 Time tracking as first-class

**time_entries** — entry_id (PK), user_id, task_id (nullable), activity_type (study/work/exercise/admin/etc), start_at, end_at, duration_minutes (stored for query speed), context_json (subject studied, course, location), created_at

### 3.5 Scheduling (recurring + one-offs)

**calendar_events** — event_id (PK), user_id, title, start_at, end_at, location, recurrence_rule (RRULE string or JSON), status, created_at, updated_at

SQLite is fine for storage; recurrence expansion happens in code.

### 3.6 Habits & metrics (derived, not hand-entered)

**metrics_daily** — user_id, date, metric_key (study_minutes, deep_work_minutes, tasks_done), value; primary key (user_id, date, metric_key)

Don't store "habit streak" as truth; derive it.

### 3.7 The event log (non-negotiable)

**events** — event_id (PK), user_id, created_at, event_type (FACT_UPSERT, TASK_CREATE, TASK_UPDATE, TIME_LOG, GOAL_UPDATE, SCHEMA_CHANGE, etc.), payload_json, source_message_id, applied (bool), apply_error (text)

Projection code reads unapplied events, applies them idempotently, marks applied.

### 3.8 Dynamic expansion without chaos

**schema_versions** — version (PK), applied_at, description

**schema_changes** — change_id (PK), version, sql_text, created_at, created_by (agent/manual), status (proposed/applied/rejected), rationale_json

Rule: agent can propose schema changes; your system applies them only if they pass checks (even if "auto-approved" later).

---

## Module boundaries (each one must be testable in isolation)

### A. Conversation Intelligence (orchestrator)

Responsibilities: choose which tools to call; keep the agent from hallucinating changes; manage clarification when data is missing.

Outputs per turn: assistant_reply, proposed_events[] (structured), queries[] used to retrieve context, confidence + warnings.

### B. Context Retrieval module

Pulls relevant facts/goals/tasks for this turn; includes "today plan", "active milestones", "recent time logs". Retrieval strategy: deterministic filters (active goals, due tasks); lightweight semantic index (optional later).

### C. Scheduling module

Creates/updates calendar_events; generates "today agenda"; checks conflicts; recommends blocks (study/work/rest).

### D. Progress Tracking module

Computes milestone status from tasks + time_entries + metrics; detects drift ("you're behind on X by Y hours this week").

### E. Study Monitoring module

Interprets study intents ("I studied calculus 90 minutes"); writes time_entries with course/topic metadata; computes mastery proxy metrics.

### F. Habit Analysis module

Streaks, consistency, triggers, regressions; proposes experiments ("move study block earlier", "reduce context switching").

Each module: only reads/writes via events + a narrow repository interface; never calls the LLM directly except through the orchestrator (keeps behavior consistent).

---

## Incremental learning from conversations

**Step 1: Extract "claims" and "intents"** — From a user message, classify into: Fact claims, Preferences, Commitments, Completions, Time logs, New goals.

**Step 2: Convert to proposed events** — Examples: FACT_UPSERT (education.current_courses += ...), TASK_CREATE ("Read chapter 3"), TIME_LOG (45 minutes study, topic X), GOAL_UPDATE (add internship goal + milestones).

**Step 3: Apply with verification rules** — If a fact conflicts with an existing fact with high confidence → create an event requiring confirmation, or store with lower confidence + validity window. If user says "actually" / "update" → treat as authoritative and end previous validity (valid_to).

**Step 4: Produce user-visible confirmation** — Never silently mutate important records. The assistant reply should include a short "Logged:" section.

---

## Failure modes and hardening

- **Hallucinated updates:** event proposals must include evidence (message_id references); confidence gating (low confidence => ask a question or store as tentative); "diff view" for critical fields (role, degree, deadlines).
- **Schema sprawl:** default to facts.key/value_json extension; only migrate when query performance requires it or a new entity becomes core; require schema_change rationale + tests.
- **Inconsistent time tracking:** no negative durations; no overlaps per "focus category" unless explicitly allowed; when user reports time without timestamps, store as "approximate" with flags.
- **Goal drift and metric gaming:** tie goals to measurable success_metrics_json; compute progress from time_entries/tasks, not self-reported "I'm doing great"; weekly review ritual.
- **SQLite concurrency (Streamlit multi-session):** WAL mode; single DB access layer with retries and short transactions; per-user locks for projections if needed; separate "write events" transaction from "apply projections" transaction.

---

## Implementation blueprint (minimal viable that can grow)

**Phase 1: Reliable logging + retrieval** — Tables: users, messages, facts, goals, milestones, tasks, time_entries, events. Orchestrator that retrieves context, proposes events, applies projections, replies with "what was logged".

**Phase 2: Scheduling + weekly review** — calendar_events + conflict detection; weekly metrics_daily generation; "plan the week" and "review the week" flows.

**Phase 3: Advanced personalization** — habit experiments + A/B style interventions (lightweight); optional vector index (can be SQLite + FTS5 for a lot of cases).

---

## Non-negotiable engineering rules

- No direct writes to state tables from the LLM; only event proposals.
- Every event is idempotent (replay-safe).
- Migrations are versioned; "dynamic schema" must go through schema_changes.
- Structured outputs from the model (JSON) validated before writing.
- Observability: store tool calls, decisions, apply errors.
- User correction path: UI to fix facts/tasks/time logs.

---

## Data categories to store (practical set)

Identity & constraints; Education; Work; Goals; Tasks; Time; Habits; Preferences; Health/life admin (optional).

---

## What a perfect assistant is (core properties)

A perfect assistant must satisfy five non-negotiable dimensions: **Accuracy**, **Contextual Awareness**, **Strategic Alignment**, **Reliability Under Stress**, **Adaptive Learning**. If any one fails, the assistant becomes decorative instead of functional.

Cognitive architecture: Long-term memory (structured identity model); Situational awareness (current priorities, time constraints, risk, deadlines); Decision intelligence (tradeoffs, opportunity cost, long-term compounding). Operational resilience (ambiguity, contradictions, emotional states, edge cases). Behavioral design (support vs challenge, empathy vs precision, prevent goal drift). Adaptive learning (patterns, bottlenecks, micro-experiments). Strategic intelligence (three horizons: Immediate, Mid-Term, Long-Term). Failure tolerance; Human-aware design; Communication quality; Ethical core (autonomy, privacy, empowerment).

**Final definition:** A context-aware, outcome-driven, strategically aligned system that maintains structured long-term memory, adapts through measured feedback, withstands ambiguity and stress, and continuously optimizes decisions across short-, mid-, and long-term horizons — while strengthening the user's autonomy instead of replacing it. It is not reactive, not generic, not flattering. It is reliable, precise, adaptive, and aligned with compounding long-term progress.

---

## Unified model: cognitive operating system

You're not building a chatbot. You're building a cognitive operating system — a structured, evolving, resilient assistant that behaves like a strategic partner, not a reactive text generator.

**I. What a perfect assistant actually is** — Outcome optimization under constraints. Five core properties: Accuracy (grounded in structured state); Contextual awareness; Strategic coherence; Operational resilience; Adaptive learning.

**II. Structural architecture** — Interface layer (Streamlit: chat, dashboard, time logs, goals, correction UI; opacity creates fragility). Agent runtime: Orchestrator (decides per turn; outputs response, event proposals, confidence; LLM never writes directly to the database); Modular tools (Context Retrieval, Scheduling, Task & Goal, Time Tracking, Habit & Pattern Analysis; each reads via repository, writes only via events). Memory: users, facts (key/value JSON, confidence, validity, provenance), goals, milestones, tasks, time_entries, metrics_daily, calendar_events, events (event log non-negotiable: replay, rollback, deterministic projection).

**III. Behavioral intelligence** — Three horizons: Immediate (today), Mid-Term (weeks/months), Long-Term (years). Reconcile constantly.

**IV. Learning mechanism** — Extract claims → event proposals (FACT_UPSERT, TASK_CREATE, TASK_UPDATE, TIME_LOG, GOAL_UPDATE, SCHEMA_CHANGE) → apply via projection (validate, idempotent, log errors) → transparency (what was logged, what changed, what assumptions; silent mutation destroys trust).

**V. Stress & failure analysis** — Hallucinated updates (structured JSON, confidence gating, diff for critical fields); Schema chaos (facts first, schema versioning); Time inconsistencies (no negative durations, overlap detection, approximate flags); Goal drift (measurable metrics, derive from actions); SQLite (WAL, short transactions, retry, repository abstraction).

**VI. Communication & ethical core** — Precise, adaptive, no flattery, balance empathy/rigor; preserve autonomy, avoid dependency, protect privacy, strengthen independent competence. Objective is compounding growth.

**VIII. Final unified definition** — A structured, event-driven, context-aware cognitive system that maintains durable long-term memory, processes state changes deterministically, analyzes behavior across time horizons, detects drift and inefficiency, and continuously optimizes decisions under real-world constraints — while remaining transparent, resilient, and aligned with long-term compounding progress. It is architected for coherence, stability, and measurable improvement over time.

---

## Production file tree and layer responsibilities

```
adaptive_assistant/
├── app/                      # Streamlit UI layer
│   ├── main.py
│   ├── pages/
│   │   ├── dashboard.py
│   │   ├── chat.py
│   │   ├── goals.py
│   │   ├── schedule.py
│   │   └── review.py
│   └── components/
│       ├── chat_ui.py
│       ├── task_table.py
│       ├── calendar_view.py
│       └── metrics_panel.py
├── agent/                    # LLM + orchestration layer
│   ├── orchestrator.py
│   ├── prompt_templates.py
│   ├── structured_outputs.py
│   ├── decision_engine.py
│   ├── confidence_scoring.py
│   └── conversation_context.py
├── modules/                  # Deterministic business logic modules
│   ├── scheduling/
│   ├── goals/
│   ├── tasks/
│   ├── time_tracking/
│   ├── habits/
│   └── memory/
├── events/                   # Event system (core of architecture)
│   ├── event_types.py
│   ├── event_schema.py
│   ├── event_store.py
│   ├── event_dispatcher.py
│   └── projections/
├── db/                       # Database layer
│   ├── database.py
│   ├── connection.py
│   ├── repository/
│   ├── migrations/
│   └── schema.sql
├── services/                 # Cross-module orchestration services
├── config/
├── utils/
├── tests/
├── scripts/
├── data/
├── .env
├── requirements.txt
└── README.md
```

**Layer responsibilities:** (1) **app/** — Only UI logic; no direct database writes; no business logic. (2) **agent/** — LLM interaction, structured event proposals, context retrieval, decision routing; does NOT apply events or directly modify database tables. (3) **modules/** — Pure deterministic logic; given input state → returns output; no LLM calls. (4) **events/** — Safety layer; all mutations flow: User → LLM → Event Proposal → Event Store → Projection → State Tables; no bypass. (5) **db/** — Only place that touches SQLite; repository pattern. (6) **services/** — High-level workflows (weekly review, daily planning, etc.); combine modules but remain deterministic.

**Critical constraints:** LLM never writes directly to state tables; every mutation is an event; every event is idempotent; projections are replayable; migrations are versioned; modules do not import UI; UI does not import projections directly.

---

## Migration governance

**Three-stage migration pipeline:**

- **Stage 1 — Assistant proposal (automatic):** When a domain stabilizes, the assistant generates rationale, usage frequency, query pressure evidence, proposed table schema, data migration plan, impact analysis. Stored as a migration proposal record. No schema change yet.

- **Stage 2 — Pre-migration simulation (automatic):** System runs schema validation, test migration in temp schema, replay relevant events, performance test basic queries. If failure → proposal rejected. If pass → marked ready for approval.

- **Stage 3 — Human approval (required):** You see why this table is needed, what changes, what tables are affected, reversible (Yes/No). You approve with one action. System applies migration and logs version.

The assistant should never apply structural schema changes without approval. Proposals and pre-validation are automated; application requires human approval.

---

## Next step: exploratory build

To get something running quickly and start recording behavior without building the full system first, use the **Exploratory documentation** ([EXPLORATORY_24H.md](EXPLORATORY_24H.md)). It describes a minimal event-driven version you can run in 24 hours and use daily. That version is the first step toward this architecture.
