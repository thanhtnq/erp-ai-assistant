#!/usr/bin/env python3
import psycopg2
conn = psycopg2.connect(host='localhost', port=5432, dbname='v57udemo2011', user='postgres', password='123')
cur = conn.cursor()
cur.execute("SELECT idcode, companyfn, masterfn, userid_cookie, date_post, notes_memo FROM memo_long_table WHERE companyfn=%s ORDER BY date_post DESC LIMIT 5", ('ABC',))
rows = cur.fetchall()
for r in rows:
    print(r)
cur.close()
conn.close()
