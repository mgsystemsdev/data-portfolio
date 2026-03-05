import streamlit as st

st.title("Personal Task & Goal Assistant")

tab_overview, tab_how, tab_technical, tab_system, tab_run = st.tabs([
    "Overview", "How it works", "Technical design", "System design", "Run"
])

with tab_overview:
    st.subheader("What it is")
    st.markdown(
        "An **event-driven personal assistant** built with Streamlit, SQLite, and OpenAI. "
        "You chat naturally; the assistant responds with memory of past conversations. "
        "Behind the scenes it silently extracts tasks, goals, time logs, and facts into a structured store."
    )
    st.subheader("Problem it solves")
    st.markdown(
        "Personal productivity and goal-tracking often live in scattered notes and chats. "
        "This app turns conversation into **structured data** (tasks, goals, time logs) without changing how you type. "
        "Everything is stored as append-only events and projected into state tables—auditable and replayable."
    )
    st.subheader("Technology stack")
    st.markdown(
        "- **Streamlit** — Chat UI and sidebar dashboard\n"
        "- **OpenAI** — Conversational model and structured extraction\n"
        "- **SQLite** (WAL mode) — Conversations, messages, events, tasks, goals, time_logs\n"
        "- **Event sourcing** — Append-only events; state tables updated via projection"
    )

with tab_how:
    st.subheader("Flow")
    st.markdown(
        "**Two-phase turn:** (1) **Conversation** — always works; the model replies in natural language with context. "
        "(2) **Extraction** — silent, best-effort; the same turn can produce events for new tasks, goal updates, time logs, or notes. "
        "You send a message; the assistant responds; behind the scenes events are appended and projected into tasks, goals, and time_logs."
    )

with tab_technical:
    st.subheader("Design decisions")
    st.markdown(
        "- **Event sourcing** — Avoids contradictory facts and allows replay if extractors improve.\n"
        "- **Conversation first** — User always gets a coherent reply; extraction is additive.\n"
        "- **Exploratory phase** — Built for daily use and pattern learning before locking production architecture."
    )

with tab_system:
    st.subheader("Architecture")
    st.markdown(
        "**Layers:**\n"
        "- **Agent** — Orchestrator runs chat then extraction; prompts in `agent/prompts/` (chat.txt, extract.txt).\n"
        "- **Events** — Event store (append-only) and projector (events → tasks, goals, time_logs).\n"
        "- **DB** — SQLite schema (conversations, messages, events, tasks, goals, time_logs); snapshot support for backup/restore."
    )

with tab_run:
    st.subheader("Run locally")
    st.markdown("From the repository root:")
    st.code("cd Ai/assistant && streamlit run assistant.py", language="bash")
    st.markdown("Requires `OPENAI_API_KEY` in `Ai/assistant/.env`.")
    st.subheader("Source")
    st.markdown("`Ai/assistant/` — agent, config, db, events, and docs.")
