"""
Check which PG tables exist for ERP extract.
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

tables_to_check = [
    "scm_sal_main", "scm_sal_data",
    "scm_pur_main", "scm_pur_data",
    "scm_stk_main", "scm_stk_data",
    "stk_code_main", "stk_code_data",
    "adm_cnt_main", "adm_cnt_data",
    "gen_ledger_detail", "gnl_maint_all",
    "stkm_main_all", "memo_long_table",
    "prj_pbill_main", "prjcode_main", "gen_ledger_main",
]

for tbl in tables_to_check:
    cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s)", (tbl,))
    exists = cur.fetchone()[0]
    if exists:
        # Count rows
        cur.execute(f"SELECT COUNT(*) FROM {tbl}")
        count = cur.fetchone()[0]
        print(f"  ✅ {tbl}: {count} rows")
    else:
        print(f"  ❌ {tbl}: NOT FOUND")
        # Search for similar
        search = tbl.replace("_", "%")
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_name LIKE %s LIMIT 5", (search,))
        similar = [r[0] for r in cur.fetchall()]
        if similar:
            print(f"     Similar: {similar}")

cur.close()
conn.close()
