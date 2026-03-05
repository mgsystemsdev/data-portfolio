"""Append-only event store."""
import json
from db.database import get_connection


def append_event(event_type: str, payload_dict: dict, source_message_id: str | None = None) -> int:
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO events (event_type, payload, source_message_id) VALUES (?, ?, ?)",
        (event_type, json.dumps(payload_dict), source_message_id),
    )
    conn.commit()
    eid = cur.lastrowid
    conn.close()
    return eid


def get_all_events():
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, event_type, payload, source_message_id, created_at "
        "FROM events ORDER BY id"
    ).fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "event_type": r[1],
            "payload": r[2],
            "source_message_id": r[3],
            "created_at": r[4],
        }
        for r in rows
    ]
