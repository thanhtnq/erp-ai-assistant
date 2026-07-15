"""
ERP AI Assistant — Settings Router
Per-user/company settings for Fraud Detection and Demand Planning defaults.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException

from api.auth import verify_api_key
from api.database import get_chat_conn

router = APIRouter()


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def init_settings_table(conn):
    """Create ai_settings table if not exists."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ai_settings (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     TEXT NOT NULL DEFAULT '',
            masterfn    TEXT NOT NULL,
            companyfn   TEXT NOT NULL,
            module      TEXT NOT NULL,  -- 'fraud' or 'demand'
            setting_key TEXT NOT NULL,
            setting_val TEXT NOT NULL,
            updated_at  TEXT NOT NULL,
            UNIQUE(user_id, masterfn, companyfn, module, setting_key)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_ai_settings_scope
        ON ai_settings(user_id, masterfn, companyfn, module)
    """)
    conn.commit()


# ─── Fraud Detection Default Settings ──────────────────────────────────────

FRAUD_DEFAULTS = {
    "scan_type": "all",
    "severity": "all",
    "max_findings": "8",
}

DEMAND_DEFAULTS = {
    "horizon_days": "90",
    "sku_filter": "all",
    "location_filter": "all",
    "service_factor": "0.95",
    "result_limit": "100",
    "auto_run": "n",
}


@router.get("/settings/{module}")
async def get_settings(
    module: str,
    masterfn: str,
    companyfn: str,
    user_id: str = "",
    _key: str = Depends(verify_api_key),
):
    """Get settings for a module (fraud or demand)."""
    if module not in ("fraud", "demand"):
        raise HTTPException(400, "module must be 'fraud' or 'demand'")

    conn = get_chat_conn()
    init_settings_table(conn)

    defaults = FRAUD_DEFAULTS if module == "fraud" else DEMAND_DEFAULTS

    # Get user-specific settings
    rows = conn.execute("""
        SELECT setting_key, setting_val FROM ai_settings
        WHERE user_id=? AND masterfn=? AND companyfn=? AND module=?
    """, (user_id, masterfn, companyfn, module)).fetchall()

    # Get company-wide settings (user_id='')
    company_rows = conn.execute("""
        SELECT setting_key, setting_val FROM ai_settings
        WHERE user_id='' AND masterfn=? AND companyfn=? AND module=?
    """, (masterfn, companyfn, module)).fetchall()

    conn.close()

    # Merge: user settings override company defaults, which override global defaults
    settings = dict(defaults)
    for r in company_rows:
        settings[r["setting_key"]] = r["setting_val"]
    for r in rows:
        settings[r["setting_key"]] = r["setting_val"]

    return {
        "module": module,
        "masterfn": masterfn,
        "companyfn": companyfn,
        "user_id": user_id,
        "settings": settings,
    }


@router.put("/settings/{module}")
async def update_settings(
    module: str,
    masterfn: str,
    companyfn: str,
    setting_key: str,
    setting_val: str,
    user_id: str = "",
    _key: str = Depends(verify_api_key),
):
    """Update a single setting for a module."""
    if module not in ("fraud", "demand"):
        raise HTTPException(400, "module must be 'fraud' or 'demand'")

    conn = get_chat_conn()
    init_settings_table(conn)

    now = now_iso()
    conn.execute("""
        INSERT INTO ai_settings (user_id, masterfn, companyfn, module, setting_key, setting_val, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, masterfn, companyfn, module, setting_key)
        DO UPDATE SET setting_val=excluded.setting_val, updated_at=excluded.updated_at
    """, (user_id, masterfn, companyfn, module, setting_key, setting_val, now))
    conn.commit()
    conn.close()

    return {
        "status": "updated",
        "module": module,
        "setting_key": setting_key,
        "setting_val": setting_val,
    }


@router.delete("/settings/{module}")
async def reset_setting(
    module: str,
    masterfn: str,
    companyfn: str,
    setting_key: str,
    user_id: str = "",
    _key: str = Depends(verify_api_key),
):
    """Reset a setting to default (delete user override)."""
    if module not in ("fraud", "demand"):
        raise HTTPException(400, "module must be 'fraud' or 'demand'")

    conn = get_chat_conn()
    init_settings_table(conn)

    conn.execute("""
        DELETE FROM ai_settings
        WHERE user_id=? AND masterfn=? AND companyfn=? AND module=? AND setting_key=?
    """, (user_id, masterfn, companyfn, module, setting_key))
    conn.commit()
    conn.close()

    return {
        "status": "reset",
        "module": module,
        "setting_key": setting_key,
    }
