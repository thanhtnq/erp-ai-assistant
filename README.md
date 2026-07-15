# Globe3 ERP AI Assistant V2

Multi-tenant chatbot with RAG knowledge base + live ERP data queries.

---

## Architecture

```
documents/ (docx/pdf)  ──► ingest_knowledge.py ──► SQLite (erp_knowledge.db)
PostgreSQL tickets      ──► ingest_tickets.py   ──► + ChromaDB (chroma_db/)
                                                          │
User query ──► POST /chat/stream ──► intent detection     │
                                 ──► ambiguity check       │
                                 ──► hybrid search ────────┘
                                 ──► Gemini LLM → SSE stream

Live ERP queries ──► skills/ (Node.js) ──► PostgreSQL
                       ├─ globe3-sales   (list/count/aggregate sales docs)
                       └─ globe3-analyst (ad-hoc Text-to-SQL)
```

**Key services:**

| Service | Default URL | Required |
|---|---|---|
| FastAPI server | `http://localhost:8000` | Yes |
| Gemini API | `generativelanguage.googleapis.com` | Yes (API key) |
| Skills server | `http://localhost:3001` | For live ERP data |
| PostgreSQL | `localhost:5432` | For ingest + skills |

---

## Prerequisites

- **Python 3.10+** with `venv`
- **Node.js 18+** and `npm`
- **Gemini API key** — get one at [aistudio.google.com](https://aistudio.google.com)
- **PostgreSQL** — required for ticket ingest and skills; optional for knowledge-only setup

---

## First-Run Setup (step by step)

### Step 1 — Python environment

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / Mac

pip install -r requirements.txt
```

### Step 2 — Configure environment

```bash
copy .env.example .env
```

Edit `.env` and fill in your values:

```env
GEMINI_API_KEY=your-gemini-api-key-here
CHAT_API_KEY=change-this-to-a-strong-random-string
PG_HOST=localhost
PG_DBNAME=your-database-name
PG_USER=postgres
PG_PASSWORD=your-postgres-password
```

### Step 3 — Initialize the knowledge database (run once)

```bash
python knowledge_schema.py
```

Creates `data/erp_knowledge.db` with the 4-tier schema.
Skip if the file already exists.

### Step 4 — Test embedding (verify API key works)

```bash
python -c "from embedding_helper import test_embedding; test_embedding()"
# Expected: [embed] OK — dims: 3072
```

If this fails, check `GEMINI_API_KEY` in `.env`.

### Step 5 — Ingest documents

Place your DOCX/PDF files under `documents/_global/{Domain}/` then run:

```bash
cd ingest
python ingest_knowledge.py
```

Valid domain names: `Sales`, `Purchase`, `Finance`, `Inventory`, `CRM`,
`Human Resources`, `Project`, `Fixed Assets`, `Service Manager`, `General`

### Step 6 — Start the API server

```bash
# From project root (activate venv first)
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

API is live at `http://localhost:8000`.
All endpoints require header `X-API-Key` matching your `CHAT_API_KEY`.

### Step 7 (optional) — Start the Skills server (live ERP data)

```bash
cd skills
npm install
node server.js        # starts on port 3001
```

Required only when chat intent is `data_query` (live PostgreSQL queries).

---

## Daily Operation

```bash
# Activate venv, then:
uvicorn api:app --host 0.0.0.0 --port 8000 --reload   # API
cd skills && node server.js                             # Skills (optional)
python schedule/scheduler.py                            # Auto-ingest daemon (optional)
```

---

## SCM Training / Sales Analytics

This repo also includes an SCM sales training module migrated from the standalone
AI Training System. Its purpose is to analyze `scm_sal_main` and `scm_sal_data`
data for customer, product, revenue, trend, churn, and forecast use cases.

The module reuses the main `.env` PostgreSQL settings (`PG_HOST`, `PG_DBNAME`,
`PG_USER`, `PG_PASSWORD`) and writes generated datasets/models under a scoped
folder:

```text
data/scm_training/{PG_DBNAME}/{masterfn}/{companyfn-or-_all_companies}/
```

`masterfn` is the required client scope. `companyfn` is optional for training a
specific entity; omit it to train all entities under one `masterfn`. Chat queries
use the `masterfn/companyfn` sent by the frontend cookies, so there is no
hard-coded company scope.

### Commands

```bash
# Extract and transform SCM sales datasets
python -m scm_training.main extract --masterfn <cookmfnunique> --companyfn <cookcfnunique>

# Optional date range
python -m scm_training.main extract --masterfn <cookmfnunique> --companyfn <cookcfnunique> --date-from 2025-01-01 --date-to 2025-12-31

# Train churn + forecast models
python -m scm_training.main train --model all --masterfn <cookmfnunique> --companyfn <cookcfnunique>

# Query processed datasets
python -m scm_training.main query --masterfn <cookmfnunique> --companyfn <cookcfnunique> --query "Top customers by purchases"
python -m scm_training.main query --masterfn <cookmfnunique> --companyfn <cookcfnunique> --query "Revenue for February 2010"

# Product potential / trend analysis
python -m scm_training.main trend --masterfn <cookmfnunique> --companyfn <cookcfnunique> --days 90 --top 10

# Standalone SCM training scheduler
python -m scm_training.main scheduled
```

### Features

- Extract sales headers and line items from `scm_sal_main` and `scm_sal_data`
- Build processed Parquet datasets for customer, product, sales trend, retention,
  and revenue-by-date analysis
- Train ML models for customer churn prediction and sales revenue forecasting
- Analyze top potential products using recent growth, momentum, consistency,
  revenue, and customer reach
- Query processed datasets with a lightweight prompt-style interface

Generated files are ignored by git:

```text
data/scm_training/<database>/<masterfn>/<companyfn>/processed/
data/scm_training/<database>/<masterfn>/<companyfn>/models/
data/scm_training/<database>/<masterfn>/<companyfn>/analysis/
logs/scm_training/
```

Note: this module is currently a separate training/analytics pipeline. The live
chat data-query path still goes through `skills/` for live ERP lookups. SCM
training/analytics questions such as churn, forecast, potential products, and
revenue-by-month are routed to the scoped SCM training artifacts when available.

---

## Ingest Pipeline

### Ingest documents (docx / pdf)

```bash
cd ingest
python ingest_knowledge.py              # normal run (skips unchanged files)
python ingest_knowledge.py --dry-run    # preview — no DB writes
python ingest_knowledge.py --force      # re-ingest all files
python ingest_knowledge.py --workers 1  # sequential (debug mode)
python ingest_knowledge.py --file path/to/file.docx   # single file
```

**How it works:** DOCX/PDF → Markdown (via markitdown) → heading-based sections →
steps extracted by positional heuristic → Gemini embeddings (REST) → ChromaDB + SQLite.
No LLM calls during ingest — ~10× faster than v1.

Document scope via path:
- `documents/_global/{Domain}/` — shared across all companies
- `documents/clients/{COMPANY_CODE}/{Domain}/` — company-specific

### Rebuild ChromaDB without re-ingesting

If ChromaDB is missing or was deleted (e.g. after switching embedding models):

```bash
# Delete old vector store first
rmdir /s /q data\chroma_db       # Windows
# rm -rf data/chroma_db          # Linux / Mac

python rebuild_chroma.py
```

Reads all entry versions from `erp_knowledge.db` and re-embeds them. No LLM calls.

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
Logs: `schedule/scheduler.log`, `schedule/ingest_knowledge.log`, `schedule/ingest_tickets.log`

---

## Configuration

### Scheduled fraud detection

The fraud engine is a background analytics module, not a chatbot. It reads the previous
30 days, builds per-user baselines, evaluates independent rules, and stores idempotent
alerts in `fraud_alert`. Configure `FRAUD_SCHEDULER_SCOPES` as a JSON array of
`masterfn`/`companyfn` objects and enable the job with `FRAUD_SCHEDULER_ENABLED=true`.
The scheduler starts automatically inside FastAPI and stops with the API process; a
separate `schedule/scheduler.py` process is not required for fraud detection.

ERP installations must provide the read-only normalized view named by
`FRAUD_TRANSACTION_VIEW`. Required columns are `masterfn`, `companyfn`,
`transaction_id`, `user_id`, `occurred_at`, `created_at`, `amount`, `discount`,
`refund_count`, `void_count`, `invoice_modifications`, and JSON `metadata`. This adapter
boundary avoids guessing customer-specific ERP audit fields and allows a future model to
replace the rule engine without changing alert storage or APIs.

Active alerts are exposed at `GET /api/fraud-alerts`; detail and acknowledge, resolve,
or hide actions are under `/api/fraud-alerts/{id}`. All calls require company scope and
the existing API-key authentication.

### Environment variables (`.env` at project root)

| Variable | Used by | Notes |
|---|---|---|
| `GEMINI_API_KEY` | api.py, ingest | Required — Gemini LLM + embeddings |
| `CHAT_API_KEY` | api.py | `X-API-Key` header for all chat requests |
| `PG_HOST` | ingest, skills | Default: `localhost` |
| `PG_PORT` | ingest, skills | Default: `5432` |
| `PG_DBNAME` | ingest, skills | ERP source database |
| `PG_USER` | ingest, skills | Default: `postgres` |
| `PG_PASSWORD` | ingest, skills | |
| `SKILLS_SERVER_URL` | api.py | Default: `http://localhost:3001` |
| `LLM_WORKERS` | ingest | Parallel embed threads (default: `4`) |

Config source: `ingest/ingest_config.py` — single file for all model names, paths, and tuning constants.

### Models

| Role | Model |
|---|---|
| Chat + admin tasks | `gemini-2.0-flash` |
| Document ingest / classification | *(no LLM — heading heuristic)* |
| Ticket classification | `gemini-2.0-flash` |
| Embeddings | `gemini-embedding-001` (3072 dims) |
| Reranker | `ms-marco-MiniLM-L-6-v2` (local CrossEncoder) |

---

## Skills Server (Live ERP Data)

The skills server runs separately from the Python API.

```bash
cd skills
npm install
node server.js        # starts on port 3001
```

The Python API calls `http://localhost:3001` (override via `SKILLS_SERVER_URL` env var) when chat intent is `data_query`.

### Available skill modules

| Module | Folder | Purpose |
|---|---|---|
| globe3-sales | `skills/globe3-sales/` | List, count, aggregate sales documents — invoices, quotations, orders, credit notes, etc. |
| globe3-analyst | `skills/globe3-analyst/` | Ad-hoc Text-to-SQL — custom SELECT queries with auto-injected company scope |

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
| Health | Live service status — Gemini API, ChromaDB, PostgreSQL, skills |
| Analytics | User activity — messages, feedback trends, top queries, per-user table |

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
rebuild_chroma.py         Rebuild ChromaDB from SQLite without re-running LLM
embedding_helper.py       ChromaDB + Gemini embeddings (REST) + CrossEncoder reranker
ROLE.md                   LLM system prompt — assistant behavior + guardrails
globe3-ui.css             Design system CSS
.env.example              Environment variable template — copy to .env

ingest/
  ingest_knowledge.py     Parse docx/pdf → Markdown → sections → embed → SQLite + ChromaDB
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
  chroma_db/              ChromaDB vector store (rebuild with rebuild_chroma.py)

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
