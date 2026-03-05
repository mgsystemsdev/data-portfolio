import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from openai import OpenAI
from config import OPENAI_API_KEY
from db import (
    init_db,
    create_session,
    save_message,
    get_conversation_history,
    get_system_state,
    get_topic_concepts,
    update_system_state,
    get_current_run,
    build_resume_block,
    reset_for_new_run,
    close_session,
    generate_session_summary,
)
from state_parser import strip_state_block
from orchestration import handle_user_message
from topics import TOPIC_MENU

MAX_CONTEXT_MESSAGES = 30

# ── Init ──────────────────────────────────────────────

init_db()
client = OpenAI(api_key=OPENAI_API_KEY)

st.set_page_config(
    page_title="Code & Analytics Apprenticeship",
    page_icon="🔧",
    layout="wide",
)

# ── Session State ─────────────────────────────────────

if "session_id" not in st.session_state:
    st.session_state.session_id = create_session()

if "messages" not in st.session_state:
    history = get_conversation_history(st.session_state.session_id)
    if history:
        st.session_state.messages = history
    else:
        st.session_state.messages = [
            {"role": "assistant", "content": "Welcome to the Code & Analytics Apprenticeship.\n\nSelect a topic from the sidebar or type a topic name to begin."}
        ]

# ── Sidebar: System State ─────────────────────────────

with st.sidebar:
    st.markdown("## 📌 System State")
    state = get_system_state()

    run = get_current_run()
    run_number = run["run_number"] if run else 1

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Run", run_number)
    with col2:
        topic_display = state.get("topic", "None")
        st.metric("Topic", topic_display[:12] if topic_display != "None" else "—")

    category_label = state.get("category", "general")
    if category_label in ("general", "None"):
        category_label = "All categories"
    st.markdown(f"**Category:** {category_label}")
    st.markdown(f"**Current Concept:** {state.get('current_concept', 'None')}")
    st.markdown(f"**Last Locked:** {state.get('last_locked', 'None')}")

    # Concept progress for current topic/category
    topic = state.get("topic", "None")
    category = state.get("category", "general")
    concepts = get_topic_concepts(topic, category) if topic != "None" else []

    if concepts:
        st.divider()
        st.markdown("### 📋 Concept Progress")
        for c in concepts:
            icon = "✅" if c["locked"] else "⬜"
            st.markdown(f"{icon} {c['concept_name']}")

    st.divider()

    # Topic/Category selector
    with st.expander("🎯 Topic Practice"):
        topic_options = list(TOPIC_MENU.keys())
        selected_topic = st.selectbox(
            "Select Topic",
            topic_options,
            index=topic_options.index(topic) if topic in topic_options else 0,
        )
        category_options = ["(All categories)"] + TOPIC_MENU.get(selected_topic, [])
        selected_category = st.selectbox(
            "Select Category",
            category_options,
        )

        if st.button("▶️ Practice This Topic", use_container_width=True):
            chosen_category = selected_category if selected_category != "(All categories)" else "general"
            update_system_state(
                topic=selected_topic,
                category=chosen_category,
                current_concept="None",
            )
            close_session(st.session_state.session_id)
            generate_session_summary(st.session_state.session_id)
            st.session_state.session_id = create_session()
            resume = build_resume_block(topic=selected_topic, category=chosen_category)
            # Persist resume so the agent sees it in conversation history when the user sends the first message
            save_message(
                st.session_state.session_id,
                "assistant",
                resume,
                topic=selected_topic,
                concept=None,
                status="complete",
            )
            st.session_state.messages = [{"role": "assistant", "content": resume}]
            st.rerun()

    if st.button("▶️ Resume", use_container_width=True):
        resume = build_resume_block()
        save_message(
            st.session_state.session_id,
            "assistant",
            resume,
            topic=state.get("topic"),
            concept=state.get("current_concept"),
            status="complete",
        )
        st.session_state.messages = [{"role": "assistant", "content": resume}]
        st.rerun()

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🔄 New Session", use_container_width=True):
            close_session(st.session_state.session_id)
            generate_session_summary(st.session_state.session_id)
            st.session_state.session_id = create_session()
            resume = build_resume_block()
            save_message(
                st.session_state.session_id,
                "assistant",
                resume,
                topic=state.get("topic"),
                concept=state.get("current_concept"),
                status="complete",
            )
            st.session_state.messages = [{"role": "assistant", "content": resume}]
            st.rerun()
    with col_b:
        if st.button("🔁 New Run", use_container_width=True):
            close_session(st.session_state.session_id)
            generate_session_summary(st.session_state.session_id)
            reset_for_new_run()
            st.session_state.session_id = create_session()
            resume = build_resume_block()
            save_message(
                st.session_state.session_id,
                "assistant",
                resume,
                topic=state.get("topic"),
                concept=state.get("current_concept"),
                status="complete",
            )
            st.session_state.messages = [{"role": "assistant", "content": resume}]
            st.rerun()

# ── Main Chat ─────────────────────────────────────────

st.title("🔧 Code & Analytics Apprenticeship")
st.caption("One concept at a time. Any topic. Full depth.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Type a topic, paste your output, or ask a question..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        placeholder = st.empty()
        try:
            full_response = handle_user_message(
                st.session_state.session_id,
                prompt,
                client=client,
                max_context_messages=MAX_CONTEXT_MESSAGES,
                on_chunk=lambda text: placeholder.markdown(text),
            )
            placeholder.markdown(strip_state_block(full_response))
        except Exception as e:
            st.error(f"OpenAI API error: {e}")
            st.stop()

    st.session_state.messages.append({
        "role": "assistant",
        "content": strip_state_block(full_response),
    })
    st.rerun()
