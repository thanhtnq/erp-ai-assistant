"""Check stk_sku_data columns."""
import psycopg2

conn = psycopg2.connect(
    host='localhost', port=5432,
    dbname='v57udemo2011',
    user='postgres', password='123'
)
cur = conn.cursor()

# Check stk_sku_data columns
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'stk_sku_data' 
    ORDER BY ordinal_position
""")
cols = cur.fetchall()
print("=== stk_sku_data columns ===")
for c_name, c_type in cols:
    if any(k in c_name.lower() for k in ['qnty', 'amount', 'stkcode', 'stktype', 'stkgroup', 'desc']):
        print(f'  {c_name}: {c_type}')

# Show first row
print("\n=== stk_sku_data first row ===")
cur.execute('SELECT * FROM "stk_sku_data" WHERE tag_deleted_yn = \'n\' LIMIT 1')
row = cur.fetchone()
if row:
    col_names = [desc[0] for desc in cur.description]
    for i, val in enumerate(row):
        if val is not None:
            print(f'  {col_names[i]} = {str(val)[:80]}')

# Check scm_sal_data columns for qnty
print("\n=== scm_sal_data qnty/amount columns ===")
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'scm_sal_data' 
      AND (column_name LIKE '%qnty%' OR column_name LIKE '%amount%')
    ORDER BY ordinal_position
""")
for r in cur.fetchall():
    print(f'  {r[0]}: {r[1]}')

# Check scm_stk_data columns
print("\n=== scm_stk_data qnty/amount columns ===")
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'scm_stk_data' 
      AND (column_name LIKE '%qnty%' OR column_name LIKE '%amount%' OR column_name LIKE '%stkcode%')
    ORDER BY ordinal_position
""")
for r in cur.fetchall():
    print(f'  {r[0]}: {r[1]}')

# Check scm_pur_data columns
print("\n=== scm_pur_data qnty/amount columns ===")
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'scm_pur_data' 
      AND (column_name LIKE '%qnty%' OR column_name LIKE '%amount%' OR column_name LIKE '%stkcode%')
    ORDER BY ordinal_position
""")
for r in cur.fetchall():
    print(f'  {r[0]}: {r[1]}')

cur.close()
conn.close()
