"""Check foreign key columns in SCM data tables."""
import psycopg2

conn = psycopg2.connect(
    host='localhost', port=5432,
    dbname='v57udemo2011',
    user='postgres', password='123'
)
cur = conn.cursor()

# Check columns that might be foreign keys in scm_sal_data
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'scm_sal_data' 
    ORDER BY ordinal_position
""")
cols = cur.fetchall()
print("=== scm_sal_data columns ===")
for c_name, c_type in cols:
    if 'uniquenum' in c_name.lower() or 'main' in c_name.lower() or 'pri' in c_name.lower() or 'fn' in c_name.lower():
        print(f'  {c_name}: {c_type}')

# Also check scm_pur_data
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'scm_pur_data' 
    ORDER BY ordinal_position
""")
cols = cur.fetchall()
print("\n=== scm_pur_data columns ===")
for c_name, c_type in cols:
    if 'uniquenum' in c_name.lower() or 'main' in c_name.lower() or 'pri' in c_name.lower() or 'fn' in c_name.lower():
        print(f'  {c_name}: {c_type}')

# Check scm_stk_data
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'scm_stk_data' 
    ORDER BY ordinal_position
""")
cols = cur.fetchall()
print("\n=== scm_stk_data columns ===")
for c_name, c_type in cols:
    if 'uniquenum' in c_name.lower() or 'main' in c_name.lower() or 'pri' in c_name.lower() or 'fn' in c_name.lower():
        print(f'  {c_name}: {c_type}')

# Show first row of scm_sal_data to see actual values
print("\n=== scm_sal_data first row ===")
cur.execute('SELECT * FROM "scm_sal_data" LIMIT 1')
row = cur.fetchone()
col_names = [desc[0] for desc in cur.description]
for i, val in enumerate(row):
    if val is not None:
        print(f'  {col_names[i]} = {str(val)[:80]}')

cur.close()
conn.close()
