"""
Create a small deploy ZIP for the context-first chat changes.

The package intentionally excludes runtime state/log files. It is meant for
copying source changes to a server where the app is already installed.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]

DEPLOY_FILES = [
    ".gitignore",
    "api.py",
    "api/chat.py",
    "api/database.py",
    "api/llm.py",
    "api/routers/chat.py",
    "api/search.py",
    "api/semantic/retrieval.py",
    "api/conversation_state.py",
    "cfml-examples/admin_dashboard.cfm",
    "cfml-examples/ai_assistant.cfm",
    "docs/context-first-deploy-checklist.md",
    "docs/context-first-llm-query-engine-tasks.md",
    "scripts/chat_http_load_smoke.py",
    "scripts/context_scale_smoke.py",
    "scripts/package_context_first_deploy.py",
    "tests/test_admin_semantic.py",
    "tests/test_ai_analytics.py",
    "tests/test_fraud_engine.py",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="context-first-deploy.zip")
    args = parser.parse_args()

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = ROOT / out_path

    missing = [path for path in DEPLOY_FILES if not (ROOT / path).exists()]
    if missing:
        raise SystemExit(f"Missing deploy file(s): {', '.join(missing)}")

    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel in DEPLOY_FILES:
            zf.write(ROOT / rel, rel)

    print(f"OK wrote {out_path} files={len(DEPLOY_FILES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
