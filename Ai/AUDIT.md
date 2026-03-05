# Deep Audit: Teacher, Teacher Practice, Metacode

## 1. Directory & Structural Layout

### Full Directory Tree (Teacher, Teacher Practice, Metacode only)

```
Ai/
├── teacher/
│   ├── app/
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── desktop.py
│   │   ├── learner_analytics.py
│   │   ├── orchestration.py
│   │   ├── prompts.py
│   │   ├── state_parser.py
│   │   ├── state_schema.py
│   │   ├── teacher.py
│   │   └── transition_engine.py
│   ├── docs/
│   │   ├── info.md
│   │   ├── knowledge_file.md
│   │   ├── layer1_why_v2.md ... layer4_complete_v2.md
│   │   ├── prompt_v6.md
│   │   └── stage_method_map_v2.pdf
│   └── requirements.txt
├── teacher_pract/
│   ├── config.py
│   ├── db.py
│   ├── desktop.py
│   ├── knowledge_file_v7.md
│   ├── learner_analytics.py
│   ├── orchestration.py
│   ├── prompt_pract_v1.md
│   ├── prompts.py
│   ├── python_mastery.py
│   ├── state_parser.py
│   ├── state_schema.py
│   ├── streamlit_app.py
│   ├── topics.py
│   ├── transition_engine.py
│   ├── .env
│   └── .gitignore
└── metacode/
    ├── config.py
    ├── db.py
    ├── desktop.py
    ├── knowledge_file_v7.md
    ├── learner_analytics.py
    ├── orchestration.py
    ├── prompt_v7.md
    ├── prompts.py
    ├── python_mastery.py
    ├── state_parser.py
    ├── state_schema.py
    ├── streamlit_app.py
    ├── topics.py
    ├── transition_engine.py
    ├── .env
    └── .gitignore
```

### Entry Points

| App | Entry Point | How to Run |
|-----|-------------|------------|
| **Teacher** | `teacher/app/teacher.py` | `streamlit run teacher/app/teacher.py` |
| **Teacher** | `teacher/app/desktop.py` | `python teacher/app/desktop.py` (Flet) |
| **Teacher Pract** | `teacher_pract/streamlit_app.py` | `streamlit run streamlit_app.py` (from teacher_pract/) |
| **Teacher Pract** | `teacher_pract/desktop.py` | `python desktop.py` (from teacher_pract/) |
| **Metacode** | `metacode/streamlit_app.py` | Same pattern as Teacher Pract |
| **Metacode** | `metacode/desktop.py` | Same pattern as Teacher Pract |

### Streamlit Boot Logic

- **Teacher:** `teacher/app/teacher.py`: `init_db()`, `client = OpenAI(...)`, `st.set_page_config(...)`, then session_state init and sidebar/main chat.
- **Teacher Practice / Metacode:** `streamlit_app.py` lines 28–51: same pattern — init_db(), OpenAI client, set_page_config, then `if "session_id" not in st.session_state` / `if "messages" not in st.session_state`.

### Multiple App Entry Files

- **Teacher:** Two: Streamlit (`teacher.py`) and Flet (`desktop.py`).
- **Teacher Practice / Metacode:** Two each: `streamlit_app.py` and `desktop.py`.

### Unused / Orphaned Files

- No clearly orphaned Python files. Docs (prompt_v6.md, knowledge_file.md, etc.) are used via DOCS_DIR in prompts. Teacher Pract and Metacode: all listed files are referenced.

### Hidden / Config Files

- **Teacher:** No `.env` in teacher/ or teacher/app/.
- **Teacher Practice / Metacode:** `.env` present. `.gitignore` lists `.env`, `apprentice.db`, `__pycache__/`.

### Environment Variables

- **Teacher:** Not centralized for secrets. `config.py` reads only DB_PATH and DOCS_DIR from os.path; API key is hardcoded.
- **Teacher Practice / Metacode:** Centralized in config.py: `load_dotenv()`, then `OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")`, OPENAI_MODEL, DB_PATH, DOCS_DIR.

### .env File

- **Teacher:** No. No `.env` under teacher/.
- **Teacher Practice / Metacode:** Yes.

### API Key Hardcoded

- **Teacher:** Yes. `teacher/app/config.py` line 3 contains a literal API key string. **Risk: Critical** — key in source and likely in version control.
- **Teacher Practice / Metacode:** No; key from env. **High** risk if .env is ever committed.

### requirements.txt / pyproject.toml

- **Teacher:** `teacher/requirements.txt` exists: streamlit, openai, flet. No pyproject.toml in repo.
- **Teacher Practice / Metacode:** No requirements.txt and no pyproject.toml in their directories.

### Dependencies

- Minimal and consistent: streamlit, openai, flet; Teacher Pract and Metacode use python-dotenv. Not bloated.

---

## 2. Architectural Layering

### Separation of Concerns

- **Teacher:** UI in `teacher.py` (Streamlit) and `desktop.py` (Flet) — render and call `handle_user_message`. Orchestration in `orchestration.py`. LLM calls only there. Data in `db.py`. Clear separation.
- **Teacher Practice / Metacode:** Same: UI → `handle_user_message` → prompts, DB, state_parser, transition_engine.

### Cohesion and Single Responsibility

- Orchestration, state_parser, transition_engine, db, prompts are single-purpose. Some long helpers in learner_analytics and prompts.

### Business Logic in UI Callbacks

- **Teacher:** Sidebar (New Session, New Run, Resume, Stage Practice) calls update_system_state, close_session, create_session, build_resume_block, save_message. Some business logic in UI; main “next step” is orchestration-driven.
- **Teacher Practice / Metacode:** Topic/category selection, Challenge Mode, New Session/Run, Resume trigger DB and state updates from UI.

### Circular Imports

- None observed. Dependency direction is one-way.

### Global Mutable State

- **Teacher:** Module-level `client = OpenAI(...)` in teacher.py. No other global mutables in app layer.
- **Teacher Practice / Metacode:** Global `client` in streamlit apps. Desktop creates client inside send callback. **Risk: Low** for single-process use.

---

## 3. OpenAI / LLM Integration

### Where OpenAI is Called

- **All three:** Only in `orchestration.py`. Teacher: lines 57–70 (`client.chat.completions.create(..., stream=True, temperature=0.3, max_tokens=4096)`). Teacher Pract / Metacode: same.

### Centralized Wrapper

- No separate “LLM service” module. Single call site is `handle_user_message` in orchestration — effectively centralized in one function.

### Model Names

- All: `OPENAI_MODEL = "gpt-4o"` in config. Config-driven but hardcoded in config.

### Temperature and max_tokens

- All: `temperature=0.3`, `max_tokens=4096`. Consistent.

### Error Handling

- On exception during streaming: `set_message_status(assistant_msg_id, "failed")` then `raise`. No retries, no backoff, no timeout. UI catches and shows generic error.

### Retries / Timeouts

- None for the OpenAI call. **Risk: Medium** for flaky networks.

### Logging of Raw Responses

- Full assistant text stored in DB. No separate observability logging.

### Validation of Responses

- Content passed to `parse_state_updates`; parser and transition_engine validate structure. No pre-validation of “valid chat response.”

### JSON Parsing and Malformed Output

- **Teacher:** state_parser is regex-only. No JSON from model for state.
- **Teacher Pract / Metacode:** Strict block with JSON; `json.loads` caught; proposal with rejection_reason; transition_engine records not applied. Regex fallback when block missing. Malformed JSON does not crash; **Risk: Low** for crash; **Medium** for state not updating.

---

## 4. Prompt Design

### Where Prompts Are Defined

- **Teacher:** `teacher/app/prompts.py` — reads `docs/prompt_v6.md` and `docs/knowledge_file.md`; embeds STAGE_METHOD_MAP and large inline blocks.
- **Teacher Practice:** `teacher_pract/prompts.py` — reads `prompt_pract_v1.md`, `knowledge_file_v7.md`; adds state, concept progress, learner context, identity, optional python_mastery layer.
- **Metacode:** `metacode/prompts.py` — same structure, using `prompt_v7.md` and `knowledge_file_v7.md`.

### Inline vs Modular

- Core instructional text is in external .md files. State formatting, progress, learner context, and long rule blocks are inline in prompts.py. Hybrid.

### Duplication

- Teacher Pract and Metacode prompts are nearly identical (only prompt file name differs). Teacher is different (stages/methods vs topics/concepts).

### Versioning

- Filenames suggest versions (prompt_v6, prompt_v7, prompt_pract_v1, knowledge_file_v7). No runtime version or A/B in code.

### System vs User Roles

- One system message from `build_system_prompt()`. User/assistant from conversation history. Clear.

### Determinism

- Prompts deterministic given same state and DB. Temperature 0.3 allows variation in output.

### Prompt Size and Injection

- Prompt size not bounded; system prompt can grow. **Risk: Medium.** User messages passed as-is; no sanitization. **Risk: Medium** for prompt injection.

---

## 5. Topic Decomposition Logic

- **Teacher:** No “topic decomposition.” Progression by stages (S0–S12) and methods. No subtopic IDs or decomposition structure.
- **Teacher Practice / Metacode:** Decomposition is LLM-driven. Parser extracts “decomposition” (regex); transition engine stores in `system_state.decomposition`. Structure enforced by engine (no overwrite if already set). Concepts have concept_number and concept_name; no separate IDs. Stored; not regenerated. User can resume at topic/concept via sidebar. No explicit prerequisite or difficulty in code.

---

## 6. Practice / Evaluation Logic

- **Teacher:** “Practice” is method-by-method; parser looks for “Method N — name locked”; transition engine locks. No separate grading step.
- **Teacher Practice / Metacode:** Same at concept level; parser looks for “Concept N — name locked” or STATE_UPDATE with action lock. No automated grading; “correct” = model emits lock + parser/engine accept. Student answer stored in conversations. Retries and misconceptions tracked via concept_progress and learner_events.

---

## 7. State Management

### On Page Reload

- **Streamlit:** Script re-runs; session_id and messages from st.session_state or DB. Reload restores from DB.
- **Flet desktop:** No automatic reload from disk on startup; one session and in-memory messages; history loaded from DB once. New run = new session unless logic added to restore.

### session_state Usage

- **Teacher:** session_id, messages, resume_stage. Heavily used.
- **Teacher Pract / Metacode:** session_id, messages. No global clear; messages replaced on New Session/Run/Resume.

### Persistence

- All three: SQLite (apprentice.db per app). No other DB or file storage.

### Race Conditions

- transition_engine uses version check and retry on SQLITE_BUSY. No cross-process locking. **Risk: Medium** if two tabs or processes share same DB.

### State Mutation Predictability

- Mutations only through transition_engine and DB. Order: save assistant message → parse → apply in one transaction. Predictable for single-threaded use.

---

## 8. Control Flow

### Next Step

- **Teacher:** Determined by model and prompt (current stage, next unlocked method). No separate orchestrator object; flow is user message → handle_user_message → model → parse → apply.
- **Teacher Practice / Metacode:** Same; one handle_user_message; model decides what to say and whether to announce/lock/decompose.

### Central Orchestrator

- Orchestration is the single entry point. No formal “flow graph” in code; state machine is in prompt and transition_engine.

### Linear Flow / Skip / Back

- **Teacher:** Linear by stage/method; sidebar allows “Practice This Stage” and “Resume.”
- **Teacher Pract / Metacode:** User can select topic/category, “Practice This Topic,” “Resume.” Flow within topic is linear.
- **Determinism:** Same state + user message → same API call; model reply not deterministic.

---

## 9. Error Handling

- **OpenAI fails:** Exception in orchestration; message marked failed; re-raise; UI shows generic “OpenAI API error.” No retry, no structured logging.
- **JSON parsing fails (pract/metacode):** Caught in state_parser; proposal with rejection_reason; transition_engine records not applied.
- **Invalid API key:** Request fails; same generic UI error.
- **Empty topic input:** No explicit check in orchestration; model handles.
- **Surfaced to user:** Yes. **Logged:** Only via DB (status, state_events).

---

## 10. Performance & Cost

- **Caching:** None. Every user message triggers new completion.
- **Prompt reuse:** System prompt rebuilt each time; no cache.
- **Token counts:** Not monitored.
- **Context growth:** History capped (e.g. 30 in pract/metacode). System prompt unbounded. **Risk: Medium** for token growth.

---

## 11. Security

- **API key in frontend:** No; server-side only.
- **Prompt injection:** User input not sanitized. **Risk: Medium.**
- **Input sanitized:** No. Only model output (STATE_UPDATE) validated.
- **Malicious input:** Could confuse model; engine validates topic against TOPIC_MENU. Limited impact.

---

## 12. Code Health

### Longest Functions / Files >300 Lines

- **Teacher:** db.py (918), learner_analytics.py (593), prompts.py (497), desktop.py (395).
- **Teacher Pract:** db.py (931), learner_analytics.py (623), desktop.py (474).
- **Metacode:** db.py (931), learner_analytics.py (623), desktop.py (426).

### Complexity

- Highest in db.py, learner_analytics.py, transition_engine.py, prompts.py.

### Naming

- Consistent. Filenames match roles (orchestration, state_parser, transition_engine, learner_analytics, prompts, db).

---

## 13. Scalability

- **10 users:** Possible if each has own process/DB. Shared SQLite not designed for concurrency.
- **100 / 1000:** Not designed; no pooling, no async.
- **Concurrency:** WAL + version check; no multi-writer scaling. **Blocking:** All I/O blocking. **Async:** Not used.

---

## 14. Strategic Classification

### Teacher

- **Type:** Structured tool / early platform fragment.
- **Fragile:** (1) Hardcoded API key in config. (2) **Teacher Flet desktop:** `analyze_user_message` is **called but not imported** in desktop.py (line 299) — **NameError on send.** (3) Desktop also double-saves user message and double-calls analytics.
- **Leverage:** Env-based config; fix desktop import and single path for save + analytics.
- **Debt:** API key in repo; desktop logic duplicated and broken.

### Teacher Practice

- **Type:** Structured tool with topic/concept and challenge mode.
- **Fragile:** Reliance on model emitting valid STATE_UPDATE JSON for locks; regex fallback does not allow lock.
- **Leverage:** Add requirements.txt; consider shared package with Metacode.
- **Debt:** Duplication with Metacode; .env with secrets.

### Metacode

- **Type:** Same as Teacher Practice.
- **Fragile:** Same STATE_UPDATE/regex reliance.
- **Leverage:** Share code with Teacher Practice.
- **Debt:** Same duplication and .env risk.

---

## Summary Table

| Finding | Teacher | Teacher Pract | Metacode |
|--------|---------|---------------|----------|
| API key in source | **Critical** (config) | High (.env) | High (.env) |
| .env / env vars | None | Centralized | Centralized |
| requirements.txt | Yes | No | No |
| Desktop send_message bug | **NameError** (missing import) | No | No |
| LLM calls | Orchestration only | Same | Same |
| Retries / timeouts | None | None | None |
| Caching | None | None | None |
| Largest file | db.py 918 | db.py 931 | db.py 931 |

---

**Single most fragile architectural component (all three):** Reliance on the model to emit the exact state-update format (regex in Teacher, JSON block in Pract/Metacode) for progression, with no automated fallback or recovery when the model drifts.

**Single highest leverage improvement:** Teacher: remove hardcoded API key and fix desktop (import `analyze_user_message`, single path for save + analytics). Pract/Metacode: add requirements.txt and consider a shared package for common modules.

**Fastest-compounding debt:** Teacher’s config and desktop bugs (security and runtime failure), and the duplication between Teacher Practice and Metacode (two nearly identical codebases to maintain).
