# CLAUDE.md

Globe3 ERP AI Assistant V2 — multi-tenant chatbot with RAG knowledge base + live ERP data queries.

**External requirements:** Gemini API key (`GEMINI_API_KEY` env var), PostgreSQL (optional for ingest, required for skills/).

## Quick Start

```bash
venv\Scripts\activate
# Copy .env.example → .env and fill in GEMINI_API_KEY + DB credentials
# Required env vars: GEMINI_API_KEY, CHAT_API_KEY, PG_*, SKILLS_SERVER_URL
uvicorn api:app --host 0.0.0.0 --port 8000 --reload

# In a separate terminal — required for live ERP data queries:
node skills/server.js
```

## Key Commands

```bash
# One-time setup
python knowledge_schema.py

# Rebuild ChromaDB from SQLite (use after deleting chroma_db/ or switching models)
python rebuild_chroma.py

# Scheduler
python schedule/scheduler.py [--run-now] [--status]

# Debug
cd debug && python check_knowledge.py [--domain Sales] [--search "term"] [--flagged]

# Skills (Node.js — one-time)
cd skills && npm install
```

Full ingest commands → see `rules/03-ingest.md`
Full API endpoints → see `rules/04-api.md`

## Architecture & Files

See `rules/01-architecture.md` — data flow, search pipeline, key files, multi-tenancy, company scope.

**CFML templates + design system:** `../cfml-examples/` (admin_dashboard.cfm, ai_assistant.cfm, widget_ai_assistant.cfm, globe3-ui.css)

## Detailed Rules

See `rules/` for topic-specific guidance:

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
`memory/MEMORY.md`

Check this file first when starting a new session — it indexes key project decisions, confirmed patterns, and user preferences that are not derivable from reading the code alone.

## Update Convention

When the user says **"cập nhật CLAUDE.md"**, automatically update BOTH:
1. `.claude/CLAUDE.md` — add/modify the relevant section
2. `.claude/memory/` — create or update the relevant memory file(s) in the memory folder

Always keep both in sync. CLAUDE.md is the quick-reference; memory files are the detailed record.
