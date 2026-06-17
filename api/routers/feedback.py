"""
ERP AI Assistant — Feedback Router
Endpoints: /feedback/submit, /feedback/bulk
"""
from fastapi import APIRouter, Depends
from api.auth import verify_api_key
from api.models import FeedbackRequest, FeedbackBulkRequest
from api.database import get_chat_conn
from api.utils import now_iso

router = APIRouter()


@router.post("/submit")
async def feedback_submit(
    body: FeedbackRequest,
    _key: str = Depends(verify_api_key),
):
    """Submit feedback (upvote/downvote) for a knowledge entry version."""
    if body.rating not in ("up", "down"):
        return {"status": "error", "detail": "rating must be 'up' or 'down'"}

    conn = get_chat_conn()
    conn.execute("""
        INSERT INTO feedback_log (user_id, company_id, entry_version_id, rating,
                                  query_text, reason, comment, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (body.user_id, body.company_id, body.entry_version_id, body.rating,
          body.query_text, body.reason, body.comment, now_iso()))
    conn.commit()
    conn.close()
    return {"status": "ok"}


@router.post("/bulk")
async def feedback_bulk(
    body: FeedbackBulkRequest,
    _key: str = Depends(verify_api_key),
):
    """Submit multiple feedback entries at once."""
    conn = get_chat_conn()
    now = now_iso()
    for r in body.ratings:
        if r.get("rating") not in ("up", "down"):
            continue
        conn.execute("""
            INSERT INTO feedback_log (user_id, company_id, entry_version_id, rating,
                                      query_text, reason, comment, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (body.user_id, body.company_id, r.get("entry_version_id"), r.get("rating"),
              r.get("query_text"), r.get("reason"), r.get("comment"), now))
    conn.commit()
    conn.close()
    return {"status": "ok", "count": len(body.ratings)}
