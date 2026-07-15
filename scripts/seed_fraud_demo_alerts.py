import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import psycopg2.extras
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env", override=True)

from api.services.erp_db import get_erp_conn  # noqa: E402


MASTERFN = "banleong369878mfn"
COMPANYFN = "p23091210332792616"
MEMO_USAGE = "ai_fraud_detection"


def _alert(
    key: str,
    severity: str,
    rule_code: str,
    rule_name: str,
    title: str,
    description: str,
    user_id: str,
    transaction_id: str,
    risk_score: float,
    amount: float,
    metric: float,
    baseline: float,
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "key": key,
        "severity": severity,
        "rule_code": rule_code,
        "rule_name": rule_name,
        "title": title,
        "description": description,
        "user_id": user_id,
        "transaction_id": transaction_id,
        "risk_score": risk_score,
        "amount": amount,
        "metric": metric,
        "baseline": baseline,
        "payload": {
            "id": key,
            "demo": True,
            "created_by": "codex",
            "created_at": now,
            "source": "DEMO",
            "status": "NEW",
            "severity": severity,
            "rule_code": rule_code,
            "rule_name": rule_name,
            "title": title,
            "description": description,
            "user_id": user_id,
            "transaction_id": transaction_id,
            "risk_score": risk_score,
            "metadata": {
                "amount": amount,
                "metric": metric,
                "baseline": baseline,
                "explanation": "Demo alert inserted into memo_long_table for Fraud Detection UI validation.",
            },
        },
    }


DEMO_ALERTS: List[Dict[str, Any]] = [
    _alert(
        "afd_demo_001",
        "CRITICAL",
        "HIGH_AMT",
        "HIGH_TRANSACTION_AMOUNT",
        "High amount vs baseline",
        "Sales invoice amount 48,500.00 is 4.8x this user's normal 30-day average.",
        "ALANLEE",
        "SI-DEMO-9001",
        94,
        48500,
        4.8,
        10100,
    ),
    _alert(
        "afd_demo_002",
        "HIGH",
        "FREQ_SPIK",
        "FREQUENCY_SPIKE",
        "Unusual daily transaction volume",
        "User created 27 transactions today while normal daily baseline is 6.",
        "BLGERALD",
        "SO-DEMO-7782",
        82,
        0,
        27,
        6,
    ),
    _alert(
        "afd_demo_003",
        "HIGH",
        "BACKDATE",
        "BACKDATED_TRANSACTION",
        "Backdated transaction",
        "Credit note transaction date is 12 days earlier than creation date.",
        "CATHERINE",
        "CN-DEMO-3310",
        76,
        1280,
        12,
        7,
    ),
    _alert(
        "afd_demo_004",
        "MEDIUM",
        "OFF_HOUR",
        "OUTSIDE_WORKING_HOURS",
        "Transaction outside normal hours",
        "Invoice update was posted at 02:14, outside the user's normal activity window.",
        "ADAM",
        "INV-DEMO-5521",
        68,
        7320,
        2.14,
        8,
    ),
]


def seed() -> Dict[str, Any]:
    conn = get_erp_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """
            DELETE FROM memo_long_table
            WHERE tag_table_usage = %s
              AND masterfn = %s
              AND companyfn = %s
              AND tag_others04 = 'DEMO'
            """,
            [MEMO_USAGE, MASTERFN, COMPANYFN],
        )
        deleted = cur.rowcount

        inserted = []
        for item in DEMO_ALERTS:
            cur.execute(
                """
                INSERT INTO memo_long_table (
                    tag_table_usage,
                    tag_memo_type,
                    tag_datasource,
                    uniquenum_pri,
                    uniquenum_sec,
                    uniquenum_uniq,
                    masterfn,
                    holdfn,
                    groupfn,
                    companyfn,
                    userid_cookie,
                    tag_deleted_yn,
                    tag_void_yn,
                    tag_others01,
                    tag_others02,
                    tag_others03,
                    tag_others04,
                    var_25_001,
                    var_25_002,
                    var_25_003,
                    var_50_001,
                    var_50_002,
                    var_50_003,
                    var_50_004,
                    num_20_2_d_001,
                    num_20_2_d_002,
                    num_20_2_d_003,
                    num_20_2_d_004,
                    date_post,
                    date_lastupdate,
                    date_trans,
                    notes_memo
                )
                VALUES (
                    %s, 'fraud_alert', 'ai', %s, %s, %s,
                    %s, %s, %s, %s, 'AI_FRAUD',
                    'n', 'n',
                    %s, 'NEW', %s, 'DEMO',
                    %s, %s, 'DEMO',
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    NOW(), NOW(), NOW(),
                    %s
                )
                RETURNING idcode, uniquenum_pri
                """,
                [
                    MEMO_USAGE,
                    item["key"],
                    item["transaction_id"][:30],
                    f"afduniq{item['key'][-3:]}",
                    MASTERFN,
                    MASTERFN,
                    MASTERFN,
                    COMPANYFN,
                    item["severity"],
                    item["rule_code"],
                    item["user_id"][:25],
                    item["transaction_id"][:25],
                    item["rule_name"][:50],
                    item["title"][:50],
                    item["transaction_id"][:50],
                    item["key"][:50],
                    item["risk_score"],
                    item["amount"],
                    item["metric"],
                    item["baseline"],
                    json.dumps(item["payload"], ensure_ascii=False),
                ],
            )
            inserted.append(dict(cur.fetchone()))
        return {"deleted_demo_rows": deleted, "inserted": inserted}
    finally:
        conn.close()


if __name__ == "__main__":
    print(json.dumps(seed(), indent=2, default=str))
