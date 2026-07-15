#!/usr/bin/env python3
"""Test POST to FastAPI /admin/memo using only stdlib (no requests).
Usage: python tools/test_post_api_memo.py
"""
import json
import urllib.request

import os
API_URL = os.environ.get('API_URL', "http://127.0.0.1:8000/admin/memo")
API_KEY = "YJfgXD-P5WF9p3VCT1XN_ehsnB2KK_OfIYedBxz_J8M"

payload = {
    "companyfn": "ABC",
    "masterfn": "M001",
    "created_by": "tester",
    "content": "Smoke test memo via API",
    "source_table": "test_src",
    "doc_number": "DOC-123",
    "module": "TestMod",
    "segment": "SegA",
    "var_50_001": "v1",
}

data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(API_URL, data=data, method='POST')
req.add_header('Content-Type', 'application/json')
req.add_header('X-API-Key', API_KEY)

try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        resp_text = resp.read().decode('utf-8')
        print('Status:', resp.getcode())
        print('Response:', resp_text)
except Exception as e:
    print('Request failed:', e)
