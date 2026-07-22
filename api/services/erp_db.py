"""
ERP AI Assistant — PostgreSQL ERP Database Service
Queries real ERP data from Globe3 PostgreSQL database for fraud detection and demand planning.
"""
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=True)

try:
    import psycopg2
    import psycopg2.extras
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False


def get_erp_conn():
    """Get a connection to the ERP PostgreSQL database."""
    if not HAS_PSYCOPG2:
        raise RuntimeError("psycopg2 is not installed. Run: pip install psycopg2-binary")
    
    conn = psycopg2.connect(
        host=os.getenv("PG_HOST", "localhost"),
        port=int(os.getenv("PG_PORT", "5432")),
        dbname=os.getenv("PG_DBNAME", "v57udemo2011"),
        user=os.getenv("PG_USER", "postgres"),
        password=os.getenv("PG_PASSWORD", "123"),
    )
    conn.autocommit = True
    return conn


def now_iso():
    return datetime.now(timezone.utc).isoformat()


# ─── Fraud Detection Queries ────────────────────────────────────────────────

def query_duplicate_ap_invoices(masterfn: str, companyfn: str,
                                 date_from: Optional[str] = None,
                                 date_to: Optional[str] = None,
                                 limit: int = 10):
    """
    Detect duplicate AP invoices by matching vendor, amount, and date proximity.
    Uses scm_pur_main (Purchase Invoice headers) + scm_pur_data (line items).
    Join: scm_pur_data.uniquenum_sec = scm_pur_main.uniquenum_pri
    """
    conn = get_erp_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    where = """m.tag_deleted_yn = 'n' AND m.tag_void_yn = 'n'
               AND m.cslsegm = 'pur_pi'
               AND m.masterfn = %s AND m.companyfn = %s"""
    params = [masterfn, companyfn]
    
    if date_from:
        where += " AND m.date_post >= %s"
        params.append(date_from)
    if date_to:
        where += " AND m.date_post <= %s"
        params.append(date_to)
    
    # Find invoices with same vendor (holdfn) and similar amounts
    sql = f"""
        SELECT 
            m.idcode,
            m.uniquenum_pri AS docnum,
            m.holdfn AS vendor_id,
            m.date_post,
            m.wflow_status,
            m.notes_memo,
            COALESCE(d.amount_total, 0) AS amount
        FROM scm_pur_main m
        LEFT JOIN (
            SELECT uniquenum_sec, SUM(COALESCE(amount_forex, 0)) AS amount_total
            FROM scm_pur_data
            WHERE tag_deleted_yn = 'n'
            GROUP BY uniquenum_sec
        ) d ON d.uniquenum_sec = m.uniquenum_pri
        WHERE {where}
        ORDER BY m.date_post DESC
        LIMIT %s
    """

    params.append(limit)
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    # Detect duplicates: same vendor, similar amount, close dates
    findings = []
    for i, row in enumerate(rows):
        for j in range(i + 1, len(rows)):
            r2 = rows[j]
            if row["vendor_id"] == r2["vendor_id"] and row["amount"] > 0 and r2["amount"] > 0:
                amt_diff = abs(row["amount"] - r2["amount"]) / max(row["amount"], r2["amount"])
                if amt_diff < 0.05:  # Within 5% amount difference
                    findings.append({
                        "severity": "critical",
                        "title": "Duplicate AP Invoice Detected",
                        "description": (
                            f"Invoice {row['docnum']} (${row['amount']:,.2f}) "
                            f"matches invoice {r2['docnum']} (${r2['amount']:,.2f}). "
                            f"Same vendor, similar amount."
                        ),
                        "source_id": str(row["docnum"]),
                        "finding_type": "ap_invoice",
                        "risk_score": 96,
                    })
                    break
    
    return findings


def query_new_vendor_high_value(masterfn: str, companyfn: str,
                                 date_from: Optional[str] = None,
                                 date_to: Optional[str] = None,
                                 limit: int = 5):
    """
    Detect new vendors with unusually high first transactions.
    Uses adm_cnt_main (vendor master) and scm_pur_main (purchase invoices).
    Join: scm_pur_data.uniquenum_sec = scm_pur_main.uniquenum_pri
    """
    conn = get_erp_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    where = """m.tag_deleted_yn = 'n' AND m.tag_void_yn = 'n'
               AND m.cslsegm = 'pur_pi'
               AND m.masterfn = %s AND m.companyfn = %s"""
    params = [masterfn, companyfn]
    
    if date_from:
        where += " AND m.date_post >= %s"
        params.append(date_from)
    if date_to:
        where += " AND m.date_post <= %s"
        params.append(date_to)
    
    sql = f"""
        SELECT 
            m.idcode,
            m.uniquenum_pri AS docnum,
            m.holdfn AS vendor_id,
            m.date_post,
            COALESCE(d.amount_total, 0) AS amount,
            c.date_post AS vendor_created_date,
            c.tag_active_yn
        FROM scm_pur_main m
        LEFT JOIN (
            SELECT uniquenum_sec, SUM(COALESCE(amount_forex, 0)) AS amount_total
            FROM scm_pur_data
            WHERE tag_deleted_yn = 'n'
            GROUP BY uniquenum_sec
        ) d ON d.uniquenum_sec = m.uniquenum_pri
        LEFT JOIN adm_cnt_main c ON c.uniquenum_pri = m.holdfn
            AND c.masterfn = m.masterfn
        WHERE {where}
            AND c.date_post >= m.date_post - INTERVAL '90 days'
        ORDER BY m.date_post DESC
        LIMIT %s
    """
    params.append(limit)
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    findings = []
    threshold = 25000  # $25,000 new vendor threshold
    for row in rows:
        if row["amount"] > threshold:
            findings.append({
                "severity": "high",
                "title": "New Vendor - High Value Transaction",
                "description": (
                    f"Vendor {row['vendor_id']} received payment of ${row['amount']:,.2f} "
                    f"— exceeds new vendor threshold of ${threshold:,.2f}."
                ),
                "source_id": str(row["vendor_id"]),
                "finding_type": "vendor",
                "risk_score": 84,
            })
    
    return findings


def query_inventory_anomalies(masterfn: str, companyfn: str,
                               date_from: Optional[str] = None,
                               date_to: Optional[str] = None,
                               limit: int = 5):
    """
    Detect inventory anomalies: negative stock, unusual adjustments.
    Uses scm_stk_main and scm_stk_data.
    Join: scm_stk_data.uniquenum_sec = scm_stk_main.uniquenum_pri
    """
    conn = get_erp_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    where = """m.tag_deleted_yn = 'n' AND m.tag_void_yn = 'n'
               AND m.masterfn = %s AND m.companyfn = %s"""
    params = [masterfn, companyfn]
    
    if date_from:
        where += " AND m.date_post >= %s"
        params.append(date_from)
    if date_to:
        where += " AND m.date_post <= %s"
        params.append(date_to)
    
    sql = f"""
        SELECT 
            m.idcode,
            m.uniquenum_pri AS docnum,
            m.date_post,
            m.notes_memo,
            d.stkcode_code,
            d.qnty_total AS qnty,
            d.amount_forex AS amount

        FROM scm_stk_main m
        JOIN scm_stk_data d ON d.uniquenum_sec = m.uniquenum_pri
            AND d.tag_deleted_yn = 'n'
        WHERE {where}
            AND (d.qnty_total < 0 OR ABS(d.qnty_total) > 1000)
        ORDER BY ABS(d.qnty_total) DESC
        LIMIT %s
    """
    params.append(limit)
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    findings = []
    for row in rows:
        findings.append({
            "severity": "medium",
            "title": "Inventory Movement Anomaly",
            "description": (
                f"Stock adjustment {row['docnum']}: SKU {row['stkcode_code']} "
                f"quantity {row['qnty']:,.2f} "
                f"(amount: ${abs(row['amount'] or 0):,.2f}). "
                f"Unusual movement flagged for review."
            ),
            "source_id": str(row["docnum"]),
            "finding_type": "inventory",
            "risk_score": 65,
        })
    
    return findings


def query_finance_anomalies(masterfn: str, companyfn: str,
                             date_from: Optional[str] = None,
                             date_to: Optional[str] = None,
                             limit: int = 5):
    """
    Detect finance anomalies: unusual journal entries, round amounts.
    Uses gen_ledger_detail.
    """
    conn = get_erp_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    where = """masterfn = %s AND companyfn = %s"""
    params = [masterfn, companyfn]
    
    if date_from:
        where += " AND date_post >= %s"
        params.append(date_from)
    if date_to:
        where += " AND date_post <= %s"
        params.append(date_to)
    
    sql = f"""
        SELECT 
            idcode,
            uniquenum_pri AS docnum,
            date_post,
            amount_forex AS amount,
            acctnumdisp AS acctnum
        FROM gen_ledger_detail
        WHERE {where}
            AND ABS(amount_forex) > 50000
        ORDER BY ABS(amount_forex) DESC
        LIMIT %s
    """

    params.append(limit)
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    findings = []
    for row in rows:
        findings.append({
            "severity": "medium",
            "title": "Large Journal Entry",
            "description": (
                f"Journal {row['docnum']}: ${abs(row['amount']):,.2f} "
                f"(account: {row['acctnum']}). "
                f"Large amount flagged for review."
            ),
            "source_id": str(row["docnum"]),
            "finding_type": "finance",
            "risk_score": 55,
        })
    
    return findings


FINANCE_FORMTRANS = {
    "bank_payment": ("csh_paym", "Bank Payment"),
    "bank_receipt": ("csh_recp", "Bank Receipt"),
    "general_journal": ("sub_jour", "General Journal"),
}


def _finance_date_filters(date_from: Optional[str], date_to: Optional[str], params: list) -> str:
    where = ""
    if date_from:
        where += " AND m.date_post >= %s"
        params.append(date_from)
    else:
        where += " AND m.date_post >= CURRENT_DATE - INTERVAL '365 days'"
    if date_to:
        where += " AND m.date_post <= %s"
        params.append(date_to)
    return where


def query_finance_formtrans_anomalies(masterfn: str, companyfn: str,
                                      source_type: str,
                                      date_from: Optional[str] = None,
                                      date_to: Optional[str] = None,
                                      limit: int = 5):
    """
    Detect finance form anomalies for Bank Payment, Bank Receipt, and General Journal.

    These three documents share the finance form pipeline:
    - fin_mod_main: document header
    - fin_mod_data: finance row items
    - gen_ledger_detail: posted GL evidence
    """
    if source_type not in FINANCE_FORMTRANS:
        raise ValueError(f"Unsupported finance source_type: {source_type}")

    fromtrans, label = FINANCE_FORMTRANS[source_type]
    conn = get_erp_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    findings = []

    base_params = [masterfn, companyfn, fromtrans]
    date_sql = _finance_date_filters(date_from, date_to, base_params)
    active_sql = """
        COALESCE(m.tag_deleted_yn, 'n') = 'n'
        AND COALESCE(m.tag_void_yn, 'n') = 'n'
        AND m.masterfn = %s
        AND m.companyfn = %s
        AND m.tag_table_usage = %s
    """

    # 1) Large finance document by header amount.
    cur.execute(
        f"""
        SELECT
            m.uniquenum_pri,
            m.dnum_auto,
            m.dnum_reference,
            m.dnum_check,
            m.date_trans,
            m.date_post,
            m.userid_cookie,
            m.party_code,
            m.party_desc,
            m.curr_short_forex,
            COALESCE(m.amount_local, 0) AS amount_local
        FROM fin_mod_main m
        WHERE {active_sql}
          {date_sql}
          AND ABS(COALESCE(m.amount_local, 0)) >= %s
        ORDER BY ABS(COALESCE(m.amount_local, 0)) DESC
        LIMIT %s
        """,
        base_params + [50000, limit],
    )
    for row in cur.fetchall():
        amount = float(row["amount_local"] or 0)
        doc = row["dnum_auto"] or row["uniquenum_pri"]
        findings.append({
            "severity": "high" if abs(amount) >= 100000 else "medium",
            "title": f"Large {label} Amount",
            "description": (
                f"{label} {doc} has local amount {abs(amount):,.2f}. "
                "This is above the finance review threshold and should be checked against approval and supporting documents."
            ),
            "source_id": str(row["uniquenum_pri"]),
            "finding_type": source_type,
            "risk_score": 82 if abs(amount) >= 100000 else 68,
            "evidence": {
                "source_type": source_type,
                "fromtrans": fromtrans,
                "uniquenum_pri": str(row["uniquenum_pri"]),
                "source_transaction_id": f"finance:{fromtrans}:{row['uniquenum_pri']}",
                "document_no": doc,
                "reference_no": row["dnum_reference"],
                "check_no": row["dnum_check"],
                "party_code": row["party_code"],
                "party_name": row["party_desc"],
                "amount_local": amount,
                "currency": row["curr_short_forex"],
                "transaction_date": str(row["date_trans"]) if row["date_trans"] else None,
                "created_at": str(row["date_post"]) if row["date_post"] else None,
                "created_by": row["userid_cookie"],
                "audit_hint": "Review fin_mod_main, fin_mod_data, gen_ledger_detail and the document audit trail for this source_id.",
            },
        })

    # 2) Duplicate payment reference/check/doc evidence.
    # Bank receipt references can be reused in normal receipt workflows, so do not
    # treat them as fraud signals for the demo/default rules.
    if source_type == "bank_payment" and os.getenv("FRAUD_ENABLE_DUPLICATE_FINANCE_REFERENCE", "false").lower() in {"1", "true", "yes", "y"}:
        dup_params = [masterfn, companyfn, fromtrans]
        dup_date_sql = _finance_date_filters(date_from, date_to, dup_params)
        cur.execute(
            f"""
            WITH docs AS (
                SELECT *
                FROM (
                    SELECT
                        m.uniquenum_pri,
                        m.dnum_auto,
                        m.dnum_reference,
                        m.dnum_check,
                        m.party_code,
                        m.party_desc,
                        m.curr_short_forex,
                        m.date_post,
                        ABS(COALESCE(m.amount_local, 0)) AS amount_local,
                        COALESCE(NULLIF(TRIM(m.dnum_check), ''), NULLIF(TRIM(m.dnum_reference), ''), NULLIF(TRIM(m.dnum_auto), '')) AS ref_key
                    FROM fin_mod_main m
                    WHERE {active_sql}
                      {dup_date_sql}
                    ORDER BY m.date_post DESC
                    LIMIT 5000
                ) recent_docs
            ),
            dupes AS (
                SELECT
                    ref_key, party_code, curr_short_forex, amount_local, COUNT(*) AS doc_count
                FROM docs
                WHERE ref_key IS NOT NULL AND amount_local > 0
                GROUP BY ref_key, party_code, curr_short_forex, amount_local
                HAVING COUNT(*) > 1
            )
            SELECT d.*, x.doc_count
            FROM docs d
            JOIN dupes x
              ON x.ref_key = d.ref_key
             AND COALESCE(x.party_code, '') = COALESCE(d.party_code, '')
             AND COALESCE(x.curr_short_forex, '') = COALESCE(d.curr_short_forex, '')
             AND x.amount_local = d.amount_local
            ORDER BY d.date_post DESC
            LIMIT %s
            """,
            dup_params + [limit],
        )
        for row in cur.fetchall():
            doc = row["dnum_auto"] or row["uniquenum_pri"]
            findings.append({
                "severity": "critical",
                "title": f"Duplicate {label} Reference",
                "description": (
                    f"{label} {doc} shares reference/check {row['ref_key']} with "
                    f"{row['doc_count']} document(s) for the same party and amount."
                ),
                "source_id": str(row["uniquenum_pri"]),
                "finding_type": source_type,
                "risk_score": 94,
                "evidence": {
                    "source_type": source_type,
                    "fromtrans": fromtrans,
                    "uniquenum_pri": str(row["uniquenum_pri"]),
                    "source_transaction_id": f"finance:{fromtrans}:{row['uniquenum_pri']}",
                    "document_no": doc,
                    "reference_key": row["ref_key"],
                    "party_code": row["party_code"],
                    "party_name": row["party_desc"],
                    "amount_local": float(row["amount_local"] or 0),
                    "duplicate_count": int(row["doc_count"] or 0),
                    "audit_hint": "Compare fin_mod_main references/check number and review audit trail for duplicate entry or re-submit.",
                },
            })

    # 3) Backdated finance document.
    back_params = [masterfn, companyfn, fromtrans]
    back_date_sql = _finance_date_filters(date_from, date_to, back_params)
    cur.execute(
        f"""
        SELECT
            m.uniquenum_pri,
            m.dnum_auto,
            m.date_trans,
            m.date_post,
            m.userid_cookie,
            m.party_code,
            m.party_desc,
            (m.date_post::date - m.date_trans::date)::int AS lag_days
        FROM fin_mod_main m
        WHERE {active_sql}
          {back_date_sql}
          AND m.date_trans IS NOT NULL
          AND m.date_post IS NOT NULL
          AND m.date_post::date - m.date_trans::date >= 14
        ORDER BY lag_days DESC
        LIMIT %s
        """,
        back_params + [limit],
    )
    for row in cur.fetchall():
        doc = row["dnum_auto"] or row["uniquenum_pri"]
        lag_days = int(row["lag_days"] or 0)
        findings.append({
            "severity": "high" if lag_days >= 30 else "medium",
            "title": f"Backdated {label}",
            "description": (
                f"{label} {doc} was created/posted {lag_days} day(s) after the transaction date. "
                "Review the audit trail and period-close approval."
            ),
            "source_id": str(row["uniquenum_pri"]),
            "finding_type": source_type,
            "risk_score": 80 if lag_days >= 30 else 64,
            "evidence": {
                "source_type": source_type,
                "fromtrans": fromtrans,
                "uniquenum_pri": str(row["uniquenum_pri"]),
                "source_transaction_id": f"finance:{fromtrans}:{row['uniquenum_pri']}",
                "document_no": doc,
                "transaction_date": str(row["date_trans"]) if row["date_trans"] else None,
                "created_at": str(row["date_post"]) if row["date_post"] else None,
                "created_by": row["userid_cookie"],
                "lag_days": lag_days,
                "party_code": row["party_code"],
                "party_name": row["party_desc"],
                "audit_hint": "Check who created/edited this document and whether backdating was approved.",
            },
        })

    # 4) GL posting imbalance for the same finance document.
    gl_params = [masterfn, companyfn, fromtrans]
    gl_date_sql = _finance_date_filters(date_from, date_to, gl_params)
    cur.execute(
        f"""
        SELECT
            m.uniquenum_pri,
            m.dnum_auto,
            m.date_post,
            COUNT(g.idcode) AS gl_rows,
            SUM(COALESCE(g.amount_local, 0)) AS gl_balance_local
        FROM fin_mod_main m
        JOIN gen_ledger_detail g
          ON g.uniquenum_pri = m.uniquenum_pri
         AND g.masterfn = m.masterfn
         AND g.companyfn = m.companyfn
        WHERE {active_sql}
          {gl_date_sql}
        GROUP BY m.uniquenum_pri, m.dnum_auto, m.date_post
        HAVING ABS(SUM(COALESCE(g.amount_local, 0))) > 0.1
        ORDER BY ABS(SUM(COALESCE(g.amount_local, 0))) DESC
        LIMIT %s
        """,
        gl_params + [limit],
    )
    for row in cur.fetchall():
        doc = row["dnum_auto"] or row["uniquenum_pri"]
        balance = float(row["gl_balance_local"] or 0)
        findings.append({
            "severity": "critical",
            "title": f"Unbalanced GL Posting for {label}",
            "description": (
                f"{label} {doc} has GL posting balance {balance:,.2f} across {row['gl_rows']} row(s). "
                "Finance should verify the posting and rounding adjustment."
            ),
            "source_id": str(row["uniquenum_pri"]),
            "finding_type": source_type,
            "risk_score": 97,
            "evidence": {
                "source_type": source_type,
                "fromtrans": fromtrans,
                "uniquenum_pri": str(row["uniquenum_pri"]),
                "source_transaction_id": f"finance:{fromtrans}:{row['uniquenum_pri']}",
                "document_no": doc,
                "gl_rows": int(row["gl_rows"] or 0),
                "gl_balance_local": balance,
                "audit_hint": "Review gen_ledger_detail rows for this document and compare against fin_mod_data.",
            },
        })

    cur.close()
    conn.close()
    findings.sort(key=lambda item: item["risk_score"], reverse=True)
    return findings[:limit]


def query_bank_payment_anomalies(masterfn: str, companyfn: str,
                                 date_from: Optional[str] = None,
                                 date_to: Optional[str] = None,
                                 limit: int = 5):
    return query_finance_formtrans_anomalies(masterfn, companyfn, "bank_payment", date_from, date_to, limit)


def query_bank_receipt_anomalies(masterfn: str, companyfn: str,
                                 date_from: Optional[str] = None,
                                 date_to: Optional[str] = None,
                                 limit: int = 5):
    return query_finance_formtrans_anomalies(masterfn, companyfn, "bank_receipt", date_from, date_to, limit)


def query_general_journal_anomalies(masterfn: str, companyfn: str,
                                    date_from: Optional[str] = None,
                                    date_to: Optional[str] = None,
                                    limit: int = 5):
    return query_finance_formtrans_anomalies(masterfn, companyfn, "general_journal", date_from, date_to, limit)


# ─── Demand Planning Queries ────────────────────────────────────────────────

def query_sales_history(masterfn: str, companyfn: str,
                         sku_filter: str = "all",
                         location_filter: str = "all",
                         days: int = 90):
    """
    Get sales history for demand forecasting.
    Uses scm_sal_main (Sales Order headers) and scm_sal_data (items).
    Join: scm_sal_data.uniquenum_sec = scm_sal_main.uniquenum_pri
    """
    conn = get_erp_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    where = """m.tag_deleted_yn = 'n' AND m.tag_void_yn = 'n'
               AND m.cslsegm = 'sal_soe'
               AND m.masterfn = %s AND m.companyfn = %s"""
    params = [masterfn, companyfn]
    
    # Use date range: if days > 0, filter by last N days; otherwise no date filter
    if days > 0:
        where += " AND m.date_post >= NOW() - INTERVAL '%s days'"
        params.append(days)

    
    if sku_filter != "all":
        where += " AND d.stkcode_code = %s"
        params.append(sku_filter)
    if location_filter != "all":
        where += " AND m.location_code = %s"
        params.append(location_filter)
    
    sql = f"""
        SELECT 
            d.stkcode_code AS sku,
            m.location_code AS location,
            SUM(COALESCE(d.qnty_total, 0)) AS total_qty,
            SUM(COALESCE(d.amount_forex, 0)) AS total_amount,
            COUNT(DISTINCT m.uniquenum_pri) AS order_count,
            MAX(m.date_post) AS last_order_date
        FROM scm_sal_main m
        JOIN scm_sal_data d ON d.uniquenum_sec = m.uniquenum_pri
            AND d.tag_deleted_yn = 'n'
        WHERE {where}
        GROUP BY d.stkcode_code, m.location_code
        ORDER BY total_qty DESC
        LIMIT 50
    """
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def query_current_stock(masterfn: str, companyfn: str,
                         sku_filter: str = "all",
                         location_filter: str = "all"):
    """
    Get current stock levels from scm_stk_data (stock movement data).
    Uses qnty_total and amount_forex columns.
    """
    conn = get_erp_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    where = """tag_deleted_yn = 'n'
               AND masterfn = %s AND companyfn = %s"""
    params = [masterfn, companyfn]
    
    if sku_filter != "all":
        where += " AND stkcode_code = %s"
        params.append(sku_filter)
    
    sql = f"""
        SELECT 
            stkcode_code AS sku,
            stkcode_desc AS description,
            COALESCE(SUM(qnty_total), 0) AS on_hand_qty,
            COALESCE(SUM(amount_forex), 0) AS stock_value
        FROM scm_stk_data
        WHERE {where}
        GROUP BY stkcode_code, stkcode_desc
        ORDER BY stkcode_code
        LIMIT 100
    """
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def query_sku_master(masterfn: str, companyfn: str):
    """Get SKU master data from stk_sku_data."""
    conn = get_erp_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cur.execute("""
        SELECT 
            stkcode_code AS sku,
            stkcode_desc AS description,
            level_min,
            level_max,
            level_reorder,
            amt_cost_stdnormal AS std_cost,
            amt_price_stdnormal AS std_price
        FROM stk_sku_data
        WHERE tag_deleted_yn = 'n'
            AND masterfn = %s AND companyfn = %s
        ORDER BY stkcode_code
        LIMIT 200
    """, (masterfn, companyfn))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def query_on_order_stock(masterfn: str, companyfn: str,
                          sku_filter: str = "all",
                          location_filter: str = "all"):
    """
    Get on-order (PO not yet received) quantities per SKU.
    Uses scm_pur_main (PO headers) + scm_pur_data (PO lines).
    Filters for PO status = 'open' or 'confirmed' (not yet fully received).
    """
    conn = get_erp_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    where = """m.tag_deleted_yn = 'n' AND m.tag_void_yn = 'n'
               AND m.cslsegm = 'pur_poe'
               AND m.wflow_status IN ('open','confirmed')
               AND m.masterfn = %s AND m.companyfn = %s"""
    params = [masterfn, companyfn]
    
    if sku_filter != "all":
        where += " AND d.stkcode_code = %s"
        params.append(sku_filter)
    if location_filter != "all":
        where += " AND m.location_code = %s"
        params.append(location_filter)
    
    sql = f"""
        SELECT 
            d.stkcode_code AS sku,
            m.location_code AS location,
            SUM(COALESCE(d.qnty_total, 0) - COALESCE(d.qnty_received, 0)) AS on_order_qty
        FROM scm_pur_main m
        JOIN scm_pur_data d ON d.uniquenum_sec = m.uniquenum_pri
            AND d.tag_deleted_yn = 'n'
        WHERE {where}
        GROUP BY d.stkcode_code, m.location_code
        ORDER BY d.stkcode_code
        LIMIT 200
    """
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def query_committed_stock(masterfn: str, companyfn: str,
                           sku_filter: str = "all",
                           location_filter: str = "all"):
    """
    Get committed (SO not yet delivered) quantities per SKU.
    Uses scm_sal_main (SO headers) + scm_sal_data (SO lines).
    Filters for SO status = 'open' or 'confirmed' (not yet fully delivered).
    """
    conn = get_erp_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    where = """m.tag_deleted_yn = 'n' AND m.tag_void_yn = 'n'
               AND m.cslsegm = 'sal_soe'
               AND m.wflow_status IN ('open','confirmed')
               AND m.masterfn = %s AND m.companyfn = %s"""
    params = [masterfn, companyfn]
    
    if sku_filter != "all":
        where += " AND d.stkcode_code = %s"
        params.append(sku_filter)
    if location_filter != "all":
        where += " AND m.location_code = %s"
        params.append(location_filter)
    
    sql = f"""
        SELECT 
            d.stkcode_code AS sku,
            m.location_code AS location,
            SUM(COALESCE(d.qnty_total, 0) - COALESCE(d.qnty_delivered, 0)) AS committed_qty
        FROM scm_sal_main m
        JOIN scm_sal_data d ON d.uniquenum_sec = m.uniquenum_pri
            AND d.tag_deleted_yn = 'n'
        WHERE {where}
        GROUP BY d.stkcode_code, m.location_code
        ORDER BY d.stkcode_code
        LIMIT 200
    """
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


