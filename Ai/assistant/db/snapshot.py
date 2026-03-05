"""Save and load snapshots by stream_id."""
import json
from .database import get_connection


def save(stream_id: str, version: int, data: dict):
    conn = get_connection()
    conn.execute(
        """INSERT OR REPLACE INTO snapshots (stream_id, version, data, updated_at)
           VALUES (?, ?, ?, datetime('now'))""",
        (stream_id, version, json.dumps(data)),
    )
    conn.commit()
    conn.close()


def load(stream_id: str) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT version, data FROM snapshots WHERE stream_id = ?",
        (stream_id,),
    ).fetchone()
    conn.close()
    if not row:
        return None
    return {"version": row[0], "data": json.loads(row[1])}
