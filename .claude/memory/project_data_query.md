---
name: Data Query Pipeline
description: How data_query intent works — detection, follow-up context, Round 3 prompt format rules
type: project
originSessionId: f63f54d9-5d34-44e5-9bb2-c7fa26764c3f
---
Live ERP data path in `api.py` — bypasses RAG, calls Node.js skills server.

**Why:** Separate from RAG path so live DB queries don't get mixed with knowledge-base lookups.

**How to apply:** When modifying intent detection, follow-up handling, or response formatting for data queries.

## Intent Detection (`detect_intent`)
- Runs on **original** query first
- If not `data_query` AND `is_followup=True`: also runs on **rewritten** query (topic-expanded)
- Rewritten query used when follow-up loses ERP entity keywords (e.g. "so what is the total?" → "total amount sales orders 2014")
- Log line: `[intent] data_query via rewrite: '...'`

## Follow-up Context
- `rewrite_query()` expands short follow-ups with topic from history
- `_rewritten_q` passed to `run_data_query` (not original `q.text`) when `is_followup=True`
- History text always passed to `run_data_query` for context

## Round 3 Prompt Rules (enforced in `run_data_query`)
1. Result in 1–2 plain sentences — no redundant bold `**Label: value**`
2. **ALL monetary amounts must include currency code** (e.g. `66,197,143.79 SGD`) — from `curr_short_forex` field
3. Markdown table if multiple rows
4. Blank line before closing
5. Exactly ONE friendly closing question (no bullet list)
6. No intro line to suggestions

## SSE Event Structure (data_query path)
```
status  → "Querying ERP data..."
intro   → main answer text (rsplit on last \n\n)
closing → friendly question (split from intro on last blank line)
total   → {total: 0}
meta    → {sources: [], version_ids: []}
done    → {}
```
Mirrors RAG path structure → same CSS styling for closing.

## Timeout Handling
- `call_ollama_chat` timeout: 120s (up from 60s)
- Retries: 2 automatic retries on TimeoutError/OSError
- On exhaustion: friendly user-facing error message (language-aware)
