"""Check if there's actual data in the ERP database."""
import psycopg2

conn = psycopg2.connect(
    host='localhost', port=5432,
    dbname='v57udemo2011',
    user='postgres', password='123'
)
cur = conn.cursor()

# Check row counts for key tables
key_tables = [
    'scm_pur_body', 'scm_pur_data', 'scm_pur_main',
    'scm_sal_body', 'scm_sal_data', 'scm_sal_main',
    'scm_stk_body', 'scm_stk_data', 'scm_stk_main',
    'gen_ledger_detail', 'gen_ledger_stk', 'gen_ledger_wip',
    'stk_sku_data', 'stk_code_data', 'stk_code_main',
    'sm_co_sku_day', 'sm_loc_sku_day',
    'fin_bud_data', 'fin_bud_main',
    'memo_long_table',
    'set_co_data', 'set_co_main',
    'adm_cnt_data', 'adm_cnt_main',
]

for tbl in key_tables:
    try:
        cur.execute(f'SELECT COUNT(*) FROM "{tbl}"')
        count = cur.fetchone()[0]
        print(f'{tbl}: {count} rows')
        
        if count > 0:
            # Show first row column names and values
            cur.execute(f'SELECT * FROM "{tbl}" LIMIT 1')
            row = cur.fetchone()
            col_names = [desc[0] for desc in cur.description]
            print(f'  Columns with data:')
            for i, val in enumerate(row):
                if val is not None:
                    val_str = str(val)[:60]
                    print(f'    {col_names[i]}: {val_str}')
    except Exception as e:
        print(f'{tbl}: ERROR - {e}')

cur.close()
conn.close()
