# CLAUDE.md

Globe3 ERP AI Assistant V2 — multi-tenant chatbot with RAG knowledge base + live ERP data queries.

**External requirements:** Ollama at `http://localhost:11434`, PostgreSQL (optional for ingest, required for skills/).

## Quick Start

```bash
venv\Scripts\activate
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

## Key Commands

```bash
# One-time setup
python knowledge_schema.py
ollama pull qwen3.5:cloud && ollama pull qwen3.5:397b-cloud && ollama pull qwen3-embedding:0.6b

# Ingest
cd ingest
python ingest_knowledge.py [--dry-run] [--force] [--workers 1]
python ingest_tickets.py [--company ABC] [--limit 50] [--dry-run]

# Scheduler
python schedule/scheduler.py [--run-now] [--status]

# Debug
cd debug && python check_knowledge.py [--domain Sales] [--search "term"] [--flagged]

# Skills (Node.js)
cd skills && npm install
```

## Architecture at a Glance

```
documents/ ──► ingest_knowledge.py ──► SQLite + ChromaDB
PG tickets ──► ingest_tickets.py   ──┘
                                        │
User query ──► /chat/stream ──► rewrite → intent → ambiguity check → hybrid search → LLM → SSE stream

Live ERP queries ──► skills/ (Node.js) ──► PostgreSQL
                       ├─ skill tools (list/count/aggregate)
                       └─ run_query (Text-to-SQL with safety layer)
```

## Critical File Map

| File | Role |
|---|---|
| `api.py` | FastAPI server — all endpoints, chat pipeline, admin (Phases 1–6 complete) |
| `ingest/ingest_config.py` | Single config source — models, paths, PG, tuning |
| `ROLE.md` | LLM system prompt — assistant behavior + guardrails |
| `knowledge_schema.py` | SQLite schema init |
| `embedding_helper.py` | ChromaDB + Ollama embeddings + CrossEncoder |
| `skills/_shared/orm-fetch.js` | Unified ERP DB access for all skill tools |
| `skills/_shared/query-safety.js` | SQL validation + masterfn/companyfn scope injection |
| `globe3-ui.css` | Design system CSS — import into every new UI |
| `admin_dashboard.cfm` | Admin UI — Feedback · Action Log · Documents · Scheduler · Knowledge · Health · Analytics (Phases 1–6 complete) |
| `schedule/scheduler_state.json` | Scheduler runtime state — job configs + last run info (written by scheduler + API) |
| `.claude/STYLE_GUIDE.md` | Full UI design rules |

## Detailed Rules

See `.claude/rules/` for topic-specific guidance:

| File | Covers |
|---|---|
| `00-coding-behavior.md` | Meta-level rules — think first, simplicity, surgical changes, goal-driven execution |
| `01-architecture.md` | Data flow, search pipeline, multi-tenancy, company scope |
| `02-database.md` | SQLite schema, PostgreSQL config, ERP table reference |
| `03-ingest.md` | Ingest pipeline phases, config constants, commands |
| `04-api.md` | All endpoints, chat pipeline, admin dashboard |
| `05-frontend.md` | Templates, standalone vs embedded, bot avatar, widget |
| `06-ui-design.md` | Colors, typography, components, deploy checklist |
| `07-skills.md` | Skill architecture, run_query safety, orm-fetch, doc links |
| `08-data-query.md` | data_query pipeline — intent detection, follow-up context, response format |

## Session Memory

Persistent memory across conversations is stored in:
`.claude/memory/MEMORY.md`

Check this file first when starting a new session — it indexes key project decisions, confirmed patterns, and user preferences that are not derivable from reading the code alone.

## Update Convention

When the user says **"cập nhật CLAUDE.md"**, automatically update BOTH:
1. `CLAUDE.md` — add/modify the relevant section
2. `.claude/memory/` — create or update the relevant memory file(s) in the memory folder

Always keep both in sync. CLAUDE.md is the quick-reference; memory files are the detailed record.
