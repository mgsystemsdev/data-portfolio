import streamlit as st

st.title("Concept Practice Engine")

tab_overview, tab_how, tab_technical, tab_system, tab_run = st.tabs([
    "Overview", "How it works", "Technical design", "System design", "Run"
])

with tab_overview:
    st.subheader("What it is")
    st.markdown(
        "A **topic- and concept-based practice app** for programming and technology. "
        "You select a topic from the sidebar; the engine drills one challenge at a time and locks concepts when you demonstrate understanding. "
        "**Handout mode** lets you paste or upload handout content and drill only those concepts—no new topic decomposition until the handout is complete."
    )
    st.subheader("Problem it solves")
    st.markdown(
        "Structured practice without a fixed stage sequence: focus on topics and concepts that matter to you. "
        "Handout mode supports curriculum handoffs (e.g. from the Data Analytics Apprenticeship) so you can practice exactly what was taught in a stage."
    )
    st.subheader("Technology stack")
    st.markdown(
        "- **Streamlit** or **Flet** — UI (streamlit_app.py or desktop.py)\n"
        "- **OpenAI** — Drills and state updates (orchestration only)\n"
        "- **SQLite** — Sessions, system_state, concept_progress, runs\n"
        "- **Prompts** — prompt_pract_v1.md, knowledge_file_v7.md; topics.py for topic menu"
    )

with tab_how:
    st.subheader("Flow")
    st.markdown(
        "Same as the Data Analytics Apprenticeship pattern: user message → orchestration (state, build_system_prompt, stream LLM, parse_state_updates, apply_transitions). "
        "State includes topic, category, current_concept, last_locked; sidebar shows run number, topic, category, concept progress. "
        "When **handout_mode** is active, the prompt appends handout instructions and handout content; decomposition and topic_change are not used."
    )

with tab_technical:
    st.subheader("Design decisions")
    st.markdown(
        "- **Topic/concept model** — Flexible scope; user picks topic and category.\n"
        "- **Handout drill mode** — Prompt-only override; handout content in state; completion = all handout concepts locked.\n"
        "- **Same stack as metacode** — Shared patterns (orchestration, state_parser, transition_engine, db) with different prompt and topic set."
    )

with tab_system:
    st.subheader("Architecture")
    st.markdown(
        "**Layers:**\n"
        "- **UI** — streamlit_app.py or desktop.py; topic/category from TOPIC_MENU, New Session/Run, Resume.\n"
        "- **Orchestration** — handle_user_message; optional filter in handout_mode to drop decompose/topic_change proposals.\n"
        "- **DB** — system_state (topic, category, handout_mode, active_handout), concept_progress; all_handout_concepts_locked to exit handout mode.\n"
        "- **Transition engine** — Lock/upsert concepts; unchanged by handout mode (prompt tells model not to emit topic_change/decompose)."
    )

with tab_run:
    st.subheader("Run locally")
    st.markdown("From the repository root:")
    st.code("cd Ai/teacher_pract && streamlit run streamlit_app.py", language="bash")
    st.markdown("Flet desktop: `cd Ai/teacher_pract && python desktop.py`")
    st.subheader("Source")
    st.markdown("`Ai/teacher_pract/` — streamlit_app.py, desktop.py, orchestration, db, prompts, topics.py, transition_engine.")
