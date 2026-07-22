from __future__ import annotations

import hashlib, json, os
from datetime import datetime, timezone
from typing import Protocol

import psycopg2.extras

from api.database import get_chat_conn
from api.services.erp_db import get_erp_conn
from .domain import AlertCandidate, Transaction


class TransactionSource(Protocol):
    def load(self, masterfn: str, companyfn: str, start: datetime, end: datetime) -> list[Transaction]: ...


class PostgresTransactionSource:
    """Reads a deployment-provided normalized view; keeps ERP schema decisions outside rules."""
    def __init__(self, view: str | None = None):
        self.view = view or os.getenv("FRAUD_TRANSACTION_VIEW", "fraud_transaction_source")
        if not self.view.replace("_", "").isalnum(): raise ValueError("Invalid fraud transaction view")
    def load(self, masterfn, companyfn, start, end):
        conn=get_erp_conn(); cur=conn.cursor()
        cur.execute(f"""SELECT transaction_id,user_id,occurred_at,created_at,amount,discount,
          refund_count,void_count,invoice_modifications,metadata FROM {self.view}
          WHERE masterfn=%s AND companyfn=%s
            AND (occurred_at BETWEEN %s AND %s OR created_at BETWEEN %s AND %s)""",
          (masterfn,companyfn,start,end,start,end))
        names=[d[0] for d in cur.description]; rows=[dict(zip(names,r)) for r in cur.fetchall()]
        cur.close(); conn.close()
        def dt(value):
            value = datetime.fromisoformat(value) if isinstance(value, str) else value
            return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value
        def metadata(value):
            if not value: return {}
            return json.loads(value) if isinstance(value, str) else value
        return [Transaction(str(r['transaction_id']),str(r['user_id']),dt(r['occurred_at']),dt(r['created_at']),
          float(r['amount'] or 0),float(r['discount'] or 0),int(r['refund_count'] or 0),
          int(r['void_count'] or 0),int(r['invoice_modifications'] or 0),metadata(r['metadata'])) for r in rows]


def init_alert_table(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS fraud_alert (
      id INTEGER PRIMARY KEY AUTOINCREMENT, masterfn TEXT NOT NULL, companyfn TEXT NOT NULL,
      rule_name TEXT NOT NULL, user_id TEXT NOT NULL, transaction_id TEXT NOT NULL,
      severity TEXT NOT NULL, title TEXT NOT NULL, description TEXT NOT NULL, risk_score INTEGER NOT NULL,
      status TEXT NOT NULL DEFAULT 'NEW', is_hidden INTEGER NOT NULL DEFAULT 0, query_hash TEXT NOT NULL UNIQUE,
      created_at TEXT NOT NULL, updated_at TEXT NOT NULL, resolved_by TEXT, resolved_at TEXT,
      hidden_by TEXT, hidden_at TEXT, acknowledged_by TEXT, acknowledged_at TEXT, metadata TEXT NOT NULL DEFAULT '{}');
    CREATE INDEX IF NOT EXISTS idx_fraud_alert_active ON fraud_alert(masterfn,companyfn,status,severity,created_at);
    """)


class SQLiteAlertRepository:
    def save(self, masterfn: str, companyfn: str, candidate: AlertCandidate, now: datetime) -> bool:
        conn=get_chat_conn(); init_alert_table(conn)
        try:
            raw="|".join((masterfn,companyfn,candidate.rule_name,candidate.transaction_id,candidate.user_id,candidate.event_key))
            query_hash=hashlib.sha256(raw.encode()).hexdigest()
            cur=conn.execute("""INSERT OR IGNORE INTO fraud_alert
              (masterfn,companyfn,rule_name,user_id,transaction_id,severity,title,description,risk_score,status,is_hidden,query_hash,created_at,updated_at,metadata)
              VALUES (?,?,?,?,?,?,?,?,?,'NEW',0,?,?,?,?)""",
              (masterfn,companyfn,candidate.rule_name,candidate.user_id,candidate.transaction_id,candidate.severity,
               candidate.title,candidate.description,candidate.risk_score,query_hash,now.isoformat(),now.isoformat(),json.dumps(candidate.metadata)))
            conn.commit()
            return cur.rowcount == 1
        finally:
            conn.close()


def _short(value: str, size: int) -> str:
    return (value or "")[:size]


def _rule_code(rule_name: str) -> str:
    mapping = {
        "HIGH_TRANSACTION_AMOUNT": "HIGH_AMT",
        "TRANSACTION_FREQUENCY_SPIKE": "FREQ_SPIK",
        "HIGH_REFUND_COUNT": "REFUND",
        "ABNORMAL_DISCOUNT": "DISCOUNT",
        "TOO_MANY_VOID_TRANSACTIONS": "VOID",
        "LOGIN_OUTSIDE_NORMAL_HOURS": "OFF_HOUR",
        "REPEATED_INVOICE_MODIFICATION": "REPEATMOD",
        "BACKDATED_TRANSACTION": "BACKDATE",
        "DUPLICATE_FINANCE_REFERENCE": "DUPFINREF",
        "UNBALANCED_FINANCE_GL_POSTING": "UNBALGL",
    }
    return mapping.get(rule_name, _short(rule_name.replace("_", ""), 10))


class MemoLongTableAlertRepository:
    """Persist scheduled fraud indicators in the ERP memo_long_table source DB."""

    usage = "ai_fraud_detection"

    def clear_scope(self, masterfn: str, companyfn: str, now: datetime) -> int:
        """Replace the active alert set for a scope.

        The UI is intended to show the current fraud review shortlist, not an
        ever-growing queue. Historical rows remain in memo_long_table but are
        soft-deleted so normal list/count queries no longer surface them.
        """
        conn = get_erp_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE memo_long_table
                SET tag_deleted_yn = 'y',
                    tag_others02 = 'SUPERSEDED',
                    date_lastupdate = %s,
                    userid_cookie = 'AI_FRAUD'
                WHERE tag_table_usage = %s
                  AND masterfn = %s
                  AND companyfn = %s
                  AND COALESCE(tag_deleted_yn, 'n') = 'n'
                """,
                [now, self.usage, masterfn, companyfn],
            )
            return cur.rowcount or 0
        finally:
            conn.close()

    def save(self, masterfn: str, companyfn: str, candidate: AlertCandidate, now: datetime) -> bool:
        raw = "|".join((masterfn, companyfn, candidate.rule_name, candidate.transaction_id, candidate.user_id, candidate.event_key))
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        unique_key = f"afd{digest[:20]}"
        alert_key = f"afd_{digest[:16]}"
        payload = {
            "id": alert_key,
            "source": "SCHEDULER",
            "status": "NEW",
            "severity": candidate.severity,
            "rule_code": _rule_code(candidate.rule_name),
            "rule_name": candidate.rule_name,
            "title": candidate.title,
            "description": candidate.description,
            "user_id": candidate.user_id,
            "transaction_id": candidate.transaction_id,
            "risk_score": candidate.risk_score,
            "event_key": candidate.event_key,
            "metadata": candidate.metadata,
            "created_at": now.isoformat(),
        }
        amount = candidate.metadata.get("amount") or candidate.metadata.get("value") or 0
        event_at = candidate.metadata.get("occurred_at") or now
        if isinstance(event_at, str):
            try:
                event_at = datetime.fromisoformat(event_at.replace("Z", "+00:00"))
            except ValueError:
                event_at = now
        metric = (
            candidate.metadata.get("invoice_modifications")
            or candidate.metadata.get("daily_count")
            or candidate.metadata.get("ratio")
            or candidate.metadata.get("lag_days")
            or candidate.metadata.get("value")
            or 0
        )
        threshold = candidate.metadata.get("threshold") or 0

        conn = get_erp_conn()
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(
                """
                SELECT idcode
                FROM memo_long_table
                WHERE tag_table_usage = %s
                  AND masterfn = %s
                  AND companyfn = %s
                  AND uniquenum_uniq = %s
                  AND COALESCE(tag_deleted_yn, 'n') = 'n'
                LIMIT 1
                """,
                [self.usage, masterfn, companyfn, unique_key],
            )
            if cur.fetchone():
                return False
            cur.execute(
                """
                INSERT INTO memo_long_table (
                    tag_table_usage, tag_memo_type, tag_datasource,
                    uniquenum_pri, uniquenum_sec, uniquenum_uniq,
                    masterfn, holdfn, groupfn, companyfn, userid_cookie,
                    tag_deleted_yn, tag_void_yn,
                    tag_others01, tag_others02, tag_others03, tag_others04,
                    var_25_001, var_25_002, var_25_003,
                    var_50_001, var_50_002, var_50_003, var_50_004,
                    num_20_2_d_001, num_20_2_d_002, num_20_2_d_003, num_20_2_d_004,
                    date_post, date_lastupdate, date_trans, notes_memo
                )
                VALUES (
                    %s, 'fraud_alert', 'ai',
                    %s, %s, %s,
                    %s, %s, %s, %s, 'AI_FRAUD',
                    'n', 'n',
                    %s, 'NEW', %s, 'SCHEDULER',
                    %s, %s, 'ERP',
                    %s, %s, %s, %s,
                    %s, %s, %s, 0,
                    %s, %s, %s, %s
                )
                """,
                [
                    self.usage,
                    _short(alert_key, 30),
                    _short(candidate.transaction_id, 30),
                    _short(unique_key, 30),
                    masterfn,
                    masterfn,
                    masterfn,
                    companyfn,
                    _short(candidate.severity, 10),
                    _rule_code(candidate.rule_name),
                    _short(candidate.user_id, 25),
                    _short(candidate.transaction_id, 25),
                    _short(candidate.rule_name, 50),
                    _short(candidate.title, 50),
                    _short(candidate.transaction_id, 50),
                    _short(candidate.event_key, 50),
                    candidate.risk_score,
                    amount,
                    metric,
                    now,
                    now,
                    event_at,
                    json.dumps(payload, ensure_ascii=False, default=str),
                ],
            )
            return True
        finally:
            conn.close()
