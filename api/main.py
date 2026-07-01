"""
ERP AI Assistant — Main Entry Point
FastAPI application with modular routers.
"""
import uvicorn
from pathlib import Path
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from fastapi import APIRouter
from api.database import init_chat_db, get_chat_conn
from api.auth import verify_api_key
from api.config import IMAGES_DIR
from api.routers import (
    chat, feedback, admin_feedback, admin_knowledge, admin_documents,
    admin_scheduler, admin_health, admin_analytics, admin_scm, admin_action_log,
)

# ─── CFML-compatible history routes (no /chat prefix) ──────────────────────
history_router = APIRouter()


@history_router.get("/history/{company_id}/{user_id}")
async def cfml_history_get(
    user_id: str,
    company_id: str,
    limit: int = 50,
    session_id: str = "",
    before_id: int | None = None,
    _key: str = Depends(verify_api_key),
):
    """Get chat history ??? CFML frontend calls GET /history/{company}/{user}."""
    conn = get_chat_conn()
    params = [user_id, company_id]
    query = """
        SELECT id, role, content, timestamp
        FROM chat_history
        WHERE user_id=? AND company_id=?
    """
    if session_id:
        query += " AND session_id=?"
        params.append(session_id)
    if before_id:
        query += " AND id < ?"
        params.append(before_id)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit + 1)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    has_more = len(rows) > limit
    rows = rows[:limit]
    return {
        "history": [
            {"id": r["id"], "role": r["role"], "content": r["content"],
             "timestamp": r["timestamp"]}
            for r in rows
        ],
        "has_more": has_more,
        "oldest_id": rows[-1]["id"] if rows else None,
    }

@history_router.delete("/history/{company_id}/{user_id}")
async def cfml_history_delete(
    user_id: str,
    company_id: str,
    _key: str = Depends(verify_api_key),
):
    """Delete chat history — CFML frontend calls DELETE /history/{company}/{user}."""
    conn = get_chat_conn()
    conn.execute(
        "DELETE FROM chat_history WHERE user_id=? AND company_id=?",
        (user_id, company_id)
    )
    conn.execute(
        "DELETE FROM chat_sessions WHERE user_id=? AND company_id=?",
        (user_id, company_id)
    )
    conn.commit()
    conn.close()
    return {"status": "deleted"}

app = FastAPI(
    title="ERP AI Assistant API",
    version="2.0.0",
    description="Modular API for Globe3 ERP AI Assistant — refactored from monolithic api.py",
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
_images_dir = Path(IMAGES_DIR)
if _images_dir.exists():
    app.mount("/images", StaticFiles(directory=str(_images_dir)), name="images")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Startup ──────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    init_chat_db()
    print("[OK] Chat DB initialized")

# ─── Include Routers ──────────────────────────────────────────────────────────
app.include_router(chat.router,          prefix="/chat",          tags=["Chat"])
app.include_router(feedback.router,      prefix="/feedback",      tags=["Feedback"])
app.include_router(admin_feedback.router, prefix="/admin",        tags=["Admin: Feedback"])
app.include_router(admin_knowledge.router, prefix="/admin",       tags=["Admin: Knowledge"])
app.include_router(admin_documents.router, prefix="/admin",       tags=["Admin: Documents"])
app.include_router(admin_scheduler.router, prefix="/admin",       tags=["Admin: Scheduler"])
app.include_router(admin_health.router,    prefix="/admin",       tags=["Admin: Health"])
app.include_router(admin_analytics.router, prefix="/admin",       tags=["Admin: Analytics"])
app.include_router(admin_scm.router,       prefix="/admin",       tags=["Admin: SCM Training"])
app.include_router(history_router, tags=["CFML History"])
app.include_router(admin_action_log.router, prefix="/admin",      tags=["Admin: Action Log"])


@app.get("/")
async def root():
    return {
        "app": "ERP AI Assistant API",
        "version": "2.0.0",
        "docs": "/docs",
        "endpoints": {
            "chat": "/chat/stream",
            "admin": "/admin/health",
        }
    }


if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)



