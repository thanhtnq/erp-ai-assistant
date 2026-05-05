---
description: Document and ticket ingest pipelines, scheduler, and config constants
---

# Ingest Pipeline

## Document Ingest (`ingest/ingest_knowledge.py`)

3 phases per file:

1. **Phase A (serial)** — walk sections, `get_or_create_feature/entry`, MD5 hash change detection, collect entries needing LLM
2. **Phase B (parallel)** — `ThreadPoolExecutor(max_workers=LLM_WORKERS)` calls `parse_with_llm()` for all pending entries
3. **Phase C (serial)** — DB writes (1 commit per entry), then `batch_upsert_entries()` for all ChromaDB upserts

Document scope via path:
- `documents/_global/{Domain}/` → global (all companies)
- `documents/clients/{COMPANY}/{Domain}/` → company-specific

## Ticket Ingest (`ingest/ingest_tickets.py`)

Same 3-phase pattern. Fetches from `prj_pbill_main` where `tag_closed03_yn = 'y'`.  
LLM classifies each ticket into domain, feature, entry_type, steps, notes.  
Minimum lengths: description ≥ 20 chars, solution ≥ 20 chars.

## Scheduler (`schedule/scheduler.py`)

Background daemon — runs both ingest jobs in non-blocking threads.

```bash
python schedule/scheduler.py            # start daemon
python schedule/scheduler.py --run-now  # run both jobs immediately
python schedule/scheduler.py --status   # check state
```

Logs: `schedule/scheduler.log`, `schedule/ingest_knowledge.log`, `schedule/ingest_tickets.log`

## Configuration (`ingest/ingest_config.py`)

Single source of truth. All paths are absolute via `Path(__file__)`.

```python
LLM_MODEL_INGEST  = "qwen3.5:397b-cloud"   # ingest/classify model
EMBEDDING_MODEL   = "qwen3-embedding:0.6b"  # vector embedding
VECTOR_TOP_K      = 20     # ChromaDB candidates before reranking
RERANK_TOP_N      = 3      # final results sent to LLM
LLM_WORKERS       = 4      # parallel threads (match OLLAMA_NUM_PARALLEL)
MAX_LLM_RETRIES   = 3      # Ollama timeout retries
EMBED_BATCH_SIZE  = 10     # texts per /api/embed call
CHROMA_BATCH_SIZE = 100    # items per ChromaDB upsert
```

API-level constants (defined inline in `api.py`):
```python
LLM_MODEL   = "qwen3.5:cloud"
API_KEY     = "erp-ai-secret-key-change-me"   # X-API-Key header required
MAX_ENTRIES = 5
```

## Commands

```bash
cd ingest
python ingest_knowledge.py                    # normal run
python ingest_knowledge.py --dry-run          # preview, no DB writes
python ingest_knowledge.py --force            # skip hash check
python ingest_knowledge.py --workers 1        # sequential/debug

python ingest_tickets.py [--company ABC] [--limit 50] [--dry-run] [--workers 4]
```
