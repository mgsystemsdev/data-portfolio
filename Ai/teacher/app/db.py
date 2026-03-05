import sqlite3
import json
from datetime import datetime
from config import DB_PATH


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT NOT NULL DEFAULT (datetime('now')),
            ended_at TEXT,
            stage_at_start TEXT,
            stage_at_end TEXT
        );

        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            stage TEXT,
            method TEXT,
            status TEXT,
            prompt_hash TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        );

        CREATE TABLE IF NOT EXISTS system_state (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            version INTEGER NOT NULL DEFAULT 1,
            stage TEXT NOT NULL DEFAULT 'S0',
            stage_name TEXT NOT NULL DEFAULT 'SETUP',
            stack TEXT NOT NULL DEFAULT 'None',
            shape TEXT NOT NULL DEFAULT 'Unknown',
            scope TEXT NOT NULL DEFAULT 'Not defined',
            artifacts TEXT NOT NULL DEFAULT 'None',
            last_hardened TEXT NOT NULL DEFAULT 'None',
            missing_anchors TEXT NOT NULL DEFAULT 'None',
            kpis TEXT NOT NULL DEFAULT 'None',
            prod_ready TEXT NOT NULL DEFAULT 'No',
            nb_done TEXT NOT NULL DEFAULT 'No',
            next_action TEXT NOT NULL DEFAULT 'Confirm folder structure',
            handoff_mode INTEGER NOT NULL DEFAULT 0,
            handout_pending_for_stage TEXT,
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS state_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            assistant_message_id INTEGER NOT NULL UNIQUE,
            prior_state_hash TEXT NOT NULL DEFAULT '',
            proposed_state TEXT NOT NULL DEFAULT '{}',
            applied INTEGER NOT NULL DEFAULT 0,
            rejection_reason TEXT,
            parser_mode TEXT NOT NULL DEFAULT 'regex',
            prompt_version TEXT,
            parser_version TEXT,
            timestamp TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (assistant_message_id) REFERENCES conversations(id)
        );

        CREATE TABLE IF NOT EXISTS method_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stage TEXT NOT NULL,
            method_number INTEGER NOT NULL,
            method_name TEXT NOT NULL,
            tier INTEGER NOT NULL DEFAULT 1,
            locked INTEGER NOT NULL DEFAULT 0,
            anchors_delivered TEXT NOT NULL DEFAULT '[]',
            attempts INTEGER NOT NULL DEFAULT 0,
            errors_hit TEXT NOT NULL DEFAULT '[]',
            first_seen_at TEXT,
            locked_at TEXT,
            UNIQUE(stage, method_name)
        );

        CREATE TABLE IF NOT EXISTS learner_profile (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            total_methods_locked INTEGER NOT NULL DEFAULT 0,
            total_errors INTEGER NOT NULL DEFAULT 0,
            avg_attempts_to_lock REAL NOT NULL DEFAULT 0,
            common_error_types TEXT NOT NULL DEFAULT '{}',
            slow_stages TEXT NOT NULL DEFAULT '[]',
            fast_stages TEXT NOT NULL DEFAULT '[]',
            struggle_anchors TEXT NOT NULL DEFAULT '[]',
            preferred_depth TEXT NOT NULL DEFAULT 'standard',
            notes TEXT NOT NULL DEFAULT '[]',
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS learner_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            event_type TEXT NOT NULL,
            stage TEXT,
            method TEXT,
            sentiment TEXT,
            details TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS pipeline_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_number INTEGER NOT NULL,
            started_at TEXT NOT NULL DEFAULT (datetime('now')),
            ended_at TEXT,
            stage_reached TEXT NOT NULL DEFAULT 'S0',
            methods_locked_total INTEGER NOT NULL DEFAULT 0,
            methods_first_try INTEGER NOT NULL DEFAULT 0,
            total_errors INTEGER NOT NULL DEFAULT 0,
            total_confusions INTEGER NOT NULL DEFAULT 0,
            total_breakthroughs INTEGER NOT NULL DEFAULT 0,
            notes TEXT NOT NULL DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS method_mastery (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_number INTEGER NOT NULL,
            stage TEXT NOT NULL,
            method_name TEXT NOT NULL,
            attempts INTEGER NOT NULL DEFAULT 0,
            errors INTEGER NOT NULL DEFAULT 0,
            confusions INTEGER NOT NULL DEFAULT 0,
            confidence_score INTEGER NOT NULL DEFAULT 0,
            mastery_level TEXT NOT NULL DEFAULT 'unseen',
            locked_at TEXT,
            UNIQUE(run_number, stage, method_name)
        );

        CREATE TABLE IF NOT EXISTS session_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            stage_start TEXT,
            stage_end TEXT,
            methods_covered TEXT NOT NULL DEFAULT '[]',
            methods_locked TEXT NOT NULL DEFAULT '[]',
            methods_struggled TEXT NOT NULL DEFAULT '[]',
            errors_count INTEGER NOT NULL DEFAULT 0,
            confusions_count INTEGER NOT NULL DEFAULT 0,
            breakthroughs_count INTEGER NOT NULL DEFAULT 0,
            avg_response_seconds REAL,
            summary_text TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        );

        CREATE TABLE IF NOT EXISTS struggle_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_type TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            frequency INTEGER NOT NULL DEFAULT 1,
            stages_affected TEXT NOT NULL DEFAULT '[]',
            methods_affected TEXT NOT NULL DEFAULT '[]',
            adaptation_rule TEXT NOT NULL DEFAULT '',
            first_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
            last_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(pattern_type, category)
        );

        CREATE TABLE IF NOT EXISTS learner_identity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            content TEXT NOT NULL,
            source_snippet TEXT NOT NULL DEFAULT '',
            session_id INTEGER,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(category, content)
        );
    """)
    # Seed singleton rows
    conn.execute("""
        INSERT OR IGNORE INTO system_state (id) VALUES (1)
    """)
    conn.execute("""
        INSERT OR IGNORE INTO learner_profile (id) VALUES (1)
    """)
    # Seed first pipeline run if none exists
    existing = conn.execute("SELECT COUNT(*) as c FROM pipeline_runs").fetchone()["c"]
    if existing == 0:
        conn.execute("INSERT INTO pipeline_runs (run_number) VALUES (1)")
    conn.commit()
    conn.close()
    _migrate_schema()


def _migrate_schema():
    """Add new columns/tables for existing DBs."""
    conn = get_conn()
    try:
        info = {r[1]: r for r in conn.execute("PRAGMA table_info(system_state)").fetchall()}
        if "version" not in info:
            conn.execute("ALTER TABLE system_state ADD COLUMN version INTEGER NOT NULL DEFAULT 1")
        if "handoff_mode" not in info:
            conn.execute("ALTER TABLE system_state ADD COLUMN handoff_mode INTEGER NOT NULL DEFAULT 0")
        if "handout_pending_for_stage" not in info:
            conn.execute("ALTER TABLE system_state ADD COLUMN handout_pending_for_stage TEXT")
        info_conv = {r[1]: r for r in conn.execute("PRAGMA table_info(conversations)").fetchall()}
        if "status" not in info_conv:
            conn.execute("ALTER TABLE conversations ADD COLUMN status TEXT")
        if "prompt_hash" not in info_conv:
            conn.execute("ALTER TABLE conversations ADD COLUMN prompt_hash TEXT")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS state_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                assistant_message_id INTEGER NOT NULL UNIQUE,
                prior_state_hash TEXT NOT NULL DEFAULT '',
                proposed_state TEXT NOT NULL DEFAULT '{}',
                applied INTEGER NOT NULL DEFAULT 0,
                rejection_reason TEXT,
                parser_mode TEXT NOT NULL DEFAULT 'regex',
                prompt_version TEXT,
                parser_version TEXT,
                timestamp TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (assistant_message_id) REFERENCES conversations(id)
            )
        """)
        conn.commit()
    finally:
        conn.close()


# --- Sessions ---

def create_session():
    conn = get_conn()
    state = get_system_state(conn)
    cur = conn.execute(
        "INSERT INTO sessions (stage_at_start) VALUES (?)",
        (state["stage"],)
    )
    session_id = cur.lastrowid
    conn.commit()
    conn.close()
    return session_id


def close_session(session_id):
    conn = get_conn()
    state = get_system_state(conn)
    conn.execute(
        "UPDATE sessions SET ended_at = datetime('now'), stage_at_end = ? WHERE id = ?",
        (state["stage"], session_id)
    )
    conn.commit()
    conn.close()


# --- Conversations ---

def save_message(session_id, role, content, stage=None, method=None, status=None, prompt_hash=None):
    """Save a message. Returns the new row id. For assistant messages, optional status ('pending'|'complete'|'failed') and prompt_hash."""
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO conversations (session_id, role, content, stage, method, status, prompt_hash) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (session_id, role, content, stage or None, method, status, prompt_hash)
    )
    msg_id = cur.lastrowid
    conn.commit()
    conn.close()
    return msg_id


def set_message_status(message_id, status):
    """Set status of an assistant message (pending|complete|failed)."""
    conn = get_conn()
    conn.execute("UPDATE conversations SET status = ? WHERE id = ?", (status, message_id))
    conn.commit()
    conn.close()


def set_message_content(message_id, content):
    """Set content of a message (e.g. after streaming complete)."""
    conn = get_conn()
    conn.execute("UPDATE conversations SET content = ? WHERE id = ?", (content, message_id))
    conn.commit()
    conn.close()


def insert_state_event(conn, assistant_message_id, prior_state_hash, proposed_state, parser_mode="regex", prompt_version=None):
    """Insert state_events row. Raises if UNIQUE(assistant_message_id) violated (idempotent). Returns event_id."""
    cur = conn.execute(
        """INSERT INTO state_events (assistant_message_id, prior_state_hash, proposed_state, parser_mode, prompt_version)
           VALUES (?, ?, ?, ?, ?)""",
        (assistant_message_id, prior_state_hash, proposed_state, parser_mode, prompt_version or ""),
    )
    return cur.lastrowid


def update_state_event_result(conn, assistant_message_id, applied, rejection_reason=None):
    """Mark state_events row as applied or rejected."""
    conn.execute(
        "UPDATE state_events SET applied = ?, rejection_reason = ? WHERE assistant_message_id = ?",
        (1 if applied else 0, rejection_reason, assistant_message_id),
    )


def get_conversation_history(session_id, limit=50):
    conn = get_conn()
    rows = conn.execute(
        "SELECT role, content FROM conversations WHERE session_id = ? ORDER BY id DESC LIMIT ?",
        (session_id, limit)
    ).fetchall()
    conn.close()
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]


def get_all_history(limit=200):
    conn = get_conn()
    rows = conn.execute(
        "SELECT role, content FROM conversations ORDER BY id DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]


# --- System State ---

def get_system_state(conn=None):
    close = conn is None
    if close:
        conn = get_conn()
    row = conn.execute("SELECT * FROM system_state WHERE id = 1").fetchone()
    if close:
        conn.close()
    return dict(row) if row else {}


def update_system_state(conn=None, **kwargs):
    if not kwargs:
        return
    close = conn is None
    if close:
        conn = get_conn()
    kwargs["updated_at"] = datetime.now().isoformat()
    sets = ", ".join(f"{k} = ?" for k in kwargs)
    vals = list(kwargs.values())
    conn.execute(f"UPDATE system_state SET {sets} WHERE id = 1", vals)
    if close:
        conn.commit()
        conn.close()


def get_last_locked_stage(conn=None):
    """Return the stage of the most recently locked method, or None if no method is locked."""
    close = conn is None
    if close:
        conn = get_conn()
    row = conn.execute(
        "SELECT stage FROM method_progress WHERE locked = 1 ORDER BY locked_at DESC LIMIT 1"
    ).fetchone()
    if close:
        conn.close()
    return row["stage"] if row else None


def is_stage_fully_completed(stage, conn=None):
    """Return True if the stage has at least one method and all of them are locked."""
    methods = get_stage_methods(stage, conn=conn)
    if not methods:
        return False
    return all(m.get("locked") for m in methods)


def update_system_state_with_version(conn, expected_version, **kwargs):
    """Update system_state only if version matches; increments version. Returns True if updated."""
    if not kwargs:
        return True
    kwargs["updated_at"] = datetime.now().isoformat()
    kwargs["version"] = expected_version + 1
    sets = ", ".join(f"{k} = ?" for k in kwargs)
    vals = list(kwargs.values()) + [expected_version]
    cur = conn.execute(
        f"UPDATE system_state SET {sets} WHERE id = 1 AND version = ?",
        vals,
    )
    return cur.rowcount > 0


# --- Method Progress ---

def get_stage_methods(stage, conn=None):
    close = conn is None
    if close:
        conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM method_progress WHERE stage = ? ORDER BY method_number",
        (stage,)
    ).fetchall()
    if close:
        conn.close()
    return [dict(r) for r in rows]


def upsert_method(stage, method_number, method_name, tier=1, conn=None):
    close = conn is None
    if close:
        conn = get_conn()
    conn.execute("""
        INSERT INTO method_progress (stage, method_number, method_name, tier, first_seen_at)
        VALUES (?, ?, ?, ?, datetime('now'))
        ON CONFLICT(stage, method_name) DO NOTHING
    """, (stage, method_number, method_name, tier))
    if close:
        conn.commit()
        conn.close()


def lock_method(stage, method_name, anchors=None, conn=None):
    close = conn is None
    if close:
        conn = get_conn()
    conn.execute("""
        UPDATE method_progress
        SET locked = 1, locked_at = datetime('now'), anchors_delivered = ?
        WHERE stage = ? AND method_name = ?
    """, (json.dumps(anchors or []), stage, method_name))
    if close:
        conn.commit()
        conn.close()


def increment_method_attempts(stage, method_name):
    conn = get_conn()
    conn.execute("""
        UPDATE method_progress SET attempts = attempts + 1
        WHERE stage = ? AND method_name = ?
    """, (stage, method_name))
    conn.commit()
    conn.close()


def log_method_error(stage, method_name, error_type):
    conn = get_conn()
    row = conn.execute(
        "SELECT errors_hit FROM method_progress WHERE stage = ? AND method_name = ?",
        (stage, method_name)
    ).fetchone()
    if row:
        errors = json.loads(row["errors_hit"])
        errors.append({"type": error_type, "at": datetime.now().isoformat()})
        conn.execute(
            "UPDATE method_progress SET errors_hit = ? WHERE stage = ? AND method_name = ?",
            (json.dumps(errors), stage, method_name)
        )
    conn.commit()
    conn.close()


# --- Learner Profile ---

def get_learner_profile():
    conn = get_conn()
    row = conn.execute("SELECT * FROM learner_profile WHERE id = 1").fetchone()
    conn.close()
    return dict(row) if row else {}


def update_learner_profile(**kwargs):
    if not kwargs:
        return
    conn = get_conn()
    kwargs["updated_at"] = datetime.now().isoformat()
    sets = ", ".join(f"{k} = ?" for k in kwargs)
    vals = list(kwargs.values())
    conn.execute(f"UPDATE learner_profile SET {sets} WHERE id = 1", vals)
    conn.commit()
    conn.close()


# --- Learner Events ---

def log_event(session_id, event_type, stage=None, method=None, details=None, sentiment=None):
    conn = get_conn()
    conn.execute(
        "INSERT INTO learner_events (session_id, event_type, stage, method, sentiment, details) VALUES (?, ?, ?, ?, ?, ?)",
        (session_id, event_type, stage, method, sentiment, json.dumps(details or {}))
    )
    conn.commit()
    conn.close()


def get_events(event_type=None, stage=None, limit=100):
    conn = get_conn()
    query = "SELECT * FROM learner_events WHERE 1=1"
    params = []
    if event_type:
        query += " AND event_type = ?"
        params.append(event_type)
    if stage:
        query += " AND stage = ?"
        params.append(stage)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- Pipeline Runs ---

def get_current_run(conn=None):
    close = conn is None
    if close:
        conn = get_conn()
    row = conn.execute("SELECT * FROM pipeline_runs ORDER BY run_number DESC LIMIT 1").fetchone()
    if close:
        conn.close()
    return dict(row) if row else None


def get_all_runs():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM pipeline_runs ORDER BY run_number").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def start_new_run():
    conn = get_conn()
    current = conn.execute("SELECT MAX(run_number) as m FROM pipeline_runs").fetchone()["m"] or 0
    new_num = current + 1
    conn.execute("INSERT INTO pipeline_runs (run_number) VALUES (?)", (new_num,))
    conn.commit()
    conn.close()
    return new_num


def update_run(run_number, **kwargs):
    if not kwargs:
        return
    conn = get_conn()
    sets = ", ".join(f"{k} = ?" for k in kwargs)
    vals = list(kwargs.values()) + [run_number]
    conn.execute(f"UPDATE pipeline_runs SET {sets} WHERE run_number = ?", vals)
    conn.commit()
    conn.close()


# --- Method Mastery ---

def record_mastery(run_number, stage, method_name, attempts=0, errors=0, confusions=0, conn=None):
    score = max(0, 3 - attempts - errors - confusions)
    if attempts == 0:
        level = "unseen"
    elif attempts <= 1 and errors == 0:
        level = "confident"
    elif attempts <= 2:
        level = "familiar"
    else:
        level = "fragile"

    close = conn is None
    if close:
        conn = get_conn()
    conn.execute("""
        INSERT INTO method_mastery (run_number, stage, method_name, attempts, errors, confusions, confidence_score, mastery_level)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(run_number, stage, method_name) DO UPDATE SET
            attempts = ?, errors = ?, confusions = ?,
            confidence_score = ?, mastery_level = ?
    """, (run_number, stage, method_name, attempts, errors, confusions, score, level,
          attempts, errors, confusions, score, level))
    if close:
        conn.commit()
        conn.close()


def promote_mastery(run_number, stage, method_name, conn=None):
    """Called when a method is locked — compute final mastery for this run."""
    close = conn is None
    if close:
        conn = get_conn()
    row = conn.execute(
        "SELECT * FROM method_mastery WHERE run_number = ? AND stage = ? AND method_name = ?",
        (run_number, stage, method_name)
    ).fetchone()

    if not row:
        record_mastery(run_number, stage, method_name, attempts=1, conn=conn)
        row = conn.execute(
            "SELECT * FROM method_mastery WHERE run_number = ? AND stage = ? AND method_name = ?",
            (run_number, stage, method_name)
        ).fetchone()

    # Check previous runs for progression
    prev = conn.execute("""
        SELECT mastery_level, confidence_score FROM method_mastery
        WHERE stage = ? AND method_name = ? AND run_number < ?
        ORDER BY run_number DESC LIMIT 1
    """, (stage, method_name, run_number)).fetchone()

    attempts = row["attempts"]
    errors = row["errors"]

    if prev:
        prev_level = prev["mastery_level"]
        if attempts <= 1 and errors == 0 and prev_level in ("fragile", "familiar"):
            level = "confident"
            score = 5
        elif attempts <= 1 and errors == 0 and prev_level == "confident":
            level = "hardened"
            score = 8
        elif attempts <= 1 and errors == 0:
            level = "hardened"
            score = 10
        else:
            score = max(0, 3 - attempts - errors)
            level = "familiar" if score >= 1 else "fragile"
    else:
        if attempts <= 1 and errors == 0:
            score = 3
            level = "confident"
        elif attempts <= 2:
            score = 1
            level = "familiar"
        else:
            score = 0
            level = "fragile"

    conn.execute("""
        UPDATE method_mastery SET confidence_score = ?, mastery_level = ?, locked_at = datetime('now')
        WHERE run_number = ? AND stage = ? AND method_name = ?
    """, (score, level, run_number, stage, method_name))
    if close:
        conn.commit()
        conn.close()
    return level


def get_mastery_summary(run_number=None):
    conn = get_conn()
    if run_number:
        rows = conn.execute(
            "SELECT * FROM method_mastery WHERE run_number = ? ORDER BY stage, method_name",
            (run_number,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM method_mastery ORDER BY run_number DESC, stage, method_name"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_fragile_methods():
    """Get methods that are still fragile in the latest run."""
    conn = get_conn()
    current_run = conn.execute("SELECT MAX(run_number) as m FROM pipeline_runs").fetchone()["m"] or 1
    rows = conn.execute("""
        SELECT stage, method_name, attempts, errors, confusions, mastery_level
        FROM method_mastery
        WHERE run_number = ? AND mastery_level IN ('fragile', 'familiar')
        ORDER BY confidence_score ASC
    """, (current_run,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- Struggle Patterns ---

def upsert_struggle(pattern_type, category, description, stage=None, method=None, adaptation_rule=""):
    conn = get_conn()
    existing = conn.execute(
        "SELECT * FROM struggle_patterns WHERE pattern_type = ? AND category = ?",
        (pattern_type, category)
    ).fetchone()

    if existing:
        stages = json.loads(existing["stages_affected"])
        methods = json.loads(existing["methods_affected"])
        if stage and stage not in stages:
            stages.append(stage)
        if method and method not in methods:
            methods.append(method)
        conn.execute("""
            UPDATE struggle_patterns
            SET frequency = frequency + 1, last_seen_at = datetime('now'),
                stages_affected = ?, methods_affected = ?, adaptation_rule = ?
            WHERE pattern_type = ? AND category = ?
        """, (json.dumps(stages), json.dumps(methods), adaptation_rule or existing["adaptation_rule"],
              pattern_type, category))
    else:
        conn.execute("""
            INSERT INTO struggle_patterns (pattern_type, category, description, stages_affected, methods_affected, adaptation_rule)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (pattern_type, category, description,
              json.dumps([stage] if stage else []),
              json.dumps([method] if method else []),
              adaptation_rule))
    conn.commit()
    conn.close()


def get_struggle_patterns(min_frequency=1):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM struggle_patterns WHERE frequency >= ? ORDER BY frequency DESC",
        (min_frequency,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- Learner Identity ---

def save_learner_identity(category, content, source_snippet="", session_id=None):
    """Store something the agent learned about the user as a person."""
    conn = get_conn()
    conn.execute("""
        INSERT INTO learner_identity (category, content, source_snippet, session_id)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(category, content) DO UPDATE SET
            source_snippet = ?, session_id = COALESCE(?, session_id)
    """, (category, content, source_snippet, session_id,
          source_snippet, session_id))
    conn.commit()
    conn.close()


def get_learner_identity():
    """Get everything the agent knows about the user as a person."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT category, content, source_snippet FROM learner_identity ORDER BY created_at"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- Session Summaries ---

def generate_session_summary(session_id):
    """Auto-generate and store a session summary from events and conversations."""
    conn = get_conn()

    session = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if not session:
        conn.close()
        return

    # Count events for this session
    errors = conn.execute(
        "SELECT COUNT(*) as c FROM learner_events WHERE session_id = ? AND event_type = 'error'",
        (session_id,)
    ).fetchone()["c"]
    confusions = conn.execute(
        "SELECT COUNT(*) as c FROM learner_events WHERE session_id = ? AND event_type IN ('confusion', 'frustration')",
        (session_id,)
    ).fetchone()["c"]
    breakthroughs = conn.execute(
        "SELECT COUNT(*) as c FROM learner_events WHERE session_id = ? AND event_type = 'breakthrough'",
        (session_id,)
    ).fetchone()["c"]

    # Methods touched this session (from conversations mentioning methods)
    methods_locked = conn.execute(
        "SELECT stage, method_name FROM method_progress WHERE locked_at >= ? AND locked_at <= COALESCE(?, datetime('now'))",
        (session["started_at"], session["ended_at"])
    ).fetchall()
    locked_list = [f"{r['method_name']}({r['stage']})" for r in methods_locked]

    # Struggled methods (from events)
    struggled = conn.execute("""
        SELECT DISTINCT method FROM learner_events
        WHERE session_id = ? AND event_type IN ('error', 'frustration', 'confusion') AND method IS NOT NULL
    """, (session_id,)).fetchall()
    struggled_list = [r["method"] for r in struggled]

    # Average response time
    avg_time = compute_avg_response_time(session_id, conn)

    # Build summary text
    parts = []
    parts.append(f"Session {session_id}: {session['stage_at_start'] or '?'} → {session['stage_at_end'] or '?'}")
    if locked_list:
        parts.append(f"Locked: {', '.join(locked_list)}")
    if struggled_list:
        parts.append(f"Struggled with: {', '.join(struggled_list)}")
    parts.append(f"Errors: {errors} | Confusions: {confusions} | Breakthroughs: {breakthroughs}")
    if avg_time:
        parts.append(f"Avg response time: {avg_time:.0f}s")

    summary_text = ". ".join(parts)

    conn.execute("""
        INSERT INTO session_summaries
        (session_id, stage_start, stage_end, methods_locked, methods_struggled,
         errors_count, confusions_count, breakthroughs_count, avg_response_seconds, summary_text)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session_id,
        session["stage_at_start"],
        session["stage_at_end"],
        json.dumps(locked_list),
        json.dumps(struggled_list),
        errors, confusions, breakthroughs,
        avg_time,
        summary_text,
    ))
    conn.commit()
    conn.close()


def get_recent_summaries(limit=5):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM session_summaries ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in reversed(rows)]


# --- Response Time Tracking ---

def compute_avg_response_time(session_id, conn=None):
    """Compute average seconds between assistant message and next user reply."""
    close = conn is None
    if close:
        conn = get_conn()

    rows = conn.execute("""
        SELECT role, created_at FROM conversations
        WHERE session_id = ? ORDER BY id
    """, (session_id,)).fetchall()

    if close:
        conn.close()

    if len(rows) < 2:
        return None

    from datetime import datetime as dt
    gaps = []
    for i in range(len(rows) - 1):
        if rows[i]["role"] == "assistant" and rows[i + 1]["role"] == "user":
            try:
                t1 = dt.fromisoformat(rows[i]["created_at"])
                t2 = dt.fromisoformat(rows[i + 1]["created_at"])
                gap = (t2 - t1).total_seconds()
                if 1 < gap < 3600:  # between 1 second and 1 hour
                    gaps.append(gap)
            except (ValueError, TypeError):
                pass

    return sum(gaps) / len(gaps) if gaps else None


# --- Spaced Repetition ---

def get_methods_due_for_review(days_threshold=7):
    """Find locked methods that haven't been seen in N days."""
    conn = get_conn()
    rows = conn.execute("""
        SELECT stage, method_name, locked_at,
               ROUND(julianday('now') - julianday(locked_at)) as days_since
        FROM method_progress
        WHERE locked = 1
          AND julianday('now') - julianday(locked_at) >= ?
        ORDER BY locked_at ASC
    """, (days_threshold,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_method_reviewed(stage, method_name):
    """Touch the locked_at timestamp to reset the review clock."""
    conn = get_conn()
    conn.execute(
        "UPDATE method_progress SET locked_at = datetime('now') WHERE stage = ? AND method_name = ?",
        (stage, method_name)
    )
    conn.commit()
    conn.close()


# --- Resume Block ---

def build_resume_block(stage=None):
    """Build the compact tracker block for resuming a session."""
    state = get_system_state()
    target_stage = stage or state["stage"]

    stage_names = {
        "S0": "SETUP", "S1": "LOAD", "S2": "INSPECT", "S3": "CLEAN",
        "S4": "SELECT", "S5": "TRANSFORM (Core Facts)",
        "S6": "TRANSFORM (Task Mechanics)", "S7A": "AGGREGATE (Pandas)",
        "S7B": "AGGREGATE (SQL)", "S8": "SLA ENGINE",
        "S9": "INTELLIGENCE ENGINE", "S10": "VALIDATE",
        "S11": "PRESENT", "S12": "AUTOMATE",
    }
    stage_label = stage_names.get(target_stage, target_stage)

    methods = get_stage_methods(target_stage)
    locked = [m["method_name"] for m in methods if m["locked"]]
    remaining = [m["method_name"] for m in methods if not m["locked"]]

    run = get_current_run()
    run_number = run["run_number"] if run else 1

    lines = [
        "── RESUMING SESSION ──────────────────",
        f"🧭 Stage: {target_stage} — {stage_label}",
        f"🔁 Run: {run_number}",
    ]

    for name in locked:
        lines.append(f"✅ {name} locked")

    if remaining:
        lines.append(f"📋 Remaining: {', '.join(remaining)}")
        lines.append(f"➡️ Next: {remaining[0]}")
    elif locked:
        lines.append("✅ All methods locked for this stage")
    else:
        lines.append("📋 No methods tracked yet — type 'begin' to start")

    lines.append("──────────────────────────────────────")
    return "\n".join(lines)


# --- New Run ---

def reset_for_new_run():
    """Start a new pipeline run: increment run, reset system state to S1."""
    new_run = start_new_run()
    update_system_state(
        stage="S1",
        stage_name="LOAD",
        prod_ready="No",
        nb_done="No",
        next_action="Begin Stage 1 methods",
    )
    return new_run
