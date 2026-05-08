---
name: Chat Pipeline — Ambiguity Check
description: check_ambiguity() step in /chat/stream — when it runs, skip conditions, fail-open behavior, SSE output
type: project
---

## Ambiguity Check (`check_ambiguity()` in `api.py` ~line 1462)

Added as step 5 of the `/chat/stream` pipeline, between `detect_intent()` and `search_knowledge()` / `run_data_query()`.

**Why:** Vague queries like "bị lỗi", "không được", "cách tạo?" caused incorrect or unhelpful answers. The check uses query + full chat history as context to decide if the question is specific enough before searching.

**How to apply:** If touching the chat pipeline or adding new intent types, be aware this check runs for ALL intents. Design new features accordingly.

### Logic

```
rewrite_query() → detect_intent()
  → check_ambiguity(rewritten_q, history_text, intent, lang)
      ├─ SKIP if navigation_type is set (step navigation — context is clear)
      ├─ ambiguous=True  → yield clarifying question SSE + save to history + return
      └─ ambiguous=False → continue to data_query or RAG path
```

### `check_ambiguity()` details

- Input: `_rewritten_q` (post-rewrite, has topic context from history), `history_text`, `intent`, lang code
- LLM call: `call_gemini_chat()`, retries=0
- **Fail open:** any exception → `{"ambiguous": False}` — never blocks the user
- Output JSON: `{"ambiguous": bool, "question": str | null}`

### SSE output when ambiguous

```
status  → "Cần thêm thông tin..." / "Need more information..."
intro   → the clarifying question text
total   → {total: 0}
meta    → {sources: [], version_ids: []}
done    → {}
```

Clarifying question is saved to `chat_history` so next user reply has context.
