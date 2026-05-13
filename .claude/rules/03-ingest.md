---
description: Document and ticket ingest pipelines, scheduler, and config constants
---

# Ingest Pipeline

## Document Ingest (`ingest/ingest_knowledge.py`)

**No-LLM pipeline** — uses positional heuristics and rule-based classification (no Gemini calls for documents).

3 phases per file:

1. **Phase A (serial)** — walk sections, `get_or_create_feature/entry`, MD5 hash change detection, collect entries needing embedding. `get_or_create_entry()` always runs before the section-level hash check; for existing entries it UPDATEs `type`, `is_active=1`, and `menu_path` (COALESCE). Returns `was_inactive` flag; hash-check skip is bypassed when `was_inactive=True` to force re-embed (needed when ChromaDB was cleared by Delete All).
2. **Phase B (parallel)** — `ThreadPoolExecutor(max_workers=LLM_WORKERS)` embeds all pending entries
3. **Phase C (serial)** — DB writes (1 commit per entry), then `batch_upsert_entries()` for all ChromaDB upserts

### Entry Type Classification (`classify_type()`)

Heading-first priority — checks heading before content to avoid false positives:

1. **Procedure** — heading starts with or contains an action verb (`creating`, `how to`, `adding`, `configure`, `edit`, `process`, `enter`, `approve`, `generate`, `print`, `post`, `record`, `apply`, `convert`, …)
2. **error_fix** — heading contains error keywords (`error`, `fix`, `issue`, `cannot`, `failed`, `unable`, `bug`, `problem`, `troubleshoot`)
3. **faq** — heading contains (`what is`, `what are`, `difference`, `why`, `faq`, `overview`, `about`)
4. **reference** — heading contains (`list`, `definition`, `glossary`, `status`, `field`, `setup`, `control`, `report`)
5. **Fallback content check** — if none of the above, check `content[:200]` for error keywords → `error_fix`; otherwise → `procedure`

**Key rule:** error/fix keywords are only checked in **heading** (not content) at high priority, so procedure steps that mention "cannot" or "fix" in body text don't get misclassified.

Document scope via path:
- `documents/_global/{Domain}/` → global (all companies)
- `documents/clients/{COMPANY}/{Domain}/` → company-specific

**Domain comes from folder path** — an entry's domain is determined by the folder it's stored in, not from `document_registry.domain`. To change an entry's domain, delete the document and re-upload it to the correct domain folder. Re-ingesting from the same path always keeps the original domain.

**Two-level hash check:**
1. **File-level** (before section loop): if file hash unchanged → skip entire file. Bypassed by `--force` (used by `▶ Now` button in admin dashboard).
2. **Section-level** (after `get_or_create_entry()`): if section content hash unchanged and entry was already active → skip version creation + embedding. Does NOT skip the `get_or_create_entry()` DB update.

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
LLM_MODEL_INGEST  = "gemini-2.0-flash"        # ingest/classify model
EMBEDDING_MODEL   = "models/text-embedding-004" # vector embedding (768 dims)
VECTOR_TOP_K      = 20     # ChromaDB candidates before reranking
RERANK_TOP_N      = 3      # final results sent to LLM
LLM_WORKERS       = 4      # parallel threads
MAX_LLM_RETRIES   = 3      # Gemini API retry count
EMBED_BATCH_SIZE  = 10     # texts per embed_content call
CHROMA_BATCH_SIZE = 100    # items per ChromaDB upsert
```

API-level constants (defined inline in `api.py`):
```python
LLM_MODEL   = "gemini-2.5-flash"
API_KEY     = os.getenv("CHAT_API_KEY", "erp-ai-secret-key-change-me")  # X-API-Key header
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
