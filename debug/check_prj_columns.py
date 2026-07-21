"""
Check columns of prj_pbill_body table.
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

# Check prj_pbill_body columns
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'prj_pbill_body'
    ORDER BY ordinal_position
""")
cols = cur.fetchall()
print("prj_pbill_body columns:")
for c in cols:
    print(f"  {c[0]} ({c[1]})")

# Check prj_pbill_data columns
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'prj_pbill_data'
    ORDER BY ordinal_position
""")
cols = cur.fetchall()
print("\nprj_pbill_data columns:")
for c in cols:
    print(f"  {c[0]} ({c[1]})")

cur.close()
conn.close()
