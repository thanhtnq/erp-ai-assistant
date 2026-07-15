"""Check PostgreSQL tables - full listing."""
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
print(f'Total tables: {len(tables)}')
print('ALL TABLES:')
for t in tables:
    print(f'  {t}')

# Check columns of key tables
key_tables = ['apinvoice', 'apinvoiceitem', 'vendor', 'customer', 
              'purchaseorder', 'purchaseorderitem', 'goodsreceipt',
              'salesorder', 'salesorderitem', 'inventory', 'stock',
              'gltransaction', 'journalentry', 'stk_sku_data',
              'sm_co_sku_day', 'sm_loc_sku_day']
for tbl in key_tables:
    if tbl.lower() in [t.lower() for t in tables]:
        actual_name = [t for t in tables if t.lower() == tbl.lower()][0]
        cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name='{actual_name}' ORDER BY ordinal_position")
        cols = cur.fetchall()
        print(f'\n=== {actual_name} ({len(cols)} columns) ===')
        for c_name, c_type in cols[:20]:
            print(f'  {c_name}: {c_type}')
        if len(cols) > 20:
            print(f'  ... and {len(cols)-20} more columns')

cur.close()
conn.close()
