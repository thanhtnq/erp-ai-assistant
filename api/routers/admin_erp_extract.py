"""
ERP AI Assistant — Admin ERP Extract Router
Quản lý multi-company ERP data extraction:
  - CRUD scopes (thêm/sửa/xóa công ty)
  - Trigger extract (run-now)
  - Xem trạng thái, lịch sử extract
  - Xem data stats (row counts per table per scope)
"""
import json
import os
import sys
import threading
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from starlette.requests import Request
from pydantic import BaseModel

from api.auth import verify_api_key
from api.database import get_knowledge_conn
from api.utils import now_iso, log_admin_action, _get_client_ip

router = APIRouter()

# ─── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent.parent
SCOPES_FILE = BASE_DIR / "data" / "erp_extract_scopes.json"
EXTRACT_SCRIPT = BASE_DIR / "scripts" / "extract_erp_to_sqlite.py"
SQLITE_DB = BASE_DIR / "data" / "erp_extract.db"
STATE_FILE = BASE_DIR / "data" / "erp_extract_state.json"

# ─── Pydantic Models ────────────────────────────────────────────────────────────

class ScopeCreate(BaseModel):
    masterfn: str
    companyfn: str
    name: str = ""
    enabled: bool = True
    schedule_interval: str = "weekly"
    schedule_day: str = "sunday"
    schedule_time: str = "00:00"

class ScopeUpdate(BaseModel):
    name: Optional[str] = None
    enabled: Optional[bool] = None
    schedule_interval: Optional[str] = None
    schedule_day: Optional[str] = None
    schedule_time: Optional[str] = None

class ExtractRunRequest(BaseModel):
    admin_user_id: str = "admin"
    masterfn: Optional[str] = None
    companyfn: Optional[str] = None
    dry_run: bool = False

# ─── DB Config Models ──────────────────────────────────────────────────────────

class CompanyConfigCreate(BaseModel):
    masterfn: str
    companyfn: str
    company_name: str = ""
    api_key: str = ""
    enabled: bool = True
    notes: str = ""

class CompanyConfigUpdate(BaseModel):
    company_name: Optional[str] = None
    api_key: Optional[str] = None
    enabled: Optional[bool] = None
    notes: Optional[str] = None

# ─── Helpers ────────────────────────────────────────────────────────────────────

def _read_scopes() -> dict:
    """Read scopes config file."""
    if not SCOPES_FILE.exists():
        return {"scopes": [], "global_config": {}}
    try:
        return json.loads(SCOPES_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"scopes": [], "global_config": {}}

def _write_scopes(data: dict):
    """Write scopes config file."""
    SCOPES_FILE.parent.mkdir(parents=True, exist_ok=True)
    SCOPES_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def _read_state() -> dict:
    """Read extract state (last run, status, etc.)."""
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _write_state(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

def _get_sqlite_stats() -> dict:
    """Get row counts per table from SQLite extract DB."""
    import sqlite3
    if not SQLITE_DB.exists():
        return {"status": "no_db", "tables": {}}
    try:
        conn = sqlite3.connect(str(SQLITE_DB))
        conn.row_factory = sqlite3.Row
        # Get all tables
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '_extract%' ORDER BY name"
        ).fetchall()
        stats = {}
        for t in tables:
            name = t["name"]
            row = conn.execute(f"SELECT COUNT(*) as cnt FROM \"{name}\"").fetchone()
            stats[name] = row["cnt"]
        # Get meta
        meta_rows = conn.execute("SELECT key, value FROM _extract_meta").fetchall()
        meta = {r["key"]: r["value"] for r in meta_rows}
        conn.close()
        return {"status": "ok", "tables": stats, "meta": meta}
    except Exception as e:
        return {"status": "error", "error": str(e), "tables": {}}

_extract_lock = threading.Lock()

def _run_extract_background(admin_user_id: str, masterfn: str = None, companyfn: str = None, dry_run: bool = False):
    """Run extract in background thread."""
    with _extract_lock:
        state = _read_state()
        if state.get("is_running"):
            return  # already running
        state["is_running"] = True
        state["last_run_at"] = datetime.now(timezone.utc).isoformat()
        state["last_run_by"] = admin_user_id
        state["last_run_status"] = "running"
        _write_state(state)

    start = datetime.now()
    status = "failed"
    duration = None
    error_msg = None
    try:
        cmd = [sys.executable, str(EXTRACT_SCRIPT)]
        if masterfn:
            cmd.extend(["--masterfn", masterfn])
            if companyfn:
                cmd.extend(["--companyfn", companyfn])
        if dry_run:
            cmd.append("--dry-run")

        result = subprocess.run(
            cmd, cwd=str(BASE_DIR),
            capture_output=True, text=True, timeout=7200,
        )
        if result.returncode == 0:
            status = "success"
        else:
            error_msg = result.stderr[-500:] if result.stderr else "Unknown error"
    except subprocess.TimeoutExpired:
        error_msg = "Timeout after 2 hours"
    except Exception as e:
        error_msg = str(e)
    finally:
        duration = int((datetime.now() - start).total_seconds())
        with _extract_lock:
            state = _read_state()
            state["is_running"] = False
            state["last_run_at"] = start.isoformat()
            state["last_run_status"] = status
            state["last_run_duration_sec"] = duration
            state["last_run_error"] = error_msg

            # Track consecutive failures for alerting
            if status == "success":
                state["consecutive_failures"] = 0
                state["last_alert_cleared_at"] = datetime.now(timezone.utc).isoformat()
            else:
                state["consecutive_failures"] = state.get("consecutive_failures", 0) + 1
                state["last_failure_at"] = start.isoformat()
                state["last_failure_error"] = error_msg

            _write_state(state)

        # Log to admin action log
        try:
            kconn = get_knowledge_conn()
            action = "erp_extract_completed" if status == "success" else "erp_extract_failed"
            log_admin_action(kconn, admin_user_id, action,
                             target_type="erp_extract",
                             target_id=f"{masterfn or 'all'}/{companyfn or 'all'}",
                             meta={"masterfn": masterfn, "companyfn": companyfn,
                                   "duration_sec": duration, "dry_run": dry_run,
                                   "error": error_msg})
            kconn.close()
        except Exception:
            pass

        # Create alert if 2+ consecutive failures
        if status != "success" and state.get("consecutive_failures", 0) >= 2:
            try:
                kconn = get_knowledge_conn()
                log_admin_action(kconn, "system", "erp_extract_alert",
                                 target_type="erp_extract_alert",
                                 target_id=f"{masterfn or 'all'}/{companyfn or 'all'}",
                                 meta={
                                     "alert_type": "consecutive_failure",
                                     "consecutive_failures": state["consecutive_failures"],
                                     "last_error": error_msg,
                                     "masterfn": masterfn,
                                     "companyfn": companyfn,
                                     "recommendation": "Check PG connection, scope config, and disk space.",
                                 })
                kconn.close()
            except Exception:
                pass


# ─── API Endpoints ──────────────────────────────────────────────────────────────

@router.get("/erp-extract/scopes")
async def list_scopes(_key: str = Depends(verify_api_key)):
    """List all configured extract scopes (companies)."""
    data = _read_scopes()
    return data


@router.post("/erp-extract/scopes")
async def create_scope(
    body: ScopeCreate,
    request: Request,
    _key: str = Depends(verify_api_key),
):
    """Add a new company scope for ERP extraction."""
    data = _read_scopes()
    # Check duplicate
    for s in data.get("scopes", []):
        if s["masterfn"] == body.masterfn and s["companyfn"] == body.companyfn:
            raise HTTPException(400, "Scope already exists")
    
    scope = {
        "id": f"{body.masterfn}_{body.companyfn}",
        "masterfn": body.masterfn,
        "companyfn": body.companyfn,
        "name": body.name or f"{body.masterfn}/{body.companyfn}",
        "enabled": body.enabled,
        "schedule": {
            "interval": body.schedule_interval,
            "day": body.schedule_day,
            "time": body.schedule_time,
        }
    }
    data.setdefault("scopes", []).append(scope)
    _write_scopes(data)

    kconn = get_knowledge_conn()
    log_admin_action(kconn, body.admin_user_id or "admin", "erp_extract_scope_create",
                     target_type="erp_extract_scope", target_id=scope["id"],
                     ip=_get_client_ip(request))
    kconn.close()
    return {"status": "created", "scope": scope}


@router.put("/erp-extract/scopes/{scope_id}")
async def update_scope(
    scope_id: str,
    body: ScopeUpdate,
    request: Request,
    _key: str = Depends(verify_api_key),
):
    """Update a company scope configuration."""
    data = _read_scopes()
    for s in data.get("scopes", []):
        if s["id"] == scope_id:
            if body.name is not None:
                s["name"] = body.name
            if body.enabled is not None:
                s["enabled"] = body.enabled
            if body.schedule_interval is not None:
                s.setdefault("schedule", {})["interval"] = body.schedule_interval
            if body.schedule_day is not None:
                s.setdefault("schedule", {})["day"] = body.schedule_day
            if body.schedule_time is not None:
                s.setdefault("schedule", {})["time"] = body.schedule_time
            _write_scopes(data)
            kconn = get_knowledge_conn()
            log_admin_action(kconn, "admin", "erp_extract_scope_update",
                             target_type="erp_extract_scope", target_id=scope_id,
                             ip=_get_client_ip(request))
            kconn.close()
            return {"status": "updated", "scope": s}
    raise HTTPException(404, "Scope not found")


@router.delete("/erp-extract/scopes/{scope_id}")
async def delete_scope(
    scope_id: str,
    request: Request,
    _key: str = Depends(verify_api_key),
):
    """Remove a company scope."""
    data = _read_scopes()
    before = len(data.get("scopes", []))
    data["scopes"] = [s for s in data.get("scopes", []) if s["id"] != scope_id]
    if len(data["scopes"]) == before:
        raise HTTPException(404, "Scope not found")
    _write_scopes(data)
    kconn = get_knowledge_conn()
    log_admin_action(kconn, "admin", "erp_extract_scope_delete",
                     target_type="erp_extract_scope", target_id=scope_id,
                     ip=_get_client_ip(request))
    kconn.close()
    return {"status": "deleted"}


@router.post("/erp-extract/run")
async def run_extract(
    body: ExtractRunRequest,
    request: Request,
    _key: str = Depends(verify_api_key),
):
    """Trigger ERP data extraction (async)."""
    with _extract_lock:
        state = _read_state()
        if state.get("is_running"):
            raise HTTPException(409, "Extract is already running")

    t = threading.Thread(
        target=_run_extract_background,
        args=(body.admin_user_id, body.masterfn, body.companyfn, body.dry_run),
        daemon=True,
        name="erp-extract-bg",
    )
    t.start()

    kconn = get_knowledge_conn()
    log_admin_action(kconn, body.admin_user_id, "erp_extract_run",
                     target_type="erp_extract",
                     target_id=f"{body.masterfn or 'all'}/{body.companyfn or 'all'}",
                     meta={"dry_run": body.dry_run},
                     ip=_get_client_ip(request))
    kconn.close()
    return {"status": "started", "masterfn": body.masterfn, "companyfn": body.companyfn}


@router.get("/erp-extract/status")
async def extract_status(_key: str = Depends(verify_api_key)):
    """Get current extract status and last run info."""
    state = _read_state()
    stats = _get_sqlite_stats()
    return {
        "state": state,
        "database": stats,
    }


@router.get("/erp-extract/history")
async def extract_history(
    limit: int = Query(20, ge=1, le=100),
    _key: str = Depends(verify_api_key),
):
    """Get extract run history from action log."""
    kconn = get_knowledge_conn()
    rows = kconn.execute("""
        SELECT id, admin_user_id, action, target_type, target_id, meta, ip_address, created_at
        FROM admin_action_log
        WHERE target_type='erp_extract'
        ORDER BY id DESC
        LIMIT ?
    """, (limit,)).fetchall()
    kconn.close()
    return {
        "history": [
            {
                "id": r["id"],
                "admin_user_id": r["admin_user_id"],
                "action": r["action"],
                "target_id": r["target_id"],
                "meta": json.loads(r["meta"]) if r["meta"] else {},
                "ip_address": r["ip_address"],
                "created_at": r["created_at"],
            }
            for r in rows
        ]
    }


@router.get("/erp-extract/stats")
async def extract_stats(_key: str = Depends(verify_api_key)):
    """Get detailed row counts per table per scope from SQLite."""
    import sqlite3
    if not SQLITE_DB.exists():
        return {"status": "no_db", "message": "Extract DB not found. Run extract first."}
    
    try:
        conn = sqlite3.connect(str(SQLITE_DB))
        conn.row_factory = sqlite3.Row
        
        # Get distinct scopes
        scopes = conn.execute("""
            SELECT DISTINCT scope_masterfn, scope_companyfn 
            FROM scm_sal_main 
            ORDER BY scope_masterfn, scope_companyfn
        """).fetchall()
        
        scope_list = []
        for s in scopes:
            mfn = s["scope_masterfn"]
            cfn = s["scope_companyfn"]
            tables = {}
            for tbl in ["scm_sal_main", "scm_sal_data", "scm_pur_main", "scm_pur_data",
                        "scm_stk_main", "scm_stk_data", "stk_code_main", "stk_code_data",
                        "adm_cnt_main", "adm_cnt_data", "gen_ledger_detail", "gnl_maint_all",
                        "stkm_main_all", "memo_long_table", "prj_pbill_main", "prj_pbill_body",
                        "gen_ledger_stk"]:
                try:
                    row = conn.execute(
                        f"SELECT COUNT(*) as cnt FROM \"{tbl}\" WHERE scope_masterfn=? AND scope_companyfn=?",
                        (mfn, cfn)
                    ).fetchone()
                    tables[tbl] = row["cnt"]
                except Exception:
                    tables[tbl] = -1
            scope_list.append({
                "masterfn": mfn,
                "companyfn": cfn,
                "tables": tables,
                "total_rows": sum(v for v in tables.values() if v > 0),
            })
        
        conn.close()
        return {"status": "ok", "scopes": scope_list}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/erp-extract/health")
async def extract_health(_key: str = Depends(verify_api_key)):
    """Health check for ERP extract system."""
    import sqlite3
    
    health = {
        "status": "ok",
        "checks": {},
        "warnings": [],
    }
    
    # Check 1: SQLite DB exists
    db_ok = SQLITE_DB.exists()
    health["checks"]["database_exists"] = db_ok
    if not db_ok:
        health["status"] = "degraded"
        health["warnings"].append("Extract DB not found. Run extract first.")
        return health
    
    # Check 2: DB file size
    db_size_mb = SQLITE_DB.stat().st_size / (1024 * 1024)
    health["checks"]["database_size_mb"] = round(db_size_mb, 1)
    
    # Check 3: Data freshness
    try:
        conn = sqlite3.connect(str(SQLITE_DB))
        conn.row_factory = sqlite3.Row
        
        # Check meta for last extract time
        meta_rows = conn.execute("SELECT key, value FROM _extract_meta WHERE key LIKE 'last_extract_%'").fetchall()
        last_extract_times = {}
        for r in meta_rows:
            last_extract_times[r["key"]] = r["value"]
        
        if last_extract_times:
            # Find the most recent extract time
            latest = max(last_extract_times.values())
            try:
                last_dt = datetime.fromisoformat(latest)
                age_hours = (datetime.now(timezone.utc) - last_dt.replace(tzinfo=timezone.utc)).total_seconds() / 3600
                health["checks"]["data_age_hours"] = round(age_hours, 1)
                health["checks"]["last_extract_at"] = latest
                
                if age_hours > 168:  # > 7 days
                    health["warnings"].append(f"Data is {round(age_hours/24, 1)} days old. Last extract: {latest}")
                    if health["status"] == "ok":
                        health["status"] = "degraded"
                elif age_hours > 336:  # > 14 days
                    health["warnings"].append(f"Data is critically old ({round(age_hours/24, 1)} days). Consider running extract.")
                    health["status"] = "error"
            except ValueError:
                pass
        else:
            health["warnings"].append("No extract history found. Run extract first.")
            health["status"] = "degraded"
        
        # Check 4: Row counts per scope
        scopes = conn.execute("""
            SELECT DISTINCT scope_masterfn, scope_companyfn 
            FROM scm_sal_main 
            ORDER BY scope_masterfn
        """).fetchall()
        
        scope_health = []
        for s in scopes:
            mfn = s["scope_masterfn"]
            cfn = s["scope_companyfn"]
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM scm_sal_main WHERE scope_masterfn=? AND scope_companyfn=?",
                (mfn, cfn)
            ).fetchone()
            scope_health.append({
                "masterfn": mfn,
                "companyfn": cfn,
                "row_count": row["cnt"],
                "healthy": row["cnt"] > 0,
            })
        health["checks"]["scopes"] = scope_health
        
        # Check 5: Total tables
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '_extract%' ORDER BY name"
        ).fetchall()
        health["checks"]["table_count"] = len(tables)
        
        conn.close()
    except Exception as e:
        health["checks"]["db_query_error"] = str(e)
        health["status"] = "error"
        health["warnings"].append(f"Database query error: {e}")
    
    return health


# ─── DB-based Company Config ────────────────────────────────────────────────────

def _ensure_config_table(kconn):
    """Create erp_extract_config table if not exists."""
    kconn.execute("""
        CREATE TABLE IF NOT EXISTS erp_extract_config (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            masterfn     TEXT NOT NULL,
            companyfn    TEXT NOT NULL,
            company_name TEXT NOT NULL DEFAULT '',
            api_key      TEXT NOT NULL DEFAULT '',
            enabled      INTEGER NOT NULL DEFAULT 1,
            notes        TEXT NOT NULL DEFAULT '',
            created_at   TEXT NOT NULL,
            updated_at   TEXT NOT NULL,
            UNIQUE(masterfn, companyfn)
        )
    """)
    kconn.commit()

@router.get("/erp-extract/config")
async def list_company_configs(_key: str = Depends(verify_api_key)):
    """List all company configs from database."""
    kconn = get_knowledge_conn()
    _ensure_config_table(kconn)
    rows = kconn.execute("""
        SELECT id, masterfn, companyfn, company_name, api_key, enabled, notes, created_at, updated_at
        FROM erp_extract_config
        ORDER BY company_name, masterfn
    """).fetchall()
    kconn.close()
    return {
        "configs": [
            {
                "id": r["id"],
                "masterfn": r["masterfn"],
                "companyfn": r["companyfn"],
                "company_name": r["company_name"],
                "api_key": r["api_key"],
                "enabled": bool(r["enabled"]),
                "notes": r["notes"],
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            }
            for r in rows
        ]
    }

@router.post("/erp-extract/config")
async def create_company_config(
    body: CompanyConfigCreate,
    request: Request,
    _key: str = Depends(verify_api_key),
):
    """Add a new company config to database."""
    kconn = get_knowledge_conn()
    _ensure_config_table(kconn)
    now = now_iso()
    try:
        kconn.execute("""
            INSERT INTO erp_extract_config (masterfn, companyfn, company_name, api_key, enabled, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (body.masterfn, body.companyfn, body.company_name, body.api_key,
              1 if body.enabled else 0, body.notes, now, now))
        kconn.commit()
        config_id = kconn.execute("SELECT last_insert_rowid()").fetchone()[0]
        log_admin_action(kconn, "admin", "erp_extract_config_create",
                         target_type="erp_extract_config", target_id=f"{body.masterfn}_{body.companyfn}",
                         ip=_get_client_ip(request))
        kconn.close()
        return {"status": "created", "id": config_id}
    except Exception as e:
        kconn.close()
        if "UNIQUE" in str(e):
            raise HTTPException(400, "Config already exists for this masterfn/companyfn")
        raise HTTPException(500, str(e))

@router.put("/erp-extract/config/{config_id}")
async def update_company_config(
    config_id: int,
    body: CompanyConfigUpdate,
    request: Request,
    _key: str = Depends(verify_api_key),
):
    """Update a company config in database."""
    kconn = get_knowledge_conn()
    _ensure_config_table(kconn)
    now = now_iso()
    fields = []
    values = []
    if body.company_name is not None:
        fields.append("company_name=?")
        values.append(body.company_name)
    if body.api_key is not None:
        fields.append("api_key=?")
        values.append(body.api_key)
    if body.enabled is not None:
        fields.append("enabled=?")
        values.append(1 if body.enabled else 0)
    if body.notes is not None:
        fields.append("notes=?")
        values.append(body.notes)
    if not fields:
        kconn.close()
        raise HTTPException(400, "No fields to update")
    fields.append("updated_at=?")
    values.append(now)
    values.append(config_id)
    kconn.execute(f"UPDATE erp_extract_config SET {', '.join(fields)} WHERE id=?", values)
    kconn.commit()
    log_admin_action(kconn, "admin", "erp_extract_config_update",
                     target_type="erp_extract_config", target_id=str(config_id),
                     ip=_get_client_ip(request))
    kconn.close()
    return {"status": "updated"}

@router.delete("/erp-extract/config/{config_id}")
async def delete_company_config(
    config_id: int,
    request: Request,
    _key: str = Depends(verify_api_key),
):
    """Delete a company config from database."""
    kconn = get_knowledge_conn()
    _ensure_config_table(kconn)
    kconn.execute("DELETE FROM erp_extract_config WHERE id=?", (config_id,))
    kconn.commit()
    log_admin_action(kconn, "admin", "erp_extract_config_delete",
                     target_type="erp_extract_config", target_id=str(config_id),
                     ip=_get_client_ip(request))
    kconn.close()
    return {"status": "deleted"}

@router.get("/erp-extract/dashboard")
async def extract_dashboard(_key: str = Depends(verify_api_key)):
    """Unified dashboard endpoint — returns all data in one call."""
    import sqlite3
    from datetime import datetime, timezone, timedelta
    
    result = {
        "summary": {},
        "companies": [],
        "history": [],
        "alerts": [],
        "ai_insights": [],
        "charts": {},
    }
    
    # ── 1. Read configs ──
    configs = []
    try:
        kconn = get_knowledge_conn()
        _ensure_config_table(kconn)
        rows = kconn.execute("""
            SELECT id, masterfn, companyfn, company_name, api_key, enabled, notes, created_at, updated_at
            FROM erp_extract_config ORDER BY company_name, masterfn
        """).fetchall()
        configs = [
            {
                "id": r["id"], "masterfn": r["masterfn"], "companyfn": r["companyfn"],
                "company_name": r["company_name"], "api_key": r["api_key"],
                "enabled": bool(r["enabled"]), "notes": r["notes"],
                "created_at": r["created_at"], "updated_at": r["updated_at"],
            }
            for r in rows
        ]
        kconn.close()
    except Exception:
        pass
    
    # ── 2. Read state ──
    state = _read_state()
    
    # ── 3. Read SQLite stats ──
    sqlite_stats = _get_sqlite_stats()
    db_size_mb = 0
    if SQLITE_DB.exists():
        db_size_mb = round(SQLITE_DB.stat().st_size / (1024 * 1024), 1)
    
    # ── 4. Read history ──
    history_list = []
    try:
        kconn = get_knowledge_conn()
        rows = kconn.execute("""
            SELECT id, admin_user_id, action, target_type, target_id, meta, ip_address, created_at
            FROM admin_action_log
            WHERE target_type='erp_extract'
            ORDER BY id DESC LIMIT 50
        """).fetchall()
        history_list = [
            {
                "id": r["id"], "admin_user_id": r["admin_user_id"],
                "action": r["action"], "target_id": r["target_id"],
                "meta": json.loads(r["meta"]) if r["meta"] else {},
                "created_at": r["created_at"],
            }
            for r in rows
        ]
        kconn.close()
    except Exception:
        pass
    
    # ── 5. Read alerts ──
    alerts_list = []
    try:
        kconn = get_knowledge_conn()
        rows = kconn.execute("""
            SELECT id, admin_user_id, action, target_type, target_id, meta, ip_address, created_at
            FROM admin_action_log
            WHERE target_type='erp_extract_alert'
            ORDER BY id DESC LIMIT 20
        """).fetchall()
        alerts_list = [
            {
                "id": r["id"], "type": r["action"],
                "target_id": r["target_id"],
                "meta": json.loads(r["meta"]) if r["meta"] else {},
                "created_at": r["created_at"],
            }
            for r in rows
        ]
        kconn.close()
    except Exception:
        pass
    
    # ── 6. Build company list ──
    # Merge configs with SQLite stats
    scope_stats = {}
    if sqlite_stats.get("status") == "ok":
        for tbl, cnt in sqlite_stats.get("tables", {}).items():
            pass  # We'll use per-scope stats from extract_stats
    
    # Get per-scope stats
    scope_data_list = []
    try:
        conn = sqlite3.connect(str(SQLITE_DB))
        conn.row_factory = sqlite3.Row
        scopes = conn.execute("""
            SELECT DISTINCT scope_masterfn, scope_companyfn 
            FROM scm_sal_main ORDER BY scope_masterfn
        """).fetchall()
        for s in scopes:
            mfn = s["scope_masterfn"]
            cfn = s["scope_companyfn"]
            tables = {}
            total_rows = 0
            for tbl in ["scm_sal_main", "scm_sal_data", "scm_pur_main", "scm_pur_data",
                        "scm_stk_main", "scm_stk_data", "stk_code_main", "stk_code_data",
                        "adm_cnt_main", "adm_cnt_data", "gen_ledger_detail", "gnl_maint_all",
                        "stkm_main_all", "memo_long_table", "prj_pbill_main", "prj_pbill_body",
                        "gen_ledger_stk"]:
                try:
                    row = conn.execute(
                        f"SELECT COUNT(*) as cnt FROM \"{tbl}\" WHERE scope_masterfn=? AND scope_companyfn=?",
                        (mfn, cfn)
                    ).fetchone()
                    tables[tbl] = row["cnt"]
                    if row["cnt"] > 0:
                        total_rows += row["cnt"]
                except Exception:
                    tables[tbl] = -1
            scope_data_list.append({
                "masterfn": mfn, "companyfn": cfn,
                "tables": tables, "total_rows": total_rows,
            })
        conn.close()
    except Exception:
        pass
    
    # Merge configs + scope data
    company_map = {}
    for cfg in configs:
        key = f"{cfg['masterfn']}_{cfg['companyfn']}"
        company_map[key] = {
            "id": cfg["id"],
            "masterfn": cfg["masterfn"],
            "companyfn": cfg["companyfn"],
            "company_name": cfg["company_name"],
            "enabled": cfg["enabled"],
            "notes": cfg["notes"],
            "total_rows": 0,
            "tables": {},
            "extract_status": "never",
            "ai_status": "waiting",
            "last_extract": None,
            "last_duration": None,
            "last_error": None,
            "health_score": 0,
            "sqlite_size_mb": 0,
        }
    
    for sd in scope_data_list:
        key = f"{sd['masterfn']}_{sd['companyfn']}"
        if key in company_map:
            company_map[key]["total_rows"] = sd["total_rows"]
            company_map[key]["tables"] = sd["tables"]
            company_map[key]["extract_status"] = "completed" if sd["total_rows"] > 0 else "empty"
        else:
            company_map[key] = {
                "id": 0, "masterfn": sd["masterfn"], "companyfn": sd["companyfn"],
                "company_name": f"{sd['masterfn']}/{sd['companyfn']}",
                "enabled": True, "notes": "",
                "total_rows": sd["total_rows"],
                "tables": sd["tables"],
                "extract_status": "completed" if sd["total_rows"] > 0 else "empty",
                "ai_status": "waiting",
                "last_extract": None, "last_duration": None,
                "last_error": None, "health_score": 0,
                "sqlite_size_mb": 0,
            }
    
    # Update status from state
    if state.get("is_running"):
        for key in company_map:
            company_map[key]["extract_status"] = "running"
    
    # Update from history
    for h in history_list:
        target = h.get("target_id", "")
        parts = target.split("/")
        if len(parts) == 2:
            mfn, cfn = parts
            key = f"{mfn}_{cfn}"
            if key in company_map:
                if h["action"] == "erp_extract_completed":
                    company_map[key]["extract_status"] = "completed"
                    company_map[key]["last_extract"] = h["created_at"]
                    meta = h.get("meta", {})
                    if meta.get("duration_sec"):
                        company_map[key]["last_duration"] = meta["duration_sec"]
                elif h["action"] == "erp_extract_failed":
                    company_map[key]["extract_status"] = "failed"
                    company_map[key]["last_error"] = h.get("meta", {}).get("error", "Unknown")
                    company_map[key]["last_extract"] = h["created_at"]
    
    # Calculate health scores
    now = datetime.now(timezone.utc)
    for key, comp in company_map.items():
        score = 50  # base
        if comp["extract_status"] == "completed":
            score += 20
        if comp["total_rows"] > 0:
            score += 10
        if comp["last_extract"]:
            try:
                age = (now - datetime.fromisoformat(comp["last_extract"].replace("Z", "+00:00"))).total_seconds()
                if age < 86400:  # < 1 day
                    score += 15
                elif age < 604800:  # < 7 days
                    score += 10
                else:
                    score -= 10
            except Exception:
                pass
        if comp["extract_status"] == "failed":
            score -= 20
        if not comp["enabled"]:
            score -= 10
        comp["health_score"] = max(0, min(100, score))
        
        # AI status
        if comp["extract_status"] == "completed" and comp["total_rows"] > 0:
            comp["ai_status"] = "ai_ready"
        elif comp["extract_status"] == "completed":
            comp["ai_status"] = "embedding_pending"
        elif comp["extract_status"] == "running":
            comp["ai_status"] = "extracting"
        elif comp["extract_status"] == "failed":
            comp["ai_status"] = "failed"
        else:
            comp["ai_status"] = "waiting"
    
    companies = sorted(company_map.values(), key=lambda x: x["company_name"])
    
    # ── 7. Summary ──
    total = len(companies)
    completed = sum(1 for c in companies if c["extract_status"] == "completed")
    running = sum(1 for c in companies if c["extract_status"] == "running")
    failed = sum(1 for c in companies if c["extract_status"] == "failed")
    never = sum(1 for c in companies if c["extract_status"] == "never")
    empty = sum(1 for c in companies if c["extract_status"] == "empty")
    total_rows = sum(c["total_rows"] for c in companies)
    ai_ready = sum(1 for c in companies if c["ai_status"] == "ai_ready")
    
    # Average duration
    durations = [c["last_duration"] for c in companies if c["last_duration"]]
    avg_duration = round(sum(durations) / len(durations), 1) if durations else 0
    
    # Last extract time
    last_times = [c["last_extract"] for c in companies if c["last_extract"]]
    last_extract = max(last_times) if last_times else None
    
    result["summary"] = {
        "total_companies": total,
        "completed": completed,
        "running": running,
        "failed": failed,
        "never_extracted": never,
        "empty_data": empty,
        "total_rows": total_rows,
        "sqlite_size_mb": db_size_mb,
        "last_extract_time": last_extract,
        "avg_duration_sec": avg_duration,
        "ai_ready": ai_ready,
        "is_running": state.get("is_running", False),
    }
    
    result["companies"] = companies
    result["history"] = history_list[:20]
    result["alerts"] = alerts_list
    
    # ── 8. AI Insights ──
    insights = []
    for c in companies:
        if c["extract_status"] == "failed" and c["last_error"]:
            insights.append({
                "type": "error",
                "severity": "high",
                "company": c["company_name"],
                "message": f"Extract failed: {c['last_error'][:100]}",
                "recommendation": "Check ERP connection and retry.",
            })
        if c["extract_status"] == "completed" and c["last_extract"]:
            try:
                age = (now - datetime.fromisoformat(c["last_extract"].replace("Z", "+00:00"))).total_seconds()
                if age > 604800:  # > 7 days
                    insights.append({
                        "type": "outdated",
                        "severity": "medium",
                        "company": c["company_name"],
                        "message": f"Data is {round(age/86400, 1)} days old.",
                        "recommendation": "Run extract to refresh data.",
                    })
            except Exception:
                pass
        if c["extract_status"] == "completed" and c["ai_status"] != "ai_ready":
            insights.append({
                "type": "ai_pending",
                "severity": "low",
                "company": c["company_name"],
                "message": "Extract completed but AI not ready.",
                "recommendation": "Run embedding/indexing pipeline.",
            })
    result["ai_insights"] = insights[:10]
    
    # ── 9. Charts ──
    # Extracts per day (last 7 days)
    from collections import Counter
    day_counts = Counter()
    for h in history_list:
        try:
            day = h["created_at"][:10]
            day_counts[day] += 1
        except Exception:
            pass
    result["charts"]["extracts_per_day"] = [
        {"date": d, "count": c} for d, c in sorted(day_counts.items())
    ]
    
    # Success vs Failed
    success_count = sum(1 for h in history_list if h["action"] == "erp_extract_completed")
    failed_count = sum(1 for h in history_list if h["action"] == "erp_extract_failed")
    result["charts"]["success_vs_failed"] = {
        "success": success_count,
        "failed": failed_count,
    }
    
    # Top companies by rows
    top = sorted(companies, key=lambda x: x["total_rows"], reverse=True)[:10]
    result["charts"]["top_companies"] = [
        {"name": c["company_name"], "rows": c["total_rows"]} for c in top
    ]
    
    return result


@router.get("/erp-extract/alerts")
async def extract_alerts(
    limit: int = Query(20, ge=1, le=100),
    _key: str = Depends(verify_api_key),
):
    """Get extract system alerts (consecutive failures, etc.)."""
    kconn = get_knowledge_conn()
    rows = kconn.execute("""
        SELECT id, admin_user_id, action, target_type, target_id, meta, ip_address, created_at
        FROM admin_action_log
        WHERE target_type='erp_extract_alert'
        ORDER BY id DESC
        LIMIT ?
    """, (limit,)).fetchall()
    kconn.close()
    return {
        "alerts": [
            {
                "id": r["id"],
                "type": r["action"],
                "target_id": r["target_id"],
                "meta": json.loads(r["meta"]) if r["meta"] else {},
                "created_at": r["created_at"],
            }
            for r in rows
        ]
    }
