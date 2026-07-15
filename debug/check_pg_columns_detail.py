"""Get detailed column info for SCM tables to build real queries."""
import psycopg2

conn = psycopg2.connect(
    host='localhost', port=5432,
    dbname='v57udemo2011',
    user='postgres', password='123'
)
cur = conn.cursor()

# Focus on columns we need for fraud detection and demand planning
tables_of_interest = {
    'scm_pur_main': 'Purchase Order headers',
    'scm_pur_data': 'Purchase Order items',
    'scm_pur_body': 'Purchase Order body/extended',
    'scm_sal_main': 'Sales Order headers',
    'scm_sal_data': 'Sales Order items',
    'scm_stk_main': 'Stock transaction headers',
    'scm_stk_data': 'Stock transaction items',
    'scm_stk_body': 'Stock transaction body',
    'gen_ledger_detail': 'General Ledger detail',
    'gen_ledger_stk': 'Stock ledger',
    'stk_sku_data': 'SKU master data',
    'stk_code_data': 'Stock code data',
    'sm_co_sku_day': 'Sales movement by company/SKU/day',
    'adm_cnt_main': 'Contact/vendor master',
    'set_co_data': 'Company setup data',
}

for tbl, desc in tables_of_interest.items():
    try:
        cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name='{tbl}' ORDER BY ordinal_position")
        cols = cur.fetchall()
        print(f'\n=== {tbl} ({desc}) - {len(cols)} cols ===')
        for c_name, c_type in cols:
            print(f'  {c_name}: {c_type}')
    except Exception as e:
        print(f'{tbl}: ERROR - {e}')

cur.close()
conn.close()
