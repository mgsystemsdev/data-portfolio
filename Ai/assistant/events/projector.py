"""Project events into state tables."""
import json
from db.database import get_connection


def project_event(event_type: str, payload: dict, created_at: str):
    """Apply a single event to projection tables."""
    conn = get_connection()
    try:
        if event_type == "TASK_CREATED":
            conn.execute(
                "INSERT OR REPLACE INTO tasks (task_id, title, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (payload["task_id"], payload.get("title", ""), payload.get("status", "todo"), created_at, created_at),
            )
        elif event_type == "TASK_UPDATED":
            task_id = payload.get("task_id")
            task_title = payload.get("task_title")
            if task_id:
                conn.execute(
                    "UPDATE tasks SET title = COALESCE(?, title), status = COALESCE(?, status), updated_at = ? WHERE task_id = ?",
                    (payload.get("title"), payload.get("status"), created_at, task_id),
                )
            elif task_title:
                conn.execute(
                    "UPDATE tasks SET title = COALESCE(?, title), status = COALESCE(?, status), updated_at = ? WHERE title = ?",
                    (payload.get("title"), payload.get("status"), created_at, task_title),
                )
        elif event_type == "TASK_COMPLETED":
            task_id = payload.get("task_id")
            task_title = payload.get("task_title")
            if task_id:
                conn.execute("UPDATE tasks SET status = 'done', updated_at = ? WHERE task_id = ?", (created_at, task_id))
            elif task_title:
                conn.execute("UPDATE tasks SET status = 'done', updated_at = ? WHERE title = ?", (created_at, task_title))
        elif event_type == "GOAL_CREATED":
            conn.execute(
                "INSERT OR REPLACE INTO goals (goal_id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (payload["goal_id"], payload.get("title", ""), created_at, created_at),
            )
        elif event_type == "GOAL_UPDATED":
            goal_id = payload.get("goal_id")
            goal_title = payload.get("goal_title")
            if goal_id:
                conn.execute("UPDATE goals SET title = COALESCE(?, title), updated_at = ? WHERE goal_id = ?", (payload.get("title"), created_at, goal_id))
            elif goal_title:
                conn.execute("UPDATE goals SET title = COALESCE(?, title), updated_at = ? WHERE title = ?", (payload.get("title"), created_at, goal_title))
        elif event_type == "TIME_LOGGED":
            conn.execute(
                "INSERT INTO time_logs (task_id, goal_id, duration_minutes, logged_at) VALUES (?, ?, ?, ?)",
                (payload.get("task_id"), payload.get("goal_id"), payload["duration_minutes"], created_at),
            )
        conn.commit()
    finally:
        conn.close()
