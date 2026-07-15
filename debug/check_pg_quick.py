"""Quick check: row counts and sample data from SCM tables."""
import psycopg2

conn = psycopg2.connect(
    host='localhost', port=5432,
    dbname='v57udemo2011',
    user='postgres', password='123'
)
cur = conn.cursor()

tables = [
    'scm_pur_body', 'scm_pur_data', 'scm_pur_main',
    'scm_sal_body', 'scm_sal_data', 'scm_sal_main',
    'scm_stk_body', 'scm_stk_data', 'scm_stk_main',
    'gen_ledger_detail', 'gen_ledger_stk',
    'stk_sku_data', 'stk_code_data',
    'sm_co_sku_day', 'sm_loc_sku_day',
    'fin_bud_data',
    'memo_long_table',
    'set_co_data',
]

for tbl in tables:
    try:
        cur.execute(f'SELECT COUNT(*) FROM "{tbl}"')
        count = cur.fetchone()[0]
        print(f'{tbl}: {count} rows')
    except Exception as e:
        print(f'{tbl}: ERROR - {e}')

# Show some actual data from scm_pur_main
print('\n=== scm_pur_main sample ===')
try:
    cur.execute('SELECT * FROM "scm_pur_main" LIMIT 5')
    rows = cur.fetchall()
    col_names = [desc[0] for desc in cur.description]
    for row in rows:
        for i, val in enumerate(row):
            if val is not None and col_names[i] in ('docnum', 'docdate', 'amount', 'status', 'description', 'vendor', 'companyfn', 'masterfn', 'date_post', 'tag_void_yn'):
                print(f'  {col_names[i]}: {str(val)[:80]}')
        print('  ---')
except Exception as e:
    print(f'  Error: {e}')

# Show some actual data from scm_stk_main
print('\n=== scm_stk_main sample ===')
try:
    cur.execute('SELECT * FROM "scm_stk_main" LIMIT 5')
    rows = cur.fetchall()
    col_names = [desc[0] for desc in cur.description]
    for row in rows:
        for i, val in enumerate(row):
            if val is not None and col_names[i] in ('docnum', 'docdate', 'amount', 'status', 'description', 'companyfn', 'masterfn', 'date_post', 'tag_void_yn'):
                print(f'  {col_names[i]}: {str(val)[:80]}')
        print('  ---')
except Exception as e:
    print(f'  Error: {e}')

# Show some actual data from stk_sku_data
print('\n=== stk_sku_data sample ===')
try:
    cur.execute('SELECT * FROM "stk_sku_data" LIMIT 5')
    rows = cur.fetchall()
    col_names = [desc[0] for desc in cur.description]
    for row in rows:
        for i, val in enumerate(row):
            if val is not None and col_names[i] in ('stkcode_code', 'stkcode_desc', 'companyfn', 'masterfn', 'stktype_code', 'stkgroup_code'):
                print(f'  {col_names[i]}: {str(val)[:80]}')
        print('  ---')
except Exception as e:
    print(f'  Error: {e}')

# Show some actual data from gen_ledger_detail
print('\n=== gen_ledger_detail sample ===')
try:
    cur.execute('SELECT * FROM "gen_ledger_detail" LIMIT 5')
    rows = cur.fetchall()
    col_names = [desc[0] for desc in cur.description]
    for row in rows:
        for i, val in enumerate(row):
            if val is not None and col_names[i] in ('docnum', 'docdate', 'amount', 'acctnum', 'description', 'companyfn', 'masterfn', 'date_post'):
                print(f'  {col_names[i]}: {str(val)[:80]}')
        print('  ---')
except Exception as e:
    print(f'  Error: {e}')

cur.close()
conn.close()
