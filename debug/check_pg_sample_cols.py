"""Show actual column names with data from key tables."""
import psycopg2

conn = psycopg2.connect(
    host='localhost', port=5432,
    dbname='v57udemo2011',
    user='postgres', password='123'
)
cur = conn.cursor()

tables = ['scm_pur_main', 'scm_pur_data', 'scm_sal_main', 'scm_sal_data',
          'scm_stk_main', 'scm_stk_data', 'gen_ledger_detail', 'stk_sku_data',
          'adm_cnt_main', 'sm_co_sku_day']

for tbl in tables:
    try:
        cur.execute(f'SELECT * FROM "{tbl}" LIMIT 1')
        col_names = [desc[0] for desc in cur.description]
        row = cur.fetchone()
        print(f'\n=== {tbl} ===')
        if row:
            for i, val in enumerate(row):
                if val is not None:
                    print(f'  {col_names[i]} = {str(val)[:80]}')
    except Exception as e:
        print(f'{tbl}: ERROR - {e}')

cur.close()
conn.close()
