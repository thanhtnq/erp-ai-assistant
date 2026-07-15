"""Check scm_sal_main cslsegm values and sample data."""
import psycopg2

conn = psycopg2.connect(
    host='localhost', port=5432,
    dbname='v57udemo2011',
    user='postgres', password='123'
)
cur = conn.cursor()

# Check distinct cslsegm values
cur.execute("""
    SELECT DISTINCT cslsegm FROM scm_sal_main 
    WHERE tag_deleted_yn = 'n' 
    ORDER BY cslsegm
""")
print("=== scm_sal_main cslsegm values ===")
for r in cur.fetchall():
    print(f"  '{r[0]}'")

# Check date range
cur.execute("""
    SELECT MIN(date_post), MAX(date_post) FROM scm_sal_main 
    WHERE tag_deleted_yn = 'n'
""")
r = cur.fetchone()
print(f"\n=== scm_sal_main date range ===")
print(f"  Min: {r[0]}, Max: {r[1]}")

# Check with cslsegm = 'sal_soe'
cur.execute("""
    SELECT COUNT(*) FROM scm_sal_main 
    WHERE tag_deleted_yn = 'n' AND cslsegm = 'sal_soe'
""")
print(f"\n=== scm_sal_main count with cslsegm='sal_soe' ===")
print(f"  {cur.fetchone()[0]} rows")

# Check with any cslsegm
cur.execute("""
    SELECT cslsegm, COUNT(*) FROM scm_sal_main 
    WHERE tag_deleted_yn = 'n'
    GROUP BY cslsegm
    ORDER BY COUNT(*) DESC
    LIMIT 10
""")
print(f"\n=== scm_sal_main count by cslsegm ===")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

# Check scm_sal_data join
cur.execute("""
    SELECT COUNT(*) 
    FROM scm_sal_main m
    JOIN scm_sal_data d ON d.uniquenum_sec = m.uniquenum_pri
    WHERE m.tag_deleted_yn = 'n' AND d.tag_deleted_yn = 'n'
""")
print(f"\n=== scm_sal_main + scm_sal_data join count ===")
print(f"  {cur.fetchone()[0]} rows")

# Check with date filter
cur.execute("""
    SELECT COUNT(*) 
    FROM scm_sal_main m
    JOIN scm_sal_data d ON d.uniquenum_sec = m.uniquenum_pri
    WHERE m.tag_deleted_yn = 'n' AND d.tag_deleted_yn = 'n'
      AND m.date_post >= '2010-01-01'
""")
print(f"\n=== scm_sal_main + scm_sal_data join count (since 2010) ===")
print(f"  {cur.fetchone()[0]} rows")

cur.close()
conn.close()
