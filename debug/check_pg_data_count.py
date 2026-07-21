"""Check actual data in PostgreSQL tables"""
import os, sys
from dotenv import load_dotenv
load_dotenv('.env', override=True)

import psycopg2
conn = psycopg2.connect(
    host=os.getenv('PG_HOST', 'localhost'),
    port=int(os.getenv('PG_PORT', '5432')),
    dbname=os.getenv('PG_DBNAME', 'v57udemo2011'),
    user=os.getenv('PG_USER', 'postgres'),
    password=os.getenv('PG_PASSWORD', '123'),
)
cur = conn.cursor()

# Check what masterfn/companyfn combos exist in scm_sal_main
cur.execute("SELECT masterfn, companyfn, COUNT(*) as cnt FROM scm_sal_main WHERE tag_deleted_yn='n' GROUP BY masterfn, companyfn ORDER BY cnt DESC LIMIT 10")
rows = cur.fetchall()
print('=== scm_sal_main: existing scopes ===')
for r in rows:
    print(f'  masterfn={r[0]}, companyfn={r[1]}, count={r[2]}')

print()

# Check total rows in key tables
tables = ['scm_sal_main', 'scm_sal_data', 'scm_pur_main', 'scm_pur_data', 
          'scm_stk_main', 'scm_stk_data', 'stk_code_main', 'stk_code_data',
          'adm_cnt_main', 'adm_cnt_data', 'gen_ledger_detail', 'gnl_maint_all',
          'stkm_main_all', 'memo_long_table', 'prj_pbill_main', 'prj_pbill_body',
          'gen_ledger_stk']
for t in tables:
    try:
        cur.execute(f"SELECT COUNT(*) FROM {t} WHERE tag_deleted_yn='n'")
        cnt = cur.fetchone()[0]
        print(f'  {t}: {cnt} rows')
    except Exception as e:
        print(f'  {t}: ERROR - {e}')

cur.close()
conn.close()
