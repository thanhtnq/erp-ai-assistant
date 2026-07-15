#!/usr/bin/env python3
import psycopg2
from psycopg2.extras import RealDictCursor
from ingest.ingest_config import PG_CONFIG

conn = psycopg2.connect(host=PG_CONFIG['host'], port=PG_CONFIG['port'], dbname=PG_CONFIG['dbname'], user=PG_CONFIG['user'], password=PG_CONFIG['password'])
cur = conn.cursor()
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'memo_long_table'")
rows = cur.fetchall()
print('Columns in memo_long_table:')
for r in rows:
    print('-', r[0], r[1])
cur.close()
conn.close()
