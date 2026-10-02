-- Esquema SQLite do protótipo IARTES (data/iartes.db)
-- Fonte: src/database/db.py — commit c0d5ed6

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS suites (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    test_data   TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS optimization_runs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    suite_id      INTEGER NOT NULL REFERENCES suites(id),
    provider      TEXT NOT NULL,
    result_json   TEXT NOT NULL,
    metrics_json  TEXT,
    elapsed_ms    REAL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS normalization_cache (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    provider        TEXT NOT NULL,
    step_hash       TEXT NOT NULL,
    original_text   TEXT NOT NULL,
    normalized_id   TEXT NOT NULL,
    normalized_text TEXT NOT NULL,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(provider, step_hash)
);

CREATE TABLE IF NOT EXISTS classification_cache (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    provider         TEXT NOT NULL,
    normalized_id    TEXT NOT NULL,
    step_type        TEXT NOT NULL,
    is_destructive   INTEGER NOT NULL DEFAULT 0,
    normalized_text  TEXT NOT NULL DEFAULT '',
    created_at       TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(provider, normalized_id)
);

CREATE INDEX IF NOT EXISTS idx_runs_suite ON optimization_runs(suite_id);
CREATE INDEX IF NOT EXISTS idx_norm_cache ON normalization_cache(provider, step_hash);
CREATE INDEX IF NOT EXISTS idx_class_cache ON classification_cache(provider, normalized_id);
