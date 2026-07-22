from __future__ import annotations

from abc import ABC, abstractmethod
from collections import Counter
from dataclasses import dataclass
from datetime import timedelta
import os

from .domain import AlertCandidate, Transaction, UserBaseline


@dataclass(frozen=True)
class RuleThresholds:
    amount_low_multiplier: float = 2.0
    amount_medium_multiplier: float = 5.0
    amount_high_multiplier: float = 10.0
    frequency_low_multiplier: float = 3.0
    frequency_medium_multiplier: float = 5.0
    frequency_high_multiplier: float = 8.0
    frequency_min_count: int = 10
    refund_low_count: int = 2
    refund_medium_count: int = 4
    refund_high_count: int = 8
    discount_low_multiplier: float = 3.0
    discount_medium_multiplier: float = 5.0
    discount_high_multiplier: float = 8.0
    void_low_count: int = 2
    void_medium_count: int = 4
    void_high_count: int = 8
    invoice_modifications: int = 5
    backdated_days: int = 14

    @classmethod
    def from_env(cls):
        return cls(
            amount_low_multiplier=float(os.getenv("FRAUD_AMOUNT_LOW_MULTIPLIER", "2")),
            amount_medium_multiplier=float(os.getenv("FRAUD_AMOUNT_MEDIUM_MULTIPLIER", "5")),
            amount_high_multiplier=float(os.getenv("FRAUD_AMOUNT_HIGH_MULTIPLIER", "10")),
            frequency_low_multiplier=float(os.getenv("FRAUD_FREQUENCY_LOW_MULTIPLIER", "3")),
            frequency_medium_multiplier=float(os.getenv("FRAUD_FREQUENCY_MEDIUM_MULTIPLIER", "5")),
            frequency_high_multiplier=float(os.getenv("FRAUD_FREQUENCY_HIGH_MULTIPLIER", "8")),
            frequency_min_count=int(os.getenv("FRAUD_FREQUENCY_MIN_COUNT", "10")),
            refund_low_count=int(os.getenv("FRAUD_REFUND_LOW_COUNT", "2")),
            refund_medium_count=int(os.getenv("FRAUD_REFUND_MEDIUM_COUNT", "4")),
            refund_high_count=int(os.getenv("FRAUD_REFUND_HIGH_COUNT", "8")),
            discount_low_multiplier=float(os.getenv("FRAUD_DISCOUNT_LOW_MULTIPLIER", "3")),
            discount_medium_multiplier=float(os.getenv("FRAUD_DISCOUNT_MEDIUM_MULTIPLIER", "5")),
            discount_high_multiplier=float(os.getenv("FRAUD_DISCOUNT_HIGH_MULTIPLIER", "8")),
            void_low_count=int(os.getenv("FRAUD_VOID_LOW_COUNT", "2")),
            void_medium_count=int(os.getenv("FRAUD_VOID_MEDIUM_COUNT", "4")),
            void_high_count=int(os.getenv("FRAUD_VOID_HIGH_COUNT", "8")),
            invoice_modifications=int(os.getenv("FRAUD_INVOICE_MODIFICATIONS", "5")),
            backdated_days=int(os.getenv("FRAUD_BACKDATED_DAYS", "14")),
        )


def _tier(value: float, low: float, medium: float, high: float):
    if value >= high:
        return "HIGH", 87
    if value >= medium:
        return "MEDIUM", 68
    if value >= low:
        return "LOW", 45
    return "", 0


class FraudRule(ABC):
    name: str
    @abstractmethod
    def evaluate(self, transaction: Transaction, baseline: UserBaseline,
                 context: dict) -> list[AlertCandidate]: ...

    def alert(self, t: Transaction, title: str, description: str, score: int,
              severity: str = "MEDIUM", event_key: str | None = None,
              transaction_id: str | None = None, **metadata) -> list[AlertCandidate]:
        tx_id = transaction_id or t.transaction_id
        metadata = {
            **(t.metadata or {}),
            "source_transaction_id": t.transaction_id,
            "occurred_at": t.occurred_at.isoformat(),
            "source_created_at": t.created_at.isoformat(),
            "amount": t.amount,
            "discount": t.discount,
            "refund_count": t.refund_count,
            "void_count": t.void_count,
            "invoice_modifications": t.invoice_modifications,
            **metadata,
        }
        return [AlertCandidate(self.name, t.user_id, tx_id, severity,
                               title, description, score,
                               event_key or f"{tx_id}:{t.occurred_at.isoformat()}", metadata)]


class HighAmountRule(FraudRule):
    name = "HIGH_TRANSACTION_AMOUNT"
    def __init__(self, cfg): self.cfg = cfg
    def evaluate(self, t, b, context):
        baseline_amount = b.p95_amount or b.average_amount
        ratio = abs(t.amount) / baseline_amount if baseline_amount else 0
        severity, score = _tier(
            ratio,
            self.cfg.amount_low_multiplier,
            self.cfg.amount_medium_multiplier,
            self.cfg.amount_high_multiplier,
        )
        return self.alert(
            t,
            "Transaction amount exceeds historical p95",
            f"Current amount {abs(t.amount):,.2f} is compared with {b.scope_label} historical p95 {baseline_amount:,.2f}; ratio {ratio:.1f}x.",
            score,
            severity,
            ratio=ratio,
            baseline_method="p95_amount",
            baseline_amount=baseline_amount,
            baseline_average_amount=b.average_amount,
            baseline_p95_amount=b.p95_amount,
            baseline_p99_amount=b.p99_amount,
            baseline_scope=b.scope,
            baseline_scope_key=b.scope_key,
            baseline_scope_label=b.scope_label,
            baseline_samples=b.total_transactions,
            baseline_period_start=context.get("baseline_period_start"),
            baseline_period_end=context.get("baseline_period_end"),
            baseline_history_days=context.get("baseline_history_days"),
            baseline_exclude_recent_days=context.get("baseline_exclude_recent_days"),
            baseline_median_amount=b.median_amount,
            baseline_maximum_amount=b.maximum_amount,
            threshold_low=self.cfg.amount_low_multiplier,
            threshold_medium=self.cfg.amount_medium_multiplier,
            threshold_high=self.cfg.amount_high_multiplier,
        ) if severity else []


class FrequencySpikeRule(FraudRule):
    name = "TRANSACTION_FREQUENCY_SPIKE"
    def __init__(self, cfg): self.cfg = cfg
    def evaluate(self, t, b, context):
        if b.scope == "fromtrans":
            ft = (t.metadata or {}).get("fromtrans") or (t.metadata or {}).get("document_type") or "UNKNOWN"
            count = context["daily_counts_fromtrans"][(ft, t.created_at.date())]
        elif b.scope == "user_fromtrans":
            ft = (t.metadata or {}).get("fromtrans") or (t.metadata or {}).get("document_type") or "UNKNOWN"
            count = context["daily_counts_user_fromtrans"][(t.user_id, ft, t.created_at.date())]
        else:
            count = context["daily_counts_user"][(t.user_id, t.created_at.date())]
        ratio = count / b.average_transactions_per_day if b.average_transactions_per_day else 0
        if count < self.cfg.frequency_min_count:
            return []
        severity, score = _tier(
            ratio,
            self.cfg.frequency_low_multiplier,
            self.cfg.frequency_medium_multiplier,
            self.cfg.frequency_high_multiplier,
        )
        return self.alert(
            t,
            "Transaction frequency spike",
            f"Daily count {count} is compared with {b.scope_label} normal daily average {b.average_transactions_per_day:.2f}; ratio {ratio:.1f}x.",
            score,
            severity,
            event_key=f"frequency:{b.scope_key}:{t.created_at.date().isoformat()}",
            transaction_id=f"frequency:{b.scope_key}:{t.created_at.date().isoformat()}",
            daily_count=count,
            ratio=ratio,
            baseline_daily_average=b.average_transactions_per_day,
            baseline_scope=b.scope,
            baseline_scope_key=b.scope_key,
            baseline_scope_label=b.scope_label,
            baseline_samples=b.total_transactions,
            baseline_period_start=context.get("baseline_period_start"),
            baseline_period_end=context.get("baseline_period_end"),
            minimum_count=self.cfg.frequency_min_count,
        ) if severity else []


class MetricRule(FraudRule):
    field = ""; baseline_field = ""; title = ""
    low_count_field = ""; medium_count_field = ""; high_count_field = ""
    low_multiplier_field = ""; medium_multiplier_field = ""; high_multiplier_field = ""
    def __init__(self, cfg): self.cfg = cfg
    def evaluate(self, t, b, context):
        value, normal = getattr(t, self.field), getattr(b, self.baseline_field)
        if value <= 0:
            return []
        if self.low_count_field:
            severity, score = _tier(
                value,
                getattr(self.cfg, self.low_count_field),
                getattr(self.cfg, self.medium_count_field),
                getattr(self.cfg, self.high_count_field),
            )
            return self.alert(
                t,
                self.title,
                f"Current count {value} is compared with configured count thresholds.",
                score,
                severity,
                value=value,
                baseline=normal,
                baseline_scope=b.scope,
                baseline_scope_key=b.scope_key,
                baseline_scope_label=b.scope_label,
                baseline_samples=b.total_transactions,
                baseline_period_start=context.get("baseline_period_start"),
                baseline_period_end=context.get("baseline_period_end"),
                threshold_low=getattr(self.cfg, self.low_count_field),
                threshold_medium=getattr(self.cfg, self.medium_count_field),
                threshold_high=getattr(self.cfg, self.high_count_field),
            ) if severity else []
        ratio = value / normal if normal else 0
        severity, score = _tier(
            ratio,
            getattr(self.cfg, self.low_multiplier_field),
            getattr(self.cfg, self.medium_multiplier_field),
            getattr(self.cfg, self.high_multiplier_field),
        )
        return self.alert(
            t,
            self.title,
            f"Current value {value} is compared with user baseline {normal:.2f}; ratio {ratio:.1f}x.",
            score,
            severity,
            value=value,
            baseline=normal,
            ratio=ratio,
            baseline_scope=b.scope,
            baseline_scope_key=b.scope_key,
            baseline_scope_label=b.scope_label,
            baseline_samples=b.total_transactions,
            baseline_period_start=context.get("baseline_period_start"),
            baseline_period_end=context.get("baseline_period_end"),
            threshold_low=getattr(self.cfg, self.low_multiplier_field),
            threshold_medium=getattr(self.cfg, self.medium_multiplier_field),
            threshold_high=getattr(self.cfg, self.high_multiplier_field),
        ) if severity else []


class HighRefundRule(MetricRule):
    name="HIGH_REFUND_COUNT"; field="refund_count"; baseline_field="average_refund_count"; low_count_field="refund_low_count"; medium_count_field="refund_medium_count"; high_count_field="refund_high_count"; title="High refund count"
class AbnormalDiscountRule(MetricRule):
    name="ABNORMAL_DISCOUNT"; field="discount"; baseline_field="average_discount"; low_multiplier_field="discount_low_multiplier"; medium_multiplier_field="discount_medium_multiplier"; high_multiplier_field="discount_high_multiplier"; title="Abnormal discount"
class TooManyVoidRule(MetricRule):
    name="TOO_MANY_VOID_TRANSACTIONS"; field="void_count"; baseline_field="average_void_count"; low_count_field="void_low_count"; medium_count_field="void_medium_count"; high_count_field="void_high_count"; title="Too many void transactions"


class OutsideWorkingHoursRule(FraudRule):
    name = "LOGIN_OUTSIDE_NORMAL_HOURS"
    def evaluate(self, t, b, context):
        value=t.occurred_at.time()
        return self.alert(
            t,
            "Activity outside normal working hours",
            f"Transaction time {value.isoformat(timespec='minutes')} is compared with user normal activity window {b.normal_start_hour.isoformat(timespec='minutes')}-{b.normal_end_hour.isoformat(timespec='minutes')}.",
            50,
            "LOW",
            activity_time=value.isoformat(timespec="minutes"),
            normal_start=b.normal_start_hour.isoformat(timespec="minutes"),
            normal_end=b.normal_end_hour.isoformat(timespec="minutes"),
        ) if value < b.normal_start_hour or value > b.normal_end_hour else []


class RepeatedInvoiceModificationRule(FraudRule):
    name="REPEATED_INVOICE_MODIFICATION"
    def __init__(self,cfg): self.cfg=cfg
    def evaluate(self,t,b,context):
        if t.invoice_modifications < 2:
            return []
        if t.invoice_modifications >= self.cfg.invoice_modifications:
            severity, score = "HIGH", 72
        elif t.invoice_modifications == self.cfg.invoice_modifications - 1:
            severity, score = "MEDIUM", 58
        else:
            severity, score = "LOW", 42
        return self.alert(
            t,
            "Invoice modified repeatedly",
            f"Invoice modification count {t.invoice_modifications} is compared with thresholds LOW=1, MEDIUM=2, HIGH>={self.cfg.invoice_modifications}.",
            score,
            severity,
            threshold=self.cfg.invoice_modifications,
            threshold_low=2,
            threshold_medium=self.cfg.invoice_modifications - 1,
            baseline_scope=b.scope,
            baseline_scope_key=b.scope_key,
            baseline_scope_label=b.scope_label,
            baseline_samples=b.total_transactions,
            baseline_period_start=context.get("baseline_period_start"),
            baseline_period_end=context.get("baseline_period_end"),
        )


class BackdatedTransactionRule(FraudRule):
    name="BACKDATED_TRANSACTION"
    def __init__(self,cfg): self.cfg=cfg
    def evaluate(self,t,b,context):
        lag=(t.created_at.date()-t.occurred_at.date()).days
        if lag < 3:
            return []
        if lag > self.cfg.backdated_days:
            severity, score = "HIGH", 78
        elif lag >= 7:
            severity, score = "MEDIUM", 62
        else:
            severity, score = "LOW", 42
        return self.alert(
            t,
            "Backdated transaction",
            f"Transaction date is {lag} days before creation date; compared with HIGH threshold > {self.cfg.backdated_days} days.",
            score,
            severity,
            lag_days=lag,
            threshold_high_days=self.cfg.backdated_days,
            threshold_medium_days=7,
            threshold_low_days=3,
            baseline_scope=b.scope,
            baseline_scope_key=b.scope_key,
            baseline_scope_label=b.scope_label,
            baseline_samples=b.total_transactions,
            baseline_period_start=context.get("baseline_period_start"),
            baseline_period_end=context.get("baseline_period_end"),
        )


class DuplicateFinanceReferenceRule(FraudRule):
    name = "DUPLICATE_FINANCE_REFERENCE"

    def evaluate(self, t, b, context):
        meta = t.metadata or {}
        ft = str(meta.get("fromtrans") or meta.get("document_type") or "").strip()
        if ft != "csh_paym":
            return []
        ref = str(meta.get("reference_key") or meta.get("check_no") or meta.get("reference_no") or "").strip()
        if not ref:
            return []
        key = (
            ft,
            ref.lower(),
            str(meta.get("party_code") or "").strip().lower(),
            str(meta.get("currency") or "").strip().upper(),
            round(abs(float(t.amount or 0)), 2),
        )
        count = context.get("finance_duplicate_refs", Counter()).get(key, 0)
        if count < 2:
            return []
        label = "Bank Payment"
        return self.alert(
            t,
            f"Duplicate {label} reference",
            f"{label} reference/check {ref} appears on {count} transaction(s) for the same party, currency and amount.",
            94,
            "CRITICAL",
            event_key=f"duplicate-finance-reference:{ft}:{ref.lower()}:{key[2]}:{key[3]}:{key[4]}",
            reference_key=ref,
            duplicate_count=count,
            fromtrans=ft,
            fromtrans_label=label,
            baseline_scope=b.scope,
            baseline_scope_key=b.scope_key,
            baseline_scope_label=b.scope_label,
            baseline_samples=b.total_transactions,
        )


class UnbalancedFinanceGLPostingRule(FraudRule):
    name = "UNBALANCED_FINANCE_GL_POSTING"

    def evaluate(self, t, b, context):
        meta = t.metadata or {}
        ft = str(meta.get("fromtrans") or meta.get("document_type") or "").strip()
        if ft not in {"csh_paym", "csh_recp", "sub_jour"}:
            return []
        balance = float(meta.get("gl_balance_local") or 0)
        if abs(balance) <= 0.1:
            return []
        labels = {"csh_paym": "Bank Payment", "csh_recp": "Bank Receipt", "sub_jour": "General Journal"}
        label = labels.get(ft, ft)
        return self.alert(
            t,
            f"Unbalanced GL posting for {label}",
            f"{label} has GL posting balance {balance:,.2f}; finance should compare gen_ledger_detail with the original finance rows.",
            97,
            "CRITICAL",
            event_key=f"unbalanced-finance-gl:{t.transaction_id}",
            gl_balance_local=balance,
            gl_rows=int(float(meta.get("gl_rows") or 0)),
            fromtrans=ft,
            fromtrans_label=label,
            baseline_scope=b.scope,
            baseline_scope_key=b.scope_key,
            baseline_scope_label=b.scope_label,
            baseline_samples=b.total_transactions,
        )


def default_rules(cfg: RuleThresholds) -> list[FraudRule]:
    rules = [HighAmountRule(cfg), FrequencySpikeRule(cfg), HighRefundRule(cfg),
             AbnormalDiscountRule(cfg), TooManyVoidRule(cfg),
             RepeatedInvoiceModificationRule(cfg), BackdatedTransactionRule(cfg),
             UnbalancedFinanceGLPostingRule()]
    if os.getenv("FRAUD_ENABLE_DUPLICATE_FINANCE_REFERENCE", "false").lower() in {"1", "true", "yes", "y"}:
        rules.append(DuplicateFinanceReferenceRule())
    if os.getenv("FRAUD_ENABLE_OUTSIDE_HOURS", "false").lower() in {"1", "true", "yes", "y"}:
        rules.append(OutsideWorkingHoursRule())
    return rules
