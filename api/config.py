"""
ERP AI Assistant — Configuration
Centralized config loaded from .env file.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# ─── Paths ────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
KNOWLEDGE_DB = str(PROJECT_ROOT / "data/erp_knowledge.db")
CHAT_DB      = str(PROJECT_ROOT / "data/chat_history.db")
ROLE_MD      = str(PROJECT_ROOT / "ROLE.md")
IMAGES_DIR   = str(PROJECT_ROOT / "document_images")
INGEST_DIR   = str(PROJECT_ROOT / "ingest")
SCHEDULER_STATE_FILE = PROJECT_ROOT / "schedule/scheduler_state.json"

# ─── LLM ──────────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
LLM_MODEL      = "gemini-2.5-flash"

# ─── Auth ─────────────────────────────────────────────────────────────────────
CHAT_API_KEY = os.getenv("CHAT_API_KEY", "erp-ai-secret-key-change-me")

# ─── External Services ────────────────────────────────────────────────────────
SKILLS_URL = os.getenv("SKILLS_SERVER_URL", "http://localhost:3001")

# ─── Search ───────────────────────────────────────────────────────────────────
MAX_ENTRIES = 5

try:
    from ingest.ingest_config import VECTOR_TOP_K, RERANK_TOP_N
except ImportError:
    VECTOR_TOP_K = 20
    RERANK_TOP_N = 3
