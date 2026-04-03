from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "iartes.db"


def _ensure_dir() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_connection():
    _ensure_dir()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Cria as tabelas se não existirem."""
    with get_connection() as conn:
        conn.executescript(_SCHEMA)


_SCHEMA = """
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
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    provider        TEXT NOT NULL,
    normalized_id   TEXT NOT NULL,
    step_type       TEXT NOT NULL,
    is_destructive  INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(provider, normalized_id)
);

CREATE INDEX IF NOT EXISTS idx_runs_suite ON optimization_runs(suite_id);
CREATE INDEX IF NOT EXISTS idx_norm_cache ON normalization_cache(provider, step_hash);
CREATE INDEX IF NOT EXISTS idx_class_cache ON classification_cache(provider, normalized_id);
"""


def save_suite(name: str, test_data: list[dict]) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO suites (name, test_data) VALUES (?, ?)",
            (name, json.dumps(test_data, ensure_ascii=False)),
        )
        return cursor.lastrowid


def get_suite(suite_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM suites WHERE id = ?", (suite_id,)).fetchone()
        if row is None:
            return None
        return {
            "id": row["id"],
            "name": row["name"],
            "test_data": json.loads(row["test_data"]),
            "created_at": row["created_at"],
        }


def list_suites() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT id, name, created_at FROM suites ORDER BY id DESC").fetchall()
        return [dict(row) for row in rows]


def save_optimization_run(
    suite_id: int,
    provider: str,
    result_json: dict,
    metrics_json: dict | None = None,
    elapsed_ms: float | None = None,
) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO optimization_runs (suite_id, provider, result_json, metrics_json, elapsed_ms) VALUES (?, ?, ?, ?, ?)",
            (
                suite_id,
                provider,
                json.dumps(result_json, ensure_ascii=False),
                json.dumps(metrics_json, ensure_ascii=False) if metrics_json else None,
                elapsed_ms,
            ),
        )
        return cursor.lastrowid


def get_runs_for_suite(suite_id: int) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM optimization_runs WHERE suite_id = ? ORDER BY id DESC",
            (suite_id,),
        ).fetchall()
        results = []
        for row in rows:
            results.append({
                "id": row["id"],
                "suite_id": row["suite_id"],
                "provider": row["provider"],
                "result_json": json.loads(row["result_json"]),
                "metrics_json": json.loads(row["metrics_json"]) if row["metrics_json"] else None,
                "elapsed_ms": row["elapsed_ms"],
                "created_at": row["created_at"],
            })
        return results


def get_history() -> list[dict]:
    """Retorna histórico de execuções com informações da suite."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT r.id, r.suite_id, s.name as suite_name, r.provider,
                   r.elapsed_ms, r.created_at,
                   json_extract(r.metrics_json, '$.reduction_percent') as reduction_percent
            FROM optimization_runs r
            JOIN suites s ON s.id = r.suite_id
            ORDER BY r.id DESC
            LIMIT 100
        """).fetchall()
        return [dict(row) for row in rows]
