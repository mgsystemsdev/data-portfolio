import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL
from db import (
    init_db,
    create_session,
    save_message,
    get_conversation_history,
    get_system_state,
    get_stage_methods,
    update_system_state,
    build_resume_block,
    reset_for_new_run,
    close_session,
    generate_session_summary,
)
from orchestration import handle_user_message

STAGE_NAMES = {
    "S0": "SETUP", "S1": "LOAD", "S2": "INSPECT", "S3": "CLEAN",
    "S4": "SELECT", "S5": "TRANSFORM (Core Facts)",
    "S6": "TRANSFORM (Task Mechanics)", "S7A": "AGGREGATE (Pandas)",
    "S7B": "AGGREGATE (SQL)", "S8": "SLA ENGINE",
    "S9": "INTELLIGENCE ENGINE", "S10": "VALIDATE",
    "S11": "PRESENT", "S12": "AUTOMATE",
}

# ── Init ──────────────────────────────────────────────

init_db()
client = OpenAI(api_key=OPENAI_API_KEY)

st.set_page_config(
    page_title="Data Analytics Apprenticeship",
    page_icon="🔧",
    layout="wide",
)

# ── Session State ─────────────────────────────────────

if "session_id" not in st.session_state:
    # Save where the learner actually was before resetting to S0
    _prev = get_system_state()
    st.session_state.resume_stage = _prev["stage"]
    update_system_state(
        stage="S0",
        stage_name="SETUP",
        next_action="Confirm folder structure",
        last_hardened="None",
    )
    st.session_state.session_id = create_session()

if "messages" not in st.session_state:
    history = get_conversation_history(st.session_state.session_id)
    if history:
        st.session_state.messages = history
    else:
        st.session_state.messages = [
            {"role": "assistant", "content": "Welcome to the Data Analytics Apprenticeship. Type **begin** when you're ready."}
        ]

# ── Sidebar: System State ─────────────────────────────

with st.sidebar:
    st.markdown("## 📌 System State")
    state = get_system_state()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Stage", f"{state['stage']}")
    with col2:
        st.metric("Prod Ready", state["prod_ready"])

    st.markdown(f"**Stage Name:** {state['stage_name']}")
    st.markdown(f"**Stack:** {state['stack']}")
    st.markdown(f"**Shape:** {state['shape']}")
    st.markdown(f"**Scope:** {state['scope']}")
    st.markdown(f"**Artifacts:** {state['artifacts']}")
    st.markdown(f"**Last Hardened:** {state['last_hardened']}")
    st.markdown(f"**KPIs:** {state['kpis']}")
    st.markdown(f"**NB Done:** {state['nb_done']}")
    st.markdown(f"**Next:** {state['next_action']}")

    st.divider()

    # Method progress for current stage
    methods = get_stage_methods(state["stage"])
    if methods:
        st.markdown("### 📋 Method Progress")
        for m in methods:
            icon = "✅" if m["locked"] else "⬜"
            st.markdown(f"{icon} {m['method_name']} {'(locked)' if m['locked'] else ''}")

    st.divider()

    with st.expander("🎯 Stage Practice"):
        stage_options = list(STAGE_NAMES.keys())
        current_idx = stage_options.index(state["stage"]) if state["stage"] in stage_options else 0
        practice_stage = st.selectbox(
            "Jump to stage",
            stage_options,
            index=current_idx,
            format_func=lambda s: f"{s} — {STAGE_NAMES[s]}",
        )
        if st.button("Practice This Stage"):
            new_name = STAGE_NAMES.get(practice_stage, practice_stage)
            update_system_state(stage=practice_stage, stage_name=new_name)
            close_session(st.session_state.session_id)
            generate_session_summary(st.session_state.session_id)
            st.session_state.session_id = create_session()
            st.session_state.messages = []
            resume = build_resume_block(stage=practice_stage)
            st.session_state.messages.append({"role": "assistant", "content": resume})
            save_message(st.session_state.session_id, "assistant", resume, status="complete")
            st.rerun()

    if st.button("📄 Generate Handout", use_container_width=True):
        update_system_state(handoff_mode=1)
        st.session_state.generate_handout = True
        st.rerun()

    if st.button("▶️ Resume", use_container_width=True):
        target = st.session_state.get("resume_stage", "S0")
        target_name = STAGE_NAMES.get(target, target)
        update_system_state(stage=target, stage_name=target_name)
        st.session_state.messages = []
        resume = build_resume_block(stage=target)
        st.session_state.messages.append({"role": "assistant", "content": resume})
        save_message(st.session_state.session_id, "assistant", resume, status="complete")
        st.rerun()

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🔄 New Session", use_container_width=True):
            close_session(st.session_state.session_id)
            generate_session_summary(st.session_state.session_id)
            st.session_state.session_id = create_session()
            st.session_state.messages = []
            resume = build_resume_block()
            st.session_state.messages.append({"role": "assistant", "content": resume})
            save_message(st.session_state.session_id, "assistant", resume, status="complete")
            st.rerun()
    with col_b:
        if st.button("🔁 New Run", use_container_width=True):
            close_session(st.session_state.session_id)
            generate_session_summary(st.session_state.session_id)
            reset_for_new_run()
            st.session_state.session_id = create_session()
            st.session_state.messages = []
            resume = build_resume_block()
            st.session_state.messages.append({"role": "assistant", "content": resume})
            save_message(st.session_state.session_id, "assistant", resume, status="complete")
            st.rerun()

# ── Main Chat ─────────────────────────────────────────

st.title("🔧 Data Analytics Apprenticeship")
st.caption("A senior engineer walking you through real production work — one method at a time.")

# Ensure messages exists (e.g. after long run or session reset)
if "messages" not in st.session_state:
    sid = st.session_state.get("session_id")
    st.session_state.messages = get_conversation_history(sid) if sid else [
        {"role": "assistant", "content": "Welcome to the Data Analytics Apprenticeship. Type **begin** when you're ready."}
    ]

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle pending handout generation
if st.session_state.get("generate_handout"):
    st.session_state.generate_handout = False
    with st.chat_message("user"):
        st.markdown("Generate handout.")
    st.session_state.messages.append({"role": "user", "content": "Generate handout."})

    with st.chat_message("assistant"):
        placeholder = st.empty()
        try:
            full_response = handle_user_message(
                st.session_state.session_id,
                "Generate handout.",
                client,
                on_chunk=lambda t: placeholder.markdown(t + "▌"),
            )
            placeholder.markdown(full_response)
        except Exception as e:
            st.error(f"OpenAI API error: {e}")
            st.stop()

    st.session_state.messages.append({"role": "assistant", "content": full_response})
    st.rerun()

# Chat input
if prompt := st.chat_input("Paste your output, ask a question, or say 'begin'..."):
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    if "messages" not in st.session_state:
        st.session_state.messages = []
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Stream response via orchestration (saves messages, runs parser + engine when complete)
    with st.chat_message("assistant"):
        placeholder = st.empty()
        try:
            full_response = handle_user_message(
                st.session_state.session_id,
                prompt,
                client,
                on_chunk=lambda t: placeholder.markdown(t + "▌"),
            )
            placeholder.markdown(full_response)
        except Exception as e:
            st.error(f"OpenAI API error: {e}")
            st.stop()

    if "messages" not in st.session_state:
        st.session_state.messages = get_conversation_history(st.session_state.get("session_id")) or []
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    st.rerun()
