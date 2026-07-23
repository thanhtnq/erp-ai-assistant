# Context-First Chat Deploy Checklist

Use this when deploying the context-first chatbox changes to local/server.

## Files To Deploy

Backend:

- `api.py`
- `api/chat.py`
- `api/database.py`
- `api/llm.py`
- `api/routers/chat.py`
- `api/search.py`
- `api/semantic/retrieval.py`
- `api/conversation_state.py`

Frontend/admin:

- `cfml-examples/ai_assistant.cfm`
- `cfml-examples/admin_dashboard.cfm`

Smoke scripts:

- `scripts/context_scale_smoke.py`
- `scripts/chat_http_load_smoke.py`
- `scripts/package_context_first_deploy.py`

Do not deploy runtime-only files as feature changes:

- `data/scheduler_state.json`
- `*.log`
- `api-server*.log`
- `skills-server*.log`

## Server Steps

1. Pull/copy the changed source files.
2. Install/update Python requirements if needed.
3. Restart the FastAPI API process.
4. Restart the Node skills server.
5. Open the chatbox and run the manual QA below.

To build a copyable ZIP from local:

```bash
python scripts/package_context_first_deploy.py --out context-first-deploy.zip
```

The chat database migration is automatic on API startup. It creates:

- `chat_history.session_id`
- `chat_sessions`
- `chat_result_context`
- session/result-context indexes

## Smoke Commands

Run this without starting HTTP server:

```bash
python scripts/context_scale_smoke.py --users 1000 --messages 4
```

Run this after FastAPI is already running:

```bash
python scripts/chat_http_load_smoke.py --url http://127.0.0.1:8000/chat/stream --requests 50 --concurrency 10
```

If your server uses a custom API key:

```bash
python scripts/chat_http_load_smoke.py --url http://127.0.0.1:8000/chat/stream --api-key "$CHAT_API_KEY" --requests 50 --concurrency 10
```

## Manual QA

Run these in one chat session:

```text
list of sale order 6/2026
driver infor tab SOB10344933
SOB10344932 this one
show detail
show pie chart
```

Expected:

- `driver infor` still routes to Sales Order Driver Info.
- `SOB... this one` reuses the previous tab context.
- `show detail` reuses the previous Sales Order document.
- Chart follow-up renders from the previous table when frontend has chart context.
- No answer exposes `uniquenum_pri`, `masterfn`, `companyfn`, or other internal keys.
