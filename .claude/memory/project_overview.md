---
name: Globe3 ERP AI V2 — Project Overview
description: Stack, ports, key files, quick start commands for the Globe3 chatbot project
type: project
originSessionId: f63f54d9-5d34-44e5-9bb2-c7fa26764c3f
---
Globe3 ERP AI Assistant V2 — multi-tenant hybrid chatbot.

**Why:** RAG knowledge base (procedures/FAQ) + live ERP data queries via Node.js skills.

**How to apply:** Use when starting a new session to orient quickly without re-reading all files.

## Stack
- Python FastAPI (`api.py`) — port 8000, `uvicorn api:app --host 0.0.0.0 --port 8000 --reload`
- Node.js skills server (`skills/server.js`) — port 3001, `node server.js`
- Ollama — port 11434, models: `qwen3.5:cloud` (chat), `qwen3-embedding:0.6b` (embed)
- SQLite: `data/erp_knowledge.db` (knowledge), `data/chat_history.db` (history)
- ChromaDB: `chroma_db/`
- PostgreSQL: ERP source DB (`v57udemo2011_tno`)

## Key Files
| File | Role |
|---|---|
| `api.py` | FastAPI — all endpoints, chat pipeline, intent detection, admin Phase 1–3 |
| `admin_dashboard.cfm` | Admin UI — Feedback · Action Log · Documents · Scheduler |
| `schedule/scheduler_state.json` | Scheduler runtime state (shared between API + scheduler.py daemon) |
| `skills/_shared/orm-fetch.js` | Unified ERP DB access (list/count/aggregate/runQuery) + SQL query logger |
| `skills/_shared/query-safety.js` | SQL validation + masterfn/companyfn injection |
| `skills/globe3-sales/tools.js` | Generic sales tools — all types via tag_table_usage |
| `ai_assistant.cfm` | Embedded chatbot (ColdFusion iframe) |
| `widget_ai_assistant.cfm` | Floating widget wrapper |
| `chatbox.html` | Standalone chatbot |

## Demo Credentials
- masterfn: `demo2011mfn`
- companyfn: `p11011004464072155`
