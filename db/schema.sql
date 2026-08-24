PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    ended_at TEXT, query_count INTEGER NOT NULL DEFAULT 0, last_active TEXT
);

CREATE TABLE IF NOT EXISTS farm_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    timestamp TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    user_input TEXT NOT NULL,
    triage_matched INTEGER NOT NULL DEFAULT 0,
    disease_hit TEXT, disease_id TEXT,
    severity TEXT CHECK(severity IN ('critical','moderate','low',NULL)),
    triage_score REAL,
    triage_conf TEXT CHECK(triage_conf IN ('high','medium','low','none',NULL)),
    matched_symptoms TEXT, vet_needed INTEGER NOT NULL DEFAULT 0,
    rag_sources TEXT, ai_response TEXT, response_ms INTEGER
);

CREATE INDEX IF NOT EXISTS idx_log_session   ON farm_log(session_id);
CREATE INDEX IF NOT EXISTS idx_log_timestamp ON farm_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_log_disease   ON farm_log(disease_hit);
CREATE INDEX IF NOT EXISTS idx_log_severity  ON farm_log(severity);

-- Sprint 9 tables
CREATE TABLE IF NOT EXISTS livestock (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bird_type TEXT NOT NULL,
    breed TEXT,
    quantity INTEGER NOT NULL DEFAULT 0,
    age_weeks INTEGER,
    pen TEXT,
    date_added TEXT NOT NULL DEFAULT (date('now')),
    supplier TEXT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS mortality (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL DEFAULT (date('now')),
    bird_type TEXT NOT NULL,
    count INTEGER NOT NULL DEFAULT 0,
    possible_cause TEXT,
    consultation_id INTEGER REFERENCES farm_log(id),
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS idx_mortality_date ON mortality(date);

CREATE TABLE IF NOT EXISTS feed_inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    feed_type TEXT NOT NULL,
    quantity_kg REAL NOT NULL DEFAULT 0,
    supplier TEXT,
    purchase_date TEXT DEFAULT (date('now')),
    daily_usage_kg REAL,
    notes TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS medication (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    quantity REAL NOT NULL DEFAULT 0,
    unit TEXT NOT NULL DEFAULT 'ml',
    expiry_date TEXT,
    purpose TEXT,
    supplier TEXT,
    notes TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS vaccination (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vaccine TEXT NOT NULL,
    bird_group TEXT,
    scheduled_date TEXT NOT NULL,
    completed_date TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','completed','missed')),
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS idx_vacc_date ON vaccination(scheduled_date);

CREATE TABLE IF NOT EXISTS egg_production (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL DEFAULT (date('now')),
    egg_count INTEGER NOT NULL DEFAULT 0,
    broken INTEGER NOT NULL DEFAULT 0,
    sold INTEGER NOT NULL DEFAULT 0,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS idx_eggs_date ON egg_production(date);