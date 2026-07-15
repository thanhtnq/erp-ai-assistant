"""Check how SCM tables join together."""
import psycopg2

conn = psycopg2.connect(
    host='localhost', port=5432,
    dbname='v57udemo2011',
    user='postgres', password='123'
)
cur = conn.cursor()

# Check scm_sal_body columns (likely the line items table)
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'scm_sal_body' 
    ORDER BY ordinal_position
""")
cols = cur.fetchall()
print("=== scm_sal_body columns ===")
for c_name, c_type in cols[:30]:
    print(f'  {c_name}: {c_type}')
print(f'  ... ({len(cols)} total)')

# Check scm_sal_main columns that might join
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'scm_sal_main' 
    ORDER BY ordinal_position
""")
cols = cur.fetchall()
print("\n=== scm_sal_main columns (first 30) ===")
for c_name, c_type in cols[:30]:
    print(f'  {c_name}: {c_type}')
print(f'  ... ({len(cols)} total)')

# Show first row of scm_sal_body
print("\n=== scm_sal_body first row ===")
cur.execute('SELECT * FROM "scm_sal_body" LIMIT 1')
row = cur.fetchone()
col_names = [desc[0] for desc in cur.description]
for i, val in enumerate(row):
    if val is not None:
        print(f'  {col_names[i]} = {str(val)[:80]}')

# Show first row of scm_sal_main
print("\n=== scm_sal_main first row ===")
cur.execute('SELECT * FROM "scm_sal_main" LIMIT 1')
row = cur.fetchone()
col_names = [desc[0] for desc in cur.description]
for i, val in enumerate(row):
    if val is not None:
        print(f'  {col_names[i]} = {str(val)[:80]}')

# Try to find the join relationship
print("\n=== Trying to find join columns ===")
# scm_sal_body likely has a column referencing scm_sal_main
cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'scm_sal_body' 
      AND (column_name LIKE '%uniquenum%' OR column_name LIKE '%main%' OR column_name LIKE '%pri%')
    ORDER BY ordinal_position
""")
for r in cur.fetchall():
    print(f'  scm_sal_body.{r[0]}')

cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'scm_sal_main' 
      AND (column_name LIKE '%uniquenum%' OR column_name LIKE '%body%' OR column_name LIKE '%pri%')
    ORDER BY ordinal_position
""")
for r in cur.fetchall():
    print(f'  scm_sal_main.{r[0]}')

# Check if scm_sal_body has stkcode_code and qnty columns
print("\n=== scm_sal_body key columns ===")
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'scm_sal_body' 
      AND (column_name LIKE '%stk%' OR column_name LIKE '%qnty%' OR column_name LIKE '%amount%' OR column_name LIKE '%sku%' OR column_name LIKE '%price%')
    ORDER BY ordinal_position
""")
for r in cur.fetchall():
    print(f'  {r[0]}: {r[1]}')

cur.close()
conn.close()
