"""
Test: Create ERP Extract SQLite database from schema file.
"""
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "erp_extract.db"
SCHEMA_PATH = Path(__file__).parent.parent / "scripts" / "create_erp_extract_tables.sql"

def test_create_db():
    print(f"[TEST] Creating ERP Extract DB at: {DB_PATH}")
    
    # Remove existing DB for clean test
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"[CLEAN] Removed existing DB")
    
    # Create DB from schema
    conn = sqlite3.connect(str(DB_PATH))
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(schema_sql)
    conn.commit()
    
    # Verify tables
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cur.fetchall()]
    
    print(f"\n[RESULT] Created {len(tables)} tables:")
    for t in tables:
        # Count columns
        col_cur = conn.execute(f"PRAGMA table_info({t})")
        cols = col_cur.fetchall()
        print(f"  ✅ {t} ({len(cols)} columns)")
    
    # Verify indexes
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='index' ORDER BY name")
    indexes = [row[0] for row in cur.fetchall()]
    print(f"\n[RESULT] Created {len(indexes)} indexes:")
    for idx in indexes:
        print(f"  📌 {idx}")
    
    # Verify meta table
    meta = conn.execute("SELECT * FROM _extract_meta").fetchall()
    print(f"\n[RESULT] Meta entries: {len(meta)}")
    for key, value in meta:
        print(f"  ℹ️  {key} = {value}")
    
    # Verify scope columns exist on all tables
    print("\n[VERIFY] Scope columns on all tables:")
    data_tables = [t for t in tables if not t.startswith('_')]
    for t in data_tables:
        col_cur = conn.execute(f"PRAGMA table_info({t})")
        col_names = {row[1] for row in col_cur.fetchall()}
        has_scope = "scope_masterfn" in col_names and "scope_companyfn" in col_names
        status = "✅" if has_scope else "❌"
        print(f"  {status} {t}: scope_masterfn={'✓' if 'scope_masterfn' in col_names else '✗'}, scope_companyfn={'✓' if 'scope_companyfn' in col_names else '✗'}")
    
    conn.close()
    print(f"\n[PASS] All tests passed! DB size: {DB_PATH.stat().st_size / 1024:.1f} KB")

if __name__ == "__main__":
    test_create_db()
