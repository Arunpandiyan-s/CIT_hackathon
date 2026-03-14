"""
SQLite database layer.

Phase 1 tables  : analyses
Phase 2 (future): classroom_patterns
Phase 3 (future): users (role-based access)
Phase 4 (future): knowledge_base
Phase 5 (future): early_warnings
"""
import sqlite3
import json
from datetime import datetime
from config import DB_PATH


def _connect():
    return sqlite3.connect(str(DB_PATH))


def init_db():
    """Create all tables. Safe to call multiple times (CREATE IF NOT EXISTS)."""
    conn = _connect()
    cur = conn.cursor()

    # ── Phase 1: Teacher analysis records ────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            input_type       TEXT    NOT NULL,
            extracted_text   TEXT,
            issue            TEXT,
            topic            TEXT,
            age_group        TEXT,
            activity_name    TEXT,
            activity_materials TEXT,
            activity_duration  TEXT,
            file_name        TEXT,
            created_at       TEXT    DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Phase 2: Regional pattern aggregation ─────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS classroom_patterns (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            region       TEXT,
            issue_type   TEXT,
            frequency    INTEGER DEFAULT 1,
            detected_at  TEXT    DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Phase 3: Role-based users ─────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT,
            role       TEXT,   -- teacher | manager | officer
            region     TEXT,
            created_at TEXT    DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Phase 4: Knowledge base ───────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            issue        TEXT,
            topic        TEXT,
            activity_json TEXT,
            usage_count  INTEGER DEFAULT 0,
            created_at   TEXT    DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Phase 5: Early warning signals ───────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS early_warnings (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            region      TEXT,
            issue_type  TEXT,
            severity    TEXT,   -- low | medium | high
            detected_at TEXT    DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("✓ Database initialised")


def save_analysis(
    input_type: str,
    extracted_text: str,
    result: dict,
    file_name: str = None,
):
    """Persist one teacher analysis to the database."""
    conn = _connect()
    activity = result.get("activity") or {}
    conn.execute(
        """
        INSERT INTO analyses
            (input_type, extracted_text, issue, topic, age_group,
             activity_name, activity_materials, activity_duration, file_name, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            input_type,
            extracted_text,
            result.get("issue"),
            result.get("topic"),
            result.get("age_group"),
            activity.get("name"),
            json.dumps(activity.get("materials", [])),
            activity.get("duration"),
            file_name,
            datetime.utcnow().isoformat(),
        ),
    )
    conn.commit()
    conn.close()


def get_all_analyses() -> list:
    """Retrieve all analysis records (used by future dashboard/reporting)."""
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM analyses ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return rows
