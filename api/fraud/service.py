import logging
import os
from datetime import datetime, timedelta, timezone

from .engine import FraudRuleEngine
from .repository import MemoLongTableAlertRepository, PostgresTransactionSource
from .rules import RuleThresholds, default_rules

log=logging.getLogger(__name__)

SEVERITY_RANK = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}


def _alert_priority(candidate):
    meta = candidate.metadata or {}
    ratio = float(meta.get("ratio") or 0)
    metric = float(
        meta.get("invoice_modifications")
        or meta.get("daily_count")
        or meta.get("lag_days")
        or meta.get("value")
        or 0
    )
    amount = abs(float(meta.get("amount") or 0))
    occurred = str(meta.get("occurred_at") or meta.get("source_created_at") or "")
    return (
        SEVERITY_RANK.get(candidate.severity.upper(), 0),
        int(candidate.risk_score or 0),
        ratio,
        metric,
        amount,
        occurred,
    )


class FraudDetectionService:
    def __init__(self, source=None, alerts=None, engine=None):
        self.source=source or PostgresTransactionSource(); self.alerts=alerts or MemoLongTableAlertRepository()
        self.engine=engine or FraudRuleEngine(default_rules(RuleThresholds.from_env()))
    def run(self, masterfn: str, companyfn: str, as_of: datetime | None=None):
        as_of=as_of or datetime.now(timezone.utc); start=as_of-timedelta(days=120)
        rows=self.source.load(masterfn,companyfn,start,as_of)
        candidates,baselines=self.engine.run(rows,as_of)
        min_severity = os.getenv("FRAUD_MIN_SEVERITY", "MEDIUM").upper()
        min_rank = SEVERITY_RANK.get(min_severity, SEVERITY_RANK["MEDIUM"])
        candidates = [c for c in candidates if SEVERITY_RANK.get(c.severity.upper(), 0) >= min_rank]
        candidates = sorted(candidates, key=_alert_priority, reverse=True)
        max_alerts = int(os.getenv("FRAUD_MAX_ACTIVE_ALERTS", "5"))
        if max_alerts > 0:
            candidates = candidates[:max_alerts]
        if os.getenv("FRAUD_REPLACE_ACTIVE_ALERTS", "true").lower() in {"1", "true", "yes", "y"}:
            clear = getattr(self.alerts, "clear_scope", None)
            if callable(clear):
                clear(masterfn, companyfn, as_of)
        created=sum(self.alerts.save(masterfn,companyfn,a,as_of) for a in candidates)
        result={"transactions":len(rows),"users":len(baselines),"detected":len(candidates),"created":created,"min_severity":min_severity,"max_active_alerts":max_alerts}
        log.info("Fraud scan completed scope=%s/%s result=%s",masterfn,companyfn,result)
        return result
