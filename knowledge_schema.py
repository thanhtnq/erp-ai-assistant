"""
ERP AI — Knowledge Base Schema
4-tier structure: Domain → Feature → Entry → Version

Run once to initialize the database:
    python knowledge_schema.py

Or import and call init_knowledge_db() from other scripts.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = "./data/erp_knowledge.db"


def init_knowledge_db(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")  # better concurrent read

    # ─── Tier 0: Companies ────────────────────────────────────────────
    # NULL company_id = global (shared across all companies)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            code        TEXT NOT NULL UNIQUE,   -- 'ABC', 'XYZ'
            name        TEXT NOT NULL,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # ─── Tier 1: Domain ───────────────────────────────────────────────
    # e.g. Sales, Purchase, Stock, Finance, HR
    conn.execute("""
        CREATE TABLE IF NOT EXISTS domains (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL UNIQUE,   -- 'Sales'
            description TEXT,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # ─── Tier 2: Feature ──────────────────────────────────────────────
    # e.g. Sales Quotation, Sales Order, Delivery Order
    conn.execute("""
        CREATE TABLE IF NOT EXISTS features (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            domain_id   INTEGER NOT NULL REFERENCES domains(id),
            name        TEXT NOT NULL,          -- 'Sales Quotation'
            description TEXT,
            sort_order  INTEGER DEFAULT 0,      -- matches heading number e.g. 1, 2, 3
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(domain_id, name)
        )
    """)

    # ─── Tier 3: Entry ────────────────────────────────────────────────
    # e.g. Creating Sales Quotation, Revise, Void
    # type: procedure | error_fix | faq | reference
    conn.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            feature_id  INTEGER NOT NULL REFERENCES features(id),
            name        TEXT NOT NULL,          -- 'Creating Sales Quotation'
            type        TEXT NOT NULL           -- 'procedure' | 'error_fix' | 'faq' | 'reference'
                        CHECK(type IN ('procedure', 'error_fix', 'faq', 'reference')),
            menu_path   TEXT,                   -- 'Supply Chain Mgmt > Sales Manager > ...'
            summary     TEXT,                   -- one-line description
            sort_order  INTEGER DEFAULT 0,      -- matches heading number e.g. 1.1, 1.2
            is_active   INTEGER DEFAULT 1,      -- 0 = deprecated
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(feature_id, name)
        )
    """)

    # ─── Tier 4: Entry Versions ───────────────────────────────────────
    # Each entry can have multiple versions per company
    # company_id NULL = global version (fallback for all companies)
    # company_id SET  = company-specific version (takes priority)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS entry_versions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id        INTEGER NOT NULL REFERENCES entries(id),
            company_id      INTEGER REFERENCES companies(id),  -- NULL = global
            version         INTEGER NOT NULL DEFAULT 1,
            steps           TEXT,       -- JSON array of step objects
            notes           TEXT,       -- JSON array of note strings
            raw_content     TEXT,       -- original text before LLM processing
            source_type     TEXT NOT NULL
                            CHECK(source_type IN ('document', 'ticket', 'augmented', 'manual')),
            source_ref      TEXT,       -- filename, ticket ID, etc.
            score           REAL DEFAULT 0.0,   -- feedback score (up/down ratio)
            thumbs_up       INTEGER DEFAULT 0,
            thumbs_down     INTEGER DEFAULT 0,
            is_flagged      INTEGER DEFAULT 0,  -- flagged for review
            flag_reason     TEXT,
            is_current      INTEGER DEFAULT 1,  -- 1 = latest version
            created_at      TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(entry_id, company_id, version)
        )
    """)

    # ─── Feedback ─────────────────────────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_version_id    INTEGER REFERENCES entry_versions(id),
            user_id             TEXT NOT NULL,
            company_id          INTEGER REFERENCES companies(id),
            rating              TEXT NOT NULL CHECK(rating IN ('up', 'down')),

            -- User-selected reason (for thumbs down)
            reason              TEXT CHECK(reason IN (
                                    'wrong_answer',     -- doesn't match question
                                    'incomplete',       -- missing steps/details
                                    'outdated',         -- steps don't match current system
                                    'too_complex',      -- hard to follow
                                    'missing_images',   -- screenshots would help
                                    'other',
                                    NULL
                                )),

            -- Raw comment from user (may be informal/unprofessional)
            comment_raw         TEXT,

            -- LLM-normalized comment (professional, actionable)
            comment_normalized  TEXT,

            -- LLM classification of comment
            comment_type        TEXT CHECK(comment_type IN (
                                    'content',      -- issue with the answer content
                                    'preference',   -- user wants different response style
                                    'both',         -- content issue + preference change
                                    NULL
                                )),

            -- Extracted content issue (if type=content or both)
            content_issue       TEXT,

            -- Extracted preference change (JSON, if type=preference or both)
            -- e.g. {"response_len": "detailed"} or {"language": "vi"}
            preference_change   TEXT,

            -- Whether this feedback is actionable for admin review
            is_actionable       INTEGER DEFAULT 0,

            -- What the user originally asked
            query_text          TEXT,

            created_at          TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # ─── Document Registry ────────────────────────────────────────────
    # Track which files have been ingested
    conn.execute("""
        CREATE TABLE IF NOT EXISTS document_registry (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path       TEXT NOT NULL,      -- relative path from project root
            company_id      INTEGER REFERENCES companies(id),  -- NULL = global
            domain_id       INTEGER REFERENCES domains(id),
            file_hash       TEXT,               -- MD5 of file content — detect changes
            entries_parsed  INTEGER DEFAULT 0,  -- how many entries were extracted
            status          TEXT DEFAULT 'pending'
                            CHECK(status IN ('pending', 'processing', 'done', 'failed')),
            error_message   TEXT,
            ingested_at     TEXT,
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # ─── Ingest Log ───────────────────────────────────────────────────
    # Detailed log of what changed during each ingest run
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ingest_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id     INTEGER REFERENCES document_registry(id),
            entry_id        INTEGER REFERENCES entries(id),
            action          TEXT NOT NULL   -- 'created' | 'version_added' | 'deprecated' | 'skipped'
                            CHECK(action IN ('created', 'version_added', 'deprecated', 'skipped')),
            detail          TEXT,           -- human-readable explanation
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # ─── Indexes ──────────────────────────────────────────────────────
    conn.execute("CREATE INDEX IF NOT EXISTS idx_features_domain    ON features(domain_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_entries_feature    ON entries(feature_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_entries_type       ON entries(type)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_versions_entry     ON entry_versions(entry_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_versions_company   ON entry_versions(company_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_versions_current   ON entry_versions(is_current)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_version   ON feedback(entry_version_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_registry_hash      ON document_registry(file_hash)")

    # ─── Admin Action Log ────────────────────────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS admin_action_log (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_user_id TEXT    NOT NULL,
            action        TEXT    NOT NULL,
            target_type   TEXT,
            target_id     TEXT,
            note          TEXT,
            meta          TEXT,
            ip_address    TEXT,
            created_at    TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_admin_log_action   ON admin_action_log(action)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_admin_log_user     ON admin_action_log(admin_user_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_admin_log_created  ON admin_action_log(created_at)")

    conn.commit()
    conn.close()
    print(f"[OK] Knowledge DB initialized: {db_path}")


def migrate_admin_columns(db_path=DB_PATH):
    """
    Idempotent migration: add flag lifecycle columns to entry_versions
    and ensure admin_action_log table exists.
    Safe to run on existing databases — silently skips if already present.
    """
    conn = sqlite3.connect(db_path)

    # Add flag lifecycle columns to entry_versions
    for column, col_type in [
        ("flag_status",          "TEXT"),
        ("flag_resolved_at",     "TEXT"),
        ("flag_resolved_by",     "TEXT"),
        ("flag_resolution_note", "TEXT"),
    ]:
        try:
            conn.execute(f"ALTER TABLE entry_versions ADD COLUMN {column} {col_type}")
            print(f"[OK] Migration: entry_versions.{column} added")
        except Exception:
            pass  # column already exists

    # Ensure admin_action_log table and indexes exist
    conn.execute("""
        CREATE TABLE IF NOT EXISTS admin_action_log (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_user_id TEXT    NOT NULL,
            action        TEXT    NOT NULL,
            target_type   TEXT,
            target_id     TEXT,
            note          TEXT,
            meta          TEXT,
            ip_address    TEXT,
            created_at    TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    for idx_sql in [
        "CREATE INDEX IF NOT EXISTS idx_admin_log_action  ON admin_action_log(action)",
        "CREATE INDEX IF NOT EXISTS idx_admin_log_user    ON admin_action_log(admin_user_id)",
        "CREATE INDEX IF NOT EXISTS idx_admin_log_created ON admin_action_log(created_at)",
    ]:
        try:
            conn.execute(idx_sql)
        except Exception:
            pass

    conn.commit()
    conn.close()
    print("[OK] Admin column migration complete")


def seed_initial_data(db_path=DB_PATH):
    """
    No hardcoded domains — domains are created automatically
    when documents are ingested based on folder names.

    This function only seeds the system if you want to pre-define
    domains before ingesting any documents.

    To add a domain manually:
        add_domain("Human Resources", "HR module description")
    """
    print("[OK] No seed data required — domains are created automatically from folder names.")
    print("     Folder name rules:")
    print("       Sales            → domain 'Sales'")
    print("       Human_Resources  → domain 'Human Resources'")
    print("       Fixed_Assets     → domain 'Fixed Assets'")


def add_domain(name: str, description: str = "", db_path: str = DB_PATH):
    """Manually add a domain to the DB (optional — normally auto-created on ingest)."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute(
        "INSERT OR IGNORE INTO domains (name, description) VALUES (?, ?)",
        (name, description)
    )
    conn.commit()
    conn.close()
    print(f"[OK] Domain added: {name}")


# ─── Query Helpers ────────────────────────────────────────────────────────────

def get_entry_version(conn, entry_id: int, company_id: int = None):
    """
    Get the best version for an entry given a company.
    Priority: company-specific → global
    """
    # Try company-specific first
    if company_id:
        row = conn.execute("""
            SELECT * FROM entry_versions
            WHERE entry_id = ? AND company_id = ? AND is_current = 1
            ORDER BY version DESC LIMIT 1
        """, (entry_id, company_id)).fetchone()
        if row:
            return row, "company"

    # Fallback to global
    row = conn.execute("""
        SELECT * FROM entry_versions
        WHERE entry_id = ? AND company_id IS NULL AND is_current = 1
        ORDER BY version DESC LIMIT 1
    """, (entry_id,)).fetchone()

    return (row, "global") if row else (None, None)


def search_entries(conn, query_terms: list, domain_name: str = None,
                   entry_type: str = None, company_id: int = None):
    """
    Simple keyword search across entries.
    Returns list of (entry, version, source) tuples.
    In production this will be replaced by vector search.
    """
    conditions = ["e.is_active = 1"]
    params = []

    if domain_name:
        conditions.append("d.name = ?")
        params.append(domain_name)

    if entry_type:
        conditions.append("e.type = ?")
        params.append(entry_type)

    if query_terms:
        term_conditions = []
        for term in query_terms:
            term_conditions.append("(e.name LIKE ? OR e.summary LIKE ? OR e.menu_path LIKE ?)")
            params.extend([f"%{term}%", f"%{term}%", f"%{term}%"])
        conditions.append(f"({' OR '.join(term_conditions)})")

    where = " AND ".join(conditions)

    rows = conn.execute(f"""
        SELECT e.id, e.name, e.type, e.menu_path, e.summary,
               f.name as feature_name, d.name as domain_name
        FROM entries e
        JOIN features f ON e.feature_id = f.id
        JOIN domains d  ON f.domain_id  = d.id
        WHERE {where}
        ORDER BY e.sort_order
        LIMIT 10
    """, params).fetchall()

    results = []
    for row in rows:
        version, source = get_entry_version(conn, row[0], company_id)
        if version:
            results.append({
                "entry_id":     row[0],
                "entry_name":   row[1],
                "type":         row[2],
                "menu_path":    row[3],
                "summary":      row[4],
                "feature":      row[5],
                "domain":       row[6],
                "version":      version,
                "version_source": source,
            })
    return results


def add_feedback(conn, entry_version_id: int, user_id: str,
                 company_id: int, rating: str, query_text: str,
                 comment: str = None):
    """Record user feedback and update entry score."""
    conn.execute("""
        INSERT INTO feedback
            (entry_version_id, user_id, company_id, rating, query_text, comment)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (entry_version_id, user_id, company_id, rating, query_text, comment))

    # Update score on entry_version
    if rating == "up":
        conn.execute("UPDATE entry_versions SET thumbs_up = thumbs_up + 1 WHERE id = ?",
                     (entry_version_id,))
    else:
        conn.execute("UPDATE entry_versions SET thumbs_down = thumbs_down + 1 WHERE id = ?",
                     (entry_version_id,))

    # Recalculate score: up / (up + down)
    conn.execute("""
        UPDATE entry_versions
        SET score = CAST(thumbs_up AS REAL) / NULLIF(thumbs_up + thumbs_down, 0)
        WHERE id = ?
    """, (entry_version_id,))

    conn.commit()


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Initializing ERP Knowledge Database...")
    init_knowledge_db()
    migrate_admin_columns()
    seed_initial_data()

    # Quick verification
    conn = sqlite3.connect(DB_PATH)
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    print(f"\nTables created: {[t[0] for t in tables]}")
    conn.close()

    print("\n[DONE] Knowledge DB ready.")
    print(f"       File: {os.path.abspath(DB_PATH)}")
    print("""
Next steps:
  1. Place documents in:
       documents/_global/Sales/          ← global Sales documents
       documents/_global/Human_Resources/ ← global HR documents
       documents/clients/ABC/Sales/       ← ABC-specific Sales documents
  2. Run: python ingest_knowledge.py
  3. Update api.py to use knowledge DB for retrieval
""")
