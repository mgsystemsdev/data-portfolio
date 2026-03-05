"""Streamlit chat UI with persistent conversation and sidebar dashboard."""
import csv
import io
import json
import os
from datetime import datetime

import streamlit as st

from agent import chat
from db.database import get_connection, init_db
from events.event_store import get_all_events

st.set_page_config(page_title="Personal Task & Goal Assistant", page_icon="💬")
init_db()

# -- Persistent conversation ID --
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None

# -- Load messages from DB for current conversation --
def load_messages_from_db(conv_id):
    if not conv_id:
        return []
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY created_at",
            (conv_id,),
        ).fetchall()
    finally:
        conn.close()
    return [{"role": r[0], "content": r[1]} for r in rows]

# -- Sidebar: dashboard + tools --
with st.sidebar:
    if st.button("✨ New conversation"):
        st.session_state.conversation_id = None
        st.rerun()

    st.markdown("---")

    conn = get_connection()
    try:
        # Tasks
        tasks = conn.execute("SELECT title, status FROM tasks WHERE status NOT IN ('done','completed','canceled') ORDER BY updated_at DESC LIMIT 10").fetchall()
        goals = conn.execute("SELECT title FROM goals ORDER BY updated_at DESC LIMIT 10").fetchall()
        time_logs = conn.execute("SELECT duration_minutes, logged_at FROM time_logs ORDER BY logged_at DESC LIMIT 5").fetchall()

        # -- Known facts --
        notes = conn.execute(
            "SELECT json_extract(payload, '$.content'), json_extract(payload, '$.category') "
            "FROM events WHERE event_type = 'NOTE_RECORDED' "
            "AND json_extract(payload, '$.category') IN ('identity','preference','constraint') "
            "ORDER BY created_at DESC LIMIT 8"
        ).fetchall()

        # -- Week stats --
        week_tasks = conn.execute(
            "SELECT COUNT(*) FROM events WHERE event_type='TASK_COMPLETED' "
            "AND created_at > datetime('now','-7 days')"
        ).fetchone()[0]
        week_time = conn.execute(
            "SELECT COALESCE(SUM(duration_minutes),0) FROM time_logs "
            "WHERE logged_at > datetime('now','-7 days')"
        ).fetchone()[0]

        # -- Recently completed --
        done = conn.execute(
            "SELECT title, updated_at FROM tasks WHERE status IN ('done','completed') "
            "ORDER BY updated_at DESC LIMIT 10"
        ).fetchall()

        # -- Export data --
        all_tasks = conn.execute("SELECT task_id, title, status, created_at, updated_at FROM tasks").fetchall()
        all_goals = conn.execute("SELECT goal_id, title, created_at, updated_at FROM goals").fetchall()
        all_time = conn.execute("SELECT id, task_id, goal_id, duration_minutes, logged_at FROM time_logs").fetchall()
    finally:
        conn.close()

    if tasks:
        st.markdown("### 📋 Tasks")
        for t in tasks:
            icon = "🔵" if t[1] == "doing" else "⬜"
            st.markdown(f"{icon} {t[0]}")

    if goals:
        st.markdown("### 🎯 Goals")
        for g in goals:
            st.markdown(f"• {g[0]}")

    if time_logs:
        st.markdown("### ⏱ Recent time")
        for tl in time_logs:
            st.markdown(f"• {tl[0]} min — {tl[1]}")

    # -- Known facts section --
    if notes:
        st.markdown("### 🧠 What I know")
        for n in notes:
            st.markdown(f"• `{n[1]}` {n[0]}")

    # -- Week stats section --
    st.markdown("### 📊 This week")
    st.metric("Tasks completed", week_tasks)
    st.metric("Time logged", f"{int(week_time)} min")

    # -- Recently completed --
    if done:
        with st.expander("✅ Recently completed"):
            for d in done:
                st.markdown(f"• ~~{d[0]}~~ — {d[1]}")

    st.markdown("---")

    with st.expander("Raw event log"):
        events = get_all_events()
        if events:
            st.json(events)
        else:
            st.caption("No events yet.")

    # -- JSON export --
    snapshot = {
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "tasks": [{"task_id": t[0], "title": t[1], "status": t[2], "created_at": t[3], "updated_at": t[4]} for t in all_tasks],
        "goals": [{"goal_id": g[0], "title": g[1], "created_at": g[2], "updated_at": g[3]} for g in all_goals],
        "time_logs": [{"id": l[0], "task_id": l[1], "goal_id": l[2], "duration_minutes": l[3], "logged_at": l[4]} for l in all_time],
        "events": get_all_events(),
    }
    st.download_button(
        "📥 Export Snapshot",
        data=json.dumps(snapshot, indent=2),
        file_name=f"snapshot_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json",
    )

    # -- CSV snapshot export --
    if st.button("📁 Save Snapshot to Folder"):
        today = datetime.utcnow().strftime('%Y-%m-%d')
        folder = os.path.join("snapshots", today)
        os.makedirs(folder, exist_ok=True)

        with open(os.path.join(folder, "tasks.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["task_id", "title", "status", "created_at", "updated_at"])
            w.writerows(all_tasks)

        with open(os.path.join(folder, "goals.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["goal_id", "title", "created_at", "updated_at"])
            w.writerows(all_goals)

        with open(os.path.join(folder, "time_logs.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["id", "task_id", "goal_id", "duration_minutes", "logged_at"])
            w.writerows(all_time)

        st.success(f"Snapshot saved to {folder}/")

# -- Main chat area --
st.title("💬 Personal Task & Goal Assistant")

messages = load_messages_from_db(st.session_state.conversation_id)
for msg in messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if user_input := st.chat_input("Message"):
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            conv_id, reply = chat(user_input, st.session_state.conversation_id)
            st.session_state.conversation_id = conv_id
        st.write(reply)

    st.rerun()
