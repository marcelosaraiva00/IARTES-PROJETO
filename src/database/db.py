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


# ---------------------------------------------------------------------------
# Knowledge Base -- normalização e classificação persistentes
# ---------------------------------------------------------------------------

def _step_hash(text: str) -> str:
    import hashlib
    return hashlib.md5(text.strip().lower().encode()).hexdigest()


def kb_save_normalization(
    provider: str,
    original_text: str,
    normalized_id: str,
    normalized_text: str,
) -> None:
    h = _step_hash(original_text)
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO normalization_cache
               (provider, step_hash, original_text, normalized_id, normalized_text)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(provider, step_hash) DO UPDATE SET
                 normalized_id = excluded.normalized_id,
                 normalized_text = excluded.normalized_text,
                 created_at = datetime('now')""",
            (provider, h, original_text, normalized_id, normalized_text),
        )


def kb_get_normalization(original_text: str, provider: str | None = None) -> dict | None:
    """Busca normalização na KB. Se provider=None, retorna a mais recente de qualquer provider."""
    h = _step_hash(original_text)
    with get_connection() as conn:
        if provider:
            row = conn.execute(
                "SELECT normalized_id, normalized_text, provider FROM normalization_cache WHERE step_hash = ? AND provider = ?",
                (h, provider),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT normalized_id, normalized_text, provider FROM normalization_cache WHERE step_hash = ? ORDER BY created_at DESC LIMIT 1",
                (h,),
            ).fetchone()
        if row is None:
            return None
        return {
            "normalized_id": row["normalized_id"],
            "normalized_text": row["normalized_text"],
            "source_provider": row["provider"],
        }


def kb_save_classification(
    provider: str,
    normalized_id: str,
    step_type: str,
    is_destructive: bool,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO classification_cache
               (provider, normalized_id, step_type, is_destructive)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(provider, normalized_id) DO UPDATE SET
                 step_type = excluded.step_type,
                 is_destructive = excluded.is_destructive,
                 created_at = datetime('now')""",
            (provider, normalized_id, step_type, int(is_destructive)),
        )


def kb_get_classification(normalized_id: str, provider: str | None = None) -> dict | None:
    """Busca classificação na KB. Se provider=None, retorna a mais recente."""
    with get_connection() as conn:
        if provider:
            row = conn.execute(
                "SELECT step_type, is_destructive, provider FROM classification_cache WHERE normalized_id = ? AND provider = ?",
                (normalized_id, provider),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT step_type, is_destructive, provider FROM classification_cache WHERE normalized_id = ? ORDER BY created_at DESC LIMIT 1",
                (normalized_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "step_type": row["step_type"],
            "is_destructive": bool(row["is_destructive"]),
            "source_provider": row["provider"],
        }


def kb_save_normalizations_batch(
    provider: str,
    mappings: list[tuple[str, str, str]],
) -> None:
    """Salva múltiplas normalizações de uma vez. Cada tuple: (original_text, normalized_id, normalized_text)."""
    with get_connection() as conn:
        for original_text, normalized_id, normalized_text in mappings:
            conn.execute(
                """INSERT INTO normalization_cache
                   (provider, step_hash, original_text, normalized_id, normalized_text)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(provider, step_hash) DO UPDATE SET
                     normalized_id = excluded.normalized_id,
                     normalized_text = excluded.normalized_text,
                     created_at = datetime('now')""",
                (provider, _step_hash(original_text), original_text, normalized_id, normalized_text),
            )


def kb_save_classifications_batch(
    provider: str,
    classifications: list[tuple[str, str, bool]],
) -> None:
    """Salva múltiplas classificações. Cada tuple: (normalized_id, step_type, is_destructive)."""
    with get_connection() as conn:
        for normalized_id, step_type, is_destructive in classifications:
            conn.execute(
                """INSERT INTO classification_cache
                   (provider, normalized_id, step_type, is_destructive)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(provider, normalized_id) DO UPDATE SET
                     step_type = excluded.step_type,
                     is_destructive = excluded.is_destructive,
                     created_at = datetime('now')""",
                (provider, normalized_id, step_type, int(is_destructive)),
            )


def kb_get_all_normalizations(limit: int = 500) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT provider, original_text, normalized_id, normalized_text, created_at FROM normalization_cache ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]


def kb_get_all_classifications(limit: int = 500) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT provider, normalized_id, step_type, is_destructive, created_at FROM classification_cache ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [{"provider": r["provider"], "normalized_id": r["normalized_id"],
                 "step_type": r["step_type"], "is_destructive": bool(r["is_destructive"]),
                 "created_at": r["created_at"]} for r in rows]


def kb_get_stats() -> dict:
    with get_connection() as conn:
        norm_total = conn.execute("SELECT COUNT(*) as c FROM normalization_cache").fetchone()["c"]
        class_total = conn.execute("SELECT COUNT(*) as c FROM classification_cache").fetchone()["c"]

        norm_by_provider = conn.execute(
            "SELECT provider, COUNT(*) as c FROM normalization_cache GROUP BY provider"
        ).fetchall()
        class_by_provider = conn.execute(
            "SELECT provider, COUNT(*) as c FROM classification_cache GROUP BY provider"
        ).fetchall()

        return {
            "normalizations_total": norm_total,
            "classifications_total": class_total,
            "normalizations_by_provider": {r["provider"]: r["c"] for r in norm_by_provider},
            "classifications_by_provider": {r["provider"]: r["c"] for r in class_by_provider},
        }


def kb_clear() -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM normalization_cache")
        conn.execute("DELETE FROM classification_cache")
