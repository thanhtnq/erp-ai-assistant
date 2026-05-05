"""
ERP AI — Shared Ingest Configuration
Used by: ingest_knowledge.py, ingest_tickets.py

Edit this file to configure all ingest settings.
Override sensitive values with environment variables (e.g. PG_PASSWORD, OLLAMA_URL).
"""

import os
from pathlib import Path

_BASE = Path(__file__).parent.parent  # d:\erp-ai-v2

# ─── Paths ────────────────────────────────────────────────────────────────────

KNOWLEDGE_DB  = str(_BASE / "data/erp_knowledge.db")
DOCS_DIR      = str(_BASE / "documents")
IMAGES_BASE   = str(_BASE / "document_images")
CHROMA_DIR    = str(_BASE / "data/chroma_db")

# ─── LLM ──────────────────────────────────────────────────────────────────────

OLLAMA_URL    = os.getenv("OLLAMA_URL", "http://localhost:11434")

# Model for document ingest (use larger model for better accuracy)
LLM_MODEL_INGEST = "qwen3.5:397b-cloud"

# Model for ticket classification
LLM_MODEL_TICKET = "qwen3.5:397b-cloud"

# ─── Embedding ────────────────────────────────────────────────────────────────

# Embedding model via Ollama — pull first: ollama pull qwen3-embedding:0.6b
EMBEDDING_MODEL = "qwen3-embedding:0.6b"

# Instruction prefix improves retrieval accuracy 1-5% for domain-specific tasks
EMBEDDING_INSTRUCTION = "Represent this ERP knowledge entry for semantic retrieval: "
QUERY_INSTRUCTION     = "Represent this ERP support query for retrieving relevant procedures and solutions: "

# ChromaDB collection names
CHROMA_COLLECTION_GLOBAL = "erp_knowledge_global"
CHROMA_COLLECTION_PREFIX = "erp_knowledge_"   # + company_code for company-specific

# ─── Reranker ─────────────────────────────────────────────────────────────────

# pip install sentence-transformers
# Options (quality vs speed):
#   "cross-encoder/ms-marco-MiniLM-L-6-v2"   ~80MB  fast    good
#   "cross-encoder/ms-marco-MiniLM-L-12-v2"  ~130MB medium  better
RERANKER_MODEL   = "cross-encoder/ms-marco-MiniLM-L-6-v2"
VECTOR_TOP_K     = 20     # candidates retrieved from ChromaDB before reranking
RERANK_TOP_N     = 3      # final results passed to LLM after reranking
RERANK_MIN_SCORE = -5.0   # CrossEncoder scores roughly -10 to +10; filter very irrelevant

# ─── PostgreSQL Connection ────────────────────────────────────────────────────

PG_CONFIG = {
    "host":     os.getenv("PG_HOST",     "localhost"),
    "port":     int(os.getenv("PG_PORT", "5432")),
    "dbname":   os.getenv("PG_DBNAME",   "v57udemo2011_tno"),
    "user":     os.getenv("PG_USER",     "postgres"),
    "password": os.getenv("PG_PASSWORD", "123"),
}

# ─── Ticket Query ─────────────────────────────────────────────────────────────

TICKET_QUERY = """
    SELECT
        main.dnum_auto          AS ticket_id,
        main.acctnumdesc_disc   AS subject,
        main.notes_memo         AS description,
        data.notes_memo         AS solution,
        'done'                  AS status,
        main.date_trans         AS created_at,
        main.masterfn           AS company_code
    FROM            prj_pbill_main main
    LEFT JOIN       memo_long_table data
            ON      data.companyfn       = main.companyfn
            AND     data.uniquenum_pri   = main.uniquenum_pri
            AND     data.tag_table_usage = main.tag_table_usage
            AND     data.tag_memo_type   = 'norm_notes'
    WHERE   main.tag_table_usage   = 'crm_int'
            AND main.tag_deleted_yn  = 'n'
            AND main.tag_void_yn     = 'n'
            AND main.tag_closed03_yn = 'y'
"""

# Filter by specific company fn (None = all companies)
FILTER_COMPANY_FN = None

# ─── Domain & Type Classification ─────────────────────────────────────────────

AVAILABLE_DOMAINS = [
    "Sales",
    "Purchase",
    "Finance",
    "Inventory",
    "CRM",
    "Human Resources",
    "Project",
    "Fixed Assets",
    "Service Manager",
    "General",
]

AVAILABLE_TYPES = [
    "error_fix",
    "faq",
    "reference",
    "procedure",
]

# ─── Ticket Ingest Settings ───────────────────────────────────────────────────

MIN_DESCRIPTION_LENGTH = 20
MIN_SOLUTION_LENGTH    = 20
EMBED_BATCH_SIZE       = 10   # texts per Ollama /api/embed call
CHROMA_BATCH_SIZE      = 100  # items per ChromaDB upsert call
SKIP_EXISTING          = True

# ─── LLM Concurrency & Retry ──────────────────────────────────────────────────
# LLM_WORKERS: parallel LLM call workers — tune to match OLLAMA_NUM_PARALLEL env var
LLM_WORKERS     = int(os.getenv("LLM_WORKERS", "4"))
MAX_LLM_RETRIES = 3   # retries on Ollama timeout/error
LLM_RETRY_DELAY = 5   # seconds before first retry (doubles each attempt)

# ─── Schedule Settings ────────────────────────────────────────────────────────
# Used by schedule/scheduler.py

SCHEDULE = {
    # Auto-ingest new/changed documents (checks file hash, skips unchanged)
    "ingest_documents": {
        "enabled":  True,
        "interval": "daily",        # 'hourly' | 'daily' | 'weekly'
        "time":     "02:00",        # HH:MM (for daily/weekly)
        "day":      "monday",       # day of week (for weekly only)
    },
    # Auto-sync new resolved tickets from PostgreSQL
    "ingest_tickets": {
        "enabled":  True,
        "interval": "daily",
        "time":     "03:00",
    },
}





