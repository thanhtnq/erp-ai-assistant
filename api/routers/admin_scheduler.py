"""
ERP AI Assistant — Admin Scheduler Router
Endpoints: /admin/scheduler/status, /admin/scheduler/jobs/{job}/enable, /admin/scheduler/jobs/{job}/disable,
           /admin/scheduler/jobs/{job}/run-now, /admin/scheduler/jobs/{job}/config
"""
import json
import os
import sys
import threading
import subprocess
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from starlette.requests import Request
from api.auth import verify_api_key
from api.models import AdminSchedulerAction, AdminSchedulerConfig
from api.database import get_knowledge_conn
from api.utils import now_iso, log_admin_action, _get_client_ip
from api.fraud import FraudDetectionService


router = APIRouter()

SCHEDULER_STATE_FILE = Path(__file__).parent.parent.parent / "data" / "scheduler_state.json"
INGEST_DIR = Path(__file__).parent.parent.parent / "ingest"

_SCHED_DEFAULTS = {
    "documents": {"enabled": True,  "interval": "daily", "time": "02:00", "day": "monday"},
    "tickets":   {"enabled": True,  "interval": "daily", "time": "03:00", "day": "monday"},
    "fraud":     {"enabled": False, "interval": "daily", "time": "01:00", "day": "monday"},
}

_VALID_JOBS = {"documents", "tickets", "fraud"}
_JOB_SCRIPTS = {
    "documents": "ingest_knowledge.py",
    "tickets":   "ingest_tickets.py",
}

_sched_lock = threading.Lock()


def _read_sched_state() -> dict:
    try:
        from ingest.ingest_config import SCHEDULE as _SC
        defaults = {
            "documents": {
                "enabled":  _SC.get("ingest_documents", {}).get("enabled",  True),
                "interval": _SC.get("ingest_documents", {}).get("interval", "daily"),
                "time":     _SC.get("ingest_documents", {}).get("time",     "02:00"),
                "day":      _SC.get("ingest_documents", {}).get("day",      "monday"),
            },
            "tickets": {
                "enabled":  _SC.get("ingest_tickets", {}).get("enabled",  True),
                "interval": _SC.get("ingest_tickets", {}).get("interval", "daily"),
                "time":     _SC.get("ingest_tickets", {}).get("time",     "03:00"),
                "day":      _SC.get("ingest_tickets", {}).get("day",      "monday"),
            },
            "fraud": {
                "enabled": os.getenv("FRAUD_SCHEDULER_ENABLED", "false").lower() == "true",
                "interval": os.getenv("FRAUD_SCHEDULER_INTERVAL", "daily"),
                "time": os.getenv("FRAUD_SCHEDULER_TIME", "01:00"),
                "day": os.getenv("FRAUD_SCHEDULER_DAY", "monday"),
            },
        }
    except Exception:
        import copy
        defaults = copy.deepcopy(_SCHED_DEFAULTS)

    for job in ("documents", "tickets", "fraud"):
        defaults[job].setdefault("last_run_at",          None)
        defaults[job].setdefault("last_run_status",      None)
        defaults[job].setdefault("last_run_duration_sec", None)
        defaults[job].setdefault("is_running",           False)

    if SCHEDULER_STATE_FILE.exists():
        try:
            saved = json.loads(SCHEDULER_STATE_FILE.read_text(encoding="utf-8"))
            for job, cfg in saved.items():
                if job in defaults:
                    defaults[job].update(cfg)
        except Exception:
            pass

    return defaults


def _write_sched_state(state: dict):
    SCHEDULER_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    SCHEDULER_STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _run_ingest_background(job: str, admin_user_id: str):
    with _sched_lock:
        state = _read_sched_state()
        if state[job].get("is_running"):
            return
        state[job]["is_running"] = True
        _write_sched_state(state)

    start = datetime.now()
    status = "failed"
    duration = None
    try:
        if job == "fraud":
            scopes = json.loads(os.getenv("FRAUD_SCHEDULER_SCOPES", "[]"))
            if not scopes:
                raise RuntimeError("FRAUD_SCHEDULER_SCOPES is empty")
            service = FraudDetectionService()
            for scope in scopes:
                service.run(str(scope["masterfn"]), str(scope["companyfn"]))
            status = "success"
        else:
            result = subprocess.run(
                [sys.executable, _JOB_SCRIPTS[job]], cwd=str(INGEST_DIR),
                capture_output=True, text=True, timeout=7200,
            )
            status = "success" if result.returncode == 0 else "failed"
    except subprocess.TimeoutExpired:
        status = "failed"
    except Exception:
        status = "failed"
    finally:
        duration = int((datetime.now() - start).total_seconds())
        with _sched_lock:
            state = _read_sched_state()
            state[job]["is_running"]            = False
            state[job]["last_run_at"]           = start.isoformat()
            state[job]["last_run_status"]       = status
            state[job]["last_run_duration_sec"] = duration
            _write_sched_state(state)

        try:
            kconn = get_knowledge_conn()
            action = "ingest_completed" if status == "success" else "ingest_failed"
            log_admin_action(kconn, admin_user_id, action,
                             target_type="scheduler_job", target_id=job,
                             meta={"job": job, "duration_sec": duration, "trigger": "run_now"})
            kconn.close()
        except Exception:
            pass


@router.get("/scheduler/status")
async def admin_scheduler_status(_key: str = Depends(verify_api_key)):
    with _sched_lock:
        state = _read_sched_state()
    return state


@router.post("/scheduler/jobs/{job}/enable")
async def admin_scheduler_enable(
    job: str,
    body: AdminSchedulerAction,
    request: Request,
    _key: str = Depends(verify_api_key),
):
    if job not in _VALID_JOBS:
        raise HTTPException(status_code=404, detail="Unknown job")
    with _sched_lock:
        state = _read_sched_state()
        state[job]["enabled"] = True
        _write_sched_state(state)
    kconn = get_knowledge_conn()
    log_admin_action(kconn, body.admin_user_id, "scheduler_enable",
                     target_type="scheduler_job", target_id=job,
                     ip=_get_client_ip(request))
    kconn.close()
    return {"status": "enabled"}


@router.post("/scheduler/jobs/{job}/disable")
async def admin_scheduler_disable(
    job: str,
    body: AdminSchedulerAction,
    request: Request,
    _key: str = Depends(verify_api_key),
):
    if job not in _VALID_JOBS:
        raise HTTPException(status_code=404, detail="Unknown job")
    with _sched_lock:
        state = _read_sched_state()
        state[job]["enabled"] = False
        _write_sched_state(state)
    kconn = get_knowledge_conn()
    log_admin_action(kconn, body.admin_user_id, "scheduler_disable",
                     target_type="scheduler_job", target_id=job,
                     ip=_get_client_ip(request))
    kconn.close()
    return {"status": "disabled"}


@router.post("/scheduler/jobs/{job}/run-now")
async def admin_scheduler_run_now(
    job: str,
    body: AdminSchedulerAction,
    request: Request,
    _key: str = Depends(verify_api_key),
):
    if job not in _VALID_JOBS:
        raise HTTPException(status_code=404, detail="Unknown job")
    with _sched_lock:
        state = _read_sched_state()
        if state[job].get("is_running"):
            raise HTTPException(status_code=409, detail="Job is already running")

    t = threading.Thread(
        target=_run_ingest_background,
        args=(job, body.admin_user_id),
        daemon=True,
        name=f"admin-ingest-{job}",
    )
    t.start()

    kconn = get_knowledge_conn()
    log_admin_action(kconn, body.admin_user_id, "scheduler_run_now",
                     target_type="scheduler_job", target_id=job,
                     ip=_get_client_ip(request))
    kconn.close()
    return {"status": "started"}


@router.put("/scheduler/jobs/{job}/config")
async def admin_scheduler_update_config(
    job: str,
    body: AdminSchedulerConfig,
    request: Request,
    _key: str = Depends(verify_api_key),
):
    if job not in _VALID_JOBS:
        raise HTTPException(status_code=404, detail="Unknown job")
    if body.interval not in ("hourly", "daily", "weekly"):
        raise HTTPException(status_code=400, detail="interval must be hourly|daily|weekly")

    with _sched_lock:
        state = _read_sched_state()
        state[job]["interval"] = body.interval
        state[job]["time"]     = body.time
        state[job]["day"]      = body.day
        _write_sched_state(state)

    kconn = get_knowledge_conn()
    log_admin_action(kconn, body.admin_user_id, "scheduler_update_time",
                     target_type="scheduler_job", target_id=job,
                     meta={"interval": body.interval, "time": body.time, "day": body.day},
                     ip=_get_client_ip(request))
    kconn.close()
    return {"status": "updated"}
