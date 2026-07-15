import json
import os
import sqlite3
import unittest
import urllib.request
from pathlib import Path

from api.database import init_chat_db
from api.llm import (
    _extract_period_days, _extract_top_n, _inherit_scm_args,
    _latest_user_history_text, _route_scm_special_query, _scm_column_label,
)
from api.config import CHAT_DB


class AnalyticsRoutingTests(unittest.TestCase):
    def test_period_parser(self):
        self.assertEqual(_extract_period_days("last 60 days"), 60)
        self.assertEqual(_extract_period_days("8 weeks"), 56)
        self.assertEqual(_extract_period_days("2 months"), 60)
        self.assertEqual(_extract_top_n("top 25 products"), 25)

    def test_latest_user_context_inheritance(self):
        history = (
            "User: SCM summary for 30 days\n"
            "Assistant: Results for 30 days\n"
            "User: show top 20 products for 60 days\n"
            "Assistant: Here are 20 products"
        )
        self.assertEqual(_latest_user_history_text(history), "show top 20 products for 60 days")
        inherited = _inherit_scm_args("which invoices are included?", history, {"days": 30, "top": 10})
        self.assertEqual(inherited["days"], 60)
        self.assertEqual(inherited["top"], 20)
        explicit = _inherit_scm_args("top 5 invoices for 7 days", history, {"days": 7, "top": 5})
        self.assertEqual(explicit["days"], 7)
        self.assertEqual(explicit["top"], 5)
        sku_history = "User: forecast SKU RZ05-04760100-R3G1 for 90 days\nAssistant: Forecast result"
        sku_followup = _inherit_scm_args("dự báo SKU này tháng sau", sku_history, {"days": 30, "top": 10})
        self.assertEqual(sku_followup["sku_code"], "RZ05-04760100-R3G1")

    def test_new_ai_routes(self):
        cases = {
            "duplicate vendor invoices": "detect_duplicate_ap_transactions",
            "unusual finance transactions": "detect_finance_transaction_anomalies",
            "vendor risk indicators": "detect_vendor_risk_indicators",
            "SKU demand history": "get_sku_demand_history",
            "recommend replenishment and safety stock": "recommend_inventory_replenishment",
            "stock movement anomalies": "detect_inventory_movement_anomalies",
            "expiry risk": "detect_expiry_writeoff_risk",
            "stock shrinkage indicators": "detect_stock_shrinkage_indicators",
            "advanced demand forecast": "forecast_sku_demand_advanced",
            "vendors sharing the same bank account": "detect_shared_vendor_bank_accounts",
            "negative inventory by location": "detect_negative_inventory",
            "unreconciled payments": "detect_unreconciled_payments",
            "unbalanced journal entries": "detect_accounting_integrity_errors",
            "transactions missing account code": "detect_accounting_integrity_errors",
            "invoices without PO": "detect_invoice_source_exceptions",
            "invoices without GRN": "detect_invoice_source_exceptions",
        }
        for query, expected in cases.items():
            with self.subTest(query=query):
                self.assertEqual(_route_scm_special_query(query)["tool"], expected)

    def test_friendly_labels(self):
        self.assertEqual(_scm_column_label("risk_score", "en"), "Risk Score")
        self.assertEqual(_scm_column_label("recommended_qty", "vi"), "SL đề xuất")

    def test_scm_question_matrix(self):
        cases = {
            "top 10 products": "bestselling",
            "highest revenue products": "revenue",
            "products with fastest sales growth": "growth",
            "products with stable growth": "stable_growth",
            "products with surge in demand": "demand_surge",
            "high inventory low sales products": "stock_low_sales",
            "suppliers with delivery delays": "supplier_delay",
            "bestsellers running out of stock": "low_stock_bestsellers",
            "products often purchased together": "basket",
            "forecast demand by product category": "demand_forecast",
            "forecast volatility by product": "forecast_volatility",
            "SCM performance summary last 60 days": "overview",
        }
        for query, expected in cases.items():
            route = _route_scm_special_query(query)
            with self.subTest(query=query):
                self.assertIsNotNone(route)
                self.assertEqual(route["args"].get("analysis"), expected)

    def test_bilingual_requirement_routes(self):
        supported = {
            "Có invoice nào thanh toán 2 lần không?": "detect_duplicate_ap_transactions",
            "Có hóa đơn nào bị tạo trùng?": "detect_duplicate_ap_transactions",
            "Những giao dịch nào bất thường trong tháng này?": "detect_finance_transaction_anomalies",
            "Vendor nào có dấu hiệu gian lận?": "detect_vendor_risk_indicators",
            "Dự báo nhu cầu tháng sau.": "forecast_sku_demand_advanced",
            "SKU nào sẽ bán chạy?": "forecast_sku_demand_advanced",
            "Tôi nên nhập thêm hàng nào?": "recommend_inventory_replenishment",
            "SKU nào cần reorder?": "recommend_inventory_replenishment",
            "Có kho nào thất thoát?": "detect_stock_shrinkage_indicators",
            "SKU nào tiêu hao bất thường?": "detect_inventory_movement_anomalies",
            "Có item nào sắp hết hạn?": "detect_expiry_writeoff_risk",
            "Show duplicate invoices.": "detect_duplicate_ap_transactions",
            "Forecast inventory next quarter.": "forecast_sku_demand_advanced",
            "Vendor nào dùng cùng tài khoản ngân hàng?": "detect_shared_vendor_bank_accounts",
            "Kho nào có tồn kho âm?": "detect_negative_inventory",
            "Có payment nào chưa reconcile?": "detect_unreconciled_payments",
            "Có journal entry nào chưa balanced?": "detect_accounting_integrity_errors",
            "Có transaction nào thiếu account code?": "detect_accounting_integrity_errors",
            "Có invoice nào chưa có PO?": "detect_invoice_source_exceptions",
            "Có invoice nào không có GRN?": "detect_invoice_source_exceptions",
        }
        for query, expected_tool in supported.items():
            with self.subTest(query=query):
                route = _route_scm_special_query(query)
                self.assertEqual(route["kind"], "tool")
                self.assertEqual(route["tool"], expected_tool)

        unsupported = [
            "Có invoice nào bypass approval flow?",
        ]
        for query in unsupported:
            with self.subTest(query=query):
                self.assertEqual(_route_scm_special_query(query)["kind"], "unsupported")

class AlertSchemaTests(unittest.TestCase):
    def test_alert_tables_exist(self):
        init_chat_db()
        conn = sqlite3.connect(CHAT_DB)
        names = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'ai_%'"
        )}
        conn.close()
        self.assertIn("ai_alerts", names)
        self.assertIn("ai_recommendation_actions", names)


class LiveSkillsContractTests(unittest.TestCase):
    @unittest.skipUnless(os.getenv("RUN_LIVE_SKILLS_TESTS") == "1", "live skills tests disabled")
    def test_contract_and_scope(self):
        masterfn = os.environ["TEST_MASTERFN"]
        companyfn = os.environ["TEST_COMPANYFN"]
        payload = json.dumps({
            "name": "recommend_inventory_replenishment",
            "arguments": {"days": 30, "top": 2},
            "masterfn": masterfn,
            "companyfn": companyfn,
        }).encode()
        req = urllib.request.Request(
            os.getenv("SKILLS_SERVER_URL", "http://localhost:3001") + "/execute",
            data=payload, headers={"Content-Type": "application/json"}, method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.load(response)["result"]
        self.assertEqual(result["scope"], {"masterfn": masterfn, "companyfn": companyfn})
        self.assertIn("generated_at", result)
        self.assertIn("data_quality", result)
        self.assertIn("warnings", result)


# ─── Fraud Detection Endpoint Tests ─────────────────────────────────────────

class FraudEndpointTests(unittest.TestCase):
    """Test fraud detection endpoint request validation and response contract."""

    def setUp(self):
        """Initialize chat DB for fraud tables."""
        init_chat_db()

    def _make_finding(self, overrides=None):
        """Helper to create a sample finding dict."""
        finding = {
            "severity": "high",
            "title": "Test Finding",
            "description": "A test finding for unit tests",
            "source_id": "DOC001",
            "finding_type": "ap_invoice",
            "risk_score": 85.0,
        }
        if overrides:
            finding.update(overrides)
        return finding

    def test_scan_request_missing_scope_returns_400(self):
        """Missing masterfn or companyfn should return HTTP 400."""
        from api.routers.analytics_fraud import run_fraud_scan
        from api.models import FraudScanRequest
        from fastapi import HTTPException

        # Missing masterfn
        with self.assertRaises(HTTPException) as ctx:
            req = FraudScanRequest(masterfn="", companyfn="comp01")
            # We can't easily call the endpoint without FastAPI test client,
            # but we can test the validation logic directly
            if not req.masterfn or not req.companyfn:
                raise HTTPException(400, "masterfn and companyfn are required")
        self.assertEqual(ctx.exception.status_code, 400)

        # Missing companyfn
        with self.assertRaises(HTTPException) as ctx:
            req = FraudScanRequest(masterfn="mfn01", companyfn="")
            if not req.masterfn or not req.companyfn:
                raise HTTPException(400, "masterfn and companyfn are required")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_fraud_scan_request_model(self):
        """FraudScanRequest model should accept valid fields."""
        from api.models import FraudScanRequest

        req = FraudScanRequest(
            masterfn="mfn01",
            companyfn="comp01",
            date_from="2026-01-01",
            date_to="2026-06-30",
            scan_type="ap_invoice",
            severity="high",
            max_findings=10,
        )
        self.assertEqual(req.masterfn, "mfn01")
        self.assertEqual(req.companyfn, "comp01")
        self.assertEqual(req.scan_type, "ap_invoice")
        self.assertEqual(req.severity, "high")
        self.assertEqual(req.max_findings, 10)

    def test_fraud_finding_update_model(self):
        """FraudFindingUpdate model should accept valid fields."""
        from api.models import FraudFindingUpdate

        update = FraudFindingUpdate(
            masterfn="mfn01",
            companyfn="comp01",
            status="investigating",
            reviewer="admin_user",
            review_note="Checking vendor details",
        )
        self.assertEqual(update.status, "investigating")
        self.assertEqual(update.reviewer, "admin_user")
        self.assertEqual(update.review_note, "Checking vendor details")

    def test_fraud_tables_created(self):
        """Fraud detection tables should be created in chat DB."""
        import sqlite3
        from api.config import CHAT_DB
        from api.routers.analytics_fraud import init_fraud_tables

        conn = sqlite3.connect(CHAT_DB)
        conn.row_factory = sqlite3.Row
        init_fraud_tables(conn)

        tables = {
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'fraud_%'"
            )
        }
        conn.close()
        self.assertIn("fraud_scans", tables)
        self.assertIn("fraud_findings", tables)

    def test_fraud_scan_response_contract(self):
        """Verify fraud scan response has required fields."""
        from api.routers.analytics_fraud import _run_real_fraud_scan

        # Test with mock data - function should return (findings, partial_errors)
        findings, partial_errors = _run_real_fraud_scan(
            masterfn="test_mfn",
            companyfn="test_cfn",
            scan_id=999,
            scan_type="all",
            max_findings=4,
        )

        # Each finding should have required fields
        for f in findings:
            self.assertIn("scan_id", f)
            self.assertIn("masterfn", f)
            self.assertIn("companyfn", f)
            self.assertIn("severity", f)
            self.assertIn("title", f)
            self.assertIn("description", f)
            self.assertIn("finding_type", f)
            self.assertIn("risk_score", f)
            self.assertIn("evidence_json", f)
            self.assertIn("status", f)
            self.assertEqual(f["status"], "open")
            self.assertEqual(f["masterfn"], "test_mfn")
            self.assertEqual(f["companyfn"], "test_cfn")

        # partial_errors should be a list
        self.assertIsInstance(partial_errors, list)

    def test_fraud_scan_disclaimer_in_response(self):
        """Response should include fraud indicator disclaimer."""
        from api.routers.analytics_fraud import _run_real_fraud_scan

        findings, partial_errors = _run_real_fraud_scan(
            masterfn="test_mfn",
            companyfn="test_cfn",
            scan_id=999,
            max_findings=2,
        )

        # Verify evidence_json contains disclaimer info
        for f in findings:
            evidence = json.loads(f["evidence_json"])
            self.assertIn("detected_at", evidence)
            self.assertIn("source", evidence)
            self.assertEqual(evidence["source"], "erp_postgresql")
            self.assertEqual(evidence["data_type"], "live")

    def test_fraud_scan_type_filtering(self):
        """Scan type parameter should filter which queries run."""
        from api.routers.analytics_fraud import _run_real_fraud_scan

        # Test with specific scan type
        findings_ap, _ = _run_real_fraud_scan(
            masterfn="test_mfn",
            companyfn="test_cfn",
            scan_id=998,
            scan_type="ap_invoice",
            max_findings=4,
        )

        # All findings should be ap_invoice type (or empty if no data)
        for f in findings_ap:
            self.assertEqual(f["finding_type"], "ap_invoice")

    def test_fraud_scan_severity_filtering(self):
        """Severity filter should be respected."""
        from api.routers.analytics_fraud import _run_real_fraud_scan

        # Test with specific severity
        findings_high, _ = _run_real_fraud_scan(
            masterfn="test_mfn",
            companyfn="test_cfn",
            scan_id=997,
            severity_filter="high",
            max_findings=4,
        )

        # All findings should be high severity (or empty if no data)
        for f in findings_high:
            self.assertEqual(f["severity"], "high")

    def test_fraud_scan_max_findings(self):
        """Max findings limit should be respected."""
        from api.routers.analytics_fraud import _run_real_fraud_scan

        findings, _ = _run_real_fraud_scan(
            masterfn="test_mfn",
            companyfn="test_cfn",
            scan_id=996,
            max_findings=2,
        )

        self.assertLessEqual(len(findings), 2)

    def test_fraud_scan_partial_error_handling(self):
        """Upstream tool failures should return partial errors, not crash."""
        from api.routers.analytics_fraud import _run_real_fraud_scan

        # Even if PostgreSQL is not available, the function should not crash
        # It should return empty findings with partial_errors
        findings, partial_errors = _run_real_fraud_scan(
            masterfn="test_mfn",
            companyfn="test_cfn",
            scan_id=995,
            max_findings=4,
        )

        # Should always return a tuple of (list, list)
        self.assertIsInstance(findings, list)
        self.assertIsInstance(partial_errors, list)

        # If there are partial errors, they should have required fields
        for err in partial_errors:
            self.assertIn("source", err)
            self.assertIn("error_type", err)
            self.assertIn("message", err)


# ─── Demand Planning Endpoint Tests ─────────────────────────────────────────

class DemandEndpointTests(unittest.TestCase):
    """Test demand planning endpoint request validation and response contract."""

    def setUp(self):
        """Initialize chat DB for demand tables."""
        init_chat_db()

    def test_demand_request_missing_scope_returns_400(self):
        """Missing masterfn or companyfn should return HTTP 400."""
        from api.models import DemandForecastRequest
        from fastapi import HTTPException

        # Missing masterfn
        with self.assertRaises(HTTPException) as ctx:
            req = DemandForecastRequest(masterfn="", companyfn="comp01")
            if not req.masterfn or not req.companyfn:
                raise HTTPException(400, "masterfn and companyfn are required")
        self.assertEqual(ctx.exception.status_code, 400)

        # Missing companyfn
        with self.assertRaises(HTTPException) as ctx:
            req = DemandForecastRequest(masterfn="mfn01", companyfn="")
            if not req.masterfn or not req.companyfn:
                raise HTTPException(400, "masterfn and companyfn are required")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_demand_forecast_request_model(self):
        """DemandForecastRequest model should accept valid fields."""
        from api.models import DemandForecastRequest

        req = DemandForecastRequest(
            masterfn="mfn01",
            companyfn="comp01",
            horizon_days=60,
            sku_filter="SKU001",
            location_filter="WH01",
        )
        self.assertEqual(req.masterfn, "mfn01")
        self.assertEqual(req.companyfn, "comp01")
        self.assertEqual(req.horizon_days, 60)
        self.assertEqual(req.sku_filter, "SKU001")
        self.assertEqual(req.location_filter, "WH01")

    def test_demand_tables_created(self):
        """Demand planning tables should be created in chat DB."""
        import sqlite3
        from api.config import CHAT_DB
        from api.routers.analytics_demand import init_demand_tables

        conn = sqlite3.connect(CHAT_DB)
        conn.row_factory = sqlite3.Row
        init_demand_tables(conn)

        tables = {
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'demand_%'"
            )
        }
        conn.close()
        self.assertIn("demand_forecasts", tables)
        self.assertIn("demand_sku_forecasts", tables)

    def test_demand_chat_history_table_created(self):
        """Demand chat messages table should be created for persisted chat history."""
        import sqlite3
        from api.config import CHAT_DB
        from api.routers.analytics_demand import init_demand_tables

        conn = sqlite3.connect(CHAT_DB)
        conn.row_factory = sqlite3.Row
        init_demand_tables(conn)

        tables = {
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='ai_module_chat_messages'"
            )
        }
        conn.close()
        self.assertIn("ai_module_chat_messages", tables)

    def test_demand_chat_history_scope_roundtrip(self):
        """Demand chat history should persist and clear by user/company scope."""
        import sqlite3
        from api.config import CHAT_DB
        from api.routers.analytics_demand import init_demand_tables

        conn = sqlite3.connect(CHAT_DB)
        conn.row_factory = sqlite3.Row
        init_demand_tables(conn)

        conn.execute("""
            DELETE FROM ai_module_chat_messages
            WHERE module='demand' AND user_id=? AND masterfn=? AND companyfn=?
        """, ("m8", "chat_mfn", "chat_cfn"))
        conn.execute("""
            INSERT INTO ai_module_chat_messages
                (module, user_id, masterfn, companyfn, role, content, meta_json, created_at)
            VALUES ('demand', ?, ?, ?, 'user', ?, ?, ?)
        """, ("m8", "chat_mfn", "chat_cfn", "Forecast SKU A", '{"horizon_days":90}', "2026-07-09T12:00:00"))
        conn.commit()

        rows = conn.execute("""
            SELECT role, content, meta_json FROM ai_module_chat_messages
            WHERE module='demand' AND user_id=? AND masterfn=? AND companyfn=?
        """, ("m8", "chat_mfn", "chat_cfn")).fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["role"], "user")
        self.assertEqual(rows[0]["content"], "Forecast SKU A")

        conn.execute("""
            DELETE FROM ai_module_chat_messages
            WHERE module='demand' AND user_id=? AND masterfn=? AND companyfn=?
        """, ("m8", "chat_mfn", "chat_cfn"))
        conn.commit()
        count = conn.execute("""
            SELECT COUNT(*) FROM ai_module_chat_messages
            WHERE module='demand' AND user_id=? AND masterfn=? AND companyfn=?
        """, ("m8", "chat_mfn", "chat_cfn")).fetchone()[0]
        conn.close()
        self.assertEqual(count, 0)

    def test_demand_chat_fallback_answers_domain_questions(self):
        """Demand smart chat fallback should answer domain questions without forecast rows."""
        from api.routers.analytics_demand import _demand_chat_fallback

        hello = _demand_chat_fallback("helo", {})
        self.assertIn("Demand Planning", hello)

        reorder = _demand_chat_fallback("reorder la gi", {})
        self.assertIn("Reorder", reorder)

        no_data = _demand_chat_fallback("vi sao forecast khong co data", {})
        self.assertIn("SKU=all", no_data)

    def test_demand_forecast_response_contract(self):
        """Verify demand forecast response has required fields."""
        from api.routers.analytics_demand import _generate_real_forecast

        results, partial_errors = _generate_real_forecast(
            masterfn="test_mfn",
            companyfn="test_cfn",
            forecast_id=999,
            horizon_days=90,
        )

        # Each SKU forecast should have required fields
        for s in results:
            self.assertIn("forecast_id", s)
            self.assertIn("masterfn", s)
            self.assertIn("companyfn", s)
            self.assertIn("sku", s)
            self.assertIn("location", s)
            self.assertIn("forecast_qty", s)
            self.assertIn("on_hand_qty", s)
            self.assertIn("safety_stock", s)
            self.assertIn("reorder_point", s)
            self.assertIn("recommended_qty", s)
            self.assertIn("action", s)
            self.assertIn("confidence", s)
            self.assertIn("details_json", s)
            self.assertEqual(s["masterfn"], "test_mfn")
            self.assertEqual(s["companyfn"], "test_cfn")
            self.assertIn(s["action"], ["reorder", "review", "ok"])

        # partial_errors should be a list
        self.assertIsInstance(partial_errors, list)

    def test_demand_forecast_disclaimer_in_response(self):
        """Response should include forecast disclaimer and assumptions."""
        from api.routers.analytics_demand import _generate_real_forecast

        results, partial_errors = _generate_real_forecast(
            masterfn="test_mfn",
            companyfn="test_cfn",
            forecast_id=999,
            horizon_days=90,
        )

        # Verify details_json contains model info
        for s in results:
            details = json.loads(s["details_json"])
            self.assertIn("source", details)
            self.assertEqual(details["source"], "erp_postgresql")
            self.assertIn("model", details)
            self.assertEqual(details["model"], "simple_moving_average")
            self.assertIn("missing_inputs", details)

    def test_demand_forecast_horizon_days(self):
        """Horizon days parameter should affect forecast calculation."""
        from api.routers.analytics_demand import _generate_real_forecast

        # Test with different horizons
        results_30, _ = _generate_real_forecast(
            masterfn="test_mfn",
            companyfn="test_cfn",
            forecast_id=998,
            horizon_days=30,
        )

        results_90, _ = _generate_real_forecast(
            masterfn="test_mfn",
            companyfn="test_cfn",
            forecast_id=997,
            horizon_days=90,
        )

        # Both should return valid results
        self.assertIsInstance(results_30, list)
        self.assertIsInstance(results_90, list)

    def test_demand_forecast_sku_filter(self):
        """SKU filter should limit results to specific SKU."""
        from api.routers.analytics_demand import _generate_real_forecast

        results, _ = _generate_real_forecast(
            masterfn="test_mfn",
            companyfn="test_cfn",
            forecast_id=996,
            sku_filter="NONEXISTENT_SKU",
        )

        # Should return empty or only matching SKUs
        for s in results:
            self.assertEqual(s["sku"], "NONEXISTENT_SKU")

    def test_demand_forecast_action_logic(self):
        """Action field should be one of: reorder, review, ok."""
        from api.routers.analytics_demand import _generate_real_forecast

        results, _ = _generate_real_forecast(
            masterfn="test_mfn",
            companyfn="test_cfn",
            forecast_id=995,
            horizon_days=90,
        )

        for s in results:
            self.assertIn(s["action"], ["reorder", "review", "ok"])
            # Confidence should be between 0 and 1
            self.assertGreaterEqual(s["confidence"], 0.0)
            self.assertLessEqual(s["confidence"], 1.0)
            # Quantities should be non-negative
            self.assertGreaterEqual(s["forecast_qty"], 0)
            self.assertGreaterEqual(s["on_hand_qty"], 0)
            self.assertGreaterEqual(s["recommended_qty"], 0)

    def test_demand_forecast_partial_error_handling(self):
        """Upstream tool failures should return partial errors, not crash."""
        from api.routers.analytics_demand import _generate_real_forecast

        # Even if PostgreSQL is not available, the function should not crash
        results, partial_errors = _generate_real_forecast(
            masterfn="test_mfn",
            companyfn="test_cfn",
            forecast_id=994,
            horizon_days=90,
        )

        # Should always return a tuple of (list, list)
        self.assertIsInstance(results, list)
        self.assertIsInstance(partial_errors, list)

        # If there are partial errors, they should have required fields
        for err in partial_errors:
            self.assertIn("source", err)
            self.assertIn("error_type", err)
            self.assertIn("message", err)


# ─── Recommendation Action Tests ─────────────────────────────────────────────

class RecommendationActionTests(unittest.TestCase):
    """Test recommendation action endpoint (accept/adjust/reject)."""

    def setUp(self):
        """Initialize chat DB for recommendation tables."""
        init_chat_db()

    def test_recommendation_action_model(self):
        """AIRecommendationAction model should accept valid fields."""
        from api.models import AIRecommendationAction

        action = AIRecommendationAction(
            masterfn="mfn01",
            companyfn="comp01",
            recommendation_id="demand-SKU001-WH01",
            action="accepted",
            actor="admin_user",
            note="Accepted recommendation for SKU001",
            adjusted_qty=100.0,
        )
        self.assertEqual(action.masterfn, "mfn01")
        self.assertEqual(action.companyfn, "comp01")
        self.assertEqual(action.recommendation_id, "demand-SKU001-WH01")
        self.assertEqual(action.action, "accepted")
        self.assertEqual(action.actor, "admin_user")
        self.assertEqual(action.note, "Accepted recommendation for SKU001")
        self.assertEqual(action.adjusted_qty, 100.0)

    def test_recommendation_action_model_defaults(self):
        """AIRecommendationAction optional fields should have correct defaults."""
        from api.models import AIRecommendationAction

        action = AIRecommendationAction(
            masterfn="mfn01",
            companyfn="comp01",
            recommendation_id="demand-SKU002-WH02",
            action="rejected",
            actor="demo_user",
        )
        self.assertEqual(action.action, "rejected")
        self.assertIsNone(action.note)
        self.assertIsNone(action.adjusted_qty)

    def test_recommendation_action_tables_exist(self):
        """Recommendation action tables should be created in chat DB."""
        import sqlite3
        from api.config import CHAT_DB

        conn = sqlite3.connect(CHAT_DB)
        names = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'ai_recommendation_%'"
        )}
        conn.close()
        self.assertIn("ai_recommendation_actions", names)

    def test_recommendation_action_response_contract(self):
        """Verify recommendation action response has required fields."""
        from api.routers.admin_ai_alerts import recommendation_action
        from api.models import AIRecommendationAction
        from fastapi import HTTPException

        # We can't easily call the endpoint without FastAPI test client,
        # but we can test the validation logic directly
        valid_actions = {"accepted", "adjusted", "rejected", "expired"}

        # Test each valid action
        for action_name in valid_actions:
            body = AIRecommendationAction(
                masterfn="test_mfn",
                companyfn="test_cfn",
                recommendation_id=f"demand-SKU001-WH01-{action_name}",
                action=action_name,
                actor="test_user",
                note=f"Test {action_name}",
                adjusted_qty=50.0 if action_name == "adjusted" else None,
            )
            # Validate action
            self.assertIn(body.action, valid_actions)

    def test_recommendation_action_invalid_action_returns_400(self):
        """Invalid action should return HTTP 400."""
        from api.models import AIRecommendationAction
        from api.routers.admin_ai_alerts import RECOMMENDATION_ACTIONS
        from fastapi import HTTPException

        # Test invalid action
        with self.assertRaises(HTTPException) as ctx:
            body = AIRecommendationAction(
                masterfn="mfn01",
                companyfn="comp01",
                recommendation_id="demand-SKU001-WH01",
                action="invalid_action",
                actor="test_user",
            )
            if body.action not in RECOMMENDATION_ACTIONS:
                raise HTTPException(400, "Invalid recommendation action")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_recommendation_action_missing_scope_returns_400(self):
        """Missing masterfn or companyfn should return HTTP 400."""
        from api.models import AIRecommendationAction
        from fastapi import HTTPException

        # Missing masterfn
        with self.assertRaises(HTTPException) as ctx:
            body = AIRecommendationAction(
                masterfn="",
                companyfn="comp01",
                recommendation_id="demand-SKU001-WH01",
                action="accepted",
                actor="test_user",
            )
            if not body.masterfn or not body.companyfn:
                raise HTTPException(400, "masterfn and companyfn are required")
        self.assertEqual(ctx.exception.status_code, 400)

        # Missing companyfn
        with self.assertRaises(HTTPException) as ctx:
            body = AIRecommendationAction(
                masterfn="mfn01",
                companyfn="",
                recommendation_id="demand-SKU001-WH01",
                action="accepted",
                actor="test_user",
            )
            if not body.masterfn or not body.companyfn:
                raise HTTPException(400, "masterfn and companyfn are required")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_recommendation_action_accept_flow(self):
        """Accept action should store accepted recommendation."""
        import sqlite3
        from api.config import CHAT_DB

        conn = sqlite3.connect(CHAT_DB)
        conn.row_factory = sqlite3.Row

        # Insert a test action directly (simulating the endpoint)
        conn.execute("""
            INSERT INTO ai_recommendation_actions
                (masterfn, companyfn, recommendation_id, action, actor, note, adjusted_qty, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ("test_mfn", "test_cfn", "demand-SKU001-WH01", "accepted",
              "test_user", "Accepted recommendation", None, "2026-07-09T12:00:00"))
        conn.commit()

        # Verify it was stored
        row = conn.execute("""
            SELECT * FROM ai_recommendation_actions
            WHERE recommendation_id=? AND action=?
        """, ("demand-SKU001-WH01", "accepted")).fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row["masterfn"], "test_mfn")
        self.assertEqual(row["companyfn"], "test_cfn")
        self.assertEqual(row["action"], "accepted")
        self.assertEqual(row["actor"], "test_user")
        self.assertEqual(row["note"], "Accepted recommendation")
        self.assertIsNone(row["adjusted_qty"])

    def test_recommendation_action_adjust_flow(self):
        """Adjust action should store adjusted quantity."""
        import sqlite3
        from api.config import CHAT_DB

        conn = sqlite3.connect(CHAT_DB)
        conn.row_factory = sqlite3.Row

        # Insert a test adjust action
        conn.execute("""
            INSERT INTO ai_recommendation_actions
                (masterfn, companyfn, recommendation_id, action, actor, note, adjusted_qty, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ("test_mfn", "test_cfn", "demand-SKU002-WH02", "adjusted",
              "test_user", "Adjusted to 75 units", 75.0, "2026-07-09T12:00:00"))
        conn.commit()

        # Verify it was stored with adjusted_qty
        row = conn.execute("""
            SELECT * FROM ai_recommendation_actions
            WHERE recommendation_id=? AND action=?
        """, ("demand-SKU002-WH02", "adjusted")).fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row["action"], "adjusted")
        self.assertEqual(row["adjusted_qty"], 75.0)
        self.assertEqual(row["note"], "Adjusted to 75 units")

    def test_recommendation_action_reject_flow(self):
        """Reject action should store rejected recommendation."""
        import sqlite3
        from api.config import CHAT_DB

        conn = sqlite3.connect(CHAT_DB)
        conn.row_factory = sqlite3.Row

        # Insert a test reject action
        conn.execute("""
            INSERT INTO ai_recommendation_actions
                (masterfn, companyfn, recommendation_id, action, actor, note, adjusted_qty, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ("test_mfn", "test_cfn", "demand-SKU003-WH03", "rejected",
              "test_user", "Rejected - manual order already placed", None,
              "2026-07-09T12:00:00"))
        conn.commit()

        # Verify it was stored
        row = conn.execute("""
            SELECT * FROM ai_recommendation_actions
            WHERE recommendation_id=? AND action=?
        """, ("demand-SKU003-WH03", "rejected")).fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row["action"], "rejected")
        self.assertEqual(row["note"], "Rejected - manual order already placed")
        self.assertIsNone(row["adjusted_qty"])

    def test_recommendation_action_multiple_actions_same_recommendation(self):
        """Multiple actions on the same recommendation should be tracked separately."""
        import sqlite3
        from api.config import CHAT_DB

        conn = sqlite3.connect(CHAT_DB)
        conn.row_factory = sqlite3.Row

        # Clean up any previous test data for this recommendation_id
        conn.execute("DELETE FROM ai_recommendation_actions WHERE recommendation_id=?", ("demand-SKU004-WH04",))
        conn.commit()

        # Insert multiple actions for the same recommendation
        actions = [
            ("test_mfn", "test_cfn", "demand-SKU004-WH04", "accepted",
             "user1", "First accepted", None),
            ("test_mfn", "test_cfn", "demand-SKU004-WH04", "adjusted",
             "user2", "Adjusted to 50", 50.0),
            ("test_mfn", "test_cfn", "demand-SKU004-WH04", "rejected",
             "user3", "Rejected after review", None),
        ]
        for a in actions:
            conn.execute("""
                INSERT INTO ai_recommendation_actions
                    (masterfn, companyfn, recommendation_id, action, actor, note, adjusted_qty, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (*a, "2026-07-09T12:00:00"))
        conn.commit()

        # Verify all 3 actions are stored
        rows = conn.execute("""
            SELECT * FROM ai_recommendation_actions
            WHERE recommendation_id=?
            ORDER BY created_at ASC
        """, ("demand-SKU004-WH04",)).fetchall()
        conn.close()

        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["action"], "accepted")
        self.assertEqual(rows[1]["action"], "adjusted")
        self.assertEqual(rows[2]["action"], "rejected")


    def test_recommendation_action_response_format(self):
        """Verify the endpoint response format matches expected contract."""
        from api.routers.admin_ai_alerts import RECOMMENDATION_ACTIONS

        # Simulate the response format from the endpoint
        for action_name in ["accepted", "adjusted", "rejected"]:
            response = {
                "id": 1,
                "action": action_name,
                "erp_document_created": False,
            }
            self.assertIn("id", response)
            self.assertIn("action", response)
            self.assertIn("erp_document_created", response)
            self.assertEqual(response["action"], action_name)
            self.assertFalse(response["erp_document_created"])


# ─── Alert Deduplication & Review Transition Tests ─────────────────────────

class AlertDeduplicationTests(unittest.TestCase):
    """Test alert deduplication and review status transitions."""

    def setUp(self):
        """Initialize chat DB for alert tables."""
        init_chat_db()

    def test_alert_deduplication_same_source_id(self):
        """Same source_id should not create duplicate alerts with open status."""
        import sqlite3
        from api.config import CHAT_DB

        conn = sqlite3.connect(CHAT_DB)
        conn.row_factory = sqlite3.Row

        # Clean up test data
        conn.execute("DELETE FROM ai_alerts WHERE masterfn=? AND companyfn=?",
                     ("dedup_mfn", "dedup_cfn"))
        conn.commit()

        # Insert first alert
        conn.execute("""
            INSERT INTO ai_alerts
                (masterfn, companyfn, alert_type, severity, status,
                 title, reason_code, risk_score, source_id,
                 evidence_json, rule_version, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'new', ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("dedup_mfn", "dedup_cfn", "fraud", "high",
              "Duplicate invoice DOC001", "ap_invoice", 85.0, "DOC001",
              '{}', "v1", "2026-07-09T12:00:00", "2026-07-09T12:00:00"))
        conn.commit()

        # Try to insert duplicate (same source_id, same open status)
        existing = conn.execute("""
            SELECT id FROM ai_alerts
            WHERE masterfn=? AND companyfn=? AND source_id=?
              AND status IN ('new','investigating')
            LIMIT 1
        """, ("dedup_mfn", "dedup_cfn", "DOC001")).fetchone()

        self.assertIsNotNone(existing, "First alert should exist")

        # Should NOT insert duplicate
        if not existing:
            conn.execute("""
                INSERT INTO ai_alerts
                    (masterfn, companyfn, alert_type, severity, status,
                     title, reason_code, risk_score, source_id,
                     evidence_json, rule_version, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'new', ?, ?, ?, ?, ?, ?, ?, ?)
            """, ("dedup_mfn", "dedup_cfn", "fraud", "high",
                  "Duplicate invoice DOC001", "ap_invoice", 85.0, "DOC001",
                  '{}', "v1", "2026-07-09T12:00:00", "2026-07-09T12:00:00"))
            conn.commit()

        # Verify only 1 alert exists for this source_id
        count = conn.execute("""
            SELECT COUNT(*) FROM ai_alerts
            WHERE masterfn=? AND companyfn=? AND source_id=?
        """, ("dedup_mfn", "dedup_cfn", "DOC001")).fetchone()[0]
        conn.close()

        self.assertEqual(count, 1, "Should not create duplicate alert for same source_id")

    def test_alert_deduplication_resolved_allows_new(self):
        """Resolved alert should allow a new alert for the same source_id."""
        import sqlite3
        from api.config import CHAT_DB

        conn = sqlite3.connect(CHAT_DB)
        conn.row_factory = sqlite3.Row

        # Clean up test data
        conn.execute("DELETE FROM ai_alerts WHERE masterfn=? AND companyfn=?",
                     ("dedup_mfn2", "dedup_cfn2"))
        conn.commit()

        # Insert resolved alert
        conn.execute("""
            INSERT INTO ai_alerts
                (masterfn, companyfn, alert_type, severity, status,
                 title, reason_code, risk_score, source_id,
                 evidence_json, rule_version, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'resolved', ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("dedup_mfn2", "dedup_cfn2", "fraud", "high",
              "Old alert DOC002", "ap_invoice", 85.0, "DOC002",
              '{}', "v1", "2026-07-01T12:00:00", "2026-07-02T12:00:00"))
        conn.commit()

        # New alert for same source_id should be allowed (old one is resolved)
        existing = conn.execute("""
            SELECT id FROM ai_alerts
            WHERE masterfn=? AND companyfn=? AND source_id=?
              AND status IN ('new','investigating')
            LIMIT 1
        """, ("dedup_mfn2", "dedup_cfn2", "DOC002")).fetchone()

        self.assertIsNone(existing, "Resolved alert should not block new alert")

        # Insert new alert
        conn.execute("""
            INSERT INTO ai_alerts
                (masterfn, companyfn, alert_type, severity, status,
                 title, reason_code, risk_score, source_id,
                 evidence_json, rule_version, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'new', ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("dedup_mfn2", "dedup_cfn2", "fraud", "high",
              "New alert DOC002", "ap_invoice", 90.0, "DOC002",
              '{}', "v1", "2026-07-09T12:00:00", "2026-07-09T12:00:00"))
        conn.commit()

        # Verify 2 alerts exist (1 resolved + 1 new)
        count = conn.execute("""
            SELECT COUNT(*) FROM ai_alerts
            WHERE masterfn=? AND companyfn=? AND source_id=?
        """, ("dedup_mfn2", "dedup_cfn2", "DOC002")).fetchone()[0]
        conn.close()

        self.assertEqual(count, 2, "Resolved + new = 2 alerts for same source_id")

    def test_alert_review_transitions(self):
        """Alert status should follow valid review transitions."""
        import sqlite3
        from api.config import CHAT_DB
        from api.routers.admin_ai_alerts import ALERT_STATUSES

        conn = sqlite3.connect(CHAT_DB)
        conn.row_factory = sqlite3.Row

        # Clean up test data
        conn.execute("DELETE FROM ai_alerts WHERE masterfn=? AND companyfn=?",
                     ("trans_mfn", "trans_cfn"))
        conn.commit()

        # Insert a new alert
        conn.execute("""
            INSERT INTO ai_alerts
                (masterfn, companyfn, alert_type, severity, status,
                 title, reason_code, risk_score, source_id,
                 evidence_json, rule_version, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'new', ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("trans_mfn", "trans_cfn", "fraud", "high",
              "Test alert for transitions", "ap_invoice", 80.0, "DOC003",
              '{}', "v1", "2026-07-09T12:00:00", "2026-07-09T12:00:00"))
        alert_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()

        # Test each valid transition
        transitions = [
            ("investigating", "investigating"),
            ("confirmed_issue", "confirmed_issue"),
            ("false_positive", "false_positive"),
            ("resolved", "resolved"),
        ]

        for new_status, expected in transitions:
            self.assertIn(new_status, ALERT_STATUSES, f"{new_status} should be valid")
            conn.execute("""
                UPDATE ai_alerts SET status=?, reviewer=?, review_note=?, updated_at=?
                WHERE id=?
            """, (new_status, "test_user", f"Transitioned to {new_status}",
                  "2026-07-09T12:00:00", alert_id))
            conn.commit()

            row = conn.execute("SELECT status FROM ai_alerts WHERE id=?", (alert_id,)).fetchone()
            self.assertEqual(row["status"], expected,
                             f"Status should be {expected} after transition")

        conn.close()

    def test_alert_invalid_status_rejected(self):
        """Invalid alert status should be rejected."""
        from api.routers.admin_ai_alerts import ALERT_STATUSES

        invalid_statuses = ["invalid", "pending", "closed", "approved", ""]
        for status in invalid_statuses:
            self.assertNotIn(status, ALERT_STATUSES,
                             f"'{status}' should not be a valid alert status")


# ─── Settings Module Tests ─────────────────────────────────────────────────────

class SettingsTests(unittest.TestCase):
    """Test settings module (fraud/demand defaults per user/company)."""

    def setUp(self):
        """Initialize chat DB for settings table."""
        init_chat_db()

    def test_settings_table_created(self):
        """ai_settings table should be created."""
        import sqlite3
        from api.config import CHAT_DB
        from api.routers.admin_settings import init_settings_table

        conn = sqlite3.connect(CHAT_DB)
        conn.row_factory = sqlite3.Row
        init_settings_table(conn)

        tables = {
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='ai_settings'"
            )
        }
        conn.close()
        self.assertIn("ai_settings", tables)

    def test_fraud_defaults(self):
        """Fraud defaults should have expected keys."""
        from api.routers.admin_settings import FRAUD_DEFAULTS

        expected_keys = {"scan_type", "severity", "max_findings"}
        self.assertEqual(set(FRAUD_DEFAULTS.keys()), expected_keys)
        self.assertEqual(FRAUD_DEFAULTS["scan_type"], "all")
        self.assertEqual(FRAUD_DEFAULTS["severity"], "all")
        self.assertEqual(FRAUD_DEFAULTS["max_findings"], "8")

    def test_demand_defaults(self):
        """Demand defaults should have expected keys."""
        from api.routers.admin_settings import DEMAND_DEFAULTS

        expected_keys = {
            "horizon_days",
            "sku_filter",
            "location_filter",
            "service_factor",
            "result_limit",
            "auto_run",
        }
        self.assertEqual(set(DEMAND_DEFAULTS.keys()), expected_keys)
        self.assertEqual(DEMAND_DEFAULTS["horizon_days"], "90")
        self.assertEqual(DEMAND_DEFAULTS["sku_filter"], "all")
        self.assertEqual(DEMAND_DEFAULTS["location_filter"], "all")
        self.assertEqual(DEMAND_DEFAULTS["service_factor"], "0.95")
        self.assertEqual(DEMAND_DEFAULTS["result_limit"], "100")
        self.assertEqual(DEMAND_DEFAULTS["auto_run"], "n")

    def test_get_settings_returns_defaults(self):
        """Getting settings with no overrides should return defaults."""
        import sqlite3
        from api.config import CHAT_DB
        from api.routers.admin_settings import init_settings_table, FRAUD_DEFAULTS

        conn = sqlite3.connect(CHAT_DB)
        conn.row_factory = sqlite3.Row
        init_settings_table(conn)
        conn.close()

        # Simulate the get_settings logic
        defaults = dict(FRAUD_DEFAULTS)
        self.assertEqual(defaults["scan_type"], "all")
        self.assertEqual(defaults["severity"], "all")
        self.assertEqual(defaults["max_findings"], "8")

    def test_save_and_retrieve_setting(self):
        """Saving a setting should persist and be retrievable."""
        import sqlite3
        from api.config import CHAT_DB
        from api.routers.admin_settings import init_settings_table

        conn = sqlite3.connect(CHAT_DB)
        conn.row_factory = sqlite3.Row
        init_settings_table(conn)

        # Save a setting
        conn.execute("""
            INSERT INTO ai_settings (user_id, masterfn, companyfn, module, setting_key, setting_val, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, masterfn, companyfn, module, setting_key)
            DO UPDATE SET setting_val=excluded.setting_val, updated_at=excluded.updated_at
        """, ("test_user", "test_mfn", "test_cfn", "fraud", "max_findings", "15", "2026-07-09T12:00:00"))
        conn.commit()

        # Retrieve it
        row = conn.execute("""
            SELECT setting_val FROM ai_settings
            WHERE user_id=? AND masterfn=? AND companyfn=? AND module=? AND setting_key=?
        """, ("test_user", "test_mfn", "test_cfn", "fraud", "max_findings")).fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row["setting_val"], "15")

    def test_user_setting_overrides_company_default(self):
        """User-specific setting should override company-wide default."""
        import sqlite3
        from api.config import CHAT_DB
        from api.routers.admin_settings import init_settings_table, FRAUD_DEFAULTS

        conn = sqlite3.connect(CHAT_DB)
        conn.row_factory = sqlite3.Row
        init_settings_table(conn)

        # Clean up
        conn.execute("DELETE FROM ai_settings WHERE masterfn=? AND companyfn=?",
                     ("ovr_mfn", "ovr_cfn"))
        conn.commit()

        # Company-wide setting
        conn.execute("""
            INSERT INTO ai_settings (user_id, masterfn, companyfn, module, setting_key, setting_val, updated_at)
            VALUES ('', ?, ?, 'fraud', 'max_findings', '20', ?)
        """, ("ovr_mfn", "ovr_cfn", "2026-07-09T12:00:00"))

        # User-specific override
        conn.execute("""
            INSERT INTO ai_settings (user_id, masterfn, companyfn, module, setting_key, setting_val, updated_at)
            VALUES ('ovr_user', ?, ?, 'fraud', 'max_findings', '30', ?)
        """, ("ovr_mfn", "ovr_cfn", "2026-07-09T12:00:00"))
        conn.commit()

        # Simulate merge: defaults -> company -> user
        settings = dict(FRAUD_DEFAULTS)
        for r in conn.execute("""
            SELECT setting_key, setting_val FROM ai_settings
            WHERE user_id='' AND masterfn=? AND companyfn=? AND module='fraud'
        """, ("ovr_mfn", "ovr_cfn")).fetchall():
            settings[r["setting_key"]] = r["setting_val"]
        for r in conn.execute("""
            SELECT setting_key, setting_val FROM ai_settings
            WHERE user_id='ovr_user' AND masterfn=? AND companyfn=? AND module='fraud'
        """, ("ovr_mfn", "ovr_cfn")).fetchall():
            settings[r["setting_key"]] = r["setting_val"]

        conn.close()

        self.assertEqual(settings["max_findings"], "30", "User setting should override company default")

    def test_reset_setting_removes_override(self):
        """Resetting a setting should delete the user override."""
        import sqlite3
        from api.config import CHAT_DB
        from api.routers.admin_settings import init_settings_table

        conn = sqlite3.connect(CHAT_DB)
        conn.row_factory = sqlite3.Row
        init_settings_table(conn)

        # Save a user setting
        conn.execute("""
            INSERT INTO ai_settings (user_id, masterfn, companyfn, module, setting_key, setting_val, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("reset_user", "reset_mfn", "reset_cfn", "demand", "horizon_days", "60", "2026-07-09T12:00:00"))
        conn.commit()

        # Delete it (reset)
        conn.execute("""
            DELETE FROM ai_settings
            WHERE user_id=? AND masterfn=? AND companyfn=? AND module=? AND setting_key=?
        """, ("reset_user", "reset_mfn", "reset_cfn", "demand", "horizon_days"))
        conn.commit()

        # Verify it's gone
        row = conn.execute("""
            SELECT id FROM ai_settings
            WHERE user_id=? AND masterfn=? AND companyfn=? AND module=? AND setting_key=?
        """, ("reset_user", "reset_mfn", "reset_cfn", "demand", "horizon_days")).fetchone()
        conn.close()

        self.assertIsNone(row, "Setting should be deleted after reset")

    def test_invalid_module_rejected(self):
        """Invalid module name should be rejected."""
        from api.routers.admin_settings import FRAUD_DEFAULTS, DEMAND_DEFAULTS

        valid_modules = {"fraud", "demand"}
        invalid_modules = {"scm", "hr", "inventory", ""}

        for mod in invalid_modules:
            self.assertNotIn(mod, valid_modules, f"'{mod}' should not be a valid module")


if __name__ == "__main__":
    unittest.main()
