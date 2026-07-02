"""
Smoke test for step image mapping.

Usage:
    python debug/test_step_image_map.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.search import build_step_image_map


def assert_true(cond: bool, message: str):
    if not cond:
        raise AssertionError(message)


def main() -> int:
    entry = {
        "img_folder": "clients/demo/finance/sales_order",
        "raw_content": "Step 1 text\n![img](step01.png)\nStep 2 text\n![img](step02.png)",
        "steps": [
            {"step_number": 1, "image": "step01_meta.png"},
            {"step_number": 3, "image": "step03_meta.png"},
        ],
    }

    image_map = build_step_image_map(entry)
    assert_true(image_map[1] == "clients/demo/finance/sales_order/step01_meta.png", "Step metadata should win over raw content for step 1")
    assert_true(image_map[2] == "clients/demo/finance/sales_order/step02.png", "Raw content image should fill missing step 2")
    assert_true(image_map[3] == "clients/demo/finance/sales_order/step03_meta.png", "Step 3 image should be preserved")

    print("OK: step image mapping merges metadata and raw content correctly.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
