"""In-process fraud scheduler started and stopped with FastAPI."""
from __future__ import annotations

import json
import logging
import os
import threading
from datetime import datetime
from pathlib import Path

from .service import FraudDetectionService

log = logging.getLogger(__name__)
STATE_FILE = Path(__file__).resolve().parents[2] / "data" / "scheduler_state.json"
_stop = threading.Event()
_thread: threading.Thread | None = None
_run_lock = threading.Lock()


def _read_fraud_state() -> dict:
    default = {
        "enabled": os.getenv("FRAUD_SCHEDULER_ENABLED", "false").lower() == "true",
        "interval": os.getenv("FRAUD_SCHEDULER_INTERVAL", "daily"),
        "time": os.getenv("FRAUD_SCHEDULER_TIME", "01:00"),
        "day": os.getenv("FRAUD_SCHEDULER_DAY", "monday"),
        "last_run_at": None, "last_run_status": None,
        "last_run_duration_sec": None, "is_running": False,
    }
    if STATE_FILE.exists():
        try:
            default.update(json.loads(STATE_FILE.read_text(encoding="utf-8")).get("fraud", {}))
        except (OSError, ValueError):
            log.exception("Cannot read fraud scheduler state")
    return default


def _write_fraud_state(values: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    state = {}
    if STATE_FILE.exists():
        try: state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError): pass
    state["fraud"] = values
    temporary = STATE_FILE.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, indent=2), encoding="utf-8")
    temporary.replace(STATE_FILE)


def _is_due(cfg: dict, now: datetime) -> bool:
    if not cfg.get("enabled") or cfg.get("is_running"): return False
    try: hour, minute = (int(v) for v in cfg.get("time", "01:00").split(":"))
    except (TypeError, ValueError): return False
    last = datetime.fromisoformat(cfg["last_run_at"]) if cfg.get("last_run_at") else None
    interval = cfg.get("interval", "daily")
    if interval == "hourly":
        return now.minute == minute and (not last or (last.year,last.month,last.day,last.hour) != (now.year,now.month,now.day,now.hour))
    if now.hour != hour or now.minute != minute: return False
    if interval == "weekly" and now.strftime("%A").lower() != cfg.get("day", "monday").lower(): return False
    return not last or last.date() != now.date()


def run_fraud_job() -> bool:
    if not _run_lock.acquire(blocking=False): return False
    cfg = _read_fraud_state(); start = datetime.now(); cfg["is_running"] = True; _write_fraud_state(cfg)
    status = "failed"; last_result = None
    try:
        scopes = json.loads(os.getenv("FRAUD_SCHEDULER_SCOPES", "[]"))
        if not scopes: raise RuntimeError("FRAUD_SCHEDULER_SCOPES is empty")
        service = FraudDetectionService()
        results = []
        for scope in scopes:
            result = service.run(str(scope["masterfn"]), str(scope["companyfn"]))
            result["masterfn"] = str(scope["masterfn"]); result["companyfn"] = str(scope["companyfn"])
            results.append(result)
        last_result = {
            "scopes": len(results),
            "transactions": sum(r["transactions"] for r in results),
            "users": sum(r["users"] for r in results),
            "detected": sum(r["detected"] for r in results),
            "created": sum(r["created"] for r in results),
            "by_scope": {f"{r['masterfn']}|{r['companyfn']}": {
                k:r[k] for k in ("transactions","users","detected","created")
            } for r in results},
        }
        status = "success"; return True
    except Exception:
        log.exception("In-process fraud scheduler failed"); return False
    finally:
        cfg = _read_fraud_state(); cfg.update({
            "is_running": False, "last_run_at": start.isoformat(),
            "last_run_status": status,
            "last_run_duration_sec": int((datetime.now()-start).total_seconds()),
        })
        if last_result is not None: cfg["last_result"] = last_result
        _write_fraud_state(cfg); _run_lock.release()


def _loop() -> None:
    log.info("FastAPI fraud scheduler started")
    while not _stop.wait(20):
        cfg = _read_fraud_state()
        if _is_due(cfg, datetime.now()): run_fraud_job()


def start_fraud_scheduler() -> None:
    global _thread
    if _thread and _thread.is_alive(): return
    _stop.clear(); _thread = threading.Thread(target=_loop, name="fraud-scheduler", daemon=True); _thread.start()


def stop_fraud_scheduler() -> None:
    _stop.set()
    if _thread and _thread.is_alive(): _thread.join(timeout=5)


def fraud_scheduler_running() -> bool:
    return bool(_thread and _thread.is_alive())
