"""
ERP AI Assistant — Admin Feedback Router
Endpoints: /admin/feedback, /admin/feedback/flag, /admin/feedback/flag/resolve
"""
from fastapi import APIRouter, Depends, HTTPException
from starlette.requests import Request
from api.auth import verify_api_key
from api.models import AdminFlagAction, AdminFlagResolve
from api.database import get_knowledge_conn, get_chat_conn
from api.utils import now_iso, log_admin_action, _get_client_ip

router = APIRouter()



@router.get("/feedback")
async def admin_feedback_list(
    days: int = 30,
    limit: int = 50,
    offset: int = 0,
    _key: str = Depends(verify_api_key),
):
    """List feedback entries with optional date filter."""
    import os
    from api.config import CHAT_DB
    if not os.path.exists(CHAT_DB):
        return {"total": 0, "items": []}

    from datetime import datetime, timedelta
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()

    conn = get_chat_conn()
    total = conn.execute(
        "SELECT COUNT(*) FROM feedback_log WHERE created_at >= ?", (since,)
    ).fetchone()[0]
    rows = conn.execute("""
        SELECT id, user_id, company_id, entry_version_id, rating,
               query_text, reason, comment, created_at
        FROM feedback_log WHERE created_at >= ?
        ORDER BY created_at DESC LIMIT ? OFFSET ?
    """, (since, limit, offset)).fetchall()
    conn.close()
    return {
        "total": total,
        "items": [dict(r) for r in rows],
    }


@router.post("/feedback/flag")
async def admin_feedback_flag(
    body: AdminFlagAction,
    request: Request,
    _key: str = Depends(verify_api_key),
):
    """Flag a knowledge entry version for review."""
    if not body.entry_version_id:
        raise HTTPException(status_code=400, detail="entry_version_id is required")

    conn = get_knowledge_conn()
    conn.execute(
        "UPDATE entry_versions SET is_flagged=1, flag_reason=?, flag_status='pending' WHERE id=?",
        (body.reason or "Flagged by admin", body.entry_version_id)
    )
    conn.commit()
    log_admin_action(conn, body.admin_user_id, "flag_entry",
                     target_type="entry_version", target_id=str(body.entry_version_id),
                     note=body.reason, ip=_get_client_ip(request))
    conn.close()
    return {"status": "flagged"}


@router.post("/feedback/flag/resolve")
async def admin_feedback_flag_resolve(
    body: AdminFlagResolve,
    request: Request,
    _key: str = Depends(verify_api_key),
):
    """Resolve a flagged entry version."""
    conn = get_knowledge_conn()
    conn.execute(
        "UPDATE entry_versions SET flag_status='resolved', flag_resolution_note=? WHERE id=?",
        (body.resolution_note or "", body.entry_version_id)
    )
    conn.commit()
    log_admin_action(conn, body.admin_user_id, "resolve_flag",
                     target_type="entry_version", target_id=str(body.entry_version_id),
                     note=body.resolution_note, ip=_get_client_ip(request))
    conn.close()
    return {"status": "resolved"}
