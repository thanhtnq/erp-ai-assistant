"""
ERP AI Assistant — Admin Knowledge Router
Endpoints: /admin/knowledge/stats, /admin/knowledge/entries, /admin/knowledge/entries/{id}, /admin/knowledge/entries/{id}/versions
"""
import json
import os
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from api.auth import verify_api_key
from api.models import AdminFlagAction
from api.database import get_knowledge_conn
from api.utils import now_iso, log_admin_action, _get_client_ip

router = APIRouter()


@router.get("/knowledge/stats")
async def admin_knowledge_stats(_key: str = Depends(verify_api_key)):
    from api.config import KNOWLEDGE_DB
    if not os.path.exists(KNOWLEDGE_DB):
        return {"domains": 0, "features": 0, "entries": 0, "versions": 0,
                "flagged": 0, "by_type": {}, "by_source": {}}
    kconn = get_knowledge_conn()
    domains  = kconn.execute("SELECT COUNT(*) FROM domains").fetchone()[0]
    features = kconn.execute("SELECT COUNT(*) FROM features").fetchone()[0]
    entries  = kconn.execute("SELECT COUNT(*) FROM entries WHERE is_active=1").fetchone()[0]
    versions = kconn.execute("SELECT COUNT(*) FROM entry_versions WHERE is_current=1").fetchone()[0]
    flagged  = kconn.execute(
        "SELECT COUNT(*) FROM entry_versions WHERE is_flagged=1 AND is_current=1"
    ).fetchone()[0]
    by_type = {r[0]: r[1] for r in kconn.execute(
        "SELECT type, COUNT(*) FROM entries WHERE is_active=1 GROUP BY type"
    ).fetchall()}
    by_source = {r[0]: r[1] for r in kconn.execute(
        "SELECT source_type, COUNT(*) FROM entry_versions WHERE is_current=1 GROUP BY source_type"
    ).fetchall()}
    kconn.close()
    return {"domains": domains, "features": features, "entries": entries,
            "versions": versions, "flagged": flagged,
            "by_type": by_type, "by_source": by_source}


@router.get("/knowledge/entries")
async def admin_knowledge_entries(
    domain:     str = None,
    feature_id: int = None,
    entry_type: str = None,
    company:    str = None,
    flagged:    int = None,
    search:     str = None,
    limit:      int = 20,
    offset:     int = 0,
    _key: str = Depends(verify_api_key),
):
    from api.config import KNOWLEDGE_DB
    if not os.path.exists(KNOWLEDGE_DB):
        return {"total": 0, "items": [], "domains": []}
    kconn = get_knowledge_conn()
    where, params = ["e.is_active = 1"], []
    if domain:
        where.append("d.name = ?");             params.append(domain)
    if feature_id:
        where.append("e.feature_id = ?");       params.append(feature_id)
    if entry_type:
        where.append("e.type = ?");             params.append(entry_type)
    if flagged == 1:
        where.append("ev.is_flagged = 1")
    if company == "global":
        where.append("ev.company_id IS NULL")
    elif company:
        where.append("co.code = ?");            params.append(company)
    if search:
        where.append("(e.name LIKE ? OR e.summary LIKE ? OR f.name LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
    w = "WHERE " + " AND ".join(where)
    total = kconn.execute(f"""
        SELECT COUNT(DISTINCT e.id)
        FROM entries e
        JOIN features f  ON e.feature_id  = f.id
        JOIN domains d   ON f.domain_id   = d.id
        LEFT JOIN entry_versions ev ON ev.entry_id = e.id AND ev.is_current = 1
        LEFT JOIN companies co      ON ev.company_id = co.id
        {w}
    """, params).fetchone()[0]
    rows = kconn.execute(f"""
        SELECT e.id, e.name, e.type, e.menu_path, e.summary,
               f.id AS feature_id, f.name AS feature,
               d.name AS domain,
               COUNT(DISTINCT ev.id)                              AS version_count,
               COALESCE(SUM(ev.thumbs_up),   0)                  AS thumbs_up,
               COALESCE(SUM(ev.thumbs_down), 0)                  AS thumbs_down,
               MAX(ev.score)                                      AS score,
               SUM(CASE WHEN ev.is_flagged=1 THEN 1 ELSE 0 END)  AS flagged_count,
               GROUP_CONCAT(DISTINCT ev.source_type)              AS source_types,
               GROUP_CONCAT(DISTINCT co.code)                     AS company_codes
        FROM entries e
        JOIN features f  ON e.feature_id  = f.id
        JOIN domains d   ON f.domain_id   = d.id
        LEFT JOIN entry_versions ev ON ev.entry_id = e.id AND ev.is_current = 1
        LEFT JOIN companies co      ON ev.company_id = co.id
        {w}
        GROUP BY e.id, e.name, e.type, e.menu_path, e.summary,
                 f.id, f.name, d.name
        ORDER BY d.name, f.sort_order, e.sort_order
        LIMIT ? OFFSET ?
    """, params + [limit, offset]).fetchall()
    domains_list = [r[0] for r in kconn.execute(
        "SELECT name FROM domains ORDER BY name"
    ).fetchall()]
    kconn.close()
    items = []
    for r in rows:
        items.append({
            "id":            r[0], "name": r[1], "type": r[2],
            "menu_path":     r[3], "summary": r[4],
            "feature_id":    r[5], "feature": r[6], "domain": r[7],
            "version_count": r[8] or 0,
            "thumbs_up":     r[9], "thumbs_down": r[10],
            "score":         round(r[11] * 100, 1) if r[11] else None,
            "flagged_count": r[12] or 0,
            "source_types":  r[13].split(",") if r[13] else [],
            "company_codes": r[14].split(",") if r[14] else [],
        })
    return {"total": total, "items": items, "domains": domains_list}


@router.get("/knowledge/entries/{entry_id}")
async def admin_knowledge_entry_detail(
    entry_id: int,
    _key: str = Depends(verify_api_key),
):
    from api.config import KNOWLEDGE_DB
    if not os.path.exists(KNOWLEDGE_DB):
        raise HTTPException(status_code=404, detail="Knowledge DB not found")
    kconn = get_knowledge_conn()
    row = kconn.execute("""
        SELECT e.id, e.name, e.type, e.menu_path, e.summary,
               f.name AS feature, d.name AS domain, e.created_at
        FROM entries e
        JOIN features f ON e.feature_id = f.id
        JOIN domains d  ON f.domain_id  = d.id
        WHERE e.id = ?
    """, (entry_id,)).fetchone()
    if not row:
        kconn.close()
        raise HTTPException(status_code=404, detail="Entry not found")
    versions = kconn.execute("""
        SELECT ev.id, ev.version, ev.source_type, ev.source_ref,
               ev.steps, ev.notes,
               ev.thumbs_up, ev.thumbs_down, ev.score,
               ev.is_flagged, ev.flag_reason, ev.flag_status,
               ev.flag_resolution_note,
               COALESCE(c.code, 'global') AS company_code,
               ev.created_at
        FROM entry_versions ev
        LEFT JOIN companies c ON ev.company_id = c.id
        WHERE ev.entry_id = ? AND ev.is_current = 1
        ORDER BY ev.company_id NULLS FIRST, ev.version DESC
    """, (entry_id,)).fetchall()
    kconn.close()
    vers_list = []
    for v in versions:
        steps, notes = [], []
        try:
            if v[4]: steps = json.loads(v[4])
        except Exception: pass
        try:
            if v[5]: notes = json.loads(v[5])
        except Exception: pass
        vers_list.append({
            "id": v[0], "version": v[1], "source_type": v[2], "source_ref": v[3],
            "steps": steps, "notes": notes,
            "thumbs_up": v[6], "thumbs_down": v[7],
            "score": round(v[8] * 100, 1) if v[8] else None,
            "is_flagged": bool(v[9]), "flag_reason": v[10],
            "flag_status": v[11], "flag_resolution_note": v[12],
            "company_code": v[13], "created_at": v[14],
        })
    return {
        "id": row[0], "name": row[1], "type": row[2],
        "menu_path": row[3], "summary": row[4],
        "feature": row[5], "domain": row[6], "created_at": row[7],
        "versions": vers_list,
    }


@router.delete("/knowledge/entries/{entry_id}")
async def admin_delete_knowledge_entry(
    entry_id: int,
    body: AdminFlagAction,
    request: Request,
    _key: str = Depends(verify_api_key),
):
    from api.config import KNOWLEDGE_DB
    if not os.path.exists(KNOWLEDGE_DB):
        raise HTTPException(status_code=404, detail="Knowledge DB not found")
    kconn = get_knowledge_conn()
    row = kconn.execute(
        "SELECT id, name FROM entries WHERE id = ? AND is_active = 1", (entry_id,)
    ).fetchone()
    if not row:
        kconn.close()
        raise HTTPException(status_code=404, detail="Entry not found or already deleted")
    entry_name = row["name"]
    kconn.execute("UPDATE entries SET is_active = 0 WHERE id = ?", (entry_id,))
    log_admin_action(kconn, body.admin_user_id, "delete_entry",
                     target_type="entry", target_id=str(entry_id),
                     note=entry_name, ip=_get_client_ip(request))
    kconn.close()
    return {"deleted": True, "entry_id": entry_id, "name": entry_name}


@router.delete("/knowledge/entries")
async def admin_delete_all_knowledge_entries(
    body: AdminFlagAction,
    request: Request,
    _key: str = Depends(verify_api_key),
):
    from api.config import KNOWLEDGE_DB
    if not os.path.exists(KNOWLEDGE_DB):
        return {"deleted": True, "count": 0}
    kconn = get_knowledge_conn()
    count = kconn.execute(
        "SELECT COUNT(*) FROM entries WHERE is_active = 1"
    ).fetchone()[0]
    kconn.execute("UPDATE entries SET is_active = 0 WHERE is_active = 1")
    log_admin_action(kconn, body.admin_user_id, "delete_all_entries",
                     target_type="entry",
                     note=f"Deactivated {count} entries",
                     ip=_get_client_ip(request))
    kconn.close()
    return {"deleted": True, "count": count}
