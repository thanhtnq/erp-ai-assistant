import json
import os
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import psycopg2.extras
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from api.auth import verify_api_key
from api.services.erp_db import get_erp_conn

router = APIRouter()

SCHEDULER_STATE_FILE = Path(__file__).resolve().parents[2] / "data" / "scheduler_state.json"
MEMO_USAGE = "ai_fraud_detection"
ACTIVE = ("NEW", "ACKNOWLEDGED", "ACK")

RULE_LABELS = {
    "HIGH_TRANSACTION_AMOUNT": "High transaction amount",
    "TRANSACTION_FREQUENCY_SPIKE": "Frequency spike",
    "HIGH_REFUND_COUNT": "High refund count",
    "ABNORMAL_DISCOUNT": "Abnormal discount",
    "TOO_MANY_VOID_TRANSACTIONS": "Too many voids",
    "LOGIN_OUTSIDE_NORMAL_HOURS": "Outside working hours",
    "REPEATED_INVOICE_MODIFICATION": "Repeated invoice modification",
    "BACKDATED_TRANSACTION": "Backdated transaction",
    "DUPLICATE_FINANCE_REFERENCE": "Duplicate finance reference",
    "UNBALANCED_FINANCE_GL_POSTING": "Unbalanced finance GL posting",
}


class AlertAction(BaseModel):
    actor: str


def _json_default(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def _parse_notes(raw: Optional[str]) -> Dict[str, Any]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {"text": parsed}
    except (TypeError, ValueError):
        return {"text": raw}


def _dt(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def _num(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_status(value: Optional[str]) -> str:
    status = (value or "NEW").upper()
    if status == "ACK":
        return "ACKNOWLEDGED"
    return status


def _memo_item(row: Dict[str, Any]) -> Dict[str, Any]:
    payload = _parse_notes(row.get("notes_memo"))
    status = _normalize_status(payload.get("status") or row.get("tag_others02"))
    severity = (payload.get("severity") or row.get("tag_others01") or "LOW").upper()
    rule_name = payload.get("rule_name") or row.get("var_50_001") or row.get("tag_others03") or "UNKNOWN_RULE"
    risk_score = _num(payload.get("risk_score") if payload.get("risk_score") is not None else row.get("num_20_2_d_001")) or 0
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    if not metadata:
        metadata = {
            k: v
            for k, v in payload.items()
            if k
            not in {
                "id",
                "title",
                "description",
                "severity",
                "status",
                "risk_score",
                "rule_name",
                "rule",
                "user_id",
                "transaction_id",
                "metadata",
            }
        }

    return {
        "id": row.get("idcode"),
        "alert_key": row.get("uniquenum_pri"),
        "rule_name": rule_name,
        "rule": rule_name,
        "title": payload.get("title") or row.get("var_50_002") or rule_name,
        "description": payload.get("description") or payload.get("text") or "",
        "severity": severity,
        "status": status,
        "risk_score": risk_score,
        "masterfn": row.get("masterfn"),
        "companyfn": row.get("companyfn"),
        "user_id": payload.get("user_id") or row.get("var_25_001") or row.get("userid_cookie"),
        "transaction_id": (
            metadata.get("source_transaction_id")
            or payload.get("transaction_id")
            or row.get("var_25_002")
            or row.get("uniquenum_sec")
        ),
        "source": payload.get("source") or row.get("tag_others04") or row.get("tag_datasource"),
        "created_at": _dt(row.get("date_post")),
        "updated_at": _dt(row.get("date_lastupdate")),
        "event_at": _dt(row.get("date_trans")),
        "metadata": metadata,
    }


def _safe_transaction_view() -> str:
    view = os.getenv("FRAUD_TRANSACTION_VIEW", "fraud_transaction_source")
    if not view.replace("_", "").isalnum():
        raise HTTPException(500, "Invalid FRAUD_TRANSACTION_VIEW")
    return view


def _thresholds() -> Dict[str, Any]:
    def f(name: str, default: str) -> float:
        try:
            return float(os.getenv(name, default))
        except ValueError:
            return float(default)

    def i(name: str, default: str) -> int:
        try:
            return int(os.getenv(name, default))
        except ValueError:
            return int(default)

    return {
        "amount_low_multiplier": f("FRAUD_AMOUNT_LOW_MULTIPLIER", "2"),
        "amount_medium_multiplier": f("FRAUD_AMOUNT_MEDIUM_MULTIPLIER", "3"),
        "amount_high_multiplier": f("FRAUD_AMOUNT_HIGH_MULTIPLIER", "5"),
        "frequency_low_multiplier": f("FRAUD_FREQUENCY_LOW_MULTIPLIER", "2"),
        "frequency_medium_multiplier": f("FRAUD_FREQUENCY_MEDIUM_MULTIPLIER", "3"),
        "frequency_high_multiplier": f("FRAUD_FREQUENCY_HIGH_MULTIPLIER", "5"),
        "frequency_min_count": i("FRAUD_FREQUENCY_MIN_COUNT", "5"),
        "refund_low_count": i("FRAUD_REFUND_LOW_COUNT", "1"),
        "refund_medium_count": i("FRAUD_REFUND_MEDIUM_COUNT", "2"),
        "refund_high_count": i("FRAUD_REFUND_HIGH_COUNT", "4"),
        "discount_low_multiplier": f("FRAUD_DISCOUNT_LOW_MULTIPLIER", "2"),
        "discount_medium_multiplier": f("FRAUD_DISCOUNT_MEDIUM_MULTIPLIER", "3"),
        "discount_high_multiplier": f("FRAUD_DISCOUNT_HIGH_MULTIPLIER", "5"),
        "void_low_count": i("FRAUD_VOID_LOW_COUNT", "1"),
        "void_medium_count": i("FRAUD_VOID_MEDIUM_COUNT", "2"),
        "void_high_count": i("FRAUD_VOID_HIGH_COUNT", "4"),
        "invoice_modifications": i("FRAUD_INVOICE_MODIFICATIONS", "3"),
        "backdated_days": i("FRAUD_BACKDATED_DAYS", "7"),
    }


def _load_alert_item(alert_id: int, masterfn: str, companyfn: str) -> Dict[str, Any]:
    conn = get_erp_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """
            SELECT *
            FROM memo_long_table
            WHERE idcode = %s
              AND tag_table_usage = %s
              AND masterfn = %s
              AND companyfn = %s
              AND COALESCE(tag_deleted_yn, 'n') = 'n'
            """,
            [alert_id, MEMO_USAGE, masterfn, companyfn],
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Fraud alert not found")
        return _memo_item(dict(row))
    finally:
        conn.close()


def _metric_value(item: Dict[str, Any]) -> Any:
    meta = item.get("metadata") or {}
    rule = item.get("rule_name")
    if rule == "REPEATED_INVOICE_MODIFICATION":
        return meta.get("invoice_modifications")
    if rule == "HIGH_TRANSACTION_AMOUNT":
        return meta.get("amount")
    if rule == "ABNORMAL_DISCOUNT":
        return meta.get("discount")
    if rule == "HIGH_REFUND_COUNT":
        return meta.get("refund_count")
    if rule == "TOO_MANY_VOID_TRANSACTIONS":
        return meta.get("void_count")
    if rule == "TRANSACTION_FREQUENCY_SPIKE":
        return meta.get("daily_count")
    if rule == "BACKDATED_TRANSACTION":
        return meta.get("lag_days")
    return meta.get("value")


def _money(value: Any) -> str:
    try:
        return f"{float(value):,.2f}"
    except (TypeError, ValueError):
        return "-"


def _business_insight(item: Dict[str, Any]) -> Dict[str, Any]:
    meta = item.get("metadata") or {}
    rule = item.get("rule_name") or "UNKNOWN_RULE"
    doc = meta.get("document_no") or item.get("transaction_id") or "this document"
    user = item.get("user_id") or "this user"
    module = meta.get("fromtrans_label") or meta.get("document_type") or meta.get("fromtrans") or "this ERP transaction type"
    severity = (item.get("severity") or "LOW").upper()

    if rule == "HIGH_TRANSACTION_AMOUNT":
        amount = _money(meta.get("amount"))
        baseline = _money(meta.get("baseline_p95_amount") or meta.get("baseline_amount") or meta.get("baseline_average_amount"))
        ratio = meta.get("ratio")
        ratio_text = f"{float(ratio):.1f} times" if ratio not in (None, "") else "much"
        return {
            "user_summary": (
                f"{doc} should be reviewed because its amount is SGD {amount}, "
                f"which is {ratio_text} higher than what {user} normally enters for {module}."
            ),
            "plain_comparison": (
                f"Normal reference: most past {module} transactions by {user} were at or below SGD {baseline}. "
                f"This transaction is SGD {amount}."
            ),
            "business_rationale": [
                "The transaction amount is far outside the user's normal pattern for this document type.",
                "This does not prove fraud, but it is large enough that finance/control should verify the business reason.",
                "Priority is HIGH because the difference is not a small variation; it is an extreme outlier.",
            ],
            "reviewer_checklist": [
                "Open the audit trail and confirm who created or changed the document.",
                "Check whether customer order, quotation, approval, or supporting document justifies the amount.",
                "If the amount is valid, acknowledge the alert; if not, escalate to finance control.",
            ],
        }

    if rule == "REPEATED_INVOICE_MODIFICATION":
        mods = int(float(meta.get("invoice_modifications") or 0))
        return {
            "user_summary": f"{doc} should be reviewed because it was modified {mods} time(s).",
            "plain_comparison": "Repeated edits can be normal, but several changes on the same document deserve an audit trail check.",
            "business_rationale": [
                "The document was changed repeatedly after creation.",
                "Repeated edits may indicate correction work, approval changes, or unauthorized manipulation.",
                f"Priority is {severity} based on the number of changes.",
            ],
            "reviewer_checklist": [
                "Review the audit trail and changed fields.",
                "Check whether changes happened after approval, customer confirmation, or invoice posting.",
                "Confirm the changes were approved by the responsible supervisor.",
            ],
        }

    return {
        "user_summary": f"{doc} should be reviewed because it is unusual for {user}'s normal ERP activity.",
        "plain_comparison": "The alert compares this transaction with the user's historical behavior for the same ERP scope.",
        "business_rationale": [
            "The transaction differs from the user's normal pattern.",
            "This is a review indicator, not a fraud verdict.",
            f"Priority is {severity} based on the configured control rule.",
        ],
        "reviewer_checklist": [
            "Open the audit trail and confirm the business reason.",
            "Compare the document with approval and supporting records.",
            "Acknowledge if valid; escalate if the explanation is weak or missing.",
        ],
    }


def _fallback_ai_insight(item: Dict[str, Any]) -> Dict[str, Any]:
    meta = item.get("metadata") or {}
    rule = item.get("rule_name") or "UNKNOWN_RULE"
    thresholds = _thresholds()
    metric = _metric_value(item)
    severity = (item.get("severity") or "LOW").upper()
    confidence = {"CRITICAL": 0.88, "HIGH": 0.78, "MEDIUM": 0.63, "LOW": 0.48}.get(severity, 0.5)

    evidence = [
        f"Rule matched: {RULE_LABELS.get(rule, rule)}",
        f"Severity: {severity}; risk score: {item.get('risk_score', 0)}",
        f"Document: {meta.get('document_no') or item.get('transaction_id') or '-'}",
        f"User: {item.get('user_id') or '-'}",
    ]
    if metric not in (None, ""):
        evidence.append(f"Rule metric value: {metric}")

    if rule == "REPEATED_INVOICE_MODIFICATION":
        mods = int(float(meta.get("invoice_modifications") or 0))
        threshold = int(thresholds["invoice_modifications"])
        if mods >= threshold:
            summary = f"AI flags this document because it was edited {mods} times, meeting the configured HIGH threshold of {threshold} edits."
        elif mods == threshold - 1:
            summary = f"AI flags this document as MEDIUM because it was edited {mods} times, just below the HIGH threshold of {threshold} edits."
        else:
            summary = f"AI flags this document as LOW because it has {mods} edit event(s); it is worth checking but not yet a strong fraud signal."
        suggested_thresholds = [
            {"setting_key": "FRAUD_INVOICE_MODIFICATIONS", "current": threshold, "suggested": threshold, "reason": "Keep HIGH at configured repeated-edit threshold; use LOW/MEDIUM for early warning."},
            {"severity": "LOW", "condition": "invoice_modifications = 1"},
            {"severity": "MEDIUM", "condition": f"invoice_modifications = {max(1, threshold - 1)}"},
            {"severity": "HIGH", "condition": f"invoice_modifications >= {threshold}"},
        ]
    else:
        label = RULE_LABELS.get(rule, rule.replace("_", " ").title())
        summary = f"AI flags this as {severity} because {label.lower()} deviates from the user's historical baseline."
        suggested_thresholds = [
            {"setting_key": "current_rule", "current": meta.get("threshold") or "baseline multiplier", "suggested": "review after 7-14 days of production data", "reason": "Use baseline panel to tune this rule per company/user behavior."}
        ]

    return {
        "alert_id": item.get("id"),
        "ai_model": "rule-plus-ai-explainer-v1",
        "ai_available": False,
        "confidence": confidence,
        **_business_insight(item),
        "summary": summary,
        "risk_rationale": evidence,
        "evidence": {
            "transaction_id": item.get("transaction_id"),
            "document_no": meta.get("document_no"),
            "user_id": item.get("user_id"),
            "rule": rule,
            "metric": metric,
            "event_at": item.get("event_at"),
            "created_at": item.get("created_at"),
            "updated_at": item.get("updated_at"),
        },
        "suggested_actions": [
            "Open the transaction audit trail and verify who changed the document.",
            "Compare document amount/discount/refund/void pattern with the same user's normal behavior.",
            "If business reason is valid, acknowledge the alert; otherwise escalate to finance control.",
        ],
        "suggested_thresholds": suggested_thresholds,
        "questions_for_reviewer": [
            "Was the change approved by a supervisor?",
            "Did the edit happen after customer confirmation or invoice posting?",
            "Is this pattern repeated by the same user across multiple documents?",
        ],
    }


def _try_ai_insight(item: Dict[str, Any], fallback: Dict[str, Any]) -> Dict[str, Any]:
    try:
        from api.llm import LLM_MODEL, call_gemini_chat

        prompt = (
            "You are an ERP fraud-control analyst. Return ONLY valid compact JSON with keys: "
            "summary, confidence, risk_rationale, suggested_actions, suggested_thresholds, questions_for_reviewer. "
            "Write for an ERP business user, not a developer. Avoid alert IDs, internal rule codes, JSON field names, "
            "and jargon unless absolutely necessary. Do not claim fraud is proven. Treat this as a human-review indicator.\n\n"
            f"Alert JSON:\n{json.dumps(item, ensure_ascii=False, default=_json_default)}\n\n"
            f"Rule thresholds:\n{json.dumps(_thresholds(), ensure_ascii=False)}\n\n"
            f"Deterministic baseline insight:\n{json.dumps(fallback, ensure_ascii=False, default=_json_default)}"
        )
        msg = call_gemini_chat(
            [
                {"role": "system", "content": "Explain fraud indicators in plain ERP business language. Output JSON only."},
                {"role": "user", "content": prompt},
            ],
            timeout=30,
            retries=0,
        )
        raw = (msg.get("content") or "").strip()
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            parsed = json.loads(raw[start : end + 1])
            if isinstance(parsed, dict):
                return {
                    **fallback,
                    **parsed,
                    "alert_id": item.get("id"),
                    "ai_model": LLM_MODEL,
                    "ai_available": True,
                }
    except Exception as exc:
        fallback["ai_error"] = str(exc)[:240]
    return fallback


def _base_where(masterfn: str, companyfn: str) -> Tuple[List[str], List[Any]]:
    return [
        "tag_table_usage = %s",
        "masterfn = %s",
        "companyfn = %s",
        "COALESCE(tag_deleted_yn, 'n') = 'n'",
        "COALESCE(tag_void_yn, 'n') = 'n'",
    ], [MEMO_USAGE, masterfn, companyfn]


def _filtered_where(
    masterfn: str,
    companyfn: str,
    status: str = "",
    severity: str = "",
    date_from: str = "",
    date_to: str = "",
    search: str = "",
) -> Tuple[str, List[Any]]:
    where, params = _base_where(masterfn, companyfn)
    where.append("var_50_001 <> 'DUPLICATE_FINANCE_REFERENCE'")

    if status:
        where.append("UPPER(COALESCE(tag_others02, 'NEW')) = %s")
        params.append(status.upper())
    else:
        where.append("UPPER(COALESCE(tag_others02, 'NEW')) IN %s")
        params.append(tuple(ACTIVE))

    if severity:
        where.append("UPPER(COALESCE(tag_others01, 'LOW')) = %s")
        params.append(severity.upper())

    if date_from:
        where.append("COALESCE(date_trans, date_post) >= %s")
        params.append(date_from)

    if date_to:
        where.append("COALESCE(date_trans, date_post) < (%s::date + INTERVAL '1 day')")
        params.append(date_to)

    if search:
        needle = f"%{search}%"
        where.append(
            """(
                notes_memo ILIKE %s
                OR var_50_001 ILIKE %s
                OR var_50_002 ILIKE %s
                OR var_25_001 ILIKE %s
                OR var_25_002 ILIKE %s
                OR uniquenum_pri ILIKE %s
                OR uniquenum_sec ILIKE %s
            )"""
        )
        params.extend([needle] * 7)

    return " AND ".join(where), params


@router.get("/fraud-alerts")
async def list_fraud_alerts(
    masterfn: str = Query(...),
    companyfn: str = Query(...),
    status: str = "",
    severity: str = "",
    date_from: str = "",
    date_to: str = "",
    search: str = "",
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _key: str = Depends(verify_api_key),
):
    where, params = _filtered_where(masterfn, companyfn, status, severity, date_from, date_to, search)
    conn = get_erp_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(f"SELECT COUNT(*) AS count FROM memo_long_table WHERE {where}", params)
        total = int(cur.fetchone()["count"])
        cur.execute(
            f"""
            SELECT *
            FROM memo_long_table
            WHERE {where}
            ORDER BY COALESCE(num_20_2_d_001, 0) DESC, COALESCE(date_trans, date_post) DESC, idcode DESC
            LIMIT %s OFFSET %s
            """,
            params + [limit, offset],
        )
        rows = cur.fetchall()
        return {"total": total, "limit": limit, "offset": offset, "items": [_memo_item(dict(row)) for row in rows]}
    finally:
        conn.close()


@router.get("/fraud-alerts-summary")
async def fraud_alert_summary(
    masterfn: str = Query(...),
    companyfn: str = Query(...),
    _key: str = Depends(verify_api_key),
):
    state: Dict[str, Any] = {}
    if SCHEDULER_STATE_FILE.exists():
        try:
            state = json.loads(SCHEDULER_STATE_FILE.read_text(encoding="utf-8")).get("fraud", {})
        except (OSError, ValueError):
            pass
    result = state.get("last_result", {})
    scoped = result.get("by_scope", {}).get(f"{masterfn}|{companyfn}") if isinstance(result, dict) else None
    if scoped:
        state = dict(state)
        state["last_result"] = {**scoped, "masterfn": masterfn, "companyfn": companyfn}

    where, params = _base_where(masterfn, companyfn)
    conn = get_erp_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            f"""
            SELECT UPPER(COALESCE(tag_others02, 'NEW')) AS status, COUNT(*) AS count
            FROM memo_long_table
            WHERE {' AND '.join(where)}
            GROUP BY UPPER(COALESCE(tag_others02, 'NEW'))
            """,
            params,
        )
        rows = cur.fetchall()
        counts = {_normalize_status(row["status"]): int(row["count"]) for row in rows}
        cur.execute(
            f"""
            SELECT UPPER(COALESCE(tag_others01, 'LOW')) AS severity, COUNT(*) AS count
            FROM memo_long_table
            WHERE {' AND '.join(where)}
              AND UPPER(COALESCE(tag_others02, 'NEW')) IN %s
            GROUP BY UPPER(COALESCE(tag_others01, 'LOW'))
            """,
            params + [tuple(ACTIVE)],
        )
        severity_rows = cur.fetchall()
        severity_counts = {str(row["severity"]).upper(): int(row["count"]) for row in severity_rows}
        return {"scheduler": state, "alert_counts": counts, "severity_counts": severity_counts}
    finally:
        conn.close()


@router.get("/fraud-baselines")
async def fraud_baselines(
    masterfn: str = Query(...),
    companyfn: str = Query(...),
    days: int = Query(60, ge=1, le=365),
    _key: str = Depends(verify_api_key),
):
    view = _safe_transaction_view()
    cfg = _thresholds()
    conn = get_erp_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            f"""
            WITH scoped AS (
                SELECT *
                FROM {view}
                WHERE masterfn = %s
                  AND companyfn = %s
                  AND COALESCE(occurred_at, created_at) >= NOW() - (%s || ' days')::interval
            ),
            user_day AS (
                SELECT user_id, COALESCE(occurred_at::date, created_at::date) AS day_key, COUNT(*) AS daily_count
                FROM scoped
                GROUP BY user_id, COALESCE(occurred_at::date, created_at::date)
            )
            SELECT
                COUNT(*) AS transactions,
                COUNT(DISTINCT user_id) AS users,
                AVG(ABS(COALESCE(amount,0))) AS avg_amount,
                percentile_cont(0.5) WITHIN GROUP (ORDER BY ABS(COALESCE(amount,0))) AS median_amount,
                MAX(ABS(COALESCE(amount,0))) AS max_amount,
                AVG(COALESCE(discount,0)) AS avg_discount,
                percentile_cont(0.95) WITHIN GROUP (ORDER BY COALESCE(discount,0)) AS p95_discount,
                MAX(COALESCE(discount,0)) AS max_discount,
                AVG(COALESCE(refund_count,0)) AS avg_refund_count,
                MAX(COALESCE(refund_count,0)) AS max_refund_count,
                AVG(COALESCE(void_count,0)) AS avg_void_count,
                MAX(COALESCE(void_count,0)) AS max_void_count,
                AVG(COALESCE(invoice_modifications,0)) AS avg_invoice_modifications,
                SUM(CASE WHEN COALESCE(invoice_modifications,0) = 1 THEN 1 ELSE 0 END) AS modification_low_candidates,
                SUM(CASE WHEN COALESCE(invoice_modifications,0) = %s - 1 THEN 1 ELSE 0 END) AS modification_medium_candidates,
                SUM(CASE WHEN COALESCE(invoice_modifications,0) >= %s THEN 1 ELSE 0 END) AS modification_high_candidates,
                AVG(GREATEST(0, (created_at::date - occurred_at::date))) AS avg_backdated_days,
                MAX(GREATEST(0, (created_at::date - occurred_at::date))) AS max_backdated_days,
                (SELECT AVG(daily_count) FROM user_day) AS avg_daily_count,
                (SELECT MAX(daily_count) FROM user_day) AS max_daily_count
            FROM scoped
            """,
            [masterfn, companyfn, days, cfg["invoice_modifications"], cfg["invoice_modifications"]],
        )
        row = dict(cur.fetchone() or {})

        def n(key: str, default: float = 0) -> float:
            return float(row.get(key) or default)

        categories = [
            {
                "rule": "HIGH_TRANSACTION_AMOUNT",
                "label": RULE_LABELS["HIGH_TRANSACTION_AMOUNT"],
                "average": n("avg_amount"),
                "median": n("median_amount"),
                "max": n("max_amount"),
                "current_setting": f"LOW>={cfg['amount_low_multiplier']}x, MEDIUM>={cfg['amount_medium_multiplier']}x, HIGH>={cfg['amount_high_multiplier']}x user average",
                "suggested_setting": "Use tiered severity so 2x is early warning and 5x+ is high risk.",
                "apply_ai": "AI compares each transaction against the user's rolling amount baseline and explains the ratio.",
            },
            {
                "rule": "TRANSACTION_FREQUENCY_SPIKE",
                "label": RULE_LABELS["TRANSACTION_FREQUENCY_SPIKE"],
                "average": n("avg_daily_count"),
                "max": n("max_daily_count"),
                "current_setting": f"Minimum {cfg['frequency_min_count']} docs/day and LOW>={cfg['frequency_low_multiplier']}x, MEDIUM>={cfg['frequency_medium_multiplier']}x, HIGH>={cfg['frequency_high_multiplier']}x daily average",
                "suggested_setting": "Use minimum count plus ratio so low-volume users do not trigger noisy alerts.",
                "apply_ai": "AI checks whether the burst fits normal user timing or needs review.",
            },
            {
                "rule": "HIGH_REFUND_COUNT",
                "label": RULE_LABELS["HIGH_REFUND_COUNT"],
                "average": n("avg_refund_count"),
                "max": n("max_refund_count"),
                "current_setting": f"LOW>={cfg['refund_low_count']}, MEDIUM>={cfg['refund_medium_count']}, HIGH>={cfg['refund_high_count']} refund count",
                "suggested_setting": "Use absolute refund count tiers; compare with user baseline during review.",
                "apply_ai": "AI highlights refund activity that deviates from the user's own baseline.",
            },
            {
                "rule": "ABNORMAL_DISCOUNT",
                "label": RULE_LABELS["ABNORMAL_DISCOUNT"],
                "average": n("avg_discount"),
                "p95": n("p95_discount"),
                "max": n("max_discount"),
                "current_setting": f"LOW>={cfg['discount_low_multiplier']}x, MEDIUM>={cfg['discount_medium_multiplier']}x, HIGH>={cfg['discount_high_multiplier']}x user discount baseline",
                "suggested_setting": "Use p95 discount as a company sanity check, user baseline as primary check.",
                "apply_ai": "AI separates normal promotional discount patterns from user-specific outliers.",
            },
            {
                "rule": "TOO_MANY_VOID_TRANSACTIONS",
                "label": RULE_LABELS["TOO_MANY_VOID_TRANSACTIONS"],
                "average": n("avg_void_count"),
                "max": n("max_void_count"),
                "current_setting": f"LOW>={cfg['void_low_count']}, MEDIUM>={cfg['void_medium_count']}, HIGH>={cfg['void_high_count']} void count",
                "suggested_setting": "Use absolute void count tiers; compare with user baseline during review.",
                "apply_ai": "AI asks whether voids were operational corrections or suspicious repeated cancellations.",
            },
            {
                "rule": "REPEATED_INVOICE_MODIFICATION",
                "label": RULE_LABELS["REPEATED_INVOICE_MODIFICATION"],
                "average": n("avg_invoice_modifications"),
                "low_candidates": int(row.get("modification_low_candidates") or 0),
                "medium_candidates": int(row.get("modification_medium_candidates") or 0),
                "high_candidates": int(row.get("modification_high_candidates") or 0),
                "current_setting": f"LOW=1, MEDIUM={max(1, int(cfg['invoice_modifications']) - 1)}, HIGH>={int(cfg['invoice_modifications'])}",
                "suggested_setting": "Use 1 edit as early warning, 2 as medium, 3+ as high until reviewer history is enough",
                "apply_ai": "AI ranks repeated edits by count, timing, user, and document evidence.",
            },
            {
                "rule": "BACKDATED_TRANSACTION",
                "label": RULE_LABELS["BACKDATED_TRANSACTION"],
                "average": n("avg_backdated_days"),
                "max": n("max_backdated_days"),
                "current_setting": f">{int(cfg['backdated_days'])} days backdated",
                "suggested_setting": "Keep high severity for backdating beyond configured days",
                "apply_ai": "AI explains whether the transaction date is unusually earlier than creation date.",
            },
        ]
        return {
            "scope": {"masterfn": masterfn, "companyfn": companyfn, "days": days},
            "transactions": int(row.get("transactions") or 0),
            "users": int(row.get("users") or 0),
            "thresholds": cfg,
            "categories": categories,
        }
    finally:
        conn.close()


@router.get("/fraud-dashboard")
async def fraud_dashboard(
    masterfn: str = Query(...),
    companyfn: str = Query(...),
    _key: str = Depends(verify_api_key),
):
    view = _safe_transaction_view()
    conn = get_erp_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            f"""
            SELECT COALESCE(
                date_trunc('month', MAX(COALESCE(occurred_at, created_at))),
                date_trunc('month', NOW())
            ) AS period_start
            FROM {view}
            WHERE masterfn = %s
              AND companyfn = %s
            """,
            [masterfn, companyfn],
        )
        period_start = cur.fetchone()["period_start"]
        cur.execute(
            f"""
            WITH month_tx AS (
                SELECT
                    COALESCE(
                        NULLIF(metadata->>'fromtrans', ''),
                        NULLIF(metadata->>'document_type', ''),
                        split_part(transaction_id, ':', 2),
                        'UNKNOWN'
                    ) AS fromtrans,
                    COUNT(*) AS transactions,
                    COUNT(DISTINCT user_id) AS users,
                    SUM(ABS(COALESCE(amount, 0))) AS total_amount,
                    AVG(ABS(COALESCE(amount, 0))) AS avg_amount
                FROM {view}
                WHERE masterfn = %s
                  AND companyfn = %s
                  AND COALESCE(occurred_at, created_at) >= %s
                  AND COALESCE(occurred_at, created_at) < (%s::timestamp + INTERVAL '1 month')
                GROUP BY 1
            ),
            alert_tx AS (
                SELECT
                    COALESCE(
                        NULLIF((notes_memo::jsonb->'metadata'->>'fromtrans'), ''),
                        NULLIF((notes_memo::jsonb->'metadata'->>'document_type'), ''),
                        split_part(COALESCE(var_25_002, uniquenum_sec, ''), ':', 2),
                        'UNKNOWN'
                    ) AS fromtrans,
                    COUNT(*) AS alerts,
                    SUM(CASE WHEN UPPER(COALESCE(tag_others01, 'LOW')) = 'HIGH' THEN 1 ELSE 0 END) AS high_alerts,
                    SUM(CASE WHEN UPPER(COALESCE(tag_others01, 'LOW')) = 'MEDIUM' THEN 1 ELSE 0 END) AS medium_alerts,
                    SUM(CASE WHEN UPPER(COALESCE(tag_others01, 'LOW')) = 'LOW' THEN 1 ELSE 0 END) AS low_alerts
                FROM memo_long_table
                WHERE tag_table_usage = %s
                  AND masterfn = %s
                  AND companyfn = %s
                  AND COALESCE(tag_deleted_yn, 'n') = 'n'
                  AND UPPER(COALESCE(tag_others02, 'NEW')) IN %s
                GROUP BY 1
            )
            SELECT
                COALESCE(m.fromtrans, a.fromtrans) AS fromtrans,
                COALESCE(m.transactions, 0) AS transactions,
                COALESCE(m.users, 0) AS users,
                COALESCE(m.total_amount, 0) AS total_amount,
                COALESCE(m.avg_amount, 0) AS avg_amount,
                COALESCE(a.alerts, 0) AS alerts,
                COALESCE(a.high_alerts, 0) AS high_alerts,
                COALESCE(a.medium_alerts, 0) AS medium_alerts,
                COALESCE(a.low_alerts, 0) AS low_alerts
            FROM month_tx m
            FULL OUTER JOIN alert_tx a ON a.fromtrans = m.fromtrans
            ORDER BY COALESCE(a.alerts, 0) DESC, COALESCE(m.transactions, 0) DESC, COALESCE(m.fromtrans, a.fromtrans)
            """,
            [masterfn, companyfn, period_start, period_start, MEMO_USAGE, masterfn, companyfn, tuple(ACTIVE)],
        )
        rows = [dict(row) for row in cur.fetchall()]
        total_transactions = sum(int(r.get("transactions") or 0) for r in rows)
        total_alerts = sum(int(r.get("alerts") or 0) for r in rows)
        return {
            "scope": {"masterfn": masterfn, "companyfn": companyfn},
            "month": period_start.strftime("%Y-%m") if hasattr(period_start, "strftime") else str(period_start)[:7],
            "total_transactions": total_transactions,
            "total_alerts": total_alerts,
            "fromtrans": rows,
            "ai_entrypoints": [
                "Review fromtrans with high alert rate first.",
                "Open a module row to filter records, then use AI Insight on the document.",
                "Use AI baseline to decide whether rule thresholds should be tightened or relaxed for that module.",
            ],
        }
    finally:
        conn.close()


@router.get("/fraud-alerts/{alert_id}/ai-insight")
async def fraud_alert_ai_insight(
    alert_id: int,
    masterfn: str = Query(...),
    companyfn: str = Query(...),
    _key: str = Depends(verify_api_key),
):
    item = _load_alert_item(alert_id, masterfn, companyfn)
    fallback = _fallback_ai_insight(item)
    return _try_ai_insight(item, fallback)


@router.get("/fraud-alerts/{alert_id}")
async def get_fraud_alert(
    alert_id: int,
    masterfn: str = Query(...),
    companyfn: str = Query(...),
    _key: str = Depends(verify_api_key),
):
    return _load_alert_item(alert_id, masterfn, companyfn)


def _transition(alert_id: int, masterfn: str, companyfn: str, actor: str, target: str) -> Dict[str, Any]:
    closed_col = {
        "ACKNOWLEDGED": "tag_closed01_yn",
        "RESOLVED": "tag_closed02_yn",
        "HIDDEN": "tag_closed03_yn",
    }[target]
    conn = get_erp_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """
            SELECT idcode
            FROM memo_long_table
            WHERE idcode = %s
              AND tag_table_usage = %s
              AND masterfn = %s
              AND companyfn = %s
              AND COALESCE(tag_deleted_yn, 'n') = 'n'
            """,
            [alert_id, MEMO_USAGE, masterfn, companyfn],
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Fraud alert not found")
        cur.execute(
            f"""
            UPDATE memo_long_table
            SET tag_others02 = %s,
                {closed_col} = 'y',
                userid_cookie = %s,
                date_lastupdate = NOW()
            WHERE idcode = %s
            RETURNING idcode
            """,
            [target, actor[:10], alert_id],
        )
        conn.commit()
        return {"id": alert_id, "status": target}
    finally:
        conn.close()


@router.post("/fraud-alerts/{alert_id}/acknowledge")
async def acknowledge(
    alert_id: int,
    body: AlertAction,
    masterfn: str = Query(...),
    companyfn: str = Query(...),
    _key: str = Depends(verify_api_key),
):
    return _transition(alert_id, masterfn, companyfn, body.actor, "ACKNOWLEDGED")


@router.post("/fraud-alerts/{alert_id}/resolve")
async def resolve(
    alert_id: int,
    body: AlertAction,
    masterfn: str = Query(...),
    companyfn: str = Query(...),
    _key: str = Depends(verify_api_key),
):
    return _transition(alert_id, masterfn, companyfn, body.actor, "RESOLVED")


@router.post("/fraud-alerts/{alert_id}/hide")
async def hide(
    alert_id: int,
    body: AlertAction,
    masterfn: str = Query(...),
    companyfn: str = Query(...),
    _key: str = Depends(verify_api_key),
):
    return _transition(alert_id, masterfn, companyfn, body.actor, "HIDDEN")
