"""
ERP AI — Ingest Scheduler
Auto-runs document, ticket, fraud detection, and ERP extract on a schedule.

Usage:
    python scheduler.py           # start scheduler (runs in background)
    python scheduler.py --run-now # run all jobs immediately and exit
    python scheduler.py --status  # show next scheduled run times

Requires: pip install schedule
"""

import argparse
import json
import logging
import subprocess
import sys
import threading
import os
from datetime import datetime
from pathlib import Path

try:
    import schedule
    import time
except ImportError:
    print("[ERROR] schedule not installed. Run: pip install schedule")
    sys.exit(1)

# Add ingest folder to path
sys.path.insert(0, str(Path(__file__).parent.parent / "ingest"))
from ingest_config import SCHEDULE
sys.path.insert(0, str(Path(__file__).parent.parent))
from api.fraud import FraudDetectionService

# Shared with the admin scheduler API; one state file is the source of truth.
STATE_FILE = Path(__file__).parent.parent / "data" / "scheduler_state.json"
_state_lock = threading.Lock()


def _read_state() -> dict:
    """Return state file contents, falling back to ingest_config.SCHEDULE."""
    defaults = {
        "documents": {
            "enabled":  SCHEDULE.get("ingest_documents", {}).get("enabled",  True),
            "interval": SCHEDULE.get("ingest_documents", {}).get("interval", "daily"),
            "time":     SCHEDULE.get("ingest_documents", {}).get("time",     "02:00"),
            "day":      SCHEDULE.get("ingest_documents", {}).get("day",      "monday"),
            "last_run_at": None, "last_run_status": None,
            "last_run_duration_sec": None, "is_running": False,
        },
        "tickets": {
            "enabled":  SCHEDULE.get("ingest_tickets", {}).get("enabled",  True),
            "interval": SCHEDULE.get("ingest_tickets", {}).get("interval", "daily"),
            "time":     SCHEDULE.get("ingest_tickets", {}).get("time",     "03:00"),
            "day":      SCHEDULE.get("ingest_tickets", {}).get("day",      "monday"),
            "last_run_at": None, "last_run_status": None,
            "last_run_duration_sec": None, "is_running": False,
        },
        "fraud": {
            "enabled": os.getenv("FRAUD_SCHEDULER_ENABLED", "false").lower() == "true",
            "interval": os.getenv("FRAUD_SCHEDULER_INTERVAL", "daily"),
            "time": os.getenv("FRAUD_SCHEDULER_TIME", "01:00"),
            "day": os.getenv("FRAUD_SCHEDULER_DAY", "monday"),
            "last_run_at": None, "last_run_status": None,
            "last_run_duration_sec": None, "is_running": False,
        },
        "erp_extract": {
            "enabled":  True,
            "interval": "weekly",
            "time":     "00:00",
            "day":      "sunday",
            "last_run_at": None, "last_run_status": None,
            "last_run_duration_sec": None, "is_running": False,
        },
    }
    if STATE_FILE.exists():
        try:
            saved = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            for job, cfg in saved.items():
                if job in defaults:
                    defaults[job].update(cfg)
        except Exception:
            pass
    return defaults


def _write_state(state: dict):
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except Exception as e:
        log.warning(f"Could not write state file: {e}")

# ─── Logging ──────────────────────────────────────────────────────────────────

LOG_FILE = Path(__file__).parent / "scheduler.log"

logging.basicConfig(
    level   = logging.INFO,
    format  = "%(asctime)s [%(levelname)s] %(message)s",
    handlers = [
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger("scheduler")

# ─── Job runners ──────────────────────────────────────────────────────────────

INGEST_DIR = Path(__file__).parent.parent / "ingest"

# Guard flags — prevent overlapping runs of the same job type
_running: dict = {"documents": False, "tickets": False, "fraud": False, "erp_extract": False}
_running_lock = threading.Lock()


def _run_in_thread(job_fn, job_name: str):
    """Run a job function in a daemon thread, skipping if already running."""
    with _running_lock:
        if _running.get(job_name):
            log.warning(f"  {job_name} ingest already running — skipping scheduled trigger")
            return
        _running[job_name] = True

    def _target():
        try:
            job_fn()
        finally:
            with _running_lock:
                _running[job_name] = False

    t = threading.Thread(target=_target, daemon=True, name=f"ingest-{job_name}")
    t.start()


def _update_job_state(job: str, status: str, start: datetime):
    elapsed = int((datetime.now() - start).total_seconds())
    with _state_lock:
        state = _read_state()
        state[job]["is_running"]            = False
        state[job]["last_run_at"]           = start.isoformat()
        state[job]["last_run_status"]       = status
        state[job]["last_run_duration_sec"] = elapsed
        _write_state(state)


def _mark_running(job: str):
    with _state_lock:
        state = _read_state()
        state[job]["is_running"] = True
        _write_state(state)


def run_ingest_documents():
    """Run ingest_knowledge.py — processes new/changed documents."""
    log.info("▶ Starting document ingest...")
    _mark_running("documents")
    start = datetime.now()
    status = "failed"
    try:
        result = subprocess.run(
            [sys.executable, "ingest_knowledge.py"],
            cwd     = INGEST_DIR,
            capture_output = True,
            text    = True,
            timeout = 7200,
        )
        elapsed = (datetime.now() - start).seconds
        if result.returncode == 0:
            status = "success"
            log.info(f"✓ Document ingest completed in {elapsed}s")
            lines = result.stdout.strip().split("\n")
            for line in lines[-5:]:
                if line.strip():
                    log.info(f"  {line}")
        else:
            log.error(f"✗ Document ingest failed (code {result.returncode}) in {elapsed}s")
            log.error(result.stderr[-500:] if result.stderr else "No stderr")
    except subprocess.TimeoutExpired:
        log.error("✗ Document ingest timed out after 2 hours")
    except Exception as e:
        log.error(f"✗ Document ingest error: {e}")
    finally:
        _update_job_state("documents", status, start)


def run_ingest_tickets():
    """Run ingest_tickets.py — syncs new resolved tickets from PostgreSQL."""
    log.info("▶ Starting ticket ingest...")
    _mark_running("tickets")
    start = datetime.now()
    status = "failed"
    try:
        result = subprocess.run(
            [sys.executable, "ingest_tickets.py"],
            cwd     = INGEST_DIR,
            capture_output = True,
            text    = True,
            timeout = 3600,
        )
        elapsed = (datetime.now() - start).seconds
        if result.returncode == 0:
            status = "success"
            log.info(f"✓ Ticket ingest completed in {elapsed}s")
            lines = result.stdout.strip().split("\n")
            for line in lines[-5:]:
                if line.strip():
                    log.info(f"  {line}")
        else:
            log.error(f"✗ Ticket ingest failed (code {result.returncode}) in {elapsed}s")
            log.error(result.stderr[-500:] if result.stderr else "No stderr")
    except subprocess.TimeoutExpired:
        log.error("✗ Ticket ingest timed out after 1 hour")
    except Exception as e:
        log.error(f"✗ Ticket ingest error: {e}")
    finally:
        _update_job_state("tickets", status, start)

def run_fraud_detection():
    """Run fraud detection for configured tenant scopes."""
    log.info("Starting scheduled fraud detection..."); _mark_running("fraud")
    start=datetime.now(); status="failed"
    try:
        scopes=json.loads(os.getenv("FRAUD_SCHEDULER_SCOPES", "[]"))
        if not scopes: raise RuntimeError("FRAUD_SCHEDULER_SCOPES is empty")
        service=FraudDetectionService()
        for scope in scopes: service.run(str(scope["masterfn"]),str(scope["companyfn"]))
        status="success"
    except Exception:
        log.exception("Scheduled fraud detection failed")
    finally: _update_job_state("fraud",status,start)


def run_erp_extract():
    """Run ERP data extraction for all enabled scopes."""
    log.info("▶ Starting ERP extract...")
    _mark_running("erp_extract")
    start = datetime.now()
    status = "failed"
    try:
        from schedule.run_erp_extract import run_erp_extract as _run_extract
        results = _run_extract(incremental=True)
        success_count = sum(1 for r in results if r["status"] == "success")
        fail_count = sum(1 for r in results if r["status"] != "success")
        elapsed = (datetime.now() - start).seconds
        log.info(f"✓ ERP extract completed: {success_count} OK, {fail_count} failed in {elapsed}s")
        if fail_count > 0:
            for r in results:
                if r["status"] != "success":
                    log.error(f"  FAILED {r['scope']}: {r.get('error', 'Unknown')}")
        status = "success" if fail_count == 0 else "partial"
    except Exception as e:
        log.error(f"✗ ERP extract error: {e}")
    finally:
        _update_job_state("erp_extract", status, start)


# ─── Schedule setup ───────────────────────────────────────────────────────────

def _register_job(cfg: dict, job_fn, job_name: str) -> bool:
    """Register one job in the schedule library based on cfg dict. Returns True if registered."""
    if not cfg.get("enabled"):
        return False
    interval = cfg.get("interval", "daily")
    run_time = cfg.get("time", "02:00")
    fn = lambda: _run_in_thread(job_fn, job_name)
    if interval == "hourly":
        schedule.every().hour.do(fn)
        log.info(f"  Scheduled: {job_name} ingest — every hour")
    elif interval == "weekly":
        day = cfg.get("day", "monday").lower()
        getattr(schedule.every(), day).at(run_time).do(fn)
        log.info(f"  Scheduled: {job_name} ingest — every {day} at {run_time}")
    else:
        schedule.every().day.at(run_time).do(fn)
        log.info(f"  Scheduled: {job_name} ingest — daily at {run_time}")
    return True


def setup_schedule():
    """Configure jobs — reads state file first, falls back to ingest_config.SCHEDULE."""
    state = _read_state()
    jobs_registered = 0
    if _register_job(state["documents"], run_ingest_documents, "documents"):
        jobs_registered += 1
    if _register_job(state["tickets"], run_ingest_tickets, "tickets"):
        jobs_registered += 1
    if _register_job(state["fraud"], run_fraud_detection, "fraud"):
        jobs_registered += 1
    if _register_job(state["erp_extract"], run_erp_extract, "erp_extract"):
        jobs_registered += 1
    return jobs_registered


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="ERP AI Ingest Scheduler")
    parser.add_argument("--run-now", action="store_true", help="Run all jobs immediately and exit")
    parser.add_argument("--status",  action="store_true", help="Show next scheduled run times")
    args = parser.parse_args()

    if args.run_now:
        log.info("Running all jobs immediately...")
        _run_in_thread(run_ingest_documents, "documents")
        _run_in_thread(run_ingest_tickets, "tickets")
        if _read_state()["fraud"].get("enabled"):
            _run_in_thread(run_fraud_detection, "fraud")
        if _read_state()["erp_extract"].get("enabled"):
            _run_in_thread(run_erp_extract, "erp_extract")
        # Wait for all daemon threads to finish before exiting
        for t in threading.enumerate():
            if t.name.startswith("ingest-"):
                t.join()
        log.info("Done.")
        return

    log.info("ERP AI Ingest Scheduler starting...")
    n = setup_schedule()

    if n == 0:
        log.warning("No jobs scheduled. Check SCHEDULE config in ingest/ingest_config.py")
        return

    if args.status:
        print(f"\nScheduled jobs:")
        for job in schedule.get_jobs():
            print(f"  {job}")
        print()
        return

    log.info(f"{n} job(s) scheduled. Scheduler running... (Ctrl+C to stop)")
    log.info(f"Log file: {LOG_FILE}")

    try:
        while True:
            schedule.run_pending()
            time.sleep(30)  # check every 30 seconds
    except KeyboardInterrupt:
        log.info("Scheduler stopped.")


if __name__ == "__main__":
    main()
