from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time
from statistics import mean, median, pstdev
from typing import Any


@dataclass(frozen=True)
class Transaction:
    transaction_id: str
    user_id: str
    occurred_at: datetime
    created_at: datetime
    amount: float = 0.0
    discount: float = 0.0
    refund_count: int = 0
    void_count: int = 0
    invoice_modifications: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class UserBaseline:
    user_id: str
    scope: str
    scope_key: str
    scope_label: str
    total_transactions: int
    total_amount: float
    average_amount: float
    median_amount: float
    p95_amount: float
    p99_amount: float
    maximum_amount: float
    minimum_amount: float
    standard_deviation: float
    average_transactions_per_day: float
    average_discount: float
    average_refund_count: float
    average_void_count: float
    normal_start_hour: time
    normal_end_hour: time

    @classmethod
    def build(cls, user_id: str, rows: list[Transaction], scope: str = "user",
              scope_key: str | None = None, scope_label: str | None = None) -> "UserBaseline":
        amounts = [abs(r.amount) for r in rows]
        sorted_amounts = sorted(amounts)
        def percentile(p: float) -> float:
            if not sorted_amounts:
                return 0.0
            idx = min(len(sorted_amounts) - 1, max(0, int(round((len(sorted_amounts) - 1) * p))))
            return sorted_amounts[idx]
        days = max(1, len({r.occurred_at.date() for r in rows}))
        hours = sorted(r.occurred_at.time().replace(second=0, microsecond=0) for r in rows)
        return cls(
            user_id, scope, scope_key or user_id, scope_label or user_id,
            len(rows), sum(amounts), mean(amounts), median(amounts),
            percentile(0.95), percentile(0.99), max(amounts), min(amounts), pstdev(amounts) if len(amounts) > 1 else 0.0,
            len(rows) / days, mean(r.discount for r in rows),
            mean(r.refund_count for r in rows), mean(r.void_count for r in rows),
            hours[0], hours[-1],
        )


@dataclass(frozen=True)
class AlertCandidate:
    rule_name: str
    user_id: str
    transaction_id: str
    severity: str
    title: str
    description: str
    risk_score: int
    event_key: str
    metadata: dict[str, Any] = field(default_factory=dict)
