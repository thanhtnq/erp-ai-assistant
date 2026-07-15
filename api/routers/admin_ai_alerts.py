"""Review workflow for AI indicators and replenishment recommendations."""
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query

from api.auth import verify_api_key
from api.database import get_chat_conn
from api.models import AIAlertCreate, AIAlertReview, AIRecommendationAction

router = APIRouter()
ALERT_STATUSES = {"new", "investigating", "confirmed_issue", "false_positive", "resolved"}
RECOMMENDATION_ACTIONS = {"accepted", "adjusted", "rejected", "expired"}

# F2: Extended dispositions
ALERT_DISPOSITIONS = {
    "ignored_by_policy", "duplicate_alert", "needs_rule_tuning", "insufficient_evidence"
}
NEXT_ACTIONS = {
    "hold_payment", "check_document", "contact_buyer", "ignore", "create_correction"
}

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def _migrate_alert_columns(conn):
    """Add new columns to ai_alerts if missing (migration for existing DBs)."""
    existing = {row[1] for row in conn.execute("PRAGMA table_info(ai_alerts)").fetchall()}
    for col in ("disposition_reason", "next_action", "rule_feedback"):
        if col not in existing:
            try:
                conn.execute(f"ALTER TABLE ai_alerts ADD COLUMN {col} TEXT")
            except Exception:
                pass

def _migrate_recommendation_columns(conn):
    """Add new columns to ai_recommendation_actions if missing."""
    existing = {row[1] for row in conn.execute("PRAGMA table_info(ai_recommendation_actions)").fetchall()}
    for col in ("reject_reason",):
        if col not in existing:
            try:
                conn.execute(f"ALTER TABLE ai_recommendation_actions ADD COLUMN {col} TEXT")
            except Exception:
                pass

@router.post("/ai-alerts")
async def create_alert(body: AIAlertCreate, _key: str = Depends(verify_api_key)):
    if not body.masterfn or not body.companyfn:
        raise HTTPException(400, "masterfn and companyfn are required")
    now = now_iso(); conn = get_chat_conn()
    _migrate_alert_columns(conn)
    cur = conn.execute("""INSERT INTO ai_alerts
      (masterfn,companyfn,alert_type,severity,status,title,reason_code,risk_score,source_id,evidence_json,rule_version,created_at,updated_at)
      VALUES (?,?,?,?, 'new', ?,?,?,?,?,?,?,?)""",
      (body.masterfn,body.companyfn,body.alert_type,body.severity,body.title,body.reason_code,
       body.risk_score,body.source_id,json.dumps(body.evidence,ensure_ascii=False),body.rule_version,now,now))
    conn.commit(); alert_id=cur.lastrowid; conn.close()
    return {"id":alert_id,"status":"new"}

@router.get("/ai-alerts")
async def list_alerts(masterfn: str, companyfn: str, status: str = "", alert_type: str = "",
                      disposition: str = "", limit: int = 50, offset: int = 0,
                      _key: str = Depends(verify_api_key)):
    where=["masterfn=?","companyfn=?"]; params=[masterfn,companyfn]
    if status: where.append("status=?"); params.append(status)
    if alert_type: where.append("alert_type=?"); params.append(alert_type)
    if disposition: where.append("disposition_reason=?"); params.append(disposition)
    conn=get_chat_conn(); _migrate_alert_columns(conn); w=" AND ".join(where)
    total=conn.execute(f"SELECT COUNT(*) FROM ai_alerts WHERE {w}",params).fetchone()[0]
    rows=conn.execute(f"SELECT * FROM ai_alerts WHERE {w} ORDER BY risk_score DESC,created_at DESC LIMIT ? OFFSET ?",params+[min(limit,100),offset]).fetchall()
    conn.close(); items=[]
    for row in rows:
        item=dict(row); item["evidence"]=json.loads(item.pop("evidence_json") or "{}"); items.append(item)
    return {"total":total,"items":items}

@router.patch("/ai-alerts/{alert_id}")
async def review_alert(alert_id: int, body: AIAlertReview, _key: str = Depends(verify_api_key)):
    if body.status not in ALERT_STATUSES: raise HTTPException(400,"Invalid alert status")
    conn=get_chat_conn(); _migrate_alert_columns(conn)
    row=conn.execute("SELECT id, status FROM ai_alerts WHERE id=? AND masterfn=? AND companyfn=?",(alert_id,body.masterfn,body.companyfn)).fetchone()
    if not row: conn.close(); raise HTTPException(404,"Alert not found in this company scope")
    previous_status = row["status"]
    # Build update with extended fields
    updates = ["status=?","reviewer=?","review_note=?","updated_at=?"]
    params = [body.status, body.reviewer, body.note, now_iso()]
    if body.disposition_reason:
        updates.append("disposition_reason=?")
        params.append(body.disposition_reason)
    if body.next_action:
        updates.append("next_action=?")
        params.append(body.next_action)
    if body.rule_feedback:
        updates.append("rule_feedback=?")
        params.append(body.rule_feedback)
    params.append(alert_id)
    conn.execute(f"UPDATE ai_alerts SET {', '.join(updates)} WHERE id=?", params)
    # Write review history
    conn.execute("""INSERT INTO alert_review_history
      (alert_id,masterfn,companyfn,previous_status,new_status,reviewer,note,disposition_reason,next_action,rule_feedback,created_at)
      VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
      (alert_id,body.masterfn,body.companyfn,previous_status,body.status,body.reviewer,body.note,
       body.disposition_reason,body.next_action,body.rule_feedback,now_iso()))
    conn.commit(); conn.close()
    return {"id":alert_id,"status":body.status}

@router.post("/ai-recommendations/actions")
async def recommendation_action(body: AIRecommendationAction, _key: str = Depends(verify_api_key)):
    if body.action not in RECOMMENDATION_ACTIONS: raise HTTPException(400,"Invalid recommendation action")
    conn=get_chat_conn(); _migrate_recommendation_columns(conn)
    cur=conn.execute("""INSERT INTO ai_recommendation_actions
      (masterfn,companyfn,recommendation_id,action,actor,note,adjusted_qty,reject_reason,created_at) VALUES (?,?,?,?,?,?,?,?,?)""",
      (body.masterfn,body.companyfn,body.recommendation_id,body.action,body.actor,body.note,body.adjusted_qty,body.reject_reason,now_iso()))
    conn.commit(); action_id=cur.lastrowid; conn.close()
    return {"id":action_id,"action":body.action,"erp_document_created":False}

@router.get("/ai-recommendations/actions")
async def list_recommendation_actions(
    masterfn: str = Query(...),
    companyfn: str = Query(...),
    recommendation_id: str = Query(""),
    limit: int = Query(50, le=100),
    _key: str = Depends(verify_api_key),
):
    """List recommendation actions for a scope, optionally filtered by recommendation_id."""
    conn=get_chat_conn(); _migrate_recommendation_columns(conn)
    if recommendation_id:
        rows=conn.execute("""
            SELECT * FROM ai_recommendation_actions
            WHERE masterfn=? AND companyfn=? AND recommendation_id=?
            ORDER BY created_at DESC LIMIT ?
        """, (masterfn, companyfn, recommendation_id, limit)).fetchall()
    else:
        rows=conn.execute("""
            SELECT * FROM ai_recommendation_actions
            WHERE masterfn=? AND companyfn=?
            ORDER BY created_at DESC LIMIT ?
        """, (masterfn, companyfn, limit)).fetchall()
    conn.close()
    return {"items": [dict(r) for r in rows]}

@router.get("/ai-alerts/{alert_id}/history")
async def get_alert_review_history(
    alert_id: int,
    masterfn: str = Query(...),
    companyfn: str = Query(...),
    limit: int = Query(20, le=50),
    _key: str = Depends(verify_api_key),
):
    """Get review history for a specific alert."""
    conn=get_chat_conn()
    rows=conn.execute("""
        SELECT * FROM alert_review_history
        WHERE alert_id=? AND masterfn=? AND companyfn=?
        ORDER BY created_at DESC LIMIT ?
    """, (alert_id, masterfn, companyfn, limit)).fetchall()
    conn.close()
    return {"items": [dict(r) for r in rows]}

@router.get("/ai-alerts/count")
async def count_open_alerts(
    masterfn: str = Query(...),
    companyfn: str = Query(...),
    severity: str = Query("critical,high"),
    _key: str = Depends(verify_api_key),
):
    """Count open alerts by severity for badge display."""
    conn=get_chat_conn(); _migrate_alert_columns(conn)
    severities = [s.strip() for s in severity.split(",") if s.strip()]
    placeholders = ",".join("?" * len(severities))
    row = conn.execute(f"""
        SELECT COUNT(*) FROM ai_alerts
        WHERE masterfn=? AND companyfn=?
          AND status IN ('new','investigating')
          AND severity IN ({placeholders})
    """, [masterfn, companyfn] + severities).fetchone()
    conn.close()
    return {"count": row[0]}
