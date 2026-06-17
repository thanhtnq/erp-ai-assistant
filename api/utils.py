"""
ERP AI Assistant — Utility Functions
Shared helpers used across modules.
"""
import json
import re
from datetime import datetime, timezone
from typing import Optional


def now_iso() -> str:
    """Return current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def safe_json_loads(text: str, default=None):
    """Safely parse JSON string, returning default on failure."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default or {}


def strip_markdown_code(text: str) -> str:
    """Remove markdown code fences from a string."""
    return re.sub(r"```(?:json)?\s*", "", text).strip()


def truncate_text(text: str, max_chars: int = 200) -> str:
    """Truncate text to max_chars, appending '...' if needed."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + "..."


def parse_int_or_none(val) -> Optional[int]:
    """Try to parse an integer, return None on failure."""
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _get_client_ip(request) -> str:
    """Extract client IP from request, respecting proxies."""
    if request is None:
        return ""
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP", "")
    if real_ip:
        return real_ip.strip()
    try:
        return request.client.host if request.client else ""
    except Exception:
        return ""


def log_admin_action(conn, admin_user_id: str, action: str,
                     target_type: str = "", target_id: str = "",
                     note: str = "", meta: dict = None,
                     ip: str = "") -> None:
    """Insert a row into admin_action_log."""
    import json as _json
    now = now_iso()
    meta_json = _json.dumps(meta or {})
    conn.execute("""
        INSERT INTO admin_action_log
            (admin_user_id, action, target_type, target_id, note, meta, ip_address, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (admin_user_id, action, target_type, target_id, note, meta_json, ip, now))
    conn.commit()


