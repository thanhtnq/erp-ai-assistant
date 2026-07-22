import json
from pathlib import Path

from openpyxl import Workbook


ROOT = Path(__file__).resolve().parent.parent
OUT_DIRS = [
    ROOT / "tests" / "fixtures" / "semantic",
    ROOT / "data" / "semantic" / "samples",
]


def j(value):
    return json.dumps(value, ensure_ascii=False)


REPORTS = [
    ("SAL-QUO-LIST", "Sales Quotation Listing", "list", "sal_quo", "list_sales_documents", "quotation, quote, sales quotation"),
    ("SAL-SO-LIST", "Sales Order Listing", "list", "sal_soe", "list_sales_documents", "sales order, so, customer order"),
    ("SAL-SOC-LIST", "Sales Order Confirmation Listing", "list", "sal_soc", "list_sales_documents", "sales order confirmation, so confirmation"),
    ("SAL-DO-LIST", "Delivery Order Listing", "list", "stk_do", "list_sales_documents", "delivery order, do, shipment"),
    ("SAL-DOC-LIST", "Delivery Confirmation Listing", "list", "stk_doc", "list_sales_documents", "delivery confirmation, confirmed delivery"),
    ("SAL-INV-LIST", "Sales Invoice Listing", "list", "sal_inv", "list_sales_documents", "invoice, sales invoice, billing"),
    ("SAL-CN-LIST", "Sales Credit Note Listing", "list", "sal_cn", "list_sales_documents", "credit note, sales credit note"),
    ("SAL-DN-LIST", "Sales Debit Note Listing", "list", "sal_dn", "list_sales_documents", "debit note, sales debit note"),
    ("SAL-SO-TOP", "Top Sales Orders", "ranking", "sal_soe", "aggregate_sales_documents", "top sales order, biggest sales order, highest amount"),
    ("SAL-SALES-BY-CUSTOMER", "Sales Amount by Customer", "aggregate", "sal_inv", "aggregate_sales_documents", "sales by customer, customer revenue"),
]

COMMON_OUTPUTS = [
    ("dnum_auto", "Document No.", "string"),
    ("date_trans", "Document Date", "date"),
    ("party_code", "Customer Code", "string"),
    ("party_desc", "Customer", "string"),
    ("staff_desc", "Salesperson", "string"),
    ("curr_short_forex", "Currency", "string"),
    ("amount_forex", "Amount", "decimal"),
    ("amount_local", "Amount Local", "decimal"),
]

COMMON_FILTERS = [
    ("date_from", "Date From", "date", ">=", "yes", ""),
    ("date_to", "Date To", "date", "<", "yes", ""),
    ("party_code", "Customer Code", "string", "=", "no", ""),
    ("party_desc", "Customer Name", "string", "contains", "no", ""),
    ("staff_code", "Salesperson Code", "string", "=", "no", ""),
    ("location_code", "Location", "string", "=", "no", ""),
]

HEADER_FIELDS = [
    ("scm_sal_main", "masterfn", "security", "Master Scope", "string", "tenant, master", "Tenant/master database scope; never display."),
    ("scm_sal_main", "companyfn", "security", "Company Scope", "string", "company", "Company database scope; always required."),
    ("scm_sal_main", "uniquenum_pri", "key", "Header Key", "number", "internal id", "Header primary key; never display."),
    ("scm_sal_main", "tag_table_usage", "document_type", "Document Type Tag", "string", "doc type, type", "ERP document tag such as sal_soe or sal_inv."),
    ("scm_sal_main", "dnum_auto", "header", "Document No.", "string", "document number, so no, invoice no", "Human-facing document number."),
    ("scm_sal_main", "dnum_reference", "header", "Reference No.", "string", "reference, customer reference", "External or linked reference number."),
    ("scm_sal_main", "date_trans", "header", "Document Date", "date", "date, transaction date", "Main transaction date used for month filters."),
    ("scm_sal_main", "date_due", "header", "Due Date", "date", "payment due date", "Due date for invoice/payment tracking."),
    ("scm_sal_main", "party_code", "header", "Customer Code", "string", "customer code, debtor code", "Customer account code."),
    ("scm_sal_main", "party_desc", "header", "Customer", "string", "customer, debtor, client", "Customer display name."),
    ("scm_sal_main", "party_unique", "key", "Customer Key", "number", "customer id", "Internal customer key; never display."),
    ("scm_sal_main", "staff_code", "header", "Salesperson Code", "string", "sales rep code", "Salesperson code."),
    ("scm_sal_main", "staff_desc", "header", "Salesperson", "string", "sales rep, staff", "Salesperson display name."),
    ("scm_sal_main", "location_code", "header", "Location", "string", "branch, warehouse", "Location or branch code."),
    ("scm_sal_main", "deptunit_code", "header", "Department Code", "string", "department", "Department/unit code."),
    ("scm_sal_main", "deptunit_desc", "header", "Department", "string", "department name", "Department/unit name."),
    ("scm_sal_main", "creditterm_desc", "header", "Payment Terms", "string", "credit term", "Payment term label."),
    ("scm_sal_main", "delivtype_desc", "header", "Delivery Type", "string", "delivery method", "Delivery type label."),
    ("scm_sal_main", "sendby_desc", "header", "Ship Method", "string", "send by, shipping method", "Shipping method label."),
    ("scm_sal_main", "curr_short_forex", "header", "Currency", "string", "currency", "Foreign currency code."),
    ("scm_sal_main", "amount_forex", "measure", "Amount", "decimal", "sales amount, document amount", "Document amount in transaction currency."),
    ("scm_sal_main", "amount_local", "measure", "Amount Local", "decimal", "local amount", "Document amount in local currency."),
    ("scm_sal_main", "tag_void_yn", "status", "Void Flag", "string", "void, cancelled", "Filter n for active documents."),
    ("scm_sal_main", "tag_deleted_yn", "status", "Deleted Flag", "string", "deleted", "Filter n when the column is available."),
    ("scm_sal_main", "tag_wflow_app_yn", "status", "Workflow Approved Flag", "string", "approved, posted", "Approved documents use y when required by the report."),
]

DETAIL_FIELDS = [
    ("scm_sal_data", "uniquenum_pri", "key", "Header Key", "number", "header id", "Links detail row to header."),
    ("scm_sal_data", "masterfn", "security", "Master Scope", "string", "tenant, master", "Tenant/master scope."),
    ("scm_sal_data", "companyfn", "security", "Company Scope", "string", "company", "Company scope."),
    ("scm_sal_data", "tag_table_usage", "document_type", "Document Type Tag", "string", "doc type", "Must match header document tag."),
    ("scm_sal_data", "stkcode_code", "detail", "Item Code", "string", "product code, stock code, sku", "Item/product code."),
    ("scm_sal_data", "stkcode_desc", "detail", "Item Description", "string", "product, item", "Item/product description."),
    ("scm_sal_data", "stkcate_desc", "detail", "Item Category", "string", "category", "Stock category."),
    ("scm_sal_data", "brand_desc", "detail", "Brand", "string", "brand", "Brand description."),
    ("scm_sal_data", "qnty_total", "measure", "Quantity", "decimal", "qty, quantity", "Total quantity."),
    ("scm_sal_data", "price_unitrate_local", "measure", "Unit Price Local", "decimal", "unit price", "Unit price in local currency."),
    ("scm_sal_data", "amount_local", "measure", "Line Amount Local", "decimal", "line amount", "Line amount in local currency."),
    ("scm_sal_data", "amount_forex", "measure", "Line Amount", "decimal", "line foreign amount", "Line amount in transaction currency."),
]

SALES_CYCLE = [
    (1, "Sales Quotation", "sal_quo", "scm_sal_main", "Sales Order", "Offer prepared for customer"),
    (2, "Sales Order", "sal_soe", "scm_sal_main", "Sales Order Confirmation", "Customer order captured"),
    (3, "Sales Order Confirmation", "sal_soc", "scm_sal_main", "Delivery Order", "Order approved/confirmed"),
    (4, "Delivery Order", "stk_do", "scm_sal_main", "Delivery Confirmation", "Goods prepared for delivery"),
    (5, "Delivery Confirmation", "stk_doc", "scm_sal_main", "Sales Invoice", "Delivery confirmed"),
    (6, "Sales Invoice", "sal_inv", "scm_sal_main", "Credit/Debit Note", "Customer billed"),
    (7, "Sales Credit Note", "sal_cn", "scm_sal_main", "", "Invoice adjustment reducing receivable"),
    (8, "Sales Debit Note", "sal_dn", "scm_sal_main", "", "Invoice adjustment increasing receivable"),
]

ENGINE_COMPONENTS = [
    ("Prompt Parser", "foundation", "Detect sales intent, date ranges, entity names, list/count/top/aggregate wording.", "api.search.detect_intent + semantic retrieval"),
    ("Planner", "foundation", "Select report, tool, required filters and allowed output columns.", "api.semantic.retrieval.resolve_semantic_report"),
    ("Skill Loader", "available", "Load Sales skill/tool contracts from skills/globe3-* modules.", "skills/server.js"),
    ("SQL Generator", "foundation", "Generate SELECT-only queries from selected skill/report templates.", "DATA_QUERY_SYSTEM and direct sales tools"),
    ("SQL Validator", "foundation", "Reject unsafe SQL and hidden internal output columns.", "api.semantic.validator + api.llm guardrails"),
    ("Permission Checker", "foundation", "Enforce masterfn/companyfn/company scope and row limits.", "semantic_permissions metadata"),
    ("SQL Executor", "available", "Execute approved read-only sales data queries.", "skills/_shared/orm-fetch.js"),
    ("Response Formatter", "available", "Render business labels and concise chat/table result.", "api.llm response rules"),
    ("Logging Framework", "available", "Log ingest runs, learned questions and user feedback.", "semantic_ingest_runs + semantic_learned_queries"),
]


def build_payload():
    payload = {section: [] for section in [
        "report_catalog", "output_mapping", "filter_mapping", "table_mapping", "field_mapping",
        "child_tabs", "join_relationship", "mandatory_fields", "business_synonym",
        "business_rules", "sales_cycle", "sql_templates", "permissions",
        "sample_questions", "engine_components",
    ]}

    for report_id, name, intent, tag, tool, keywords in REPORTS:
        payload["report_catalog"].append({
            "report_id": report_id,
            "module": "sales",
            "report_name": name,
            "intent_type": intent,
            "description": f"{name} for the Sales cycle using ERP document tag {tag}.",
            "business_keywords": keywords,
            "tool_name": tool,
            "default_filters": {"tag_table_usage": tag, "tag_void_yn": "n"},
            "required_filters": ["date_from", "date_to"],
        })
        for order, (column, label, dtype) in enumerate(COMMON_OUTPUTS, 1):
            payload["output_mapping"].append({
                "report_id": report_id, "query_column": column, "output_name": label,
                "data_type": dtype, "display_order": order,
            })
        for column, label, dtype, operator, required, default in COMMON_FILTERS:
            payload["filter_mapping"].append({
                "report_id": report_id, "filter_column": column, "ui_name": label,
                "data_type": dtype, "operator": operator, "required": required,
                "default_value": default,
            })

    payload["table_mapping"] = [
        {"module": "sales", "table": "scm_sal_main", "table_role": "header", "business_label": "Sales Document Header", "description": "Shared header table for quotation, sales order, invoice and related sales documents."},
        {"module": "sales", "table": "scm_sal_data", "table_role": "detail", "business_label": "Sales Document Lines", "description": "Line items for sales documents."},
        {"module": "sales", "table": "mst_party", "table_role": "master", "business_label": "Customer Master", "description": "Customer account master data."},
        {"module": "sales", "table": "stk_code_main", "table_role": "master", "business_label": "Item Master", "description": "Item/product master data."},
    ]
    payload["field_mapping"] = [
        {"module": "sales", "table": table, "field": field, "field_role": role, "business_label": label, "data_type": dtype, "synonyms": syn, "description": desc}
        for table, field, role, label, dtype, syn, desc in HEADER_FIELDS + DETAIL_FIELDS
    ]
    payload["child_tabs"] = [
        {"module": "sales", "parent_document": doc, "child_tab": "Detail Items", "child_table": "scm_sal_data", "join_condition": "scm_sal_data.uniquenum_pri = scm_sal_main.uniquenum_pri AND scm_sal_data.tag_table_usage = scm_sal_main.tag_table_usage AND scm_sal_data.companyfn = scm_sal_main.companyfn", "business_meaning": "Shows products/services sold on the document."}
        for _, doc, _, _, _, _ in SALES_CYCLE
    ]
    payload["join_relationship"] = [
        {"parent_table": "scm_sal_main", "child_table": "scm_sal_data", "join_condition": "d.uniquenum_pri = m.uniquenum_pri AND d.tag_table_usage = m.tag_table_usage AND d.companyfn = m.companyfn", "join_type": "inner", "business_meaning": "Header to item lines."},
        {"parent_table": "scm_sal_main", "child_table": "mst_party", "join_condition": "mst_party.uniquenum_uniq = m.party_unique AND mst_party.companyfn = m.companyfn", "join_type": "left", "business_meaning": "Header to customer master."},
        {"parent_table": "scm_sal_data", "child_table": "stk_code_main", "join_condition": "stk_code_main.stkcode_code = d.stkcode_code AND stk_code_main.companyfn = d.companyfn", "join_type": "left", "business_meaning": "Line item to product master."},
    ]
    payload["mandatory_fields"] = [
        {"module": "sales", "table": "scm_sal_main", "field": "masterfn", "rule": "must come from authenticated session", "default_value": "", "applies_to": "all reports", "description": "Prevents cross-tenant data access."},
        {"module": "sales", "table": "scm_sal_main", "field": "companyfn", "rule": "must come from authenticated session", "default_value": "", "applies_to": "all reports", "description": "Prevents cross-company data access."},
        {"module": "sales", "table": "scm_sal_main", "field": "tag_void_yn", "rule": "active documents only", "default_value": "n", "applies_to": "default list/count/top reports", "description": "Exclude void/cancelled documents."},
        {"module": "sales", "table": "scm_sal_main", "field": "tag_deleted_yn", "rule": "not deleted when column is available", "default_value": "n", "applies_to": "all reports", "description": "Exclude soft-deleted rows."},
        {"module": "sales", "table": "scm_sal_main", "field": "tag_wflow_app_yn", "rule": "approved reports filter to y", "default_value": "y", "applies_to": "approved/posted reports", "description": "Represents workflow-approved business state."},
        {"module": "sales", "table": "scm_sal_main", "field": "tag_table_usage", "rule": "must be fixed by selected report", "default_value": "from report_catalog.default_filters", "applies_to": "all reports", "description": "Separates SO, invoice, quotation and delivery documents."},
        {"module": "sales", "table": "scm_sal_main", "field": "date_trans", "rule": "date range required for list queries", "default_value": "", "applies_to": "listing reports", "description": "Keeps queries bounded on large sales tables."},
    ]
    payload["business_synonym"] = [
        {"business_term": "sales order, so, customer order", "technical_term": "tag_table_usage=sal_soe", "notes": "Sales order document."},
        {"business_term": "invoice, sales invoice, billing", "technical_term": "tag_table_usage=sal_inv", "notes": "Sales invoice document."},
        {"business_term": "quotation, quote", "technical_term": "tag_table_usage=sal_quo", "notes": "Sales quotation document."},
        {"business_term": "delivery order, do, shipment", "technical_term": "tag_table_usage=stk_do", "notes": "Delivery order document."},
        {"business_term": "customer, debtor, client", "technical_term": "party_code, party_desc, party_unique", "notes": "Customer fields."},
        {"business_term": "product, item, stock, sku", "technical_term": "stkcode_code, stkcode_desc", "notes": "Item fields."},
        {"business_term": "approved, posted", "technical_term": "tag_wflow_app_yn=y", "notes": "Approved workflow state."},
        {"business_term": "draft, unapproved", "technical_term": "tag_wflow_app_yn<>y", "notes": "Draft workflow state."},
        {"business_term": "cancelled, void", "technical_term": "tag_void_yn=y", "notes": "Voided document state."},
    ]
    payload["business_rules"] = [
        {"report_id": "", "rule_name": "Company Scope", "rule_expression": "Always filter by session masterfn and companyfn.", "description": "Prevents cross-company leakage."},
        {"report_id": "", "rule_name": "Active Document Default", "rule_expression": "tag_void_yn = 'n'", "description": "Default report behavior excludes void documents."},
        {"report_id": "", "rule_name": "Approved Document", "rule_expression": "tag_wflow_app_yn = 'y'", "description": "Used when the user asks for approved/posted documents."},
        {"report_id": "", "rule_name": "Draft Document", "rule_expression": "tag_wflow_app_yn is empty or not equal to 'y'", "description": "Used when the user asks for draft/unapproved documents."},
        {"report_id": "", "rule_name": "Hidden Internal Fields", "rule_expression": "Do not render masterfn, companyfn, uniquenum_pri, party_unique, staff_unique.", "description": "Internal security/key fields are query-only."},
        {"report_id": "", "rule_name": "Bounded Listing", "rule_expression": "List queries require date range and max limit.", "description": "Protects large ERP tables."},
    ]
    payload["sales_cycle"] = [
        {"module": "sales", "sequence": seq, "document_name": doc, "tag_table_usage": tag, "source_table": table, "next_document": nxt, "business_state": state}
        for seq, doc, tag, table, nxt, state in SALES_CYCLE
    ]
    payload["sql_templates"] = [
        {"report_id": "SAL-SO-LIST", "sql_template": "SELECT dnum_auto, date_trans, party_code, party_desc, staff_desc, curr_short_forex, amount_forex, amount_local FROM scm_sal_main WHERE masterfn = :masterfn AND companyfn = :companyfn AND tag_table_usage = 'sal_soe' AND tag_void_yn = 'n' AND date_trans >= :date_from AND date_trans < :date_to ORDER BY date_trans DESC LIMIT :limit OFFSET :offset", "parameters": "masterfn, companyfn, date_from, date_to, limit, offset", "notes": "Basic bounded sales order listing."},
        {"report_id": "SAL-INV-LIST", "sql_template": "SELECT dnum_auto, date_trans, party_code, party_desc, staff_desc, curr_short_forex, amount_forex, amount_local FROM scm_sal_main WHERE masterfn = :masterfn AND companyfn = :companyfn AND tag_table_usage = 'sal_inv' AND tag_void_yn = 'n' AND date_trans >= :date_from AND date_trans < :date_to ORDER BY date_trans DESC LIMIT :limit OFFSET :offset", "parameters": "masterfn, companyfn, date_from, date_to, limit, offset", "notes": "Basic bounded sales invoice listing."},
        {"report_id": "SAL-SO-TOP", "sql_template": "SELECT dnum_auto, date_trans, party_code, party_desc, amount_local FROM scm_sal_main WHERE masterfn = :masterfn AND companyfn = :companyfn AND tag_table_usage = 'sal_soe' AND tag_void_yn = 'n' AND date_trans >= :date_from AND date_trans < :date_to ORDER BY amount_local DESC LIMIT :limit", "parameters": "masterfn, companyfn, date_from, date_to, limit", "notes": "Top sales orders by local amount."},
        {"report_id": "SAL-SALES-BY-CUSTOMER", "sql_template": "SELECT party_code, party_desc, SUM(amount_local) AS total_amount_local, COUNT(*) AS document_count FROM scm_sal_main WHERE masterfn = :masterfn AND companyfn = :companyfn AND tag_table_usage = 'sal_inv' AND tag_void_yn = 'n' AND date_trans >= :date_from AND date_trans < :date_to GROUP BY party_code, party_desc ORDER BY total_amount_local DESC LIMIT :limit", "parameters": "masterfn, companyfn, date_from, date_to, limit", "notes": "Sales invoice amount grouped by customer."},
    ]
    payload["permissions"] = [
        {"module": "sales", "rule_name": "Read Only", "rule_expression": "Only SELECT queries are allowed.", "description": "No write operations from chat."},
        {"module": "sales", "rule_name": "Company Boundary", "rule_expression": "masterfn and companyfn must be injected from session.", "description": "User cannot override security scope."},
        {"module": "sales", "rule_name": "Limit Rows", "rule_expression": "Default limit is 20; maximum limit is 100 unless explicitly approved.", "description": "Prevents heavy table scans."},
        {"module": "sales", "rule_name": "Hide Internal Keys", "rule_expression": "Do not expose masterfn, companyfn, uniquenum_pri, party_unique, staff_unique.", "description": "Response formatter hides technical keys."},
    ]
    payload["sample_questions"] = [
        {"report_id": "SAL-SO-LIST", "user_question": "list sales order in 7/2026"},
        {"report_id": "SAL-SO-LIST", "user_question": "show sales orders for July 2026"},
        {"report_id": "SAL-SO-LIST", "user_question": "which document numbers are sales orders in 7/2026"},
        {"report_id": "SAL-SO-TOP", "user_question": "top 10 sales order in 7/2026"},
        {"report_id": "SAL-INV-LIST", "user_question": "list sales invoices in July 2026"},
        {"report_id": "SAL-SALES-BY-CUSTOMER", "user_question": "sales amount by customer in 7/2026"},
    ]
    payload["engine_components"] = [
        {"component": c, "status": s, "responsibility": r, "implementation": i, "notes": ""}
        for c, s, r, i in ENGINE_COMPONENTS
    ]
    return payload


def write_json(path, payload):
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_xlsx(path, payload):
    wb = Workbook()
    wb.remove(wb.active)
    for section, rows in payload.items():
        ws = wb.create_sheet(section[:31])
        headers = sorted({key for row in rows for key in row.keys()})
        if not headers:
            ws.append(["note"])
            continue
        ws.append(headers)
        for row in rows:
            values = []
            for header in headers:
                value = row.get(header, "")
                if isinstance(value, (dict, list)):
                    value = j(value)
                values.append(value)
            ws.append(values)
        ws.freeze_panes = "A2"
        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            ws.column_dimensions[col[0].column_letter].width = min(max(max_len + 2, 12), 72)
    wb.save(path)


def main():
    payload = build_payload()
    for out_dir in OUT_DIRS:
        out_dir.mkdir(parents=True, exist_ok=True)
        write_json(out_dir / "sales_phase1_metadata.json", payload)
        write_xlsx(out_dir / "sales_phase1_metadata.xlsx", payload)
    print(json.dumps({
        "ok": True,
        "reports": len(payload["report_catalog"]),
        "field_mapping": len(payload["field_mapping"]),
        "sample_dirs": [str(p) for p in OUT_DIRS],
    }, indent=2))


if __name__ == "__main__":
    main()
