"""
ERP AI — Shared Ingest Configuration
Used by: ingest_knowledge.py, ingest_tickets.py

Sensitive values are loaded from .env at project root.
Copy .env.example → .env and fill in your credentials.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

_BASE = Path(__file__).parent.parent  # d:\erp-ai-v2
load_dotenv(_BASE / ".env", override=True)

# ─── Paths ────────────────────────────────────────────────────────────────────

KNOWLEDGE_DB  = str(_BASE / "data/erp_knowledge.db")
DOCS_DIR      = str(_BASE / "documents")
IMAGES_BASE   = str(_BASE / "document_images")
CHROMA_DIR    = str(_BASE / "data/chroma_db")

# ─── LLM ──────────────────────────────────────────────────────────────────────

GEMINI_API_KEY   = os.getenv("GEMINI_API_KEY", "")

# Model for document ingest and ticket classification
LLM_MODEL_INGEST = "gemini-2.0-flash"
LLM_MODEL_TICKET = "gemini-2.0-flash"

# ─── Embedding ────────────────────────────────────────────────────────────────

# Gemini embedding model — uses task_type parameter instead of instruction prefix
# text-embedding-004 is not available on all API keys; gemini-embedding-001 is GA (3072 dims)
EMBEDDING_MODEL = "gemini-embedding-001"

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
    "dbname":   os.getenv("PG_DBNAME",   ""),
    "user":     os.getenv("PG_USER",     "postgres"),
    "password": os.getenv("PG_PASSWORD", ""),
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
EMBED_BATCH_SIZE       = 10   # texts per Gemini embed_content call
CHROMA_BATCH_SIZE      = 100  # items per ChromaDB upsert call
SKIP_EXISTING          = True

# ─── LLM Concurrency & Retry ──────────────────────────────────────────────────
LLM_WORKERS     = int(os.getenv("LLM_WORKERS", "4"))
MAX_LLM_RETRIES = 3   # retries on Gemini timeout/error
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





