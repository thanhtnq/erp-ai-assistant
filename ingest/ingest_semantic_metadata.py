"""
ERP AI Semantic Metadata Ingest

Parses scoped ERP semantic metadata from JSON/XLSX, validates it, and stores it
in the knowledge database for report/tool selection.
"""
import argparse
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.semantic.store import get_semantic_file, replace_metadata_for_file, update_file_status
from api.semantic.validator import SemanticValidationError, load_and_validate


def ingest_file(file_id: int, dry_run: bool = False) -> dict:
    file_row = get_semantic_file(file_id)
    if not file_row:
        raise SemanticValidationError(f"semantic file id not found: {file_id}")
    path = Path(file_row["file_path"])
    payload = load_and_validate(path, expected_module=file_row["module"])
    report_count = len(payload.get("report_catalog", []))
    summary = {
        "file_id": file_id,
        "file_path": str(path),
        "module": file_row["module"],
        "scope_type": file_row["scope_type"],
        "company_code": file_row.get("company_code", ""),
        "reports": report_count,
        "dry_run": dry_run,
        "embedding_indexed": False,
    }
    if not dry_run:
        update_file_status(file_id, "processing")
        stored = replace_metadata_for_file(file_id, payload, file_row)
        update_file_status(file_id, "done", reports_parsed=stored)
        summary["reports_stored"] = stored
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file-id", type=int, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        summary = ingest_file(args.file_id, dry_run=args.dry_run)
        print(json.dumps({"ok": True, "summary": summary}, ensure_ascii=False))
        return 0
    except Exception as exc:
        if not args.dry_run:
            try:
                update_file_status(args.file_id, "failed", str(exc))
            except Exception:
                pass
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
