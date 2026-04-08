## System Architecture and Workflows

This document focuses on **architecture diagrams and workflows** for the key systems in the portfolio.

**How to use this doc:** Use the plain-English paragraph under each diagram to explain the flow in your own words; use the technical terms when you want to sound precise in an interview.

---

## 1. Personal Task & Goal Assistant (Ai/assistant)

### 1.1 High-Level Architecture

```text
+-------------------+
|   Streamlit UI    |
|  (assistant.py)   |
+---------+---------+
          |
          v
+---------+---------+
|    Orchestrator   |
| (agent/orchestrator.py) |
+---------+---------+
          |
          v
+---------+---------+
|  OpenAI LLM API   |
+---------+---------+
          |
          v
+-------------------+
|  Structured Events|
|  (event JSON)     |
+---------+---------+
          |
          v
+---------+---------+       +------------------+
|  Event Store      |       |  Projector       |
| (events table)    +------>+ (events.projector)|
+---------+---------+       +--------+---------+
                                      |
                                      v
                          +-----------+-----------+
                          |   State Tables       |
                          | (tasks, goals,      |
                          |  time_logs, etc.)   |
                          +-----------+---------+
                                      |
                                      v
                          +-----------+-----------+
                          |  Dashboards / Context |
                          +----------------------+
```

**In plain English:** The user talks to the app in a chat UI. The app sends that to a coordinator (orchestrator) that calls the AI. The AI’s structured output is saved as events in a log, then a projector turns those events into updated tasks, goals, and time logs. The UI can show that state and use it for context next time.

**Technical terms in this diagram:** Streamlit UI, orchestrator, OpenAI LLM API, structured events (JSON), event store (append-only), projector, state tables (tasks, goals, time_logs).

### 1.2 Turn Workflow (Two-Phase LLM)

```text
User Message
   |
   v
Load Context:
  - Conversation summary
  - Recent messages
  - Goals, tasks, time logs
  - Day context (gaps, overdue, weekly stats)
   |
   v
Phase 1: Conversational Reply
  - System prompt from chat.txt + context
  - Call LLM
  - Stream reply to UI
   |
   v
Persist Messages
  - save_message(user)
  - save_message(assistant)
   |
   v
Phase 2: Extraction
  - System prompt from extract.txt
  - Input: user + assistant turn
  - Call LLM to emit event JSON
   |
   v
Parse and Filter Events
  - JSON parsing
  - Keep only ALLOWED_EVENT_TYPES
   |
   v
Append Events
  - events.event_store.append_event
   |
   v
Project Events
  - events.projector.project_event
  - Update tasks/goals/time_logs tables
   |
   v
Updated State for Next Turn
```

**In plain English:** On each turn we load context (summary, tasks, goals, day context), then ask the AI for a conversational reply (phase 1) and save both messages. Then we ask the AI again to extract structured events from that turn (phase 2), filter to allowed types, append them to the event log, and project each one into the state tables so the next turn sees updated state.

**Technical terms in this diagram:** Phase 1 (conversational reply), Phase 2 (extraction), ALLOWED_EVENT_TYPES, append_event, project_event, event store, state tables.

---

## 2. Data Analytics Apprenticeship (Ai/teacher)

### 2.1 High-Level Architecture

```text
+-------------------------+
|  Streamlit / Flet UI   |
| (app/teacher.py,       |
|  app/desktop.py)       |
+-----------+-------------+
            |
            v
+-----------+-------------+
|   Orchestration Layer   |
| (app/orchestration.py)  |
+-----------+-------------+
            |
            v
+-----------+-------------+
|  Prompt Builder          |
| (docs layers + prompt_v6)|
+-----------+-------------+
            |
            v
+-----------+-------------+
|     OpenAI LLM          |
+-----------+-------------+
            |
            v
+-----------+-------------+
|   State Parser (regex)  |
| (app/state_parser.py)   |
+-----------+-------------+
            |
            v
+-----------+-------------+
| State Schema / FSM      |
| (state_schema,          |
|  transition_engine)     |
+-----------+-------------+
            |
            v
+-----------+-------------+
|   SQLite DB (app/db.py) |
|   - messages            |
|   - state_events        |
|   - learner state       |
+-------------------------+
```

**In plain English:** The learner uses the Streamlit or Flet UI. The orchestration layer builds the prompt from the current stage and locked methods, calls the AI, then runs a regex-based parser on the reply to detect method locks and stage transitions. Those become proposed transitions that the transition engine validates and applies; the result is stored in SQLite (messages and state_events).

**Technical terms in this diagram:** Streamlit/Flet UI, orchestration, prompt builder (docs, prompt_v6), OpenAI LLM, state parser (regex), state schema, transition engine (FSM), SQLite DB (state_events, messages).

### 2.2 Stage Progression Workflow

```text
User Message
   |
   v
Load State
  - Current stage (S0–S12)
  - Locked / remaining methods
  - Handoff status
   |
   v
Build System Prompt
  - Stage docs (layer1–layer4)
  - Method map
  - Current state summary
   |
   v
LLM Response
  - Explanations
  - Exercises / instructions
  - Inline markers for locks / transitions
   |
   v
State Parsing (regex)
  - Detect "Method N — ... LOCKED"
  - Detect "Proceeding to Stage Sx"
   |
   v
ProposedTransition Objects
  - action = method_lock / stage_transition
  - method_number / stage
   |
   v
Transition Engine
  - Validate allowed transitions
  - Enforce invariants
  - Idempotent per assistant_message_id
   |
   v
Persist
  - Write state_events row
  - Update learner state
```

**In plain English:** We load the current stage and locked methods, build a system prompt from the curriculum and that state, and stream the AI's teaching reply. Then we parse the reply with regex for method locks and stage moves, turn those into proposed transitions, run them through the transition engine, and write one state_events row per message so updates are idempotent.

**Technical terms in this diagram:** Load state, system prompt, LLM response, regex state parsing, ProposedTransition, transition engine, state_events (idempotent per assistant_message_id).

---

## 3. Concept Practice Engine and Code & Analytics Apprenticeship

These two systems share almost identical architecture; they differ mainly in prompts and topic content.

### 3.1 High-Level Architecture

```text
+--------------------------+
|  Streamlit / Flet UI    |
| (streamlit_app.py,      |
|  desktop.py)            |
+------------+------------+
             |
             v
+------------+------------+
|   Orchestration Layer   |
| (orchestration.py)      |
+------------+------------+
             |
             v
+------------+------------+
|   Prompt Builder        |
| (prompt_pract_v1.md or |
|  prompt_v7.md + state) |
+------------+------------+
             |
             v
+------------+------------+
|      OpenAI LLM         |
+------------+------------+
             |
             v
+------------+------------+
| State Parser            |
| (state_parser.py)       |
| - JSON block extraction |
| - Regex fallback        |
+------------+------------+
             |
             v
+------------+------------+
|  State Schema + FSM     |
| (state_schema,          |
|  transition_engine)     |
+------------+------------+
             |
             v
+------------+------------+
|   SQLite DB (db.py)     |
|  - topics / handouts    |
|  - state_events         |
|  - parser metrics       |
+-------------------------+
```

**In plain English:** The user picks a topic in the Streamlit or Flet UI. The orchestration layer builds a prompt from the topic and current concept state, calls the AI, then looks for a STATE_UPDATE JSON block in the reply. That JSON is validated and passed to the transition engine (guards); if allowed, we write a state_events row and update topic/concept state. Same pattern for both the Concept Practice Engine and the Code & Analytics Apprenticeship.

**Technical terms in this diagram:** Streamlit/Flet UI, orchestration, OpenAI LLM, state parser (JSON block + regex fallback), state_schema, validate_state_update, transition engine (guards), state_events, parser metrics.

### 3.2 STATE_UPDATE Workflow

```text
User Message
   |
   v
Load Topic and State
  - Topic/category
  - Concept list (decomposition)
  - Current locked / announced concept
   |
   v
Build System Prompt
  - Prompt file (practice or metacode)
  - Topic description and concept list
  - Current mastery state
   |
   v
LLM Response
   |
   v
Extract STATE_UPDATE Block
  - Between <<<STATE_UPDATE_START>>> and <<<STATE_UPDATE_END>>>
   |
   v
JSON Parse
   |
   v
validate_state_update
  - Allowed keys only
  - Types and length checks
  - ACTION_ENUM: none, lock, announce,
                 decompose, topic_change
   |
   v
Transition Engine
  - Guard functions (_guard_lock, _guard_announce,
                    _guard_decompose, _guard_topic_change)
  - Block destructive actions in regex mode
  - Idempotent per assistant_message_id
   |
   v
Persist and Apply
  - Insert state_events row (with parser/schema versions)
  - Update topic / concept state
```

**In plain English:** We load the topic and concept list and current mastery state, build a system prompt, and stream the AI's reply. We extract the STATE_UPDATE JSON block, validate it (allowed keys, types, action enum), run guard functions, then persist one state_events row and update the topic/concept state. Idempotent per message; regex fallback cannot perform destructive actions.

**Technical terms in this diagram:** Load topic and state, system prompt, LLM response, STATE_UPDATE block, validate_state_update, guard functions, state_events (idempotent), parser/schema versions.

---

## 4. Operational Turnover Intelligence (OTI)

### 4.1 ETL Pipeline

```text
DMRB_board.csv
   |
   v
load_data
  - Read CSV
  - Normalize columns
  - Parse dates
   |
   v
clean_data
  - Normalize unit codes
  - Derive phase, building, unit
  - Filter relevant phases
   |
   v
transform
  - Align to unit / turnover / task model
  - Compute canonical board structure
   |
   v
enrich
  - DV, aging, stall flags
  - Task pipeline state
  - SLA-style signals
   |
   v
compute_metrics
  - Aggregates and crosstabs
   |
   v
Streamlit Case Study
  - Overview
  - Pipeline view (raw vs cleaned vs board)
  - SQL logic description
  - Analysis and insights
```

**In plain English:** We start from the raw DMRB board CSV, load and normalize it, clean unit codes and filter phases, transform into a unit/turnover/task board shape, then enrich with days vacant, aging, stall flags, and SLA-style signals. Finally we compute metrics and feed the Streamlit case study (overview, pipeline view, SQL logic, analysis, insights).

**Technical terms in this diagram:** load_data, clean_data, transform, enrich, compute_metrics, ETL, normalization, derived metrics, Streamlit case study.

### 4.2 Page-Level Flow

```text
User opens "Operational Turnover Intelligence" page
   |
   v
get_pipeline_data (cached)
  - load_data
  - clean_data
  - transform
  - enrich
   |
   v
Tabs in UI
  - Overview (problem and skills)
  - Data Pipeline (raw and enriched tables)
  - SQL Logic (canonical open-turnover query)
  - Analysis (metrics, crosstabs)
  - Insights (narrative findings)
```

**In plain English:** When the user opens the OTI page, we run the pipeline (load, clean, transform, enrich) once and cache the result. The UI shows tabs: overview, data pipeline (raw vs cleaned vs board), SQL logic, analysis (metrics, crosstabs), and insights.

**Technical terms in this diagram:** get_pipeline_data, cached pipeline, tabs, Overview, Data Pipeline, SQL Logic, Analysis, Insights.

---

## 5. Operational Turnover Intelligence — Make-Ready (career txt/the-dmrb)

### 5.1 Layered Architecture

```text
+------------------------------+
|        Streamlit UI         |
|    (app.py / app_prototype) |
+---------------+--------------+
                |
                v
+---------------+--------------+
|    Services Layer            |
|  - import_service            |
|  - turnover_service          |
|  - task_service              |
|  - sla_service               |
|  - risk_service              |
|  - board_query_service       |
|  - manual_availability       |
|  - note_service              |
+---------------+--------------+
                |
                v
+---------------+--------------+
|    Domain Layer              |
|  - enrichment                |
|  - lifecycle                 |
|  - sla_engine                |
|  - risk_engine               |
|  - unit_identity             |
+---------------+--------------+
                |
                v
+---------------+--------------+
|      DB Layer                 |
|  - connection (ensure, backup)|
|  - repository (CRUD, lookups) |
|  - schema.sql + migrations    |
+------------------------------+
```

**In plain English:** The Streamlit UI only displays data and sends user actions. The services layer handles imports, turnovers, tasks, SLA, risk, and board queries. The domain layer holds pure logic for enrichment, lifecycle, SLA, risk, and unit identity. The DB layer handles connection, repository (CRUD, lookups), schema, and migrations. So the UI has no business logic; domain is pure; services orchestrate; DB persists.

**Technical terms in this diagram:** Streamlit UI, services layer, domain layer, DB layer, import_service, turnover_service, enrichment, lifecycle, sla_engine, risk_engine, repository, schema, migrations.

### 5.2 Import and Enrichment Workflow

```text
CSV Reports (Move-Outs, Pending Move-Ins,
Available Units, Pending FAs, DMRB)
   |
   v
import_service.import_report_file
  - Parse rows
  - Normalize unit identity
  - Ensure unit / turnover / tasks
  - Write import_batch and import_row
   |
   v
SQLite Core Tables
  - property, building, unit
  - turnover, task, phase
  - import_batch, import_row
   |
   v
Reconciliation / Updates
  - turnover_service
  - task_service
  - manual_availability_service
   |
   v
Domain Engines
  - lifecycle: effective_move_out, N/V/M
  - sla_engine: SLA state and breach events
  - risk_engine: risk_flag rows
   |
   v
board_query_service
  - Join core tables into board/flag rows
  - Call enrichment.enrich_row per row
   |
   v
Streamlit UI
  - DMRB Board
  - Flag Bridge
  - Turnover Detail
  - Admin / Import Tools
```

**In plain English:** CSV reports (move-outs, pending move-ins, available units, pending FAs, DMRB) are imported by the import service, which normalizes unit identity and writes to core SQLite tables (units, turnovers, tasks, etc.). Reconciliation and updates go through turnover, task, and manual-availability services. Domain engines compute lifecycle, SLA, and risk. The board query service joins tables and enriches each row, then feeds the Streamlit UI (board, flag bridge, turnover detail, admin).

**Technical terms in this diagram:** import_service, import_report_file, unit identity, import_batch, import_row, turnover_service, task_service, domain (lifecycle, sla_engine, risk_engine), board_query_service, enrich_row.

---

## 6. Guardrail and Validation Layer Summary

Across all systems, the guardrail strategy follows a consistent pattern:

```text
LLM Output
   |
   v
Extraction
  - Event JSON (assistant)
  - STATE_UPDATE JSON (practice / metacode)
  - Regex-only parsing (teacher)
   |
   v
Validation
  - Whitelisted event types
  - JSON schema checks (validate_state_update)
  - Guard functions for FSM transitions
   |
   v
Persistence
  - Append-only events (assistant)
  - state_events with idempotency keys
  - SQLite tables with foreign keys
   |
   v
Derived Views
  - Projected state tables
  - Enriched board rows and metrics
```

**In plain English:** LLM output never updates the system directly. We extract structured data (event JSON or STATE_UPDATE JSON or regex), validate it (whitelisted types, schema checks, guard functions), then persist (append-only events or idempotent state_events or SQLite tables). From that we derive the views the user sees. So we use the LLM for interpretation while controlling how and when it can change state.

**Technical terms in this diagram:** Extraction (event JSON, STATE_UPDATE JSON, regex), validation (whitelist, schema, guard functions), persistence (event log, state_events, foreign keys), derived views (projections, enriched rows).

This architecture lets you use LLMs for interpretation and explanation while **controlling how and when they are allowed to change system state**.

