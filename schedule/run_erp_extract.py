"""
Run ERP extract — gọi từ scheduler.
Hỗ trợ multi-scope, mỗi scope chạy theo lịch riêng.
Usage:
    python schedule/run_erp_extract.py                    # Run all enabled scopes
    python schedule/run_erp_extract.py --masterfn banleong369878mfn  # Run 1 scope
    python schedule/run_erp_extract.py --incremental       # Incremental mode
"""
import argparse
import json
import logging
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

SCOPES_FILE = Path(__file__).parent.parent / "data" / "erp_extract_scopes.json"
EXTRACT_SCRIPT = Path(__file__).parent.parent / "scripts" / "extract_erp_to_sqlite.py"
LOG_FILE = Path(__file__).parent.parent / "logs" / "erp_extract_scheduler.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(str(LOG_FILE), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("run_erp_extract")


def run_erp_extract(masterfn_filter=None, incremental=False):
    """Run extract for all scopes or a specific scope."""
    if not SCOPES_FILE.exists():
        logger.error(f"Scopes file not found: {SCOPES_FILE}")
        return []

    scopes_config = json.loads(SCOPES_FILE.read_text(encoding="utf-8"))
    scopes = scopes_config.get("scopes", [])

    if masterfn_filter:
        scopes = [s for s in scopes if s["masterfn"] == masterfn_filter]

    results = []
    for scope in scopes:
        if not scope.get("enabled", True):
            logger.info(f"  Skipping disabled scope: {scope.get('name', scope['masterfn'])}")
            continue

        scope_name = scope.get("name", f"{scope['masterfn']}/{scope['companyfn']}")
        logger.info(f"Starting extract for: {scope_name}")

        start = datetime.now()
        try:
            cmd = [sys.executable, str(EXTRACT_SCRIPT),
                   "--masterfn", scope["masterfn"],
                   "--companyfn", scope["companyfn"]]
            if incremental:
                cmd.append("--incremental")

            result = subprocess.run(
                cmd,
                capture_output=True, text=True, timeout=7200
            )
            elapsed = (datetime.now() - start).seconds
            status = "success" if result.returncode == 0 else "failed"
            error = result.stderr[-500:] if result.stderr and result.returncode != 0 else None

            if status == "success":
                logger.info(f"  OK {scope_name}: {elapsed}s")
            else:
                logger.error(f"  FAILED {scope_name}: {error}")

            results.append({
                "scope": scope_name,
                "masterfn": scope["masterfn"],
                "companyfn": scope["companyfn"],
                "status": status,
                "duration_sec": elapsed,
                "error": error,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        except subprocess.TimeoutExpired:
            logger.error(f"  TIMEOUT {scope_name}: exceeded 2 hours")
            results.append({
                "scope": scope_name,
                "masterfn": scope["masterfn"],
                "companyfn": scope["companyfn"],
                "status": "timeout",
                "error": "Timeout after 2 hours",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        except Exception as e:
            logger.error(f"  ERROR {scope_name}: {e}")
            results.append({
                "scope": scope_name,
                "masterfn": scope["masterfn"],
                "companyfn": scope["companyfn"],
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run ERP extract for all/specific scopes")
    parser.add_argument("--masterfn", help="Run for specific masterfn only")
    parser.add_argument("--incremental", action="store_true", help="Incremental mode")
    args = parser.parse_args()

    results = run_erp_extract(args.masterfn, args.incremental)
    print(f"\nResults: {len(results)} scope(s)")
    for r in results:
        icon = "OK" if r["status"] == "success" else "FAILED"
        print(f"  [{icon}] {r['scope']}: {r.get('duration_sec', '?')}s")
        if r.get("error"):
            print(f"    Error: {r['error']}")
