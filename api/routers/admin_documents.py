"""
ERP AI Assistant — Admin Documents Router
Endpoints: /admin/documents, /admin/documents/{id}, /admin/documents/{id}/run-now
"""
import os
import sys
import threading
import subprocess
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from starlette.requests import Request
from api.auth import verify_api_key
from api.models import AdminFlagAction
from api.database import get_knowledge_conn
from api.utils import now_iso, log_admin_action, _get_client_ip


router = APIRouter()

_DOCS_ROOT = Path(__file__).parent.parent.parent / "data" / "docs"
_INGEST_DIR = Path(__file__).parent.parent.parent / "ingest"
_VALID_DOMAINS = {"sales", "purchase", "inventory", "finance", "hr", "project", "crm", "cm", "general"}


def _get_or_create_domain_id(conn, domain: str) -> int:
    row = conn.execute(
        "SELECT id FROM domains WHERE lower(name) = lower(?)", (domain,)
    ).fetchone()
    if row:
        return row["id"]
    display_name = domain.upper() if domain in {"hr", "crm", "cm"} else domain.title()
    return conn.execute(
        "INSERT INTO domains (name) VALUES (?)", (display_name,)
    ).lastrowid


def backfill_document_domains() -> int:
    """Repair registry rows created before uploads persisted domain_id."""
    conn = get_knowledge_conn()
    repaired = 0
    rows = conn.execute(
        "SELECT id, file_path FROM document_registry WHERE domain_id IS NULL"
    ).fetchall()
    for row in rows:
        parts = Path(row["file_path"]).parts
        lower_parts = [part.lower() for part in parts]
        domain = ""
        if "_global" in lower_parts:
            index = lower_parts.index("_global")
            if index + 1 < len(parts):
                domain = lower_parts[index + 1]
        elif "clients" in lower_parts:
            index = lower_parts.index("clients")
            if index + 2 < len(parts):
                domain = lower_parts[index + 2]
        if domain not in _VALID_DOMAINS:
            domain = _auto_detect_domain(Path(row["file_path"]).name)
        domain_id = _get_or_create_domain_id(conn, domain)
        conn.execute(
            "UPDATE document_registry SET domain_id=? WHERE id=?",
            (domain_id, row["id"]),
        )
        repaired += 1
    conn.commit()
    conn.close()
    return repaired


@router.get("/documents/stats")
async def admin_documents_stats(
    _key: str = Depends(verify_api_key),
):
    """Get document statistics (counts by status and domain)."""
    kconn = get_knowledge_conn()
    by_status = {}
    for row in kconn.execute("SELECT status, COUNT(*) as cnt FROM document_registry GROUP BY status").fetchall():
        by_status[row["status"]] = row["cnt"]
    by_domain = {}
    for row in kconn.execute("""
        SELECT COALESCE(d.name, 'Unknown') as domain, COUNT(*) as cnt
        FROM document_registry r
        LEFT JOIN domains d ON r.domain_id = d.id
        GROUP BY domain
    """).fetchall():
        by_domain[row["domain"]] = row["cnt"]
    total = kconn.execute("SELECT COUNT(*) FROM document_registry").fetchone()[0]
    kconn.close()
    return {"total": total, "by_status": by_status, "by_domain": by_domain}


@router.get("/documents")
async def admin_documents_list(
    status: str = None,
    domain: str = None,
    limit: int = 50,
    offset: int = 0,
    _key: str = Depends(verify_api_key),
):
    """List uploaded documents with optional filters."""
    kconn = get_knowledge_conn()
    where, params = [], []
    if status:
        where.append("r.status = ?"); params.append(status)
    if domain:
        where.append("d.name = ?"); params.append(domain)
    w = "WHERE " + " AND ".join(where) if where else ""
    total = kconn.execute(f"""
        SELECT COUNT(*) FROM document_registry r
        LEFT JOIN domains d ON r.domain_id = d.id
        {w}
    """, params).fetchone()[0]
    rows = kconn.execute(f"""
        SELECT r.id, r.file_path, r.status, r.error_message, r.entries_parsed,
               COALESCE(d.name, '') as domain_name,
               COALESCE(c.code, '') as company_code,
               r.created_at, r.ingested_at
        FROM document_registry r
        LEFT JOIN domains d ON r.domain_id = d.id
        LEFT JOIN companies c ON r.company_id = c.id
        {w}
        ORDER BY r.created_at DESC LIMIT ? OFFSET ?
    """, params + [limit, offset]).fetchall()
    kconn.close()
    return {"total": total, "items": [dict(r) for r in rows]}


@router.post("/documents/upload")
async def admin_document_upload(
    file: UploadFile = File(...),
    company_code: str = Form(""),
    domain: str = Form(""),
    admin_user_id: str = Form(""),
    request: Request = None,
    _key: str = Depends(verify_api_key),
):
    """Upload a document for ingestion."""
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    auto_detected = False
    if not domain:
        domain = _auto_detect_domain(file.filename)
        auto_detected = True
    else:
        domain = domain.strip().lower()
        if domain not in _VALID_DOMAINS:
            raise HTTPException(status_code=400, detail=f"Invalid domain. Choose from: {', '.join(_VALID_DOMAINS)}")

    company_code = company_code.strip().upper()
    safe_name = Path(file.filename).name
    if company_code:
        target = _DOCS_ROOT / "clients" / company_code / domain / safe_name
    else:
        target = _DOCS_ROOT / "_global" / domain / safe_name

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)

    file_path_str = str(target.resolve())
    kconn = get_knowledge_conn()
    domain_id = _get_or_create_domain_id(kconn, domain)
    company_id = None
    if company_code:
        company = kconn.execute(
            "SELECT id FROM companies WHERE upper(code) = upper(?)", (company_code,)
        ).fetchone()
        company_id = company["id"] if company else None
    existing = kconn.execute(
        "SELECT id FROM document_registry WHERE file_path = ?", (file_path_str,)
    ).fetchone()
    if existing:
        kconn.execute(
            """UPDATE document_registry
               SET company_id=?, domain_id=?, status='pending', error_message=NULL
               WHERE id=?""",
            (company_id, domain_id, existing["id"])
        )
        kconn.commit()
        doc_id = existing["id"]
    else:
        cur = kconn.execute(
            """INSERT INTO document_registry
               (file_path, company_id, domain_id, status)
               VALUES (?, ?, ?, 'pending')""",
            (file_path_str, company_id, domain_id)
        )
        kconn.commit()
        doc_id = cur.lastrowid

    log_admin_action(kconn, admin_user_id, "document_uploaded",
                     target_type="document", target_id=str(doc_id),
                     meta={"file_path": file_path_str},
                     ip=_get_client_ip(request))
    kconn.close()
    return {"id": doc_id, "file_path": file_path_str, "status": "pending",
            "domain": domain, "auto_detected": auto_detected}


@router.delete("/documents/{doc_id}")
async def admin_document_delete(
    doc_id: int,
    request: Request,
    admin_user_id: str = "",
    _key: str = Depends(verify_api_key),
):
    kconn = get_knowledge_conn()
    doc = kconn.execute(
        "SELECT id, file_path FROM document_registry WHERE id = ?", (doc_id,)
    ).fetchone()
    if not doc:
        kconn.close()
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = doc["file_path"]
    try:
        Path(file_path).unlink(missing_ok=True)
    except Exception:
        pass

    kconn.execute("DELETE FROM document_registry WHERE id = ?", (doc_id,))
    kconn.commit()
    log_admin_action(kconn, admin_user_id or "admin", "document_deleted",
                     target_type="document", target_id=str(doc_id),
                     meta={"file_path": file_path},
                     ip=_get_client_ip(request))
    kconn.close()
    return {"status": "deleted"}


@router.post("/documents/{doc_id}/reingest")
@router.post("/documents/{doc_id}/run-now")
async def admin_document_run_now(
    doc_id: int,
    body: AdminFlagAction,
    request: Request,
    _key: str = Depends(verify_api_key),
):
    kconn = get_knowledge_conn()
    doc = kconn.execute(
        "SELECT id, file_path FROM document_registry WHERE id = ?", (doc_id,)
    ).fetchone()
    if not doc:
        kconn.close()
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = doc["file_path"]
    if not Path(file_path).exists():
        kconn.close()
        raise HTTPException(status_code=400, detail="File not found on disk")

    kconn.execute(
        "UPDATE document_registry SET status='processing', error_message=NULL WHERE id=?",
        (doc_id,)
    )
    kconn.commit()
    log_admin_action(kconn, body.admin_user_id, "ingest_run_now",
                     target_type="document", target_id=str(doc_id),
                     meta={"file_path": file_path},
                     ip=_get_client_ip(request))
    kconn.close()

    t = threading.Thread(target=_run_ingest_file, args=(file_path, doc_id), daemon=True)
    t.start()
    return {"status": "started"}


def _auto_detect_domain(filename: str) -> str:
    f = filename.lower()
    if any(kw in f for kw in ["sales", "so", "invoice", "quotation", "customer"]):
        return "sales"
    if any(kw in f for kw in ["purchase", "po", "procurement", "vendor", "supplier"]):
        return "purchase"
    if any(kw in f for kw in ["inventory", "stock", "warehouse", "item"]):
        return "inventory"
    if any(kw in f for kw in ["finance", "account", "gl", "payment", "receipt"]):
        return "finance"
    if any(kw in f for kw in ["hr", "employee", "payroll", "leave"]):
        return "hr"
    if any(kw in f for kw in ["project", "asset", "fleet"]):
        return "project"
    if any(kw in f for kw in ["crm", "lead", "opportunity"]):
        return "crm"
    return "general"


def _run_ingest_file(file_path: str, doc_id: int):
    """Background thread: run ingest for a single file, then update DB status."""
    try:
        abs_path = str(Path(file_path).resolve())
        try:
            _kc = get_knowledge_conn()
            _kc.execute("UPDATE document_registry SET file_path=? WHERE id=? AND file_path!=?",
                        (abs_path, doc_id, abs_path))
            _kc.commit()
            _kc.close()
        except Exception:
            pass
        result = subprocess.run(
            [sys.executable, "ingest_knowledge.py", "--file", abs_path, "--force"],
            cwd=str(_INGEST_DIR),
            capture_output=True,
            text=True,
            timeout=3600,
        )
        status = "done" if result.returncode == 0 else "failed"
        error_msg = None if status == "done" else (result.stderr or result.stdout or "Unknown error")[-2000:]
    except subprocess.TimeoutExpired:
        status, error_msg = "failed", "Ingest timed out"
    except Exception as e:
        status, error_msg = "failed", str(e)

    try:
        kconn = get_knowledge_conn()
        kconn.execute(
            "UPDATE document_registry SET status=?, error_message=? WHERE id=?",
            (status, error_msg, doc_id)
        )
        kconn.commit()
        kconn.close()
    except Exception:
        pass
