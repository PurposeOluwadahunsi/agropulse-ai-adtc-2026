"""
core/logbook.py

Farm logbook — all database read/write operations for AgroPulse AI.

Every query+response pair is persisted here automatically.
No other module writes to the database directly.

Usage:
    from core.logbook import Logbook

    lb = Logbook()
    session_id = lb.start_session()
    lb.write_entry(session_id, entry_data)
    recent = lb.get_recent(10)
    lb.end_session(session_id)
"""

from __future__ import annotations

import json
import logging
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from db.migrations import get_connection, run_migrations

logger = logging.getLogger(__name__)


@dataclass
class LogEntry:
    """
    Structured representation of one farm_log row.
    Populate this from the pipeline result then pass to Logbook.write_entry().
    """
    session_id:       str
    user_input:       str
    ai_response:      str         = ""
    triage_matched:   bool        = False
    disease_hit:      str | None  = None
    disease_id:       str | None  = None
    severity:         str | None  = None
    triage_score:     float       = 0.0
    triage_conf:      str         = "none"
    matched_symptoms: list[str]   = field(default_factory=list)
    vet_needed:       bool        = False
    rag_sources:      list[str]   = field(default_factory=list)
    response_ms:      int | None  = None


class Logbook:
    """
    Thin data-access layer over the farm_log and sessions tables.

    Instantiate once per application run.
    Automatically ensures migrations are applied on first use.
    """

    def __init__(self) -> None:
        run_migrations()
        logger.info("Logbook ready.")

    # ─────────────────────────────────────────────
    # Session management
    # ─────────────────────────────────────────────

    def start_session(self) -> str:
        """
        Insert a new session row and return its UUID.

        Returns:
            str: The new session ID.
        """
        session_id = str(uuid.uuid4())
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = get_connection()
        with conn:
            conn.execute(
                "INSERT INTO sessions (id, started_at) VALUES (?, ?);",
                (session_id, now),
            )
        conn.close()

        logger.info(f"Session started: {session_id}")
        return session_id

    def end_session(self, session_id: str) -> None:
        """
        Mark a session as ended and record its final timestamp.

        Args:
            session_id: The session UUID returned by start_session().
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_connection()
        with conn:
            conn.execute(
                "UPDATE sessions SET ended_at = ?, last_active = ? WHERE id = ?;",
                (now, now, session_id),
            )
        conn.close()
        logger.info(f"Session ended: {session_id}")

    def increment_session_query_count(self, session_id: str) -> None:
        """Increment the query counter for a session by 1."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_connection()
        with conn:
            conn.execute(
                """
                UPDATE sessions
                SET query_count = query_count + 1,
                    last_active = ?
                WHERE id = ?;
                """,
                (now, session_id),
            )
        conn.close()

    # ─────────────────────────────────────────────
    # Log writes
    # ─────────────────────────────────────────────

    def write_entry(self, entry: LogEntry) -> int:
        """
        Persist one pipeline result to farm_log.

        Args:
            entry: Populated LogEntry dataclass.

        Returns:
            int: The new row's ROWID.

        Raises:
            ValueError: If session_id or user_input are empty.
            RuntimeError: If the INSERT fails.
        """
        if not entry.session_id:
            raise ValueError("LogEntry.session_id cannot be empty.")
        if not entry.user_input:
            raise ValueError("LogEntry.user_input cannot be empty.")

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            conn = get_connection()
            with conn:
                cursor = conn.execute(
                    """
                    INSERT INTO farm_log (
                        session_id, timestamp,
                        user_input, ai_response,
                        triage_matched, disease_hit, disease_id,
                        severity, triage_score, triage_conf,
                        matched_symptoms, vet_needed,
                        rag_sources, response_ms
                    ) VALUES (
                        ?, ?,
                        ?, ?,
                        ?, ?, ?,
                        ?, ?, ?,
                        ?, ?,
                        ?, ?
                    );
                    """,
                    (
                        entry.session_id,
                        now,
                        entry.user_input,
                        entry.ai_response,
                        int(entry.triage_matched),
                        entry.disease_hit,
                        entry.disease_id,
                        entry.severity,
                        entry.triage_score,
                        entry.triage_conf,
                        json.dumps(entry.matched_symptoms),
                        int(entry.vet_needed),
                        json.dumps(entry.rag_sources),
                        entry.response_ms,
                    ),
                )
                row_id = cursor.lastrowid

            conn.close()
            self.increment_session_query_count(entry.session_id)
            logger.info(f"Log entry written: row_id={row_id}, disease={entry.disease_hit}")
            return row_id

        except Exception as exc:
            raise RuntimeError(f"Failed to write log entry: {exc}") from exc

    # ─────────────────────────────────────────────
    # Log reads
    # ─────────────────────────────────────────────

    def get_recent(self, n: int = 10) -> list[dict[str, Any]]:
        """
        Return the n most recent farm_log entries, newest first.

        Args:
            n: Number of rows to return (default 10).

        Returns:
            List of dicts with all farm_log columns.
            matched_symptoms and rag_sources are decoded from JSON.
        """
        conn = get_connection()
        rows = conn.execute(
            """
            SELECT * FROM farm_log
            ORDER BY timestamp DESC
            LIMIT ?;
            """,
            (n,),
        ).fetchall()
        conn.close()
        return [self._deserialise_row(row) for row in rows]

    def get_by_disease(self, disease_name: str) -> list[dict[str, Any]]:
        """
        Return all log entries for a specific disease, newest first.

        Args:
            disease_name: Exact disease name string (e.g. "Newcastle Disease").
        """
        conn = get_connection()
        rows = conn.execute(
            """
            SELECT * FROM farm_log
            WHERE disease_hit = ?
            ORDER BY timestamp DESC;
            """,
            (disease_name,),
        ).fetchall()
        conn.close()
        return [self._deserialise_row(row) for row in rows]

    def get_session_summary(self, session_id: str) -> dict[str, Any] | None:
        """
        Return metadata for a single session.

        Args:
            session_id: Session UUID.

        Returns:
            Dict with session columns, or None if not found.
        """
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM sessions WHERE id = ?;",
            (session_id,),
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    def get_stats(self) -> dict[str, Any]:
        """
        Return aggregate statistics across all log entries.

        Returns:
            Dict with total queries, disease breakdown, vet referral count.
        """
        conn = get_connection()

        total = conn.execute("SELECT COUNT(*) FROM farm_log;").fetchone()[0]
        triage_hits = conn.execute(
            "SELECT COUNT(*) FROM farm_log WHERE triage_matched = 1;"
        ).fetchone()[0]
        vet_referrals = conn.execute(
            "SELECT COUNT(*) FROM farm_log WHERE vet_needed = 1;"
        ).fetchone()[0]

        disease_counts = conn.execute(
            """
            SELECT disease_hit, COUNT(*) as count
            FROM farm_log
            WHERE disease_hit IS NOT NULL
            GROUP BY disease_hit
            ORDER BY count DESC;
            """
        ).fetchall()

        conn.close()

        return {
            "total_queries": total,
            "triage_hits": triage_hits,
            "vet_referrals": vet_referrals,
            "disease_breakdown": {
                row["disease_hit"]: row["count"]
                for row in disease_counts
            },
        }

    # ─────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────

    @staticmethod
    def _deserialise_row(row: Any) -> dict[str, Any]:
        """Convert a sqlite3.Row to a plain dict, decoding JSON fields."""
        d = dict(row)
        for json_field in ("matched_symptoms", "rag_sources"):
            if d.get(json_field):
                try:
                    d[json_field] = json.loads(d[json_field])
                except (json.JSONDecodeError, TypeError):
                    d[json_field] = []
            else:
                d[json_field] = []
        return d


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    print("=" * 55)
    print("AgroPulse AI — Logbook Test")
    print("=" * 55)

    lb = Logbook()

    # Test 1: Start session
    print("\n[1/5] Starting session...")
    sid = lb.start_session()
    print(f"      Session ID: {sid}")
    assert len(sid) == 36  # UUID4 format

    # Test 2: Write a full entry
    print("\n[2/5] Writing log entry...")
    entry = LogEntry(
        session_id=sid,
        user_input="My chickens are gasping and have twisted necks",
        ai_response="This looks like Newcastle Disease. Isolate affected birds immediately.",
        triage_matched=True,
        disease_hit="Newcastle Disease",
        disease_id="ND001",
        severity="critical",
        triage_score=7.0,
        triage_conf="high",
        matched_symptoms=["gasping", "twisted neck"],
        vet_needed=True,
        rag_sources=["FAO Manual No.4", "NVRI Nigeria"],
        response_ms=4200,
    )
    row_id = lb.write_entry(entry)
    print(f"      Written row ID: {row_id}")
    assert row_id > 0

    # Test 3: Write a second entry (no triage match)
    entry2 = LogEntry(
        session_id=sid,
        user_input="How often should I vaccinate my flock?",
        ai_response="Vaccinate with La Sota at day 1, day 14, then every 3 months.",
        triage_matched=False,
        rag_sources=["FAO Manual No.4"],
        response_ms=3100,
    )
    lb.write_entry(entry2)

    # Test 4: Read recent entries
    print("\n[3/5] Reading recent entries...")
    recent = lb.get_recent(5)
    print(f"      Retrieved {len(recent)} entries.")
    assert len(recent) >= 2
    print(f"      Latest entry disease: {recent[0].get('disease_hit')}")
    assert isinstance(recent[0]["matched_symptoms"], list)

    # Test 5: Stats
    print("\n[4/5] Checking stats...")
    stats = lb.get_stats()
    print(f"      Total queries   : {stats['total_queries']}")
    print(f"      Triage hits     : {stats['triage_hits']}")
    print(f"      Vet referrals   : {stats['vet_referrals']}")
    print(f"      Disease breakdown: {stats['disease_breakdown']}")
    assert stats["total_queries"] >= 2

    # Test 6: End session
    print("\n[5/5] Ending session...")
    lb.end_session(sid)
    summary = lb.get_session_summary(sid)
    print(f"      Session query count: {summary['query_count']}")
    assert summary["ended_at"] is not None

    print("\n" + "=" * 55)
    print("ALL TESTS PASSED — logbook.py is ready.")
    print("=" * 55)
    sys.exit(0)