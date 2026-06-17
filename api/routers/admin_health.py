"""
ERP AI Assistant — Admin Health Router
Endpoints: /admin/health
"""
import json
import os
import time as _time
import sqlite3
import urllib.request
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends
from api.auth import verify_api_key
from api.config import LLM_MODEL, KNOWLEDGE_DB, CHAT_DB, SKILLS_URL, SCHEDULER_STATE_FILE
from api.database import get_knowledge_conn, get_chat_conn
from api.llm import _gemini_client
from embedding_helper import get_reranker

router = APIRouter()


@router.get("/health")
async def admin_system_health(_key: str = Depends(verify_api_key)):
    checked_at = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    # Gemini API
    t0 = _time.time()
    try:
        list(_gemini_client.models.list())
        gemini_ms, gemini_status = round((_time.time() - t0) * 1000), "ok"
    except Exception:
        gemini_ms, gemini_status = None, "down"

    # ChromaDB
    try:
        from embedding_helper import CHROMA_AVAILABLE
        chroma_status = "ok" if CHROMA_AVAILABLE else "down"
    except Exception:
        chroma_status = "down"

    # PostgreSQL
    try:
        from ingest.ingest_config import PG_CONFIG as _PG
        import psycopg2
        t0 = _time.time()
        _c = psycopg2.connect(**_PG, connect_timeout=3)
        _c.close()
        pg_ms, pg_status = round((_time.time() - t0) * 1000), "ok"
    except ImportError:
        pg_ms, pg_status = None, "skip"
    except Exception:
        pg_ms, pg_status = None, "down"

    # Skills server
    t0 = _time.time()
    try:
        with urllib.request.urlopen(f"{SKILLS_URL}/tools", timeout=3) as r:
            json.loads(r.read())
        skills_ms, skills_status = round((_time.time() - t0) * 1000), "ok"
    except Exception:
        skills_ms, skills_status = None, "down"

    # Models
    try:
        from ingest.ingest_config import LLM_MODEL_INGEST as _LMI, EMBEDDING_MODEL as _EMB
    except ImportError:
        _LMI, _EMB = "gemini-2.0-flash", "text-embedding-004"

    _reranker_ok = False
    try:
        _reranker_ok = get_reranker() is not None
    except Exception:
        pass

    models = [
        {"role": "Chat",      "name": LLM_MODEL, "available": gemini_status == "ok"},
        {"role": "Ingest",    "name": _LMI,       "available": gemini_status == "ok"},
        {"role": "Embedding", "name": _EMB,        "available": gemini_status == "ok"},
        {"role": "Reranker",  "name": "ms-marco-MiniLM-L-6-v2", "available": _reranker_ok},
    ]

    # Databases
    def _db_info(path, kind):
        p = Path(path)
        info = {"path": str(p), "exists": p.exists()}
        if not p.exists():
            return info
        info["size_mb"] = round(p.stat().st_size / 1_048_576, 2)
        try:
            c = sqlite3.connect(path)
            c.row_factory = sqlite3.Row
            if kind == "knowledge":
                info["entries"]  = c.execute("SELECT COUNT(*) FROM entries WHERE is_active=1").fetchone()[0]
                info["versions"] = c.execute("SELECT COUNT(*) FROM entry_versions WHERE is_current=1").fetchone()[0]
                info["flagged"]  = c.execute("SELECT COUNT(*) FROM entry_versions WHERE is_flagged=1 AND is_current=1").fetchone()[0]
            elif kind == "chat":
                info["messages"] = c.execute("SELECT COUNT(*) FROM chat_history").fetchone()[0]
            c.close()
        except Exception:
            pass
        return info

    # Scheduler
    sched = {}
    try:
        if SCHEDULER_STATE_FILE.exists():
            raw = json.loads(SCHEDULER_STATE_FILE.read_text())
            for job, data in raw.items():
                sched[job] = {k: data.get(k) for k in
                    ("enabled", "is_running", "last_run_status", "last_run_at", "last_run_duration_sec")}
    except Exception:
        pass

    return {
        "checked_at": checked_at,
        "services": {
            "api":           {"status": "ok"},
            "gemini":        {"status": gemini_status, "model": LLM_MODEL, "response_ms": gemini_ms},
            "chromadb":      {"status": chroma_status},
            "postgres":      {"status": pg_status,    "response_ms": pg_ms},
            "skills_server": {"status": skills_status, "url": SKILLS_URL,   "response_ms": skills_ms},
        },
        "models":    models,
        "databases": {
            "knowledge":   _db_info(KNOWLEDGE_DB, "knowledge"),
            "chat_history": _db_info(CHAT_DB,      "chat"),
        },
        "scheduler": sched,
    }
