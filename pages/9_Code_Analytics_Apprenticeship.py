import streamlit as st

st.title("Code & Analytics Apprenticeship")

tab_overview, tab_how, tab_technical, tab_system, tab_run = st.tabs([
    "Overview", "How it works", "Technical design", "System design", "Run"
])

with tab_overview:
    st.subheader("What it is")
    st.markdown(
        "A **topic-based apprenticeship engine** for programming and technology. "
        "Same UI pattern as the Concept Practice Engine: select a topic from the sidebar or type a topic name, then work through concepts one challenge at a time. "
        "Structured learning with lock-on-mastery and resume support."
    )
    st.subheader("Problem it solves")
    st.markdown(
        "Learning code and analytics in a structured but topic-flexible way. "
        "The app guides you through concepts within a topic and tracks progress; you can resume and switch topics without losing state."
    )
    st.subheader("Technology stack")
    st.markdown(
        "- **Streamlit** or **Flet** — UI (streamlit_app.py or desktop.py)\n"
        "- **OpenAI** — Teaching and state updates (orchestration only)\n"
        "- **SQLite** — Sessions, system_state, concept_progress, runs\n"
        "- **Prompts** — prompt_v7.md, knowledge_file_v7.md; topics.py for topic menu"
    )

with tab_how:
    st.subheader("Flow")
    st.markdown(
        "Identical to Concept Practice Engine: user message → orchestration (get_system_state, build_system_prompt, stream LLM, save_message, parse_state_updates, apply_transitions). "
        "Sidebar shows run, topic, category, current concept, last locked, and concept progress. "
        "Welcome message invites selecting a topic from the sidebar or typing a topic name to begin."
    )

with tab_technical:
    st.subheader("Design decisions")
    st.markdown(
        "- **Topic-based** — Same conceptual model as Concept Practice Engine; different prompt/knowledge file (prompt_v7, knowledge_file_v7).\n"
        "- **Shared codebase pattern** — Metacode and teacher_pract share orchestration, db, transition_engine, state_parser; only prompts and entry point differ.\n"
        "- **No handout mode** — This app does not implement handout drill mode; that is in teacher_pract only."
    )

with tab_system:
    st.subheader("Architecture")
    st.markdown(
        "**Layers:**\n"
        "- **UI** — streamlit_app.py or desktop.py; TOPIC_MENU, session/run controls.\n"
        "- **Orchestration** — handle_user_message; prompts built from state and DB.\n"
        "- **DB** — system_state, concept_progress; build_resume_block for context.\n"
        "- **Transition engine / state_parser** — Same as teacher_pract; JSON state block with lock/advance."
    )

with tab_run:
    st.subheader("Run locally")
    st.markdown("From the repository root:")
    st.code("cd Ai/metacode && streamlit run streamlit_app.py", language="bash")
    st.markdown("Flet desktop: `cd Ai/metacode && python desktop.py`")
    st.subheader("Source")
    st.markdown("`Ai/metacode/` — streamlit_app.py, desktop.py, orchestration, db, prompts, topics.py, transition_engine.")
