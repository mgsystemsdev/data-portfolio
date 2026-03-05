# Personal Task & Goal Assistant

Event-driven personal assistant built with Streamlit, SQLite, and OpenAI. Two-phase architecture: conversation first (always works), structured extraction second (silent, best-effort).

## How it works

1. You chat naturally
2. The assistant responds conversationally with memory of past conversations
3. Behind the scenes, it silently extracts tasks, goals, time logs, and facts
4. Everything is stored as append-only events and projected into state tables

## File tree

```
assistant/
├── main.py                    # Streamlit UI (chat + sidebar dashboard)
├── requirements.txt           # Dependencies
├── .env                       # OPENAI_API_KEY (not committed)
├── assistant.db               # SQLite database (auto-created)
│
├── agent/                     # AI layer
│   ├── orchestrator.py        # Two-phase turn: conversation → extraction
│   └── prompts/
│       ├── chat.txt           # Phase 1: conversational system prompt
│       └── extract.txt        # Phase 2: structured extraction prompt
│
├── config/                    # Environment and settings
│   └── config.py              # OPENAI_API_KEY, MODEL, DB_PATH
│
├── db/                        # Database layer
│   ├── database.py            # SQLite connection (WAL mode)
│   ├── schema.sql             # Tables: conversations, messages, events, tasks, goals, time_logs
│   └── snapshot.py            # Save/load snapshots
│
├── events/                    # Event sourcing layer
│   ├── event_store.py         # Append-only event store
│   └── projector.py           # Project events → state tables
│
└── docs/                      # All documentation
    └── (see docs/README.md)
```

## Quick start

```bash
pip install -r requirements.txt
# Add your key to .env: OPENAI_API_KEY=sk-...
streamlit run assistant.py
```

## Current phase

**Exploratory** — running daily, recording everything, learning patterns. No feature creep. After 45–90 days of use, evaluate and formalize into production architecture.

## Documentation

See [docs/README.md](docs/README.md) for the full documentation index.
