"""Smoke test: POST a memo to the CF admin page.
Usage:
  python tools/test_post_memo.py --url "http://localhost/contentadmin/admin_memo_long_table.cfm" --companyfn ABC --memo "test memo"

This script sends a form POST and prints the response status and a short snippet.
Requires: requests (`pip install requests`)
"""
import argparse
import requests

parser = argparse.ArgumentParser()
parser.add_argument('--url', required=True, help='Full URL to admin_memo_long_table.cfm')
parser.add_argument('--companyfn', default='TEST', help='companyfn to post')
parser.add_argument('--masterfn', default='', help='masterfn')
parser.add_argument('--memo', default='Smoke test memo', help='Memo text')
parser.add_argument('--cookies', default='', help='Optional cookie string (name=value;name2=value2)')
args = parser.parse_args()

cookies = {}
if args.cookies:
    for pair in args.cookies.split(';'):
        if '=' in pair:
            k,v = pair.split('=',1)
            cookies[k.strip()] = v.strip()

data = {
    'TABLE_NAME': 'memo_long_table',
    'companyfn': args.companyfn,
    'masterfn': args.masterfn,
    'memo_text': args.memo,
}

print('POST', args.url)
r = requests.post(args.url, data=data, cookies=cookies, allow_redirects=True, timeout=15)
print('Status:', r.status_code)
text = r.text
print('Response snippet:\n', text[:800].replace('\n','\n'))
