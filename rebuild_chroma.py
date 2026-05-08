"""
Rebuild ChromaDB from existing SQLite knowledge base.
Use this when ChromaDB is missing or was deleted (e.g. after embedding model change).
Does NOT re-run LLM — uses data already stored in erp_knowledge.db.

Usage:
    python rebuild_chroma.py
"""

import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "ingest"))
from ingest_config import KNOWLEDGE_DB, CHROMA_BATCH_SIZE
from embedding_helper import batch_upsert_entries, CHROMA_AVAILABLE

if not CHROMA_AVAILABLE:
    print("[ERROR] ChromaDB not available. Run: pip install chromadb")
    sys.exit(1)

conn = sqlite3.connect(KNOWLEDGE_DB)
conn.row_factory = sqlite3.Row

rows = conn.execute("""
    SELECT
        ev.id          AS version_id,
        ev.entry_id,
        ev.company_id,
        ev.steps,
        ev.notes,
        ev.source_type,
        ev.is_flagged,
        e.name         AS entry_name,
        e.type         AS entry_type,
        e.menu_path,
        e.summary,
        f.name         AS feature_name,
        d.name         AS domain_name,
        c.code         AS company_code
    FROM entry_versions ev
    JOIN entries  e ON e.id = ev.entry_id
    JOIN features f ON f.id = e.feature_id
    JOIN domains  d ON d.id = f.domain_id
    LEFT JOIN companies c ON c.id = ev.company_id
    WHERE ev.is_current = 1
      AND ev.steps IS NOT NULL
      AND ev.steps != '[]'
""").fetchall()

conn.close()

print(f"[rebuild_chroma] Found {len(rows)} entry versions to index")

by_company: dict[str | None, list] = {}
for row in rows:
    try:
        steps = json.loads(row["steps"] or "[]")
        notes = json.loads(row["notes"] or "[]")
    except (json.JSONDecodeError, TypeError):
        steps, notes = [], []

    payload = {
        "version_id":  row["version_id"],
        "entry_id":    row["entry_id"],
        "domain":      row["domain_name"] or "",
        "feature":     row["feature_name"] or "",
        "name":        row["entry_name"] or "",
        "type":        row["entry_type"] or "",
        "menu_path":   row["menu_path"] or "",
        "summary":     row["summary"] or "",
        "steps":       steps,
        "notes":       notes,
        "source_type": row["source_type"] or "document",
        "is_flagged":  bool(row["is_flagged"]),
    }
    key = row["company_code"]  # None = global
    by_company.setdefault(key, []).append(payload)

total = 0
for company_code, entries in by_company.items():
    label = company_code or "_global"
    print(f"  [{label}] {len(entries)} entries ...", end=" ", flush=True)
    n = batch_upsert_entries(entries, company_code=company_code)
    print(f"{n} indexed")
    total += n

print(f"\n[rebuild_chroma] Done — {total} / {len(rows)} entries indexed in ChromaDB")
