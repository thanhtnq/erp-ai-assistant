# Data Query Pipeline (`api.py` — `run_data_query`)

Handles live ERP data questions. Bypasses RAG — calls Node.js skills server instead.

## Intent Detection (`detect_intent`)

Two-pass detection to handle follow-up queries:

```python
intent = detect_intent(q.text)          # original query
if intent != "data_query" and is_followup:
    intent = detect_intent(rewritten_q) # topic-expanded (e.g. "total amount sales orders 2014")
```

Follow-up queries often lose ERP entity keywords ("so what is the total?" has no entity).
The rewritten query (from `rewrite_query()`) re-adds the topic → correct detection.

When intent is upgraded via rewrite, log: `[intent] data_query via rewrite: '...'`

## Query Passed to `run_data_query`

For follow-ups, pass `_rewritten_q` (not `q.text`) so the LLM has full context:

```python
_data_query = _rewritten_q if is_followup and _rewritten_q != q.text else q.text
```

## Round 3 Prompt Rules

Applied in `run_data_query()` after tool results are returned:

1. Result in 1–2 plain sentences — **no bold `Label: value`** if already stated in sentence
2. **ALL monetary amounts MUST include currency code** (e.g. `66,197,143.79 SGD`) — from `curr_short_forex`
3. Markdown table if multiple rows
4. One blank line before closing
5. Exactly **ONE friendly closing question** — no bullet list, no intro heading

## SSE Event Structure

```
status  → language-aware ("Querying ERP data..." / "Đang truy vấn dữ liệu ERP...")
intro   → main answer (rsplit on last \n\n to separate from closing)
closing → friendly question — rendered same as RAG path (border-top CSS)
total   → {total: 0}
meta    → {sources: [], version_ids: []}
done    → {}
```

The `intro`/`closing` split mirrors the RAG path — frontend renders both identically.

## Timeout & Retry

- `call_ollama_chat` default timeout: **120s** (was 60s)
- Automatic retries: **2** on `TimeoutError` / `OSError`
- On exhaustion: language-aware user-facing error message (no crash)

## Ollama SQL Logger (orm-fetch.js)

Every `db.query()` wrapped in `dbQuery()` — prints to stdout:
```
[SQL] count/sales
  SELECT ... WHERE masterfn = 'x' AND ...
  → 1 row(s)  12ms
```
Params `$1`, `$2`… resolved to actual values for readability.
