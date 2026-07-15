from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor

from ingest.ingest_config import PG_CONFIG
from api.auth import verify_api_key

router = APIRouter()


def _get_pg_conn():
    return psycopg2.connect(
        host=PG_CONFIG.get('host'),
        port=PG_CONFIG.get('port'),
        dbname=PG_CONFIG.get('dbname'),
        user=PG_CONFIG.get('user'),
        password=PG_CONFIG.get('password'),
    )


@router.post("/memo")
async def create_memo(
    request: Request,
    _key: str = Depends(verify_api_key),
) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type.lower():
        raw = await request.json()
        if isinstance(raw, dict):
            data = raw
        else:
            raise HTTPException(status_code=400, detail="JSON body must be an object")
    else:
        form = await request.form()
        data = {k: v for k, v in form.items()}
        if "memo_text" in data and not data.get("content"):
            data["content"] = data["memo_text"]

    if not data.get("companyfn"):
        raise HTTPException(status_code=400, detail="companyfn and content are required")

    content = str(data.get("content", "") or "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="content is required")
    data["content"] = content

    if "created_by" not in data and "userid" in data:
        data["created_by"] = data["userid"]

    # Map incoming fields to actual DB columns for this deployment
    key_map = {
        'content': 'notes_memo',
        'created_by': 'userid_cookie',
        'module': 'cslmodule',
        'segment': 'cslsegm',
    }
    cols = []
    vals = []
    placeholders = []
    for k, v in data.items():
        if v is None:
            continue
        col = key_map.get(k, k)
        cols.append(col)
        vals.append(v)
        placeholders.append('%s')

    sql = f"INSERT INTO memo_long_table ({', '.join(cols)}) VALUES ({', '.join(placeholders)}) RETURNING idcode"
    conn = None
    try:
        conn = _get_pg_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(sql, vals)
        new = cur.fetchone()
        conn.commit()
        cur.close()
        return {"status": "ok", "id": new.get('idcode') if new else None}
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()
