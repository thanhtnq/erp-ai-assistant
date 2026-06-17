"""
ERP AI Assistant — Admin SCM Training Router
Endpoints: /admin/scm/train, /admin/scm/status, /admin/scm/models, /admin/scm/predict
"""
import json
import os
import sys
import threading
import subprocess
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from starlette.requests import Request
from api.auth import verify_api_key
from api.models import AdminFlagAction, AdminSCMPredict
from api.database import get_knowledge_conn
from api.utils import now_iso, log_admin_action, _get_client_ip


router = APIRouter()

SCM_DIR = Path(__file__).parent.parent.parent / "scm_training"
SCM_STATE_FILE = Path(__file__).parent.parent.parent / "data" / "scm_state.json"

_scm_lock = threading.Lock()


def _read_scm_state() -> dict:
    defaults = {
        "is_training": False,
        "last_train_at": None,
        "last_train_status": None,
        "last_train_duration_sec": None,
        "models": [],
    }
    if SCM_STATE_FILE.exists():
        try:
            saved = json.loads(SCM_STATE_FILE.read_text(encoding="utf-8"))
            defaults.update(saved)
        except Exception:
            pass
    return defaults


def _write_scm_state(state: dict):
    SCM_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    SCM_STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _run_scm_training(admin_user_id: str):
    with _scm_lock:
        state = _read_scm_state()
        if state.get("is_training"):
            return
        state["is_training"] = True
        _write_scm_state(state)

    from datetime import datetime
    start = datetime.now()
    status = "failed"
    duration = None
    try:
        result = subprocess.run(
            [sys.executable, "main.py"],
            cwd=str(SCM_DIR),
            capture_output=True,
            text=True,
            timeout=7200,
        )
        status = "success" if result.returncode == 0 else "failed"
    except subprocess.TimeoutExpired:
        status = "failed"
    except Exception:
        status = "failed"
    finally:
        duration = int((datetime.now() - start).total_seconds())
        with _scm_lock:
            state = _read_scm_state()
            state["is_training"]            = False
            state["last_train_at"]          = start.isoformat()
            state["last_train_status"]      = status
            state["last_train_duration_sec"] = duration
            _write_scm_state(state)

        try:
            kconn = get_knowledge_conn()
            action = "scm_training_completed" if status == "success" else "scm_training_failed"
            log_admin_action(kconn, admin_user_id, action,
                             target_type="scm", target_id="training",
                             meta={"duration_sec": duration})
            kconn.close()
        except Exception:
            pass


@router.post("/scm/train")
async def admin_scm_train(
    body: AdminFlagAction,
    request: Request,
    _key: str = Depends(verify_api_key),
):
    """Trigger SCM model training."""
    with _scm_lock:
        state = _read_scm_state()
        if state.get("is_training"):
            raise HTTPException(status_code=409, detail="Training is already running")

    t = threading.Thread(
        target=_run_scm_training,
        args=(body.admin_user_id,),
        daemon=True,
        name="scm-training",
    )
    t.start()

    kconn = get_knowledge_conn()
    log_admin_action(kconn, body.admin_user_id, "scm_training_started",
                     target_type="scm", target_id="training",
                     ip=_get_client_ip(request))
    kconn.close()
    return {"status": "started"}


@router.get("/scm/status")
async def admin_scm_status(_key: str = Depends(verify_api_key)):
    with _scm_lock:
        state = _read_scm_state()
    return state


@router.get("/scm/models")
async def admin_scm_models(_key: str = Depends(verify_api_key)):
    """List available trained models."""
    models_dir = SCM_DIR / "trained_models"
    if not models_dir.exists():
        return {"models": []}
    models = []
    for p in sorted(models_dir.iterdir()):
        if p.is_dir():
            models.append({
                "name": p.name,
                "path": str(p),
                "files": [f.name for f in p.iterdir() if f.suffix in (".pkl", ".joblib", ".pt", ".h5", ".json")],
            })
    return {"models": models}


@router.post("/scm/predict")
async def admin_scm_predict(
    body: AdminSCMPredict,
    _key: str = Depends(verify_api_key),
):
    """Run a prediction using a trained SCM model."""
    try:
        sys.path.insert(0, str(SCM_DIR))
        from scm_training.model_tool import predict
        result = predict(body.model_name, body.features)
        return {"prediction": result}
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Model tool not available: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
