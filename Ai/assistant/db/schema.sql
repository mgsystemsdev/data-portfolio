-- Conversations with rolling summary
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    summary TEXT NOT NULL DEFAULT '',
    started_at TEXT NOT NULL,
    last_active_at TEXT NOT NULL
);

-- Single canonical message store
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id);

-- Events (append-only)
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    payload TEXT NOT NULL,
    source_message_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Projection: tasks
CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'todo',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Projection: goals
CREATE TABLE IF NOT EXISTS goals (
    goal_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Projection: time logs
CREATE TABLE IF NOT EXISTS time_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT,
    goal_id TEXT,
    duration_minutes REAL NOT NULL,
    logged_at TEXT NOT NULL
);
