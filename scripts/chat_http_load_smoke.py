"""
Concurrent HTTP smoke test for the deployed chat stream endpoint.

Default query is intentionally a chart follow-up without prior result context.
That path exercises FastAPI, auth, session-scoped DB writes, SSE streaming, and
the chart fallback without requiring Gemini or the skills server.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import time
import urllib.error
import urllib.request


def _post_chat(url: str, api_key: str, idx: int, timeout: int, query: str) -> dict:
    payload = {
        "user_id": f"load_user_{idx}",
        "company_id": "load_company",
        "company_code": "load_company",
        "masterfn": "load_master",
        "companyfn": "load_companyfn",
        "session_id": f"load_session_{idx}",
        "lang": "english",
        "text": query,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-API-Key": api_key,
        },
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            elapsed = time.perf_counter() - started
            return {
                "ok": resp.status == 200 and "event: done" in body,
                "status": resp.status,
                "elapsed": elapsed,
                "body_head": body[:240],
            }
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return {"ok": False, "status": exc.code, "elapsed": time.perf_counter() - started, "body_head": body[:240]}
    except Exception as exc:
        return {"ok": False, "status": "error", "elapsed": time.perf_counter() - started, "body_head": str(exc)[:240]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=os.getenv("CHAT_STREAM_URL", "http://127.0.0.1:8000/chat/stream"))
    parser.add_argument("--api-key", default=os.getenv("CHAT_API_KEY", "erp-ai-secret-key-change-me"))
    parser.add_argument("--requests", type=int, default=50)
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--query", default="show pie chart")
    args = parser.parse_args()

    started = time.perf_counter()
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = [
            pool.submit(_post_chat, args.url, args.api_key, idx, args.timeout, args.query)
            for idx in range(args.requests)
        ]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    elapsed = time.perf_counter() - started
    ok_count = sum(1 for item in results if item["ok"])
    failed = [item for item in results if not item["ok"]]
    latencies = sorted(item["elapsed"] for item in results)
    p95 = latencies[int(len(latencies) * 0.95) - 1] if latencies else 0

    print(
        f"requests={args.requests} concurrency={args.concurrency} "
        f"ok={ok_count} failed={len(failed)} elapsed_sec={elapsed:.3f} p95_sec={p95:.3f}"
    )
    if failed:
        sample = failed[0]
        print(f"first_failure status={sample['status']} body={sample['body_head']}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
