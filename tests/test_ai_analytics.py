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


if __name__ == "__main__":
    unittest.main()
