"""Check gen_ledger_detail columns."""
import psycopg2

conn = psycopg2.connect(
    host='localhost', port=5432,
    dbname='v57udemo2011',
    user='postgres', password='123'
)
cur = conn.cursor()

# Check gen_ledger_detail columns
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'gen_ledger_detail' 
    ORDER BY ordinal_position
""")
cols = cur.fetchall()
print("=== gen_ledger_detail columns ===")
for c_name, c_type in cols[:30]:
    print(f'  {c_name}: {c_type}')
print(f'  ... ({len(cols)} total)')

# Show first row
print("\n=== gen_ledger_detail first row ===")
cur.execute('SELECT * FROM "gen_ledger_detail" LIMIT 1')
row = cur.fetchone()
if row:
    col_names = [desc[0] for desc in cur.description]
    for i, val in enumerate(row):
        if val is not None:
            print(f'  {col_names[i]} = {str(val)[:80]}')

cur.close()
conn.close()
