# Exploratory 24-Hour Build

> **Note:** The current codebase has evolved beyond this original spec. Key improvements: two-phase turn architecture (conversation + silent extraction), conversation memory (rolling summary + last 20 messages), single canonical message table, and lenient extraction. See [EXECUTION_PLAN.md](EXECUTION_PLAN.md) for the active next-steps plan.

This document describes the original "get it running in 24 hours" path: minimal scope, flat layout, concrete steps, and what not to build. This minimal version is the first step toward the full system; after 45–90 days of use, the **Explanatory / production documentation** ([ARCHITECTURE_AND_PRODUCTION.md](ARCHITECTURE_AND_PRODUCTION.md)) guides schema stabilization, new modules, and production structure.

---

## Why exploratory first

- **Build** a minimal event-driven version in 24 hours.
- **Run** for minimum 45 days.
- **Evaluate** at 60 days.
- **Formalize** at ~75–90 days.

This balances speed and maturity.

---

## Exploration mode vs production (simple explanation)

**Phase 1 — Exploratory mode (fast, minimal, learning)**

**Goal:** Get it running in 24 hours.

**What it does:**

- You talk naturally.
- It logs everything: conversations, task changes, time logs, schedule edits, decisions.
- All changes are stored as events (append-only).
- Data categories start flexible (JSON / facts table).
- It builds daily snapshots (CSV + matrix exports).
- It computes simple metrics in background.
- It does not over-structure anything yet.

Think of this phase as: **"Record everything. Organize lightly. Observe patterns."** It's a behavioral data collector with light structure.

**What happens during exploratory phase:** Over 45–90 days, it reveals which domains are actually important, which data categories repeat, where performance bottlenecks appear, where schema becomes messy, which projections are expensive, what guardrails are truly needed, what breaks under stress. You don't guess architecture; you observe it.

**Phase 2 — Production architecture:** After enough history, analyze what categories stabilized, what needs real tables, what should stay flexible, what should be archived. Then evolve toward the full architecture in the production documentation.

---

## Snapshots during exploration

Daily (or manual trigger):

- State snapshot CSV
- Goal–time alignment matrix
- Risk matrix
- Habit adherence summary
- Drift summary

This becomes your blueprint evidence.

---

## 24-hour objective

**End state after 24 hours:**

- A working Streamlit app that accepts chat.
- Calls one AI model.
- Extracts structured actions.
- Logs everything as events.
- Stores conversations.
- Builds daily snapshots (or manual export).
- Has zero schema chaos.
- Is replayable later.
- Ready for daily use immediately.

Nothing more.

---

## Decision lock (before coding)

- Use **one** AI coding tool only (Cursor recommended).
- Use **one** OpenAI model (e.g., GPT-4o or similar).
- No feature creep. No integrations. No refactors. No optimization engine. No calendar sync. No ML.
- Only: Chat, event logging, projection, snapshots.

Lock this.

---

## Minimal file tree (flat)

Keep it flat. No folders. Speed over elegance.

```
exploratory_assistant/
├── main.py
├── orchestrator.py
├── extractor_prompt.txt
├── event_store.py
├── projector.py
├── database.py
├── snapshot.py
├── schema.sql
├── .env
└── assistant.db
```

(Plus requirements.txt and optionally config.py.)

---

## Minimal database schema (exploratory)

Only these tables:

**1. conversations** — id, started_at

**2. messages** — id, conversation_id, role, content, created_at

**3. events (append-only)** — id, event_type, payload (or payload_json), authority_level, source_message_id, applied, created_at

**4. state_tasks (projection table)** — task_id, title, status, priority, due_date, updated_at

**5. state_goals (projection table)** — goal_id, title, status, target_date (and optionally created_at, updated_at)

**6. state_time_logs** — entry_id, activity_type, duration_minutes, linked_task_id, created_at

Nothing else. Flexible JSON inside events handles everything else.

---

## Event types (keep under 12)

Start with:

- TASK_CREATED
- TASK_UPDATED
- TASK_COMPLETED
- GOAL_CREATED
- GOAL_UPDATED
- TIME_LOGGED
- SCHEDULE_ADJUSTED
- NOTE_RECORDED
- (Optional: AUTHORITY_ACTION, SYSTEM_CHECK)

Keep it small.

---

## How the conversation loop works

1. User sends message.
2. Orchestrator: save raw message.
3. Retrieve basic context (tasks + goals).
4. Send to LLM with structured output format.
5. LLM returns: assistant reply, list of proposed events (JSON).
6. Validate JSON.
7. Append events to event store.
8. Run projector.
9. Save assistant reply.
10. Return to UI.

Done. No direct state mutation. Only event → projector.

If JSON invalid → fallback to plain reply. No retries logic yet. Keep simple.

---

## Dual-layer output (prompt design)

Every message triggers two parallel operations:

**Surface layer (visible to you):** Conversational, helpful, natural, organized, time-aware.

**Internal layer (invisible):** Extracts facts, detects commitments, identifies tasks and goals, detects preferences and emotional signals, updates risk signals, proposes events, suggests clarification questions. You don't see this layer directly, but it runs every time.

**Required structured output format:** Every response must return JSON with at least:

- `assistant_reply` — natural conversational reply (only this is shown to user).
- `proposed_events` — list of structured events.
- `learning_signals` — optional internal notes.

(Some variants also include extracted_facts, risk_signals, clarification_needed; the minimal set is assistant_reply, proposed_events, learning_signals.)

Only assistant_reply is shown to user. Everything else is internal.

---

## Snapshot strategy (critical)

Once per day (or manual trigger):

- Export CSV files (or one JSON): tasks_snapshot, goals_snapshot, time_snapshot, events_snapshot.
- Store in: `snapshots/YYYY-MM-DD/` (or equivalent).

This becomes your architectural evidence. Manual trigger only for the 24-hour build; no scheduler yet.

---

## What NOT to build in 24 hours

Do **not** build:

- Calendar integration
- External APIs
- ML forecasting
- Reinforcement logic
- Migration engine
- Governance system
- Optimization engine
- Habit modeling depth
- Multi-authority simulation engine

Only record and structure.

---

## Execution plan (Phase 0–7)

**PHASE 0 — Decision lock (30 minutes)**  
Lock: one AI tool, one model, no feature creep. Only chat, event logging, projection, snapshots.

**PHASE 1 — Project bootstrap (2 hours)**  
Create folder; create virtual environment (`python -m venv venv`; `pip install streamlit openai sqlite3 python-dotenv` or similar); create flat file tree as above. Keep it flat. No folders. Speed over elegance.

**PHASE 2 — Database first (3 hours)**  
Write schema.sql with only: conversations, messages, events (append-only), state_tasks, state_goals, state_time_logs. Initialize DB. Test inserting manually. Confirm event table works.

**PHASE 3 — Event system (3 hours)**  
Write event_store.py: `append_event()`, `get_unapplied_events()`, `mark_event_applied()`. Write projector.py: for each event type, update projection tables and mark applied. Keep event types under 10. Test manually: insert fake event → run projector → check state table updates. **Replay entire event history → rebuild state.** If replay works, you are safe.

**PHASE 4 — LLM structured extraction (4 hours)**  
Create extractor_prompt.txt that instructs the model to return `{ "assistant_reply": "", "proposed_events": [], "learning_signals": [] }`. In orchestrator.py: save user message; retrieve active goals + tasks; send to OpenAI with structured instruction; validate JSON; append proposed events; run projector; save assistant reply; return to UI. If JSON invalid → fallback to plain reply. No retries logic yet. Keep simple.

**PHASE 5 — Streamlit UI (3 hours)**  
main.py: Chat interface; display conversation history; show assistant reply; add "Export Snapshot" button; add "View Event Log" expandable section. No dashboard. No analytics. No charts. Just chat + event visibility.

**PHASE 6 — Snapshot system (2 hours)**  
snapshot.py (or equivalent): When triggered, export state_tasks, state_goals, state_time_logs, events (CSV or JSON). Save under `snapshots/YYYY-MM-DD/`. Manual trigger only. No scheduler yet.

**PHASE 7 — Reality test (4–5 hours)**  
Stress the system: create goals, create tasks, log time, modify tasks, miss deadlines, reprioritize, talk casually, talk emotionally, give ambiguous instructions. Check: Are events logging? Does projection remain consistent? Can you replay DB from scratch? Do snapshots export cleanly? If replay fails → fix projector logic. Do not move forward until replay is deterministic.

---

## Final state (end of 24 hours)

You now have:

- A working personal assistant
- Structured event logging
- Replayable architecture
- Snapshot exports
- No silent mutations
- Future-proof foundation
- Daily usable tool

It may not be brilliant yet. But it is: stable, structured, recording, learning-ready.

---

## Important rule after launch

**For 30 days:**

- Do **not** add features.
- Only: use it daily, log everything, export weekly snapshot, write down friction points separately.
- Architecture comes later.

Improvement comes from use. Not design.

Launch this. Use it tomorrow. Start real life interaction immediately.

---

## Relation to full architecture

This minimal version is the first step toward the full system described in the **Explanatory / production documentation** ([ARCHITECTURE_AND_PRODUCTION.md](ARCHITECTURE_AND_PRODUCTION.md)). After 45–90 days of use, that document guides schema stabilization, new modules, and production structure.
