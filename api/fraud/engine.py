from collections import Counter, defaultdict
from datetime import datetime, timedelta

from .domain import Transaction, UserBaseline


SYSTEM_USERS = {"onlinesys", "system", "sys", "admin"}


def _fromtrans(row: Transaction) -> str:
    meta = row.metadata or {}
    return str(meta.get("fromtrans") or meta.get("document_type") or "UNKNOWN").strip() or "UNKNOWN"


class FraudRuleEngine:
    """Model-independent detector; a future AI engine can implement the same run contract."""
    def __init__(self, rules, history_days: int = 90, exclude_recent_days: int = 7,
                 current_days: int = 30, min_scope_samples: int = 20, min_fromtrans_samples: int = 50):
        self.rules = list(rules)
        self.history_days = history_days
        self.exclude_recent_days = exclude_recent_days
        self.current_days = current_days
        self.min_scope_samples = min_scope_samples
        self.min_fromtrans_samples = min_fromtrans_samples

    def run(self, transactions: list[Transaction], as_of: datetime):
        history_end = as_of - timedelta(days=self.exclude_recent_days)
        history_start = history_end - timedelta(days=self.history_days)
        current_start = as_of - timedelta(days=self.current_days)
        history_user, history_user_fromtrans, history_fromtrans, current = defaultdict(list), defaultdict(list), defaultdict(list), []
        for row in transactions:
            # A backdated record is a new event by creation time even when its
            # business transaction date belongs to the historical window.
            if current_start <= row.created_at <= as_of:
                current.append(row)
            elif history_start <= row.created_at < history_end:
                ft = _fromtrans(row)
                history_user[row.user_id].append(row)
                history_user_fromtrans[(row.user_id, ft)].append(row)
                history_fromtrans[ft].append(row)
        user_baselines = {
            u: UserBaseline.build(u, rows, "user", u, f"user {u}")
            for u, rows in history_user.items() if rows
        }
        user_ft_baselines = {
            key: UserBaseline.build(key[0], rows, "user_fromtrans", f"{key[0]}:{key[1]}", f"user {key[0]} + fromtrans {key[1]}")
            for key, rows in history_user_fromtrans.items() if len(rows) >= self.min_scope_samples
        }
        ft_baselines = {
            ft: UserBaseline.build("__fromtrans__", rows, "fromtrans", ft, f"company fromtrans {ft}")
            for ft, rows in history_fromtrans.items() if len(rows) >= self.min_fromtrans_samples
        }
        baselines = dict(user_baselines)
        baselines.update({f"user_fromtrans:{k[0]}:{k[1]}": v for k, v in user_ft_baselines.items()})
        baselines.update({f"fromtrans:{k}": v for k, v in ft_baselines.items()})
        context = {
            "daily_counts_user": Counter((r.user_id, r.created_at.date()) for r in current),
            "daily_counts_user_fromtrans": Counter((r.user_id, _fromtrans(r), r.created_at.date()) for r in current),
            "daily_counts_fromtrans": Counter((_fromtrans(r), r.created_at.date()) for r in current),
            "baseline_period_start": history_start.isoformat(),
            "baseline_period_end": history_end.isoformat(),
            "baseline_history_days": self.history_days,
            "baseline_exclude_recent_days": self.exclude_recent_days,
        }
        alerts = []
        for row in current:
            ft = _fromtrans(row)
            is_system_user = row.user_id.lower() in SYSTEM_USERS
            if is_system_user:
                baseline = ft_baselines.get(ft) or user_ft_baselines.get((row.user_id, ft)) or user_baselines.get(row.user_id)
            else:
                baseline = user_ft_baselines.get((row.user_id, ft)) or user_baselines.get(row.user_id) or ft_baselines.get(ft)
            if not baseline: continue
            for rule in self.rules:
                alerts.extend(rule.evaluate(row, baseline, context))
        return alerts, baselines
