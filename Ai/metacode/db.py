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
            topic_at_start TEXT,
            topic_at_end TEXT
        );

        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            topic TEXT,
            concept TEXT,
            status TEXT DEFAULT 'complete',
            prompt_hash TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        );

        CREATE TABLE IF NOT EXISTS system_state (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            topic TEXT NOT NULL DEFAULT 'None',
            category TEXT NOT NULL DEFAULT 'general',
            current_concept TEXT NOT NULL DEFAULT 'None',
            decomposition TEXT NOT NULL DEFAULT '[]',
            last_locked TEXT NOT NULL DEFAULT 'None',
            run_number INTEGER NOT NULL DEFAULT 1,
            version INTEGER NOT NULL DEFAULT 1,
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS state_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            assistant_message_id INTEGER NOT NULL UNIQUE,
            prior_state_hash TEXT NOT NULL,
            proposed_state TEXT NOT NULL,
            applied INTEGER NOT NULL DEFAULT 0,
            rejection_reason TEXT,
            parser_mode TEXT NOT NULL,
            prompt_version TEXT,
            parser_version TEXT,
            topics_schema_version TEXT,
            mastery_schema_version TEXT,
            timestamp TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS parser_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mode TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS concept_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'general',
            concept_number INTEGER NOT NULL,
            concept_name TEXT NOT NULL,
            locked INTEGER NOT NULL DEFAULT 0,
            anchors_delivered TEXT NOT NULL DEFAULT '[]',
            attempts INTEGER NOT NULL DEFAULT 0,
            errors_hit TEXT NOT NULL DEFAULT '[]',
            first_seen_at TEXT,
            locked_at TEXT,
            UNIQUE(topic, concept_name)
        );

        CREATE TABLE IF NOT EXISTS learner_profile (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            total_concepts_locked INTEGER NOT NULL DEFAULT 0,
            total_errors INTEGER NOT NULL DEFAULT 0,
            avg_attempts_to_lock REAL NOT NULL DEFAULT 0,
            common_error_types TEXT NOT NULL DEFAULT '{}',
            slow_topics TEXT NOT NULL DEFAULT '[]',
            fast_topics TEXT NOT NULL DEFAULT '[]',
            struggle_anchors TEXT NOT NULL DEFAULT '[]',
            preferred_depth TEXT NOT NULL DEFAULT 'standard',
            notes TEXT NOT NULL DEFAULT '[]',
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS learner_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            event_type TEXT NOT NULL,
            topic TEXT,
            concept TEXT,
            sentiment TEXT,
            details TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS learning_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_number INTEGER NOT NULL,
            started_at TEXT NOT NULL DEFAULT (datetime('now')),
            ended_at TEXT,
            topic_reached TEXT NOT NULL DEFAULT 'None',
            concepts_locked_total INTEGER NOT NULL DEFAULT 0,
            concepts_first_try INTEGER NOT NULL DEFAULT 0,
            total_errors INTEGER NOT NULL DEFAULT 0,
            total_confusions INTEGER NOT NULL DEFAULT 0,
            total_breakthroughs INTEGER NOT NULL DEFAULT 0,
            notes TEXT NOT NULL DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS concept_mastery (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_number INTEGER NOT NULL,
            topic TEXT NOT NULL,
            concept_name TEXT NOT NULL,
            attempts INTEGER NOT NULL DEFAULT 0,
            errors INTEGER NOT NULL DEFAULT 0,
            confusions INTEGER NOT NULL DEFAULT 0,
            confidence_score INTEGER NOT NULL DEFAULT 0,
            mastery_level TEXT NOT NULL DEFAULT 'unseen',
            locked_at TEXT,
            UNIQUE(run_number, topic, concept_name)
        );

        CREATE TABLE IF NOT EXISTS session_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            topic_start TEXT,
            topic_end TEXT,
            concepts_covered TEXT NOT NULL DEFAULT '[]',
            concepts_locked TEXT NOT NULL DEFAULT '[]',
            concepts_struggled TEXT NOT NULL DEFAULT '[]',
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
            topics_affected TEXT NOT NULL DEFAULT '[]',
            concepts_affected TEXT NOT NULL DEFAULT '[]',
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
            confidence REAL NOT NULL DEFAULT 0.8,
            last_updated TEXT NOT NULL DEFAULT (datetime('now')),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(category, content)
        );
    """)

    conn.execute("INSERT OR IGNORE INTO system_state (id) VALUES (1)")
    conn.execute("INSERT OR IGNORE INTO learner_profile (id) VALUES (1)")

    # Migrate: standardize category "None" → "general"
    conn.execute("UPDATE system_state SET category = 'general' WHERE category = 'None'")
    conn.execute("UPDATE concept_progress SET category = 'general' WHERE category = 'None'")

    existing = conn.execute("SELECT COUNT(*) as c FROM learning_runs").fetchone()["c"]
    if existing == 0:
        conn.execute("INSERT INTO learning_runs (run_number) VALUES (1)")

    # Migrate existing DBs: add version to system_state, status/prompt_hash to conversations if missing
    try:
        conn.execute("ALTER TABLE system_state ADD COLUMN version INTEGER NOT NULL DEFAULT 1")
    except sqlite3.OperationalError:
        pass  # column already exists
    try:
        conn.execute("ALTER TABLE conversations ADD COLUMN status TEXT DEFAULT 'complete'")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("ALTER TABLE conversations ADD COLUMN prompt_hash TEXT")
    except sqlite3.OperationalError:
        pass
    for col in ("parser_version", "topics_schema_version", "mastery_schema_version"):
        try:
            conn.execute(f"ALTER TABLE state_events ADD COLUMN {col} TEXT")
        except sqlite3.OperationalError:
            pass
    try:
        conn.execute("ALTER TABLE learner_identity ADD COLUMN confidence REAL NOT NULL DEFAULT 0.8")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("ALTER TABLE learner_identity ADD COLUMN last_updated TEXT NOT NULL DEFAULT (datetime('now'))")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()


# --- Sessions ---

def create_session():
    conn = get_conn()
    state = get_system_state(conn)
    cur = conn.execute(
        "INSERT INTO sessions (topic_at_start) VALUES (?)",
        (state["topic"],)
    )
    session_id = cur.lastrowid
    conn.commit()
    conn.close()
    return session_id


def close_session(session_id):
    conn = get_conn()
    state = get_system_state(conn)
    conn.execute(
        "UPDATE sessions SET ended_at = datetime('now'), topic_at_end = ? WHERE id = ?",
        (state["topic"], session_id)
    )
    conn.commit()
    conn.close()


# --- Conversations ---

def save_message(session_id, role, content, topic=None, concept=None, status=None, prompt_hash=None):
    """Save a message. Returns the inserted row id (for use as assistant_message_id)."""
    conn = get_conn()
    if status is not None or prompt_hash is not None:
        # status/prompt_hash provided (e.g. for assistant message)
        status = status if status is not None else "complete"
        cur = conn.execute(
            "INSERT INTO conversations (session_id, role, content, topic, concept, status, prompt_hash) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (session_id, role, content, topic, concept, status, prompt_hash),
        )
    else:
        cur = conn.execute(
            "INSERT INTO conversations (session_id, role, content, topic, concept) VALUES (?, ?, ?, ?, ?)",
            (session_id, role, content, topic, concept),
        )
    msg_id = cur.lastrowid
    conn.commit()
    conn.close()
    return msg_id


def set_message_status(message_id, status):
    """Set status of a conversation row (e.g. 'pending' -> 'complete' or 'failed')."""
    conn = get_conn()
    conn.execute("UPDATE conversations SET status = ? WHERE id = ?", (status, message_id))
    conn.commit()
    conn.close()


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


# --- State Events (append-only log for transition engine) ---

def insert_state_event(conn, assistant_message_id, prior_state_hash, proposed_state, parser_mode,
                       prompt_version=None, parser_version=None, topics_schema_version=None, mastery_schema_version=None):
    """Insert a state_events row. Caller must use same conn for transaction. Returns event_id."""
    cur = conn.execute(
        """INSERT INTO state_events (assistant_message_id, prior_state_hash, proposed_state, applied, parser_mode,
           prompt_version, parser_version, topics_schema_version, mastery_schema_version)
           VALUES (?, ?, ?, 0, ?, ?, ?, ?, ?)""",
        (assistant_message_id, prior_state_hash, proposed_state, parser_mode, prompt_version,
         parser_version, topics_schema_version, mastery_schema_version),
    )
    return cur.lastrowid


def log_parser_metric(mode):
    """Log parser outcome for metrics: 'json_success', 'regex_fallback', or 'failed'."""
    conn = get_conn()
    conn.execute("INSERT INTO parser_metrics (mode) VALUES (?)", (mode,))
    conn.commit()
    conn.close()


def update_state_event_result(conn, event_id, applied, rejection_reason=None):
    """Set applied=1 or applied=0 with optional rejection_reason. Caller uses same conn."""
    conn.execute(
        "UPDATE state_events SET applied = ?, rejection_reason = ? WHERE event_id = ?",
        (1 if applied else 0, rejection_reason, event_id),
    )


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
    """Update system_state. If conn is provided, does not commit or close (for use in transaction)."""
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


def update_system_state_with_version(conn, expected_version, **kwargs):
    """
    Update system_state and increment version in one atomic step. Used only by transition engine.
    Returns True if version matched and one row was updated, False otherwise (caller should rollback).
    """
    if not conn:
        return False
    kwargs["updated_at"] = datetime.now().isoformat()
    sets = ", ".join(f"{k} = ?" for k in kwargs) + ", version = version + 1"
    vals = list(kwargs.values()) + [expected_version]
    cur = conn.execute(
        f"UPDATE system_state SET {sets} WHERE id = 1 AND version = ?",
        vals,
    )
    return cur.rowcount == 1


# --- Concept Progress ---

def get_topic_concepts(topic, category=None, conn=None):
    close = conn is None
    if close:
        conn = get_conn()
    if category and category not in ("None", "general"):
        rows = conn.execute(
            "SELECT * FROM concept_progress WHERE topic = ? AND category = ? ORDER BY concept_number",
            (topic, category)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM concept_progress WHERE topic = ? ORDER BY concept_number",
            (topic,)
        ).fetchall()
    if close:
        conn.close()
    return [dict(r) for r in rows]


def upsert_concept(topic, concept_number, concept_name, category="general", conn=None):
    close = conn is None
    if close:
        conn = get_conn()
    conn.execute("""
        INSERT INTO concept_progress (topic, category, concept_number, concept_name, first_seen_at)
        VALUES (?, ?, ?, ?, datetime('now'))
        ON CONFLICT(topic, concept_name) DO NOTHING
    """, (topic, category, concept_number, concept_name))
    if close:
        conn.commit()
        conn.close()


def lock_concept(topic, concept_name, anchors=None, conn=None):
    close = conn is None
    if close:
        conn = get_conn()
    conn.execute("""
        UPDATE concept_progress
        SET locked = 1, locked_at = datetime('now'), anchors_delivered = ?
        WHERE topic = ? AND concept_name = ?
    """, (json.dumps(anchors or []), topic, concept_name))
    if close:
        conn.commit()
        conn.close()


def increment_concept_attempts(topic, concept_name):
    conn = get_conn()
    conn.execute("""
        UPDATE concept_progress SET attempts = attempts + 1
        WHERE topic = ? AND concept_name = ?
    """, (topic, concept_name))
    conn.commit()
    conn.close()


def log_concept_error(topic, concept_name, error_type):
    conn = get_conn()
    row = conn.execute(
        "SELECT errors_hit FROM concept_progress WHERE topic = ? AND concept_name = ?",
        (topic, concept_name)
    ).fetchone()
    if row:
        errors = json.loads(row["errors_hit"])
        errors.append({"type": error_type, "at": datetime.now().isoformat()})
        conn.execute(
            "UPDATE concept_progress SET errors_hit = ? WHERE topic = ? AND concept_name = ?",
            (json.dumps(errors), topic, concept_name)
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

def log_event(session_id, event_type, topic=None, concept=None, details=None, sentiment=None):
    conn = get_conn()
    conn.execute(
        "INSERT INTO learner_events (session_id, event_type, topic, concept, sentiment, details) VALUES (?, ?, ?, ?, ?, ?)",
        (session_id, event_type, topic, concept, sentiment, json.dumps(details or {}))
    )
    conn.commit()
    conn.close()


def get_events(event_type=None, topic=None, limit=100):
    conn = get_conn()
    query = "SELECT * FROM learner_events WHERE 1=1"
    params = []
    if event_type:
        query += " AND event_type = ?"
        params.append(event_type)
    if topic:
        query += " AND topic = ?"
        params.append(topic)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- Learning Runs ---

def get_current_run(conn=None):
    close = conn is None
    if close:
        conn = get_conn()
    row = conn.execute("SELECT * FROM learning_runs ORDER BY run_number DESC LIMIT 1").fetchone()
    if close:
        conn.close()
    return dict(row) if row else None


def get_all_runs():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM learning_runs ORDER BY run_number").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def start_new_run():
    conn = get_conn()
    current = conn.execute("SELECT MAX(run_number) as m FROM learning_runs").fetchone()["m"] or 0
    new_num = current + 1
    conn.execute("INSERT INTO learning_runs (run_number) VALUES (?)", (new_num,))
    conn.commit()
    conn.close()
    return new_num


def update_run(run_number, **kwargs):
    if not kwargs:
        return
    conn = get_conn()
    sets = ", ".join(f"{k} = ?" for k in kwargs)
    vals = list(kwargs.values()) + [run_number]
    conn.execute(f"UPDATE learning_runs SET {sets} WHERE run_number = ?", vals)
    conn.commit()
    conn.close()


# --- Concept Mastery ---

def record_mastery(run_number, topic, concept_name, attempts=0, errors=0, confusions=0, conn=None):
    close = conn is None
    if close:
        conn = get_conn()
    conn.execute("""
        INSERT INTO concept_mastery (run_number, topic, concept_name, attempts, errors, confusions, confidence_score, mastery_level)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'unseen')
        ON CONFLICT(run_number, topic, concept_name) DO UPDATE SET
            attempts = attempts + ?,
            errors = errors + ?,
            confusions = confusions + ?
    """, (run_number, topic, concept_name, attempts, errors, confusions,
          max(0, 3 - attempts - errors - confusions),
          attempts, errors, confusions))

    # Recompute level from accumulated totals
    row = conn.execute(
        "SELECT attempts, errors, confusions FROM concept_mastery WHERE run_number = ? AND topic = ? AND concept_name = ?",
        (run_number, topic, concept_name)
    ).fetchone()
    total_attempts = row["attempts"]
    total_errors = row["errors"]
    total_confusions = row["confusions"]
    score = max(0, 3 - total_attempts - total_errors - total_confusions)

    if total_attempts == 0:
        level = "unseen"
    elif total_attempts <= 1 and total_errors == 0:
        level = "confident"
    elif total_attempts <= 2:
        level = "familiar"
    else:
        level = "fragile"

    conn.execute("""
        UPDATE concept_mastery SET confidence_score = ?, mastery_level = ?
        WHERE run_number = ? AND topic = ? AND concept_name = ?
    """, (score, level, run_number, topic, concept_name))
    if close:
        conn.commit()
        conn.close()


def promote_mastery(run_number, topic, concept_name, conn=None):
    """Called when a concept is locked — compute final mastery from accumulated data (not from model)."""
    close = conn is None
    if close:
        conn = get_conn()
    row = conn.execute(
        "SELECT * FROM concept_mastery WHERE run_number = ? AND topic = ? AND concept_name = ?",
        (run_number, topic, concept_name)
    ).fetchone()

    if not row:
        record_mastery(run_number, topic, concept_name, attempts=1, conn=conn)
        row = conn.execute(
            "SELECT * FROM concept_mastery WHERE run_number = ? AND topic = ? AND concept_name = ?",
            (run_number, topic, concept_name)
        ).fetchone()

    prev = conn.execute("""
        SELECT mastery_level, confidence_score FROM concept_mastery
        WHERE topic = ? AND concept_name = ? AND run_number < ?
        ORDER BY run_number DESC LIMIT 1
    """, (topic, concept_name, run_number)).fetchone()

    attempts = row["attempts"]
    errors = row["errors"]

    if prev:
        prev_level = prev["mastery_level"]
        if attempts <= 1 and errors == 0 and prev_level in ("fragile", "familiar"):
            level, score = "confident", 5
        elif attempts <= 1 and errors == 0 and prev_level == "confident":
            level, score = "hardened", 8
        elif attempts <= 1 and errors == 0:
            level, score = "hardened", 10
        else:
            score = max(0, 3 - attempts - errors)
            level = "familiar" if score >= 1 else "fragile"
    else:
        if attempts <= 1 and errors == 0:
            level, score = "confident", 3
        elif attempts <= 2:
            level, score = "familiar", 1
        else:
            level, score = "fragile", 0

    conn.execute("""
        UPDATE concept_mastery SET confidence_score = ?, mastery_level = ?, locked_at = datetime('now')
        WHERE run_number = ? AND topic = ? AND concept_name = ?
    """, (score, level, run_number, topic, concept_name))
    if close:
        conn.commit()
        conn.close()
    return level


def get_mastery_summary(run_number=None):
    conn = get_conn()
    if run_number:
        rows = conn.execute(
            "SELECT * FROM concept_mastery WHERE run_number = ? ORDER BY topic, concept_name",
            (run_number,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM concept_mastery ORDER BY run_number DESC, topic, concept_name"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_fragile_concepts():
    """Get concepts still fragile in the latest run."""
    conn = get_conn()
    current_run = conn.execute("SELECT MAX(run_number) as m FROM learning_runs").fetchone()["m"] or 1
    rows = conn.execute("""
        SELECT topic, concept_name, attempts, errors, confusions, mastery_level
        FROM concept_mastery
        WHERE run_number = ? AND mastery_level IN ('fragile', 'familiar')
        ORDER BY confidence_score ASC
    """, (current_run,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- Struggle Patterns ---

def upsert_struggle(pattern_type, category, description, topic=None, concept=None, adaptation_rule=""):
    conn = get_conn()
    existing = conn.execute(
        "SELECT * FROM struggle_patterns WHERE pattern_type = ? AND category = ?",
        (pattern_type, category)
    ).fetchone()

    if existing:
        topics = json.loads(existing["topics_affected"])
        concepts = json.loads(existing["concepts_affected"])
        if topic and topic not in topics:
            topics.append(topic)
        if concept and concept not in concepts:
            concepts.append(concept)
        conn.execute("""
            UPDATE struggle_patterns
            SET frequency = frequency + 1, last_seen_at = datetime('now'),
                topics_affected = ?, concepts_affected = ?, adaptation_rule = ?
            WHERE pattern_type = ? AND category = ?
        """, (json.dumps(topics), json.dumps(concepts),
              adaptation_rule or existing["adaptation_rule"],
              pattern_type, category))
    else:
        conn.execute("""
            INSERT INTO struggle_patterns (pattern_type, category, description, topics_affected, concepts_affected, adaptation_rule)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (pattern_type, category, description,
              json.dumps([topic] if topic else []),
              json.dumps([concept] if concept else []),
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

def save_learner_identity(category, content, source_snippet="", session_id=None, confidence=0.8):
    conn = get_conn()
    conn.execute("""
        INSERT INTO learner_identity (category, content, source_snippet, session_id, confidence, last_updated)
        VALUES (?, ?, ?, ?, ?, datetime('now'))
        ON CONFLICT(category, content) DO UPDATE SET
            source_snippet = ?, session_id = COALESCE(?, session_id),
            confidence = ?, last_updated = datetime('now')
    """, (category, content, source_snippet, session_id, confidence,
          source_snippet, session_id, confidence))
    conn.commit()
    conn.close()


def get_learner_identity():
    conn = get_conn()
    rows = conn.execute(
        "SELECT category, content, source_snippet, confidence, last_updated FROM learner_identity ORDER BY created_at"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- Session Summaries ---

def generate_session_summary(session_id):
    conn = get_conn()
    session = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if not session:
        conn.close()
        return

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

    concepts_locked = conn.execute(
        "SELECT topic, concept_name FROM concept_progress WHERE locked_at >= ? AND locked_at <= COALESCE(?, datetime('now'))",
        (session["started_at"], session["ended_at"])
    ).fetchall()
    locked_list = [f"{r['concept_name']}({r['topic']})" for r in concepts_locked]

    struggled = conn.execute("""
        SELECT DISTINCT concept FROM learner_events
        WHERE session_id = ? AND event_type IN ('error', 'frustration', 'confusion') AND concept IS NOT NULL
    """, (session_id,)).fetchall()
    struggled_list = [r["concept"] for r in struggled]

    avg_time = compute_avg_response_time(session_id, conn)

    parts = [f"Session {session_id}: {session['topic_at_start'] or '?'} → {session['topic_at_end'] or '?'}"]
    if locked_list:
        parts.append(f"Locked: {', '.join(locked_list)}")
    if struggled_list:
        parts.append(f"Struggled with: {', '.join(struggled_list)}")
    parts.append(f"Errors: {errors} | Confusions: {confusions} | Breakthroughs: {breakthroughs}")
    if avg_time:
        parts.append(f"Avg response time: {avg_time:.0f}s")

    conn.execute("""
        INSERT INTO session_summaries
        (session_id, topic_start, topic_end, concepts_locked, concepts_struggled,
         errors_count, confusions_count, breakthroughs_count, avg_response_seconds, summary_text)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session_id,
        session["topic_at_start"],
        session["topic_at_end"],
        json.dumps(locked_list),
        json.dumps(struggled_list),
        errors, confusions, breakthroughs,
        avg_time,
        ". ".join(parts),
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
    close = conn is None
    if close:
        conn = get_conn()

    rows = conn.execute("""
        SELECT role, created_at FROM conversations
        WHERE session_id = ? ORDER BY id
    """, (session_id,)).fetchall()

    if len(rows) < 2:
        if close:
            conn.close()
        return None

    if close:
        conn.close()

    gaps = []
    for i in range(len(rows) - 1):
        if rows[i]["role"] == "assistant" and rows[i + 1]["role"] == "user":
            try:
                t1 = datetime.fromisoformat(rows[i]["created_at"])
                t2 = datetime.fromisoformat(rows[i + 1]["created_at"])
                gap = (t2 - t1).total_seconds()
                if 1 < gap < 3600:
                    gaps.append(gap)
            except (ValueError, TypeError):
                pass

    return sum(gaps) / len(gaps) if gaps else None


# --- Spaced Repetition ---

def get_concepts_due_for_review(days_threshold=7):
    conn = get_conn()
    rows = conn.execute("""
        SELECT topic, concept_name, locked_at,
               ROUND(julianday('now') - julianday(locked_at)) as days_since
        FROM concept_progress
        WHERE locked = 1
          AND julianday('now') - julianday(locked_at) >= ?
        ORDER BY locked_at ASC
    """, (days_threshold,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_concept_reviewed(topic, concept_name):
    conn = get_conn()
    conn.execute(
        "UPDATE concept_progress SET locked_at = datetime('now') WHERE topic = ? AND concept_name = ?",
        (topic, concept_name)
    )
    conn.commit()
    conn.close()


# --- Resume Block ---

def build_resume_block(topic=None, category=None):
    """Build the compact tracker block for resuming a session."""
    state = get_system_state()
    target_topic = topic or state.get("topic", "None")
    target_category = category or state.get("category", "None")

    run = get_current_run()
    run_number = run["run_number"] if run else 1

    concepts = get_topic_concepts(target_topic, target_category)
    locked = [c["concept_name"] for c in concepts if c["locked"]]
    remaining = [c["concept_name"] for c in concepts if not c["locked"]]

    category_display = "All categories" if target_category in ("general", "None") else target_category
    lines = [
        "── RESUMING SESSION ──────────────────",
        f"📚 Topic: {target_topic}",
        f"📂 Category: {category_display}",
        f"🔁 Run: {run_number}",
    ]

    for name in locked:
        lines.append(f"✅ {name} locked")

    if remaining:
        lines.append(f"📋 Remaining: {', '.join(remaining)}")
        lines.append(f"➡️ Next: {remaining[0]}")
    elif locked:
        lines.append("✅ All concepts locked for this topic/category")
    elif target_topic and target_topic != "None":
        lines.append("📋 No concepts tracked yet — ready to decompose and begin")
    else:
        lines.append("📋 No topic selected — choose a topic from the sidebar to begin")

    lines.append("──────────────────────────────────────")
    return "\n".join(lines)


# --- New Run ---

def reset_for_new_run():
    """Start a new learning run: increment run, reset system state."""
    new_run = start_new_run()
    update_system_state(
        topic="None",
        category="general",
        current_concept="None",
        decomposition="[]",
        last_locked="None",
        run_number=new_run,
    )
    return new_run
