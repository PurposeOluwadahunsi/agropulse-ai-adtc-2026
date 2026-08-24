"""

Runs schema.sql idempotently on every startup.

"""
from __future__ import annotations
import logging
import sqlite3
import sys
from pathlib import Path

logger  = logging.getLogger(__name__)
DB_PATH     = Path(__file__).parent.parent / "agropulse.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def run_migrations() -> None:
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema not found: {SCHEMA_PATH}")
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    try:
        conn = get_connection()
        with conn:
            conn.executescript(sql)
        conn.close()
        logger.info("Migrations applied.")
    except sqlite3.Error as exc:
        raise RuntimeError(f"Migration failed: {exc}") from exc


def get_table_names() -> list[str]:
    conn  = get_connection()
    rows  = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;").fetchall()
    conn.close()
    return [r["name"] for r in rows]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_migrations()
    print("Tables:", get_table_names())