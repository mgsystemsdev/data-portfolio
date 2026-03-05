import streamlit as st

st.title("Data Analytics Apprenticeship")

tab_overview, tab_how, tab_technical, tab_system, tab_run = st.tabs([
    "Overview", "How it works", "Technical design", "System design", "Run"
])

with tab_overview:
    st.subheader("What it is")
    st.markdown(
        "A **stage-based learning app** for data analytics: Pandas and SQL. "
        "Structured progression through stages S0–S12 (Setup, Load, Inspect, Clean, Select, Transform, Aggregate, SLA Engine, Intelligence Engine, Validate, Present, Automate). "
        "Each stage has methods; the engine teaches one concept at a time and locks progress when you demonstrate understanding."
    )
    st.subheader("Problem it solves")
    st.markdown(
        "Learning data work in a structured way—from folder setup and loading data through cleaning, transformation, and automation—without skipping steps. "
        "The app tracks method progress, supports resume, and can generate handouts for the last locked stage for practice in a separate drill mode."
    )
    st.subheader("Technology stack")
    st.markdown(
        "- **Streamlit** or **Flet** — UI (teacher.py or desktop.py)\n"
        "- **OpenAI** — Teaching and state updates (orchestration only)\n"
        "- **SQLite** — Sessions, system_state, method_progress, concept_progress\n"
        "- **Prompts** — External .md (prompt_v6.md, knowledge_file.md); state and stage method map in prompts.py"
    )

with tab_how:
    st.subheader("Flow")
    st.markdown(
        "User message → orchestration builds system prompt from state and DB (stage, method progress, resume block) → LLM response streamed → state block parsed (regex) → transition_engine applies lock/advance. "
        "Sidebar shows stage, prod-ready flag, stack, shape; method progress and session controls (New Session, New Run, Resume, Practice This Stage)."
    )

with tab_technical:
    st.subheader("Design decisions")
    st.markdown(
        "- **Stage/method model** — Clear curriculum; progression is explicit and resumable.\n"
        "- **Single LLM call site** — All model calls in orchestration; prompts built from state and DB.\n"
        "- **Handout mode** — Optional: generate handout for last locked stage, then continue in practice app."
    )

with tab_system:
    st.subheader("Architecture")
    st.markdown(
        "**Layers:**\n"
        "- **UI** — teacher.py (Streamlit) or desktop.py (Flet); calls handle_user_message.\n"
        "- **Orchestration** — handle_user_message: get_system_state, build_system_prompt, stream LLM, save_message, parse_state_updates, apply_transitions.\n"
        "- **DB** — system_state, method_progress, sessions, messages; build_resume_block for context.\n"
        "- **Transition engine** — Applies lock/advance from parsed state block; no business logic in UI."
    )

with tab_run:
    st.subheader("Run locally")
    st.markdown("From the repository root:")
    st.code("cd Ai/teacher && streamlit run app/teacher.py", language="bash")
    st.markdown("Flet desktop: `cd Ai/teacher && python app/desktop.py`")
    st.subheader("Source")
    st.markdown("`Ai/teacher/` — app/ (teacher.py, desktop.py, orchestration, db, prompts, transition_engine), docs/.")
