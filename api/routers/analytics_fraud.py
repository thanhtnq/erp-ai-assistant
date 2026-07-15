"""
ERP AI Assistant — Fraud Detection Router
Endpoints: /analytics/fraud-scan, /analytics/fraud/results, /analytics/fraud/findings/{id}
Queries real ERP data from PostgreSQL for fraud detection.
"""
import json
import traceback
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query

from api.auth import verify_api_key
from api.database import get_chat_conn
from api.models import FraudScanRequest, FraudFindingUpdate
from api.services.erp_db import (
    query_duplicate_ap_invoices,
    query_new_vendor_high_value,
    query_inventory_anomalies,
    query_finance_anomalies,
)

router = APIRouter()

FRAUD_TYPES = {
    "ap_invoice": "AP Invoice",
    "payment": "Payment",
    "vendor": "Vendor",
    "inventory": "Inventory",
    "finance": "Finance",
}

SEVERITY_LEVELS = ["critical", "high", "medium", "low"]


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def init_fraud_tables(conn):
    """Create fraud detection tables if they don't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS fraud_scans (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            masterfn       TEXT NOT NULL,
            companyfn      TEXT NOT NULL,
            date_from      TEXT,
            date_to        TEXT,
            scan_type      TEXT NOT NULL DEFAULT 'all',
            severity_filter TEXT NOT NULL DEFAULT 'all',
            total_findings INTEGER NOT NULL DEFAULT 0,
            critical_count INTEGER NOT NULL DEFAULT 0,
            high_count     INTEGER NOT NULL DEFAULT 0,
            medium_count   INTEGER NOT NULL DEFAULT 0,
            low_count      INTEGER NOT NULL DEFAULT 0,
            status         TEXT NOT NULL DEFAULT 'completed',
            created_at     TEXT NOT NULL,
            completed_at   TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS fraud_findings (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_id        INTEGER NOT NULL,
            masterfn       TEXT NOT NULL,
            companyfn      TEXT NOT NULL,
            severity       TEXT NOT NULL DEFAULT 'medium',
            title          TEXT NOT NULL,
            description    TEXT NOT NULL DEFAULT '',
            source_id      TEXT,
            finding_type   TEXT NOT NULL DEFAULT 'other',
            risk_score     REAL NOT NULL DEFAULT 0,
            evidence_json  TEXT NOT NULL DEFAULT '{}',
            status         TEXT NOT NULL DEFAULT 'open',
            reviewer       TEXT,
            review_note    TEXT,
            created_at     TEXT NOT NULL,
            updated_at     TEXT NOT NULL,
            FOREIGN KEY (scan_id) REFERENCES fraud_scans(id)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_fraud_findings_scope
        ON fraud_findings(masterfn, companyfn, severity, status)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_fraud_scans_scope
        ON fraud_scans(masterfn, companyfn, created_at)
    """)
    conn.commit()


# ─── Query real ERP data for fraud detection ──────────────────────────────
def _run_real_fraud_scan(masterfn: str, companyfn: str, scan_id: int,
                         scan_type: str = "all", severity_filter: str = "all",
                         date_from: str = None, date_to: str = None,
                         max_findings: int = 8) -> tuple:
    """
    Run fraud detection queries against the real ERP PostgreSQL database.
    Returns (findings, partial_errors) tuple.
    partial_errors contains structured info about upstream tool failures.
    """
    findings = []
    partial_errors = []
    limit_per_type = max(1, max_findings // 4)

    def _safe_query(query_fn, query_name, *args, **kwargs):
        """Run a query safely, capturing errors as partial errors."""
        try:
            results = query_fn(*args, **kwargs)
            return results
        except Exception as e:
            partial_errors.append({
                "source": query_name,
                "error_type": type(e).__name__,
                "message": str(e)[:200],
                "detail": traceback.format_exc()[:500],
            })
            return []

    if scan_type == "all" or scan_type == "ap_invoice":
        dupes = _safe_query(
            query_duplicate_ap_invoices, "query_duplicate_ap_invoices",
            masterfn, companyfn, date_from, date_to, limit=limit_per_type
        )
        for d in dupes:
            if severity_filter == "all" or d["severity"] == severity_filter:
                findings.append(d)

    if scan_type == "all" or scan_type == "vendor":
        new_vendors = _safe_query(
            query_new_vendor_high_value, "query_new_vendor_high_value",
            masterfn, companyfn, date_from, date_to, limit=limit_per_type
        )
        for v in new_vendors:
            if severity_filter == "all" or v["severity"] == severity_filter:
                findings.append(v)

    if scan_type == "all" or scan_type == "inventory":
        inv_anomalies = _safe_query(
            query_inventory_anomalies, "query_inventory_anomalies",
            masterfn, companyfn, date_from, date_to, limit=limit_per_type
        )
        for inv in inv_anomalies:
            if severity_filter == "all" or inv["severity"] == severity_filter:
                findings.append(inv)

    if scan_type == "all" or scan_type == "finance":
        fin_anomalies = _safe_query(
            query_finance_anomalies, "query_finance_anomalies",
            masterfn, companyfn, date_from, date_to, limit=limit_per_type
        )
        for fin in fin_anomalies:
            if severity_filter == "all" or fin["severity"] == severity_filter:
                findings.append(fin)

    # Limit total findings
    findings = findings[:max_findings]

    # Add metadata for each finding
    now = now_iso()
    for f in findings:
        f["scan_id"] = scan_id
        f["masterfn"] = masterfn
        f["companyfn"] = companyfn
        f["evidence_json"] = json.dumps({
            "detected_at": now,
            "source": "erp_postgresql",
            "data_type": "live",
        })
        f["status"] = "open"
        f["created_at"] = now
        f["updated_at"] = now

    return findings, partial_errors


# ─── Endpoints ─────────────────────────────────────────────────────────────

@router.post("/analytics/fraud-scan")
async def run_fraud_scan(
    body: FraudScanRequest,
    _key: str = Depends(verify_api_key),
):
    """
    Run a fraud detection scan against live ERP data.

    Required scope: masterfn, companyfn
    Returns structured findings with severity counts and partial-error info.
    """
    if not body.masterfn or not body.companyfn:
        raise HTTPException(400, "masterfn and companyfn are required")

    conn = get_chat_conn()
    init_fraud_tables(conn)

    now = now_iso()

    # Create scan record
    cur = conn.execute("""
        INSERT INTO fraud_scans
            (masterfn, companyfn, date_from, date_to, scan_type, severity_filter,
             total_findings, critical_count, high_count, medium_count, low_count,
             status, created_at, completed_at)
        VALUES (?, ?, ?, ?, ?, ?, 0, 0, 0, 0, 0, 'running', ?, NULL)
    """, (body.masterfn, body.companyfn, body.date_from, body.date_to,
          body.scan_type or "all", body.severity or "all", now))
    scan_id = cur.lastrowid

    # Run real fraud detection queries against ERP PostgreSQL database
    findings, partial_errors = _run_real_fraud_scan(
        body.masterfn, body.companyfn, scan_id,
        scan_type=body.scan_type or "all",
        severity_filter=body.severity or "all",
        date_from=body.date_from,
        date_to=body.date_to,
        max_findings=body.max_findings or 8,
    )

    # Insert findings and also persist to ai_alerts (durable alerts)
    alerts_created = 0
    for f in findings:
        conn.execute("""
            INSERT INTO fraud_findings
                (scan_id, masterfn, companyfn, severity, title, description,
                 source_id, finding_type, risk_score, evidence_json,
                 status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (f["scan_id"], f["masterfn"], f["companyfn"], f["severity"],
              f["title"], f["description"], f["source_id"], f["finding_type"],
              f["risk_score"], f["evidence_json"], f["status"],
              f["created_at"], f["updated_at"]))

        # Deduplicate into ai_alerts: skip if same masterfn+companyfn+source_id+open status exists
        existing = conn.execute("""
            SELECT id FROM ai_alerts
            WHERE masterfn=? AND companyfn=? AND source_id=?
              AND status IN ('new','investigating')
            LIMIT 1
        """, (f["masterfn"], f["companyfn"], f["source_id"])).fetchone()

        if not existing:
            conn.execute("""
                INSERT INTO ai_alerts
                    (masterfn, companyfn, alert_type, severity, status,
                     title, reason_code, risk_score, source_id,
                     evidence_json, rule_version, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'new',
                        ?, ?, ?, ?,
                        ?, ?, ?, ?)
            """, (
                f["masterfn"], f["companyfn"],
                f["finding_type"] or "fraud",
                f["severity"],
                f["title"],
                f["finding_type"],
                f["risk_score"],
                f["source_id"],
                f["evidence_json"],
                "fraud_scan_v1",
                f["created_at"], f["updated_at"],
            ))
            alerts_created += 1

    # Update scan summary

    critical = sum(1 for f in findings if f["severity"] == "critical")
    high = sum(1 for f in findings if f["severity"] == "high")
    medium = sum(1 for f in findings if f["severity"] == "medium")
    low = sum(1 for f in findings if f["severity"] == "low")

    conn.execute("""
        UPDATE fraud_scans SET
            total_findings = ?, critical_count = ?, high_count = ?,
            medium_count = ?, low_count = ?, status = 'completed',
            completed_at = ?
        WHERE id = ?
    """, (len(findings), critical, high, medium, low, now, scan_id))
    conn.commit()
    conn.close()

    response = {
        "scan_id": scan_id,
        "status": "completed",
        "summary": {
            "total_findings": len(findings),
            "critical_count": critical,
            "high_count": high,
            "medium_count": medium,
            "low_count": low,
        },
        "findings": findings,
        "disclaimer": (
            "These findings are indicators for human review, "
            "not definitive fraud verdicts."
        ),
    }

    # Include partial errors if any upstream tool failed
    if partial_errors:
        response["partial_errors"] = partial_errors

    return response



@router.get("/analytics/fraud/results")
async def get_fraud_results(
    masterfn: str = Query(...),
    companyfn: str = Query(...),
    scan_id: int = Query(None),
    severity: str = Query("all"),
    finding_type: str = Query("all"),
    status: str = Query(""),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    _key: str = Depends(verify_api_key),
):
    """Get fraud scan results with optional filters."""
    conn = get_chat_conn()
    init_fraud_tables(conn)

    # Get latest scan if scan_id not specified
    if not scan_id:
        row = conn.execute("""
            SELECT id FROM fraud_scans
            WHERE masterfn=? AND companyfn=?
            ORDER BY created_at DESC LIMIT 1
        """, (masterfn, companyfn)).fetchone()
        if not row:
            conn.close()
            return {"total": 0, "items": [], "summary": None}
        scan_id = row["id"]

    # Get scan summary
    scan = conn.execute("""
        SELECT * FROM fraud_scans WHERE id=? AND masterfn=? AND companyfn=?
    """, (scan_id, masterfn, companyfn)).fetchone()
    if not scan:
        conn.close()
        raise HTTPException(404, "Scan not found")

    # Build query for findings
    where = ["scan_id=?", "masterfn=?", "companyfn=?"]
    params = [scan_id, masterfn, companyfn]
    if severity != "all":
        where.append("severity=?")
        params.append(severity)
    if finding_type != "all":
        where.append("finding_type=?")
        params.append(finding_type)
    if status:
        where.append("status=?")
        params.append(status)

    w = " AND ".join(where)
    total = conn.execute(f"SELECT COUNT(*) FROM fraud_findings WHERE {w}", params).fetchone()[0]
    rows = conn.execute(
        f"SELECT * FROM fraud_findings WHERE {w} ORDER BY risk_score DESC, created_at DESC LIMIT ? OFFSET ?",
        params + [limit, offset]
    ).fetchall()
    conn.close()

    items = []
    for row in rows:
        item = dict(row)
        item["evidence"] = json.loads(item.pop("evidence_json") or "{}")
        items.append(item)

    return {
        "total": total,
        "items": items,
        "summary": {
            "scan_id": scan["id"],
            "date_from": scan["date_from"],
            "date_to": scan["date_to"],
            "scan_type": scan["scan_type"],
            "total_findings": scan["total_findings"],
            "critical_count": scan["critical_count"],
            "high_count": scan["high_count"],
            "medium_count": scan["medium_count"],
            "low_count": scan["low_count"],
            "created_at": scan["created_at"],
            "completed_at": scan["completed_at"],
        },
    }


@router.patch("/analytics/fraud/findings/{finding_id}")
async def update_finding(
    finding_id: int,
    body: FraudFindingUpdate,
    _key: str = Depends(verify_api_key),
):
    """Update a fraud finding (status, review notes)."""
    conn = get_chat_conn()
    init_fraud_tables(conn)

    row = conn.execute(
        "SELECT id FROM fraud_findings WHERE id=? AND masterfn=? AND companyfn=?",
        (finding_id, body.masterfn, body.companyfn)
    ).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, "Finding not found")

    updates = []
    params = []
    if body.status:
        updates.append("status=?")
        params.append(body.status)
    if body.reviewer:
        updates.append("reviewer=?")
        params.append(body.reviewer)
    if body.review_note is not None:
        updates.append("review_note=?")
        params.append(body.review_note)

    if updates:
        updates.append("updated_at=?")
        params.append(now_iso())
        params.append(finding_id)
        conn.execute(
            f"UPDATE fraud_findings SET {', '.join(updates)} WHERE id=?",
            params
        )
        conn.commit()

    conn.close()
    return {"id": finding_id, "status": body.status or "updated"}


@router.get("/analytics/fraud/scans")
async def list_scans(
    masterfn: str = Query(...),
    companyfn: str = Query(...),
    limit: int = Query(10, le=50),
    _key: str = Depends(verify_api_key),
):
    """List recent fraud scans."""
    conn = get_chat_conn()
    init_fraud_tables(conn)
    rows = conn.execute("""
        SELECT * FROM fraud_scans
        WHERE masterfn=? AND companyfn=?
        ORDER BY created_at DESC LIMIT ?
    """, (masterfn, companyfn, limit)).fetchall()
    conn.close()
    return {"scans": [dict(r) for r in rows]}
