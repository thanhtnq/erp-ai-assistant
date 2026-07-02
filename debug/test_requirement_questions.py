"""
Smoke test for requirement-question routing and capability classification.

Usage:
    python debug/test_requirement_questions.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.chat import CAPABILITY_MATRIX, _build_capabilities_response, _is_capability_question
from api.llm import _route_scm_special_query, _looks_like_scm_analytics


def assert_true(cond: bool, message: str):
    if not cond:
        raise AssertionError(message)


def matrix_lookup(req_id: str) -> dict:
    for item in CAPABILITY_MATRIX:
        if item["id"] == req_id:
            return item
    raise AssertionError(f"Missing capability matrix entry: {req_id}")


def main() -> int:
    checks = [
        ("100.02", "InvoiceNow-Ready Solution Provider Accreditation", "Not yet"),
        ("100.04", "AI Automated Invoice Processing", "Not yet"),
        ("100.05", "AI Automated Journal Entry Suggestions", "Not yet"),
        ("100.06", "AI Anomaly Detection and Fraud Prevention", "Not yet"),
        ("102.06", "AI Demand Forecasting", "Partial"),
        ("102.08", "AI Stock Anomaly Detection", "Not yet"),
    ]
    for req_id, requirement, status in checks:
        row = matrix_lookup(req_id)
        assert_true(row["requirement"] == requirement, f"{req_id} requirement mismatch")
        assert_true(row["status"] == status, f"{req_id} status mismatch: expected {status}, got {row['status']}")

    routes = [
        ("Summary of SCM performance over the last 30 days.", "tool", "get_scm_overview"),
        ("Which products had high inventory but low sales performance?", "tool", "get_scm_overview"),
        ("Which SKUs had the highest sales growth this month?", "tool", "run_scm_model"),
        ("Which products are showing stable growth?", "tool", "run_scm_model"),
        ("Which supplier had the most delivery delays last month?", "tool", "get_scm_overview"),
        ("Forecast market demand for the next month by product group.", "tool", "run_scm_model"),
        ("Which products are most often purchased together?", "unsupported", None),
        ("Compare this month's forecast demand with last month's actual sales.", "unsupported", None),
    ]

    for question, expected_kind, expected_tool in routes:
        route = _route_scm_special_query(question)
        assert_true(route is not None, f"Expected a route for: {question}")
        assert_true(route["kind"] == expected_kind, f"Route kind mismatch for: {question}")
        if expected_tool:
            assert_true(route.get("tool") == expected_tool, f"Route tool mismatch for: {question}")
        assert_true(_looks_like_scm_analytics(question), f"Expected SCM analytics detection for: {question}")

    capability_questions = [
        "Does the solution support InvoiceNow?",
        "Do you have invoice OCR?",
        "Can you suggest journal entries?",
        "Do you do anomaly detection and fraud prevention?",
        "What can you do?",
        "Bạn hỗ trợ gì cho AI features?",
    ]
    for question in capability_questions:
        assert_true(_is_capability_question(question), f"Expected capability classification for: {question}")

    capability_md = _build_capabilities_response("en")
    for phrase in [
        "InvoiceNow-Ready Solution Provider Accreditation",
        "AI Automated Invoice Processing",
        "AI Automated Journal Entry Suggestions",
        "AI Anomaly Detection and Fraud Prevention",
        "AI Demand Forecasting",
    ]:
        assert_true(phrase in capability_md, f"Capability response missing phrase: {phrase}")

    print("OK: requirement matrix and sample question routing passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
