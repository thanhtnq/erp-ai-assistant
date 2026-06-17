"""
ERP AI Assistant — Admin Analytics Router
Endpoints: /admin/analytics/feedback, /admin/analytics/usage, /admin/analytics/performance
"""
from fastapi import APIRouter, Depends
from api.auth import verify_api_key
from api.database import get_chat_conn, get_knowledge_conn

router = APIRouter()


@router.get("/analytics/feedback")
async def admin_analytics_feedback(
    days: int = 30,
    _key: str = Depends(verify_api_key),
):
    """Aggregated feedback analytics."""
    import os
    from api.config import CHAT_DB
    if not os.path.exists(CHAT_DB):
        return {"total": 0, "up": 0, "down": 0, "by_day": [], "by_reason": {}}

    from datetime import datetime, timedelta
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()

    conn = get_chat_conn()
    total = conn.execute(
        "SELECT COUNT(*) FROM feedback_log WHERE created_at >= ?", (since,)
    ).fetchone()[0]
    up = conn.execute(
        "SELECT COUNT(*) FROM feedback_log WHERE created_at >= ? AND rating='up'", (since,)
    ).fetchone()[0]
    down = conn.execute(
        "SELECT COUNT(*) FROM feedback_log WHERE created_at >= ? AND rating='down'", (since,)
    ).fetchone()[0]
    by_day = [
        {"date": r[0], "up": r[1], "down": r[2]}
        for r in conn.execute("""
            SELECT DATE(created_at) AS d,
                   SUM(CASE WHEN rating='up'   THEN 1 ELSE 0 END),
                   SUM(CASE WHEN rating='down' THEN 1 ELSE 0 END)
            FROM feedback_log WHERE created_at >= ?
            GROUP BY d ORDER BY d
        """, (since,)).fetchall()
    ]
    by_reason = {
        r[0]: r[1] for r in conn.execute("""
            SELECT reason, COUNT(*) FROM feedback_log
            WHERE created_at >= ? AND reason IS NOT NULL AND reason != ''
            GROUP BY reason ORDER BY COUNT(*) DESC
        """, (since,)).fetchall()
    }
    conn.close()
    return {"total": total, "up": up, "down": down,
            "by_day": by_day, "by_reason": by_reason}


@router.get("/analytics/usage")
async def admin_analytics_usage(
    days: int = 30,
    _key: str = Depends(verify_api_key),
):
    """Chat usage analytics."""
    import os
    from api.config import CHAT_DB
    if not os.path.exists(CHAT_DB):
        return {"total_messages": 0, "total_sessions": 0, "by_day": [], "top_users": []}

    from datetime import datetime, timedelta
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()

    conn = get_chat_conn()
    total = conn.execute(
        "SELECT COUNT(*) FROM chat_history WHERE timestamp >= ?", (since,)
    ).fetchone()[0]
    sessions = conn.execute("""
        SELECT COUNT(DISTINCT user_id || '|' || company_id)
        FROM chat_history WHERE timestamp >= ?
    """, (since,)).fetchone()[0]
    by_day = [
        {"date": r[0], "messages": r[1], "users": r[2]}
        for r in conn.execute("""
            SELECT DATE(timestamp) AS d,
                   COUNT(*),
                   COUNT(DISTINCT user_id)
            FROM chat_history WHERE timestamp >= ?
            GROUP BY d ORDER BY d
        """, (since,)).fetchall()
    ]
    top_users = [
        {"user_id": r[0], "messages": r[1]}
        for r in conn.execute("""
            SELECT user_id, COUNT(*) AS cnt
            FROM chat_history WHERE timestamp >= ?
            GROUP BY user_id ORDER BY cnt DESC LIMIT 10
        """, (since,)).fetchall()
    ]
    conn.close()
    return {"total_messages": total, "total_sessions": sessions,
            "by_day": by_day, "top_users": top_users}


@router.get("/analytics/performance")
async def admin_analytics_performance(
    days: int = 7,
    _key: str = Depends(verify_api_key),
):
    """Performance metrics from action log."""
    import os
    from api.config import KNOWLEDGE_DB
    if not os.path.exists(KNOWLEDGE_DB):
        return {"total_actions": 0, "by_action": {}, "by_day": []}

    from datetime import datetime, timedelta
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()

    kconn = get_knowledge_conn()
    total = kconn.execute(
        "SELECT COUNT(*) FROM admin_action_log WHERE created_at >= ?", (since,)
    ).fetchone()[0]
    by_action = {
        r[0]: r[1] for r in kconn.execute("""
            SELECT action, COUNT(*) FROM admin_action_log
            WHERE created_at >= ?
            GROUP BY action ORDER BY COUNT(*) DESC
        """, (since,)).fetchall()
    }
    by_day = [
        {"date": r[0], "actions": r[1]}
        for r in kconn.execute("""
            SELECT DATE(created_at) AS d, COUNT(*)
            FROM admin_action_log WHERE created_at >= ?
            GROUP BY d ORDER BY d
        """, (since,)).fetchall()
    ]
    kconn.close()
    return {"total_actions": total, "by_action": by_action, "by_day": by_day}
