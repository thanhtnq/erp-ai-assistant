---
description: System architecture, data flow, key files, and multi-tenancy model
alwaysApply: true
---

# Architecture

## Data Flow

```
documents/ (docx/pdf)  ──► ingest_knowledge.py ──► SQLite (erp_knowledge.db)
PostgreSQL tickets      ──► ingest_tickets.py   ──► + ChromaDB (chroma_db/)
                                                          │
User query ──► POST /chat/stream ──► intent detection
                                 ──► hybrid search (vector → rerank → SQL fallback)
                                 ──► LLM (Gemini) → SSE streaming response
                                 ──► chat_history.db
```

## Key Files

| File | Role |
|------|------|
| `api.py` | FastAPI server — all endpoints, search pipeline, LLM integration |
| `embedding_helper.py` | ChromaDB, Gemini embeddings, CrossEncoder reranker |
| `knowledge_schema.py` | SQLite schema init (run once) |
| `ingest/ingest_config.py` | **Single config source** — models, DB paths, PG, tuning |
| `ROLE.md` | System prompt — assistant behavior and guardrails |
| `ingest/ingest_knowledge.py` | Parse docx/pdf → LLM classify → upsert DB |
| `ingest/ingest_tickets.py` | Fetch PG tickets → LLM classify → upsert |
| `schedule/scheduler.py` | Background daemon — parallel ingest threads |
| `skills/` | Node.js skill modules for live ERP data queries |
| `globe3-ui.css` | Design system CSS — import into every new layout |

## Search Pipeline (`search_knowledge()` in api.py)

1. **Intent detection** — `error_fix | procedure | faq | reference | any`
2. **Feature scope** — keyword-match domain/feature names to narrow search
3. **Vector search** — ChromaDB top-K (company + feature filters)
4. **Reranking** — CrossEncoder `ms-marco-MiniLM-L-6-v2`, trim to top-N
5. **SQL fallback** — keyword SQLite search if vector returns nothing
6. **Flagged entry handling** — bad-feedback entries fall back to ticket results

## Multi-Tenancy (Knowledge Base)

- `company_id = NULL` → global knowledge (shared across all tenants)
- `company_id = 'ABC'` → company-specific (takes priority over global)
- Document scope via path: `documents/_global/` vs `documents/clients/ABC/`

## Company Scope (Live ERP Queries — skills/)

Two separate identifiers must **always** be applied together:

| Field | Cookie | Meaning |
|---|---|---|
| `masterfn` | `cookmfnunique` | Client identifier — one per customer |
| `companyfn` | `cookcfnunique` | Entity/subsidiary — one client, many entities |

Both are injected automatically by `_shared/query-safety.js` and `orm-fetch.js`. Never rely on only one.

## Multi-Turn Conversation

- Last 6 messages stored per `user_id + company_id` in `chat_history.db`
- `rewrite_query()` injects prior topic into follow-up queries
- Step navigation extracted from history ("next", "previous", "step 3")
- User preferences (language, response length) persist across sessions
