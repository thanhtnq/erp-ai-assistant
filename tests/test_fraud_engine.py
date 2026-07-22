import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone
from pathlib import Path

from api.fraud.domain import AlertCandidate, Transaction
from api.fraud.engine import FraudRuleEngine
from api.fraud.repository import SQLiteAlertRepository, init_alert_table
from api.fraud.rules import RuleThresholds, default_rules
from api.fraud.service import FraudDetectionService


class MemorySource:
    def __init__(self, rows): self.rows=rows
    def load(self, *args): return self.rows

class MemoryAlerts:
    def __init__(self): self.hashes=set()
    def save(self,m,c,a,now):
        key=(m,c,a.rule_name,a.transaction_id,a.user_id,a.event_key)
        if key in self.hashes: return False
        self.hashes.add(key); return True

class FraudEngineTests(unittest.TestCase):
    def rows(self):
        now=datetime(2026,7,13,23,tzinfo=timezone.utc); rows=[]
        for day in range(10,70):
            rows.append(Transaction(f"h{day}","u1",now-timedelta(days=day,hours=11),now-timedelta(days=day,hours=11),100,5,1,1))
        rows.append(Transaction("event-1","u1",now-timedelta(days=16),now,1200,50,8,8,5))
        for n in range(10):
            rows.append(Transaction(f"event-freq-{n}","u1",now-timedelta(hours=2),now,100,5,1,1))
        return now,rows

    def test_all_requested_rules_are_pluggable_and_trigger(self):
        now,rows=self.rows(); alerts,_=FraudRuleEngine(default_rules(RuleThresholds())).run(rows,now)
        names={a.rule_name for a in alerts}
        self.assertEqual(names,{"HIGH_TRANSACTION_AMOUNT","TRANSACTION_FREQUENCY_SPIKE","HIGH_REFUND_COUNT",
          "ABNORMAL_DISCOUNT","TOO_MANY_VOID_TRANSACTIONS",
          "REPEATED_INVOICE_MODIFICATION","BACKDATED_TRANSACTION"})

    def test_finance_formtrans_rules_trigger_from_metadata(self):
        now=datetime(2026,7,13,12,tzinfo=timezone.utc)
        rows=[]
        for day in range(10,70):
            rows.append(Transaction(
                f"h{day}","u1",now-timedelta(days=day),now-timedelta(days=day),100,
                metadata={"fromtrans":"csh_paym","reference_no":f"CHK{day}","party_code":"V1","currency":"SGD"},
            ))
        rows.append(Transaction(
            "bp-1","u1",now-timedelta(days=1),now-timedelta(days=1),500,
            metadata={"fromtrans":"csh_paym","reference_no":"CHK-DUP","party_code":"V1","currency":"SGD"},
        ))
        rows.append(Transaction(
            "bp-2","u1",now-timedelta(days=1),now-timedelta(days=1),500,
            metadata={"fromtrans":"csh_paym","reference_no":"CHK-DUP","party_code":"V1","currency":"SGD"},
        ))
        rows.append(Transaction(
            "gj-1","u1",now-timedelta(days=1),now-timedelta(days=1),500,
            metadata={"fromtrans":"sub_jour","gl_balance_local":25,"gl_rows":3},
        ))
        alerts,_=FraudRuleEngine(default_rules(RuleThresholds())).run(rows,now)
        names={a.rule_name for a in alerts}
        self.assertIn("DUPLICATE_FINANCE_REFERENCE",names)
        self.assertIn("UNBALANCED_FINANCE_GL_POSTING",names)

    def test_service_is_idempotent_for_same_event(self):
        now,rows=self.rows(); repo=MemoryAlerts(); svc=FraudDetectionService(MemorySource(rows),repo)
        first=svc.run("m","c",now); second=svc.run("m","c",now)
        self.assertGreater(first["created"],0); self.assertEqual(second["created"],0)

    def test_no_baseline_means_no_unreliable_alert(self):
        now=datetime.now(timezone.utc); row=Transaction("1","new-user",now,now,999999)
        alerts,baselines=FraudRuleEngine(default_rules(RuleThresholds())).run([row],now)
        self.assertEqual(alerts,[]); self.assertEqual(baselines,{})

    def test_alert_schema_has_unique_hash_and_lifecycle_fields(self):
        conn=sqlite3.connect(":memory:"); init_alert_table(conn)
        cols={r[1] for r in conn.execute("PRAGMA table_info(fraud_alert)")}
        self.assertTrue({"query_hash","resolved_by","resolved_at","hidden_by","hidden_at","metadata"} <= cols)

    def test_sqlite_repository_never_recreates_same_hidden_or_resolved_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            db=Path(tmp)/"alerts.db"
            def connect():
                conn=sqlite3.connect(db); conn.row_factory=sqlite3.Row; return conn
            candidate=AlertCandidate("RULE","u","tx","HIGH","title","desc",80,"event-1")
            repo=SQLiteAlertRepository(); now=datetime.now(timezone.utc)
            with patch("api.fraud.repository.get_chat_conn",side_effect=connect):
                self.assertTrue(repo.save("m","c",candidate,now))
                conn=connect(); conn.execute("UPDATE fraud_alert SET status='HIDDEN',is_hidden=1"); conn.commit(); conn.close()
                self.assertFalse(repo.save("m","c",candidate,now))
                newer=AlertCandidate("RULE","u","tx","HIGH","title","desc",80,"event-2")
                self.assertTrue(repo.save("m","c",newer,now))

    def test_admin_scheduler_exposes_fraud_job(self):
        from api.routers import admin_scheduler
        with tempfile.TemporaryDirectory() as tmp, patch.object(
            admin_scheduler,"SCHEDULER_STATE_FILE",Path(tmp)/"state.json"
        ):
            state=admin_scheduler._read_sched_state()
            self.assertIn("fraud",state)
            self.assertIn("fraud",admin_scheduler._VALID_JOBS)

    def test_in_process_scheduler_daily_due_only_once(self):
        from api.fraud.background import _is_due
        now=datetime(2026,7,13,1,0)
        cfg={"enabled":True,"is_running":False,"interval":"daily","time":"01:00","day":"monday","last_run_at":None}
        self.assertTrue(_is_due(cfg,now))
        cfg["last_run_at"]="2026-07-13T01:00:02"
        self.assertFalse(_is_due(cfg,now))


if __name__ == "__main__": unittest.main()
