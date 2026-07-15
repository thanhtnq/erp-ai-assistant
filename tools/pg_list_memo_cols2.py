#!/usr/bin/env python3
import psycopg2
conn = psycopg2.connect(host='localhost', port=5432, dbname='v57udemo2011', user='postgres', password='123')
cur = conn.cursor()
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'memo_long_table'")
rows = cur.fetchall()
print('Columns in memo_long_table:')
for r in rows:
    print('-', r[0], r[1])
cur.close()
conn.close()
