"""Review workflow for AI indicators and replenishment recommendations."""
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException

from api.auth import verify_api_key
from api.database import get_chat_conn
from api.models import AIAlertCreate, AIAlertReview, AIRecommendationAction

router = APIRouter()
ALERT_STATUSES = {"new", "investigating", "confirmed_issue", "false_positive", "resolved"}
RECOMMENDATION_ACTIONS = {"accepted", "adjusted", "rejected", "expired"}

def now_iso():
    return datetime.now(timezone.utc).isoformat()

@router.post("/ai-alerts")
async def create_alert(body: AIAlertCreate, _key: str = Depends(verify_api_key)):
    if not body.masterfn or not body.companyfn:
        raise HTTPException(400, "masterfn and companyfn are required")
    now = now_iso(); conn = get_chat_conn()
    cur = conn.execute("""INSERT INTO ai_alerts
      (masterfn,companyfn,alert_type,severity,status,title,reason_code,risk_score,source_id,evidence_json,rule_version,created_at,updated_at)
      VALUES (?,?,?,?, 'new', ?,?,?,?,?,?,?,?)""",
      (body.masterfn,body.companyfn,body.alert_type,body.severity,body.title,body.reason_code,
       body.risk_score,body.source_id,json.dumps(body.evidence,ensure_ascii=False),body.rule_version,now,now))
    conn.commit(); alert_id=cur.lastrowid; conn.close()
    return {"id":alert_id,"status":"new"}

@router.get("/ai-alerts")
async def list_alerts(masterfn: str, companyfn: str, status: str = "", alert_type: str = "",
                      limit: int = 50, offset: int = 0, _key: str = Depends(verify_api_key)):
    where=["masterfn=?","companyfn=?"]; params=[masterfn,companyfn]
    if status: where.append("status=?"); params.append(status)
    if alert_type: where.append("alert_type=?"); params.append(alert_type)
    conn=get_chat_conn(); w=" AND ".join(where)
    total=conn.execute(f"SELECT COUNT(*) FROM ai_alerts WHERE {w}",params).fetchone()[0]
    rows=conn.execute(f"SELECT * FROM ai_alerts WHERE {w} ORDER BY risk_score DESC,created_at DESC LIMIT ? OFFSET ?",params+[min(limit,100),offset]).fetchall()
    conn.close(); items=[]
    for row in rows:
        item=dict(row); item["evidence"]=json.loads(item.pop("evidence_json") or "{}"); items.append(item)
    return {"total":total,"items":items}

@router.patch("/ai-alerts/{alert_id}")
async def review_alert(alert_id: int, body: AIAlertReview, _key: str = Depends(verify_api_key)):
    if body.status not in ALERT_STATUSES: raise HTTPException(400,"Invalid alert status")
    conn=get_chat_conn(); row=conn.execute("SELECT id FROM ai_alerts WHERE id=? AND masterfn=? AND companyfn=?",(alert_id,body.masterfn,body.companyfn)).fetchone()
    if not row: conn.close(); raise HTTPException(404,"Alert not found in this company scope")
    conn.execute("UPDATE ai_alerts SET status=?,reviewer=?,review_note=?,updated_at=? WHERE id=?",
                 (body.status,body.reviewer,body.note,now_iso(),alert_id)); conn.commit(); conn.close()
    return {"id":alert_id,"status":body.status}

@router.post("/ai-recommendations/actions")
async def recommendation_action(body: AIRecommendationAction, _key: str = Depends(verify_api_key)):
    if body.action not in RECOMMENDATION_ACTIONS: raise HTTPException(400,"Invalid recommendation action")
    conn=get_chat_conn(); cur=conn.execute("""INSERT INTO ai_recommendation_actions
      (masterfn,companyfn,recommendation_id,action,actor,note,adjusted_qty,created_at) VALUES (?,?,?,?,?,?,?,?)""",
      (body.masterfn,body.companyfn,body.recommendation_id,body.action,body.actor,body.note,body.adjusted_qty,now_iso()))
    conn.commit(); action_id=cur.lastrowid; conn.close()
    return {"id":action_id,"action":body.action,"erp_document_created":False}
