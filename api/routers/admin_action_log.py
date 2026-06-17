"""
ERP AI Assistant — Admin Action Log Router
Endpoints: /admin/action-log, /admin/action-log/clear
"""
from fastapi import APIRouter, Depends
from api.auth import verify_api_key
from api.database import get_knowledge_conn

router = APIRouter()


@router.get("/action-log")
async def admin_action_log_list(
    limit: int = 50,
    offset: int = 0,
    action: str = None,
    _key: str = Depends(verify_api_key),
):
    """List admin action log entries."""
    import os
    from api.config import KNOWLEDGE_DB
    if not os.path.exists(KNOWLEDGE_DB):
        return {"total": 0, "items": []}

    kconn = get_knowledge_conn()
    where, params = [], []
    if action:
        where.append("action = ?"); params.append(action)
    w = "WHERE " + " AND ".join(where) if where else ""
    total = kconn.execute(f"SELECT COUNT(*) FROM admin_action_log {w}", params).fetchone()[0]
    rows = kconn.execute(f"""
        SELECT id, admin_user_id, action, target_type, target_id, note, meta, ip_address, created_at
        FROM admin_action_log {w}
        ORDER BY created_at DESC LIMIT ? OFFSET ?
    """, params + [limit, offset]).fetchall()
    kconn.close()
    return {
        "total": total,
        "items": [dict(r) for r in rows],
    }


@router.delete("/action-log")
async def admin_action_log_clear(_key: str = Depends(verify_api_key)):
    """Clear all admin action logs."""
    import os
    from api.config import KNOWLEDGE_DB
    if not os.path.exists(KNOWLEDGE_DB):
        return {"deleted": 0}
    kconn = get_knowledge_conn()
    count = kconn.execute("SELECT COUNT(*) FROM admin_action_log").fetchone()[0]
    kconn.execute("DELETE FROM admin_action_log")
    kconn.commit()
    kconn.close()
    return {"deleted": count}
