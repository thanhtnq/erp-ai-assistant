"""Shared configuration for SCM training.

This module intentionally reuses the main project's .env/PostgreSQL settings
instead of maintaining a separate database.json file.
"""

from pathlib import Path
import re

from ingest.ingest_config import PG_CONFIG

BASE_DIR = Path(__file__).resolve().parent.parent
MODULE_DIR = Path(__file__).resolve().parent

MAPPING_FILE = MODULE_DIR / "mapping.json"
ARTIFACT_DIR = BASE_DIR / "data" / "scm_training"
LOG_DIR = BASE_DIR / "logs" / "scm_training"


def _safe_part(value: str, fallback: str) -> str:
    value = (value or "").strip()
    if not value:
        return fallback
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)[:120]


def scope_dir(masterfn: str, companyfn: str = None, dbname: str = None) -> Path:
    """Return artifact root for one database/client/entity scope."""
    db_part = _safe_part(dbname or PG_CONFIG.get("dbname"), "_db")
    master_part = _safe_part(masterfn, "_master")
    company_part = _safe_part(companyfn, "_all_companies")
    return ARTIFACT_DIR / db_part / master_part / company_part


def processed_dir(masterfn: str, companyfn: str = None, dbname: str = None) -> Path:
    return scope_dir(masterfn, companyfn, dbname) / "processed"


def models_dir(masterfn: str, companyfn: str = None, dbname: str = None) -> Path:
    return scope_dir(masterfn, companyfn, dbname) / "models"


def analysis_dir(masterfn: str, companyfn: str = None, dbname: str = None) -> Path:
    return scope_dir(masterfn, companyfn, dbname) / "analysis"


def ensure_dirs():
    for path in (ARTIFACT_DIR, LOG_DIR):
        path.mkdir(parents=True, exist_ok=True)


def ensure_scope_dirs(masterfn: str, companyfn: str = None, dbname: str = None):
    for path in (
        processed_dir(masterfn, companyfn, dbname),
        models_dir(masterfn, companyfn, dbname),
        analysis_dir(masterfn, companyfn, dbname),
    ):
        path.mkdir(parents=True, exist_ok=True)
