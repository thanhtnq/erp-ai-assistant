import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from api.semantic import store
from api.semantic.retrieval import resolve_semantic_report, semantic_context_block
from api.semantic.validator import SemanticValidationError, load_and_validate
from api.search import detect_intent


FIXTURES = Path("tests/fixtures/semantic")


class SemanticMetadataValidationTests(unittest.TestCase):
    def test_json_metadata_validates(self):
        payload = load_and_validate(FIXTURES / "sales_metadata.json", expected_module="sales")
        self.assertEqual(len(payload["report_catalog"]), 2)
        self.assertEqual(payload["report_catalog"][0]["report_id"], "SAL-SO-LIST")
        self.assertEqual(payload["report_catalog"][0]["default_filters"]["tag_table_usage"], "sal_soe")

    def test_xlsx_metadata_validates(self):
        payload = load_and_validate(FIXTURES / "sales_metadata.xlsx", expected_module="sales")
        self.assertEqual(len(payload["report_catalog"]), 2)
        self.assertTrue(any(q["user_question"] == "list sales order in 7/2026" for q in payload["sample_questions"]))

    def test_phase1_xlsx_covers_sales_foundation(self):
        payload = load_and_validate(FIXTURES / "sales_phase1_metadata.xlsx", expected_module="sales")
        self.assertEqual(len(payload["report_catalog"]), 10)
        self.assertGreaterEqual(len(payload["field_mapping"]), 30)
        self.assertGreaterEqual(len(payload["sales_cycle"]), 6)
        self.assertTrue(any(r["field"] == "companyfn" for r in payload["mandatory_fields"]))
        self.assertTrue(any(r["component"] == "SQL Validator" for r in payload["engine_components"]))
        self.assertTrue(any(r["report_id"] == "SAL-SO-LIST" for r in payload["sql_templates"]))

    def test_invalid_xlsx_missing_report_id_fails(self):
        with self.assertRaises(SemanticValidationError):
            load_and_validate(FIXTURES / "invalid_missing_report_id.xlsx", expected_module="sales")


class SemanticStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "semantic.db"

        def get_conn():
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn

        self.get_conn = get_conn
        self.patch = patch("api.semantic.store.get_knowledge_conn", get_conn)
        self.patch.start()
        store.init_semantic_db()

    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()

    def test_register_and_replace_metadata_for_file(self):
        scope = store.normalize_scope("global")
        file_id = store.register_semantic_file(str((FIXTURES / "sales_metadata.json").resolve()), scope, "sales")
        file_row = store.get_semantic_file(file_id)
        payload = load_and_validate(FIXTURES / "sales_metadata.json", expected_module="sales")
        count = store.replace_metadata_for_file(file_id, payload, file_row)
        store.update_file_status(file_id, "done", reports_parsed=count)

        self.assertEqual(count, 2)
        reports = store.list_reports(module="sales")
        self.assertEqual(len(reports), 2)
        self.assertEqual(reports[0]["default_filters"]["tag_table_usage"], "sal_soe")
        files = store.list_semantic_files(module="sales")
        self.assertEqual(files["total"], 1)
        self.assertEqual(files["items"][0]["status"], "done")

    def test_phase1_metadata_persists_foundation_sections(self):
        scope = store.normalize_scope("global")
        file_id = store.register_semantic_file(str((FIXTURES / "sales_phase1_metadata.json").resolve()), scope, "sales")
        file_row = store.get_semantic_file(file_id)
        payload = load_and_validate(FIXTURES / "sales_phase1_metadata.json", expected_module="sales")
        count = store.replace_metadata_for_file(file_id, payload, file_row)

        conn = self.get_conn()
        try:
            self.assertEqual(count, 10)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM semantic_field_mappings WHERE file_id=?", (file_id,)).fetchone()[0], 37)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM semantic_sales_cycle WHERE file_id=?", (file_id,)).fetchone()[0], 8)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM semantic_sql_templates WHERE file_id=?", (file_id,)).fetchone()[0], 4)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM semantic_permissions WHERE file_id=?", (file_id,)).fetchone()[0], 4)
        finally:
            conn.close()

    def test_phase1_xlsx_persists_blank_global_business_rules(self):
        scope = store.normalize_scope("global")
        file_id = store.register_semantic_file(str((FIXTURES / "sales_phase1_metadata.xlsx").resolve()), scope, "sales")
        file_row = store.get_semantic_file(file_id)
        payload = load_and_validate(FIXTURES / "sales_phase1_metadata.xlsx", expected_module="sales")
        count = store.replace_metadata_for_file(file_id, payload, file_row)

        conn = self.get_conn()
        try:
            self.assertEqual(count, 10)
            self.assertEqual(conn.execute(
                "SELECT COUNT(*) FROM semantic_business_rules WHERE file_id=? AND report_id=''",
                (file_id,),
            ).fetchone()[0], 6)
        finally:
            conn.close()

    def test_company_scope_requires_company_code(self):
        with self.assertRaises(ValueError):
            store.normalize_scope("company")

    def test_company_and_global_reports_can_coexist(self):
        payload = load_and_validate(FIXTURES / "sales_metadata.json", expected_module="sales")

        global_id = store.register_semantic_file(str((FIXTURES / "sales_metadata.json").resolve()), store.normalize_scope("global"), "sales")
        store.replace_metadata_for_file(global_id, payload, store.get_semantic_file(global_id))

        company_scope = store.normalize_scope("company", "ABC", "m1", "c1")
        company_id = store.register_semantic_file(str((FIXTURES / "sales_metadata_company_override.xlsx").resolve()), company_scope, "sales")
        company_payload = load_and_validate(FIXTURES / "sales_metadata_company_override.xlsx", expected_module="sales")
        store.replace_metadata_for_file(company_id, company_payload, store.get_semantic_file(company_id))

        reports = store.list_reports(module="sales")
        self.assertEqual(len(reports), 4)
        company_reports = store.list_reports(module="sales", scope_type="company", company_code="ABC")
        self.assertEqual(len(company_reports), 2)
        self.assertEqual(company_reports[0]["company_code"], "ABC")

    def test_runtime_resolver_matches_list_sales_order_query(self):
        payload = load_and_validate(FIXTURES / "sales_metadata.json", expected_module="sales")
        file_id = store.register_semantic_file(str((FIXTURES / "sales_metadata.json").resolve()), store.normalize_scope("global"), "sales")
        store.replace_metadata_for_file(file_id, payload, store.get_semantic_file(file_id))

        self.assertEqual(detect_intent("list sales order in 7/2026"), "data_query")
        match = resolve_semantic_report("list sales order in 7/2026")
        self.assertTrue(match["matched"])
        self.assertEqual(match["report_id"], "SAL-SO-LIST")
        self.assertEqual(match["tool_name"], "list_sales_documents")
        self.assertEqual(match["default_filters"]["tag_table_usage"], "sal_soe")
        self.assertIn("Selected Semantic Report", semantic_context_block(match))

        changed_month = resolve_semantic_report("list sales order in 6/2026")
        self.assertTrue(changed_month["matched"])
        self.assertEqual(changed_month["report_id"], "SAL-SO-LIST")
        self.assertEqual(detect_intent("sales orders june 2026"), "data_query")

    def test_phase1_resolver_handles_semantic_variants(self):
        payload = load_and_validate(FIXTURES / "sales_phase1_metadata.json", expected_module="sales")
        file_id = store.register_semantic_file(str((FIXTURES / "sales_phase1_metadata.json").resolve()), store.normalize_scope("global"), "sales")
        store.replace_metadata_for_file(file_id, payload, store.get_semantic_file(file_id))

        cases = {
            "which document numbers are customer orders in 7/2026": "SAL-SO-LIST",
            "show me booking in 7/2026": "SAL-SO-LIST",
            "billing in july 2026": "SAL-INV-LIST",
            "biggest customer orders last july": "SAL-SO-TOP",
        }
        for question, report_id in cases.items():
            with self.subTest(question=question):
                self.assertEqual(detect_intent(question), "data_query")
                match = resolve_semantic_report(question)
                self.assertTrue(match["matched"])
                self.assertEqual(match["report_id"], report_id)

    def test_learned_query_is_verified_by_feedback_and_reused(self):
        payload = load_and_validate(FIXTURES / "sales_metadata.json", expected_module="sales")
        file_id = store.register_semantic_file(str((FIXTURES / "sales_metadata.json").resolve()), store.normalize_scope("global"), "sales")
        store.replace_metadata_for_file(file_id, payload, store.get_semantic_file(file_id))

        question = "list sales order in 6/2026"
        match = resolve_semantic_report(question)
        learned_id = store.save_learned_query_candidate(
            question_text=question,
            normalized_question="list sales order in {month}",
            semantic_match=match,
        )
        self.assertIsNotNone(learned_id)
        learned = store.list_learned_queries(module="sales")
        self.assertEqual(learned[0]["verified"], 0)

        updated = store.record_learned_feedback(question, "up")
        self.assertEqual(updated, 1)
        verified = store.list_learned_queries(module="sales", verified=True)
        self.assertEqual(len(verified), 1)

        reused = resolve_semantic_report("list sales order in 8/2026")
        self.assertTrue(reused["matched"])
        self.assertEqual(reused["source"], "learned_query")
        self.assertEqual(reused["report_id"], "SAL-SO-LIST")


if __name__ == "__main__":
    unittest.main()
