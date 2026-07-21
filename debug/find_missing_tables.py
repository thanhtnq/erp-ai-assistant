"""
Find correct PG table names for prjcode_main and gen_ledger_main.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)

import psycopg2

conn = psycopg2.connect(
    host=os.getenv("PG_HOST", "localhost"),
    port=int(os.getenv("PG_PORT", "5432")),
    dbname=os.getenv("PG_DBNAME", "v57udemo2011"),
    user=os.getenv("PG_USER", "postgres"),
    password=os.getenv("PG_PASSWORD", "123"),
)
cur = conn.cursor()

# Find PRJ tables
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_name LIKE '%prj%' ORDER BY table_name")
prj_tables = [r[0] for r in cur.fetchall()]
print("PRJ tables:", prj_tables)

# Find GL tables
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_name LIKE '%gen%ledger%' ORDER BY table_name")
gl_tables = [r[0] for r in cur.fetchall()]
print("GL tables:", gl_tables)

# Also check for gen_ledger_main alternatives
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_name LIKE '%ledger%' ORDER BY table_name")
all_ledger = [r[0] for r in cur.fetchall()]
print("All ledger tables:", all_ledger)

cur.close()
conn.close()
