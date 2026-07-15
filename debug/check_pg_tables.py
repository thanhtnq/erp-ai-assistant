"""Check PostgreSQL tables related to fraud detection and demand planning."""
import psycopg2

conn = psycopg2.connect(
    host='localhost', port=5432,
    dbname='v57udemo2011',
    user='postgres', password='123'
)
cur = conn.cursor()

cur.execute("""
    SELECT table_name FROM information_schema.tables 
    WHERE table_schema='public' AND table_type='BASE TABLE' 
    ORDER BY table_name
""")
tables = [r[0] for r in cur.fetchall()]
print(f'Total tables: {len(tables)}')

# Show tables related to key areas
keywords = ['ap', 'invoice', 'payment', 'vendor', 'inventory', 'finance', 
            'po', 'grn', 'stock', 'sku', 'product', 'sales', 'demand', 
            'forecast', 'purchase', 'goods', 'receipt', 'order', 'quote',
            'customer', 'supplier', 'account', 'journal', 'gl', 'budget']
for kw in keywords:
    matches = [t for t in tables if kw.lower() in t.lower()]
    if matches:
        print(f'\n  [{kw}] ({len(matches)} tables):')
        for m in matches[:10]:
            print(f'    - {m}')

# Check a few sample tables for columns
sample_tables = ['apinvoice', 'apinvoiceitem', 'vendor', 'customer', 
                 'purchaseorder', 'purchaseorderitem', 'goodsreceipt',
                 'salesorder', 'salesorderitem', 'inventory', 'stock',
                 'gltransaction', 'journalentry']
for tbl in sample_tables:
    if tbl.lower() in [t.lower() for t in tables]:
        actual_name = [t for t in tables if t.lower() == tbl.lower()][0]
        cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='{actual_name}' ORDER BY ordinal_position")
        cols = [r[0] for r in cur.fetchall()]
        print(f'\n  Columns of {actual_name}:')
        for c in cols[:15]:
            print(f'    - {c}')
        if len(cols) > 15:
            print(f'    ... and {len(cols)-15} more columns')

cur.close()
conn.close()
