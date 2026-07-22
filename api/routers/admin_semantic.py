import subprocess
import sys
import threading
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from starlette.requests import Request

from api.auth import verify_api_key
from api.database import get_knowledge_conn
from api.semantic.store import (
    get_semantic_file,
    init_semantic_db,
    list_reports,
    list_learned_queries,
    list_semantic_files,
    normalize_module,
    normalize_scope,
    register_semantic_file,
    semantic_stats,
    update_file_status,
)
from api.semantic.validator import SemanticValidationError, load_and_validate
from api.utils import _get_client_ip, log_admin_action


router = APIRouter()

BASE_DIR = Path(__file__).parent.parent.parent
SEMANTIC_ROOT = BASE_DIR / "data" / "semantic"
INGEST_SCRIPT = BASE_DIR / "ingest" / "ingest_semantic_metadata.py"
ALLOWED_EXTENSIONS = {".json", ".xlsx"}


class SemanticRunRequest(BaseModel):
    admin_user_id: str = "admin"
    dry_run: bool = False


class SemanticValidateRequest(BaseModel):
    file_id: int | None = None
    file_path: str = ""
    module: str = ""


@router.get("/semantic/stats")
async def admin_semantic_stats(_key: str = Depends(verify_api_key)):
    init_semantic_db()
    return semantic_stats()


@router.get("/semantic/files")
async def admin_semantic_files(
    module: str = "",
    scope_type: str = "",
    company_code: str = "",
    limit: int = 100,
    offset: int = 0,
    _key: str = Depends(verify_api_key),
):
    return list_semantic_files(module=module, scope_type=scope_type, company_code=company_code, limit=limit, offset=offset)


@router.get("/semantic/files/{file_id}")
async def admin_semantic_file_detail(file_id: int, _key: str = Depends(verify_api_key)):
    row = get_semantic_file(file_id)
    if not row:
        raise HTTPException(status_code=404, detail="Semantic file not found")
    return row


@router.post("/semantic/upload")
async def admin_semantic_upload(
    file: UploadFile = File(...),
    scope_type: str = Form("global"),
    company_code: str = Form(""),
    masterfn: str = Form(""),
    companyfn: str = Form(""),
    module: str = Form(""),
    admin_user_id: str = Form("admin"),
    original_filename: str = Form(""),
    request: Request = None,
    _key: str = Depends(verify_api_key),
):
    init_semantic_db()
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")
    upload_name = Path(original_filename or file.filename or "").name
    suffix = Path(upload_name).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only .json and .xlsx metadata files are supported")

    try:
        module_norm = normalize_module(module)
        scope = normalize_scope(scope_type, company_code, masterfn, companyfn)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    safe_name = Path(upload_name).name
    if scope["scope_type"] == "company":
        target = SEMANTIC_ROOT / "clients" / scope["company_code"] / module_norm / safe_name
    else:
        target = SEMANTIC_ROOT / "_global" / module_norm / safe_name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)

    file_id = register_semantic_file(str(target), scope, module_norm)
    conn = get_knowledge_conn()
    log_admin_action(conn, admin_user_id, "semantic_metadata_uploaded",
                     target_type="semantic_file", target_id=str(file_id),
                     meta={"file_path": str(target.resolve()), "scope": scope, "module": module_norm},
                     ip=_get_client_ip(request))
    conn.close()
    return {
        "id": file_id,
        "file_path": str(target.resolve()),
        "filename": safe_name,
        "status": "pending",
        "scope_type": scope["scope_type"],
        "company_code": scope["company_code"],
        "module": module_norm,
    }


@router.post("/semantic/files/{file_id}/run-now")
async def admin_semantic_run_now(
    file_id: int,
    body: SemanticRunRequest,
    request: Request,
    _key: str = Depends(verify_api_key),
):
    row = get_semantic_file(file_id)
    if not row:
        raise HTTPException(status_code=404, detail="Semantic file not found")
    if not Path(row["file_path"]).exists():
        raise HTTPException(status_code=400, detail="File not found on disk")

    update_file_status(file_id, "processing")
    conn = get_knowledge_conn()
    log_admin_action(conn, body.admin_user_id, "semantic_ingest_run_now",
                     target_type="semantic_file", target_id=str(file_id),
                     meta={"file_path": row["file_path"], "dry_run": body.dry_run},
                     ip=_get_client_ip(request))
    conn.close()
    thread = threading.Thread(target=_run_ingest_background, args=(file_id, body.admin_user_id, body.dry_run), daemon=True)
    thread.start()
    return {"status": "started", "file_id": file_id}


@router.delete("/semantic/files/{file_id}")
async def admin_semantic_delete(
    file_id: int,
    request: Request,
    admin_user_id: str = "admin",
    _key: str = Depends(verify_api_key),
):
    row = get_semantic_file(file_id)
    if not row:
        raise HTTPException(status_code=404, detail="Semantic file not found")
    try:
        Path(row["file_path"]).unlink(missing_ok=True)
    except Exception:
        pass
    conn = get_knowledge_conn()
    for table in (
        "semantic_reports", "semantic_output_columns", "semantic_filters",
        "semantic_relationships", "semantic_synonyms", "semantic_sample_questions",
        "semantic_business_rules", "semantic_field_mappings", "semantic_mandatory_fields",
        "semantic_child_tabs", "semantic_sales_cycle", "semantic_sql_templates",
        "semantic_permissions", "semantic_engine_components", "semantic_ingest_runs",
    ):
        conn.execute(f"DELETE FROM {table} WHERE file_id=?", (file_id,))
    conn.execute("DELETE FROM semantic_files WHERE id=?", (file_id,))
    log_admin_action(conn, admin_user_id, "semantic_metadata_deleted",
                     target_type="semantic_file", target_id=str(file_id),
                     meta={"file_path": row["file_path"]},
                     ip=_get_client_ip(request))
    conn.commit()
    conn.close()
    return {"status": "deleted"}


@router.get("/semantic/reports")
async def admin_semantic_reports(
    module: str = "",
    scope_type: str = "",
    company_code: str = "",
    _key: str = Depends(verify_api_key),
):
    return {"items": list_reports(module=module, scope_type=scope_type, company_code=company_code)}


@router.get("/semantic/learned")
async def admin_semantic_learned(
    module: str = "",
    verified: bool | None = None,
    _key: str = Depends(verify_api_key),
):
    return {"items": list_learned_queries(module=module, verified=verified)}


@router.post("/semantic/validate")
async def admin_semantic_validate(
    body: SemanticValidateRequest,
    _key: str = Depends(verify_api_key),
):
    if body.file_id:
        row = get_semantic_file(body.file_id)
        if not row:
            raise HTTPException(status_code=404, detail="Semantic file not found")
        file_path = row["file_path"]
        module = row["module"]
    else:
        file_path = body.file_path
        module = body.module
    try:
        payload = load_and_validate(file_path, expected_module=normalize_module(module) if module else None)
    except (SemanticValidationError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "sections": {key: len(value) for key, value in payload.items()}}


def _run_ingest_background(file_id: int, admin_user_id: str, dry_run: bool = False) -> None:
    try:
        cmd = [sys.executable, str(INGEST_SCRIPT), "--file-id", str(file_id)]
        if dry_run:
            cmd.append("--dry-run")
        result = subprocess.run(cmd, cwd=str(BASE_DIR), capture_output=True, text=True, timeout=1800)
        if result.returncode != 0:
            update_file_status(file_id, "failed", (result.stderr or result.stdout or "Unknown ingest error")[-2000:])
        try:
            conn = get_knowledge_conn()
            action = "semantic_ingest_completed" if result.returncode == 0 else "semantic_ingest_failed"
            log_admin_action(conn, admin_user_id, action,
                             target_type="semantic_file", target_id=str(file_id),
                             meta={"stdout": result.stdout[-1000:], "stderr": result.stderr[-1000:]})
            conn.close()
        except Exception:
            pass
    except subprocess.TimeoutExpired:
        update_file_status(file_id, "failed", "Semantic ingest timed out")
    except Exception as exc:
        update_file_status(file_id, "failed", str(exc))
