"""
ERP AI Assistant — Database Connections
SQLite connections for knowledge DB and chat history DB.
"""
import sqlite3
import os

from api.config import KNOWLEDGE_DB, CHAT_DB


def get_knowledge_conn():
    """Get a connection to the knowledge database (erp_knowledge.db)."""
    conn = sqlite3.connect(KNOWLEDGE_DB)
    conn.row_factory = sqlite3.Row
    return conn


def get_chat_conn():
    """Get a connection to the chat history database (chat_history.db)."""
    conn = sqlite3.connect(CHAT_DB)
    conn.row_factory = sqlite3.Row
    return conn


def get_company_id_from_code(conn, company_code: str):
    """Look up company internal ID from its code."""
    if not company_code:
        return None
    row = conn.execute("SELECT id FROM companies WHERE code = ?", (company_code,)).fetchone()
    return row["id"] if row else None


def init_chat_db():
    """Initialize chat_history.db schema if not exists."""
    conn = sqlite3.connect(CHAT_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    TEXT NOT NULL,
            company_id TEXT NOT NULL DEFAULT '',
            role       TEXT NOT NULL,
            content    TEXT NOT NULL,
            timestamp  TEXT NOT NULL,
            session_id TEXT NOT NULL DEFAULT ''
        )
    """)
    # Add session_id column if missing (migration for existing DBs)
    try:
        conn.execute("ALTER TABLE chat_history ADD COLUMN session_id TEXT NOT NULL DEFAULT ''")
    except sqlite3.OperationalError:
        pass  # column already exists
    # Add session_title table for conversation titles
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            session_id TEXT PRIMARY KEY,
            user_id    TEXT NOT NULL,
            company_id TEXT NOT NULL DEFAULT '',
            title      TEXT NOT NULL DEFAULT 'Untitled chat',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_preferences (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      TEXT NOT NULL,
            company_id   TEXT NOT NULL DEFAULT '',
            language     TEXT NOT NULL DEFAULT 'auto',
            response_len TEXT NOT NULL DEFAULT 'normal',
            updated_at   TEXT NOT NULL,
            UNIQUE(user_id, company_id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS feedback_log (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id           TEXT NOT NULL,
            company_id        TEXT NOT NULL DEFAULT '',
            entry_version_id  INTEGER,
            rating            TEXT NOT NULL CHECK(rating IN ('up', 'down')),
            reason            TEXT,
            comment           TEXT,
            query_text        TEXT,
            created_at        TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ai_alerts (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            masterfn       TEXT NOT NULL,
            companyfn      TEXT NOT NULL,
            alert_type     TEXT NOT NULL,
            severity       TEXT NOT NULL DEFAULT 'medium',
            status         TEXT NOT NULL DEFAULT 'new',
            title          TEXT NOT NULL,
            reason_code    TEXT,
            risk_score     REAL,
            source_id      TEXT,
            evidence_json  TEXT NOT NULL DEFAULT '{}',
            rule_version   TEXT,
            reviewer       TEXT,
            review_note    TEXT,
            created_at     TEXT NOT NULL,
            updated_at     TEXT NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ai_alert_scope ON ai_alerts(masterfn, companyfn, status, alert_type)")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ai_recommendation_actions (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            masterfn          TEXT NOT NULL,
            companyfn         TEXT NOT NULL,
            recommendation_id TEXT NOT NULL,
            action            TEXT NOT NULL,
            actor             TEXT NOT NULL,
            note              TEXT,
            adjusted_qty      REAL,
            created_at        TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def ensure_knowledge_db_exists():
    """Check if knowledge DB file exists."""
    return os.path.exists(KNOWLEDGE_DB)
