# Globe3 ERP AI Assistant V2

Multi-tenant chatbot with RAG knowledge base + live ERP data queries.

---

## Architecture

```
documents/ (docx/pdf)  ──► ingest_knowledge.py ──► SQLite (erp_knowledge.db)
PostgreSQL tickets      ──► ingest_tickets.py   ──► + ChromaDB (chroma_db/)
                                                          │
User query ──► POST /chat/stream ──► intent detection     │
                                 ──► hybrid search ────────┘
                                 ──► LLM (Ollama) → SSE stream

Live ERP queries ──► skills/ (Node.js) ──► PostgreSQL
                       ├─ globe3-sales   (list/count/aggregate sales docs)
                       └─ globe3-analyst (ad-hoc Text-to-SQL)
```

**Key services:**

| Service | Default URL | Required |
|---|---|---|
| FastAPI server | `http://localhost:8000` | Yes |
| Ollama | `http://localhost:11434` | Yes |
| Skills server | `http://localhost:3001` | For live ERP data |
| PostgreSQL | `localhost:5432` | For ingest + skills |

---

## Prerequisites

- **Python 3.10+** with `venv`
- **Node.js 18+** and `npm`
- **Ollama** — [ollama.com](https://ollama.com)
- **PostgreSQL** — required for ticket ingest and skills; optional for knowledge-only setup

---

## Quick Start

### 1. Python environment

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / Mac

pip install -r requirements.txt
```

### 2. Pull Ollama models

```bash
ollama pull qwen3.5:cloud          # chat model (API)
ollama pull qwen3.5:397b-cloud     # ingest / classify model
ollama pull qwen3-embedding:0.6b   # embedding model
```

### 3. Initialize the knowledge database

```bash
python knowledge_schema.py
```

Creates `data/erp_knowledge.db` with the 4-tier schema (companies → domains → features → entries → versions).

### 4. Start the API server

```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

API is live at `http://localhost:8000`. All endpoints require header `X-API-Key: erp-ai-secret-key-change-me`.

---

## Skills Server (Live ERP Data)

The skills server runs separately from the Python API. It connects to PostgreSQL and serves live ERP data queries.

```bash
cd skills
npm install
node server.js        # starts on port 3001
```

The Python API calls `http://localhost:3001` when the chat intent is `data_query`.

### Available skill modules

| Module | Folder | Purpose |
|---|---|---|
| globe3-sales | `skills/globe3-sales/` | List, count, aggregate sales documents — invoices, quotations, orders, credit notes, etc. |
| globe3-analyst | `skills/globe3-analyst/` | Ad-hoc Text-to-SQL — custom SELECT queries with auto-injected company scope |

### PostgreSQL connection (skills)

The skills server reads connection settings from environment variables, with these defaults:

| Variable | Default |
|---|---|
| `PG_HOST` | `localhost` |
| `PG_PORT` | `5432` |
| `PG_DBNAME` | `v57udemo2011_tno` |
| `PG_USER` | `postgres` |
| `PG_PASSWORD` | `123` |

Set variables in your shell or a `.env` file before starting the server:

```bash
export PG_HOST=myserver
export PG_DBNAME=mydb
export PG_USER=myuser
export PG_PASSWORD=mypassword
node server.js
```

---

## Configuration

### Environment variables (Python API + ingest)

All variables have working defaults. Override only what differs from your environment.

| Variable | Default | Used by |
|---|---|---|
| `OLLAMA_URL` | `http://localhost:11434` | api.py, ingest |
| `PG_HOST` | `localhost` | ingest, skills |
| `PG_PORT` | `5432` | ingest, skills |
| `PG_DBNAME` | `v57udemo2011_tno` | ingest, skills |
| `PG_USER` | `postgres` | ingest, skills |
| `PG_PASSWORD` | `123` | ingest, skills |
| `LLM_WORKERS` | `4` | ingest (parallel LLM calls) |

Config source: `ingest/ingest_config.py` — single file for all paths, model names, and tuning constants.

### API-level constants (in `api.py`)

| Constant | Value | Notes |
|---|---|---|
| `LLM_MODEL` | `qwen3.5:cloud` | Model used for chat responses |
| `API_KEY` | `erp-ai-secret-key-change-me` | Change before deploying |
| `MAX_ENTRIES` | `5` | Max knowledge chunks sent to LLM |
| `SKILLS_URL` | `http://localhost:3001` | Override via `SKILLS_SERVER_URL` env var |

---

## Ingest Pipeline

### Ingest documents (docx / pdf)

```bash
cd ingest
python ingest_knowledge.py              # normal run
python ingest_knowledge.py --dry-run    # preview — no DB writes
python ingest_knowledge.py --force      # skip hash check, re-ingest all
python ingest_knowledge.py --workers 1  # sequential (debug mode)
```

Place documents in:
- `documents/_global/{Domain}/` — shared across all companies
- `documents/clients/{COMPANY_CODE}/{Domain}/` — company-specific

Valid domain names: `Sales`, `Purchase`, `Finance`, `Inventory`, `CRM`, `Human Resources`, `Project`, `Fixed Assets`, `Service Manager`, `General`

### Ingest support tickets (from PostgreSQL)

```bash
cd ingest
python ingest_tickets.py                       # all companies
python ingest_tickets.py --company ABC         # one company
python ingest_tickets.py --limit 50            # limit rows
python ingest_tickets.py --dry-run             # preview
python ingest_tickets.py --workers 4           # parallel threads
```

Fetches from `prj_pbill_main WHERE tag_closed03_yn = 'y'` (closed tickets only).

### Scheduler (automated ingest)

```bash
python schedule/scheduler.py            # start daemon
python schedule/scheduler.py --run-now  # run both jobs immediately
python schedule/scheduler.py --status   # check job state
```

Default schedule: documents at `02:00` daily, tickets at `03:00` daily.  
Configure via the Admin Dashboard → **Scheduler** tab, or edit `schedule/scheduler_state.json`.

Logs: `schedule/scheduler.log`, `schedule/ingest_knowledge.log`, `schedule/ingest_tickets.log`

---

## Frontend Templates

| File | Mode | Notes |
|---|---|---|
| `chatbox.html` | Standalone | Floating card, `max-width: 860px` — open directly in browser |
| `ai_assistant.cfm` | Embedded | Full-width iframe inside ColdFusion page |
| `widget_ai_assistant.cfm` | Widget | Floating button + slide-up panel |

All templates read three cookies for multi-tenancy: `cookuserloginid` (user ID), `cookmfnunique` (masterfn), `cookcfnunique` (companyfn).

---

## Admin Dashboard

Open `admin_dashboard.cfm` in a ColdFusion-enabled server or view via the web app.

| Tab | Purpose |
|---|---|
| Feedback | Review thumbs up/down, flag and resolve bad answers |
| Action Log | Full audit trail of admin actions |
| Documents | Document registry — status, re-ingest trigger |
| Scheduler | Enable/disable, configure schedule, run now |
| Knowledge | Browse all entries with full version detail |
| Health | Live service status — Ollama, ChromaDB, PostgreSQL, skills |
| Analytics | User activity — messages, feedback trends, top queries, per-user table |

---

## Testing

The project includes a comprehensive test suite with **50 unit tests** covering:
- Intent detection (data_query, procedure, error_fix, faq, reference)
- Query rewriting and navigation
- Topic extraction from conversation history
- HTTP error handling (including HTTP 500 graceful fallback)
- Response parsing
- User preferences detection
- The specific "Top 10 best selling products" query fix

### Run All Tests

**Important:** Tests must be run with the virtual environment activated.

```bash
# Windows
run_tests.bat

# Linux/Mac
chmod +x run_tests.sh
./run_tests.sh

# Or manually
.\venv\Scripts\activate    # Windows
# source venv/bin/activate  # Linux/Mac
python -m unittest discover -s tests -p "test_*.py" -v
```

### Test Structure

```
tests/
  __init__.py
  test_api.py                    # 45 tests for core functionality
  test_best_selling_query.py     # 5 tests for the HTTP 500 fix
```

---

## Debug Tools

```bash
cd debug
python check_knowledge.py                    # overview of all entries
python check_knowledge.py --domain Sales     # filter by domain
python check_knowledge.py --search "invoice" # keyword search
python check_knowledge.py --flagged          # flagged entries only
```

---

## Project Structure

```
api.py                    FastAPI server — all endpoints + chat pipeline
knowledge_schema.py       SQLite schema init (run once)
embedding_helper.py       ChromaDB + Ollama embeddings + CrossEncoder reranker
ROLE.md                   LLM system prompt — assistant behavior + guardrails
globe3-ui.css             Design system CSS

ingest/
  ingest_knowledge.py     Parse docx/pdf → LLM classify → SQLite + ChromaDB
  ingest_tickets.py       Fetch PG tickets → LLM classify → upsert
  ingest_config.py        Single config source — models, paths, PG, tuning

schedule/
  scheduler.py            Background daemon — runs ingest on schedule
  scheduler_state.json    Job config + last run state

skills/
  package.json            Node.js deps (express, pg, node-sql-parser)
  server.js               Express server — routes requests to skill modules
  _shared/
    orm-fetch.js          Unified DB access — list/count/aggregate/runQuery
    query-safety.js       SQL validation + masterfn/companyfn scope injection
  globe3-sales/
    tools.js              list/get/count/aggregate_sales_documents
    SKILL.md              LLM instruction card
  globe3-analyst/
    tools.js              run_query tool
    SKILL.md              Schema reference + query rules

data/
  erp_knowledge.db        SQLite — knowledge base (domains, features, entries)
  chat_history.db         SQLite — conversation history + feedback + preferences
  chroma_db/              ChromaDB vector store

documents/
  _global/                Global knowledge docs (shared across all companies)
  clients/                Company-specific docs

document_images/          Images extracted from docx/pdf during ingest
debug/                    Debug + inspection scripts
```

---

## Adding a New Skill Module

1. Create `skills/globe3-{module}/` with `tools.js` and `SKILL.md`
2. Add the model definition to `MODELS` in `skills/_shared/orm-fetch.js`
3. Register new tools in `skills/server.js`
4. If the module queries a new table, add it to `ALLOWED_TABLES` in `skills/_shared/query-safety.js`

Each model entry in `MODELS` defines: `table`, `masterfn_field`, `companyfn_field`, `pk`, `select_cols`, `allowed_filters`, `allowed_sorts`, `allowed_groups`, `default_filters`.
