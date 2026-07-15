"""Check detailed columns of SCM and finance tables."""
import psycopg2

conn = psycopg2.connect(
    host='localhost', port=5432,
    dbname='v57udemo2011',
    user='postgres', password='123'
)
cur = conn.cursor()

# Get ALL tables
cur.execute("""
    SELECT table_name FROM information_schema.tables 
    WHERE table_schema='public' AND table_type='BASE TABLE' 
    ORDER BY table_name
""")
tables = [r[0] for r in cur.fetchall()]

# Focus on SCM and finance tables
focus_tables = [t for t in tables if t.startswith(('scm_', 'gen_', 'fin_', 'stk_', 'sm_', 'set_'))]
print(f'Focus tables: {len(focus_tables)}')

for tbl in focus_tables:
    cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name='{tbl}' ORDER BY ordinal_position")
    cols = cur.fetchall()
    print(f'\n=== {tbl} ({len(cols)} columns) ===')
    for c_name, c_type in cols:
        print(f'  {c_name}: {c_type}')

# Also check a few sample rows from key tables
sample_tables = ['scm_pur_body', 'scm_pur_data', 'scm_pur_main',
                 'scm_stk_body', 'scm_stk_data', 'scm_stk_main',
                 'gen_ledger_detail', 'stk_sku_data']
for tbl in sample_tables:
    if tbl.lower() in [t.lower() for t in tables]:
        actual_name = [t for t in tables if t.lower() == tbl.lower()][0]
        try:
            cur.execute(f'SELECT * FROM "{actual_name}" LIMIT 3')
            rows = cur.fetchall()
            col_names = [desc[0] for desc in cur.description]
            print(f'\n=== Sample data: {actual_name} ===')
            for row in rows:
                for i, val in enumerate(row):
                    if val is not None and col_names[i] in ('docnum', 'docdate', 'amount', 'qty', 'sku', 'vendor', 'customer', 'status', 'description', 'remarks'):
                        print(f'  {col_names[i]}: {str(val)[:80]}')
                print('  ---')
        except Exception as e:
            print(f'  Error querying {actual_name}: {e}')

cur.close()
conn.close()
