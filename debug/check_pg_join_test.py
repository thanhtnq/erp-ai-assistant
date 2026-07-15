"""Test actual join between scm_sal_main and scm_sal_data."""
import psycopg2

conn = psycopg2.connect(
    host='localhost', port=5432,
    dbname='v57udemo2011',
    user='postgres', password='123'
)
cur = conn.cursor()

# Test 1: Join scm_sal_main.uniquenum_pri = scm_sal_data.uniquenum_sec
print("=== Test 1: main.uniquenum_pri = data.uniquenum_sec ===")
cur.execute("""
    SELECT m.uniquenum_pri, d.uniquenum_sec, d.stkcode_code, d.qnty_total, d.amount_forex
    FROM scm_sal_main m
    JOIN scm_sal_data d ON d.uniquenum_sec = m.uniquenum_pri
    WHERE m.tag_deleted_yn = 'n' AND d.tag_deleted_yn = 'n'
      AND m.cslsegm = 'sal_soe'
      AND d.stkcode_code IS NOT NULL AND d.stkcode_code != ''
    LIMIT 10
""")
rows = cur.fetchall()
print(f"  Found {len(rows)} rows")
for r in rows:
    print(f"  main_pri={r[0]}, data_sec={r[1]}, sku={r[2]}, qty={r[3]}, amt={r[4]}")

# Test 2: Check if scm_sal_data has a column that references main
print("\n=== scm_sal_data columns with 'main' or 'ref' in name ===")
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'scm_sal_data' 
      AND (column_name LIKE '%main%' OR column_name LIKE '%ref%' OR column_name LIKE '%link%')
    ORDER BY ordinal_position
""")
for r in cur.fetchall():
    print(f'  {r[0]}: {r[1]}')

# Test 3: Check scm_sal_data for columns that might reference main
print("\n=== scm_sal_data first row with stkcode_code != '' ===")
cur.execute("""
    SELECT * FROM scm_sal_data 
    WHERE stkcode_code IS NOT NULL AND stkcode_code != ''
    LIMIT 1
""")
row = cur.fetchone()
if row:
    col_names = [desc[0] for desc in cur.description]
    for i, val in enumerate(row):
        if val is not None:
            print(f'  {col_names[i]} = {str(val)[:80]}')

# Test 4: Check scm_pur_main and scm_pur_data join
print("\n=== Test 4: pur_main.uniquenum_pri = pur_data.uniquenum_sec ===")
cur.execute("""
    SELECT m.uniquenum_pri, d.uniquenum_sec, d.stkcode_code, d.qnty_total, d.amount_forex
    FROM scm_pur_main m
    JOIN scm_pur_data d ON d.uniquenum_sec = m.uniquenum_pri
    WHERE m.tag_deleted_yn = 'n' AND d.tag_deleted_yn = 'n'
      AND m.cslsegm = 'pur_pi'
      AND d.stkcode_code IS NOT NULL AND d.stkcode_code != ''
    LIMIT 10
""")
rows = cur.fetchall()
print(f"  Found {len(rows)} rows")
for r in rows:
    print(f"  main_pri={r[0]}, data_sec={r[1]}, sku={r[2]}, qty={r[3]}, amt={r[4]}")

# Test 5: Check scm_stk_main and scm_stk_data join
print("\n=== Test 5: stk_main.uniquenum_pri = stk_data.uniquenum_sec ===")
cur.execute("""
    SELECT m.uniquenum_pri, d.uniquenum_sec, d.stkcode_code, d.qnty_total, d.amount_forex
    FROM scm_stk_main m
    JOIN scm_stk_data d ON d.uniquenum_sec = m.uniquenum_pri
    WHERE m.tag_deleted_yn = 'n' AND d.tag_deleted_yn = 'n'
      AND d.stkcode_code IS NOT NULL AND d.stkcode_code != ''
    LIMIT 10
""")
rows = cur.fetchall()
print(f"  Found {len(rows)} rows")
for r in rows:
    print(f"  main_pri={r[0]}, data_sec={r[1]}, sku={r[2]}, qty={r[3]}, amt={r[4]}")

cur.close()
conn.close()
