# Admin AI Semantic Layer Implementation Tasks

## Objective

Create a new admin page named `admin_ai_semantic_layer.cfm` that lets an admin upload ERP semantic metadata by scope, ingest it, validate it, index it, and make it available to the chatbox data-query pipeline.

This is separate from the existing document knowledge ingest. Document ingest handles manuals/procedures. Semantic ingest handles structured ERP query metadata such as reports, filters, output columns, relationships, synonyms, and sample questions.

Target workflow:

```text
Admin selects scope
-> selects business module
-> uploads Excel/JSON metadata
-> file is registered
-> admin runs ingest
-> metadata is parsed and validated
-> metadata rows and embeddings are stored
-> chatbox uses scoped semantic metadata to select report/tool/query
```

## Design Rules

- Keep existing skill folders as execution/tool units.
- Add semantic metadata as a decision layer above skills.
- Metadata is grouped by business module, not by every small skill folder.
- Scope resolution must be:
  1. company-specific metadata
  2. global metadata
- Do not reuse `/admin/documents/upload`; create semantic-specific endpoints.
- Do not store ERP transaction data in semantic metadata.
- Every uploaded file and ingest run must be auditable.

## Proposed Files

```text
cfml-examples/admin_ai_semantic_layer.cfm          [NEW]
cfml-examples/inc_ajax_ai_admin.cfm               [UPDATE]
api/routers/admin_semantic.py                     [NEW]
api/main.py                                       [UPDATE]
ingest/ingest_semantic_metadata.py                [NEW]
api/semantic/                                     [NEW]
api/semantic/store.py                             [NEW]
api/semantic/retrieval.py                         [NEW]
api/semantic/validator.py                         [NEW]
data/semantic/                                    [NEW]
tests/test_admin_semantic.py                      [NEW]
tests/fixtures/semantic/sales_metadata.xlsx       [NEW optional]
tests/fixtures/semantic/sales_metadata.json       [NEW]
```

## Phase 1 - Metadata Contract

### Task 1.1 - Define metadata workbook/JSON contract

Required sheets or JSON sections:

```text
report_catalog
output_mapping
filter_mapping
table_mapping
join_relationship
business_synonym
sample_questions
business_rules
```

Minimum required fields:

```text
report_catalog:
- report_id
- module
- report_name
- intent_type
- description
- business_keywords
- tool_name
- default_filters
- required_filters

output_mapping:
- report_id
- query_column
- output_name
- data_type
- display_order

filter_mapping:
- report_id
- filter_column
- ui_name
- data_type
- operator
- required
- default_value

business_synonym:
- module
- business_term
- technical_term
- notes

sample_questions:
- report_id
- user_question
```

Example for `list sales order in 7/2026`:

```json
{
  "report_id": "SAL-SO-LIST",
  "module": "sales",
  "report_name": "Sales Order Listing",
  "intent_type": "list",
  "tool_name": "list_sales_documents",
  "default_filters": {
    "tag_table_usage": "sal_soe",
    "tag_void_yn": "n"
  },
  "required_filters": ["date_from", "date_to"],
  "sample_questions": [
    "list sales order in 7/2026",
    "show sales orders in July 2026"
  ]
}
```

### Test Cases

- Valid Sales JSON passes schema validation.
- Valid Excel workbook with all required sheets passes schema validation.
- Missing `report_id` fails with a clear error.
- Unknown `tool_name` fails unless configured as allowed.
- Duplicate `report_id` in the same scope/module fails.
- Company-specific metadata can reuse a global `report_id` only as an override.

## Phase 2 - Database Schema

### Task 2.1 - Add semantic metadata tables

Use the knowledge SQLite DB unless there is a strong reason to create a new DB.

Suggested tables:

```sql
semantic_files
semantic_reports
semantic_output_columns
semantic_filters
semantic_tables
semantic_relationships
semantic_synonyms
semantic_sample_questions
semantic_business_rules
semantic_ingest_runs
```

Core scope columns:

```text
scope_type       global | company
company_code     nullable
masterfn         nullable for global
companyfn        nullable for global
module           sales | purchase | inventory | finance | hr | project | analytics
```

### Task 2.2 - Add indexes

Required indexes:

```text
semantic_reports(scope_type, company_code, module, report_id)
semantic_reports(module, intent_type)
semantic_sample_questions(report_id)
semantic_files(scope_type, company_code, module, status)
semantic_ingest_runs(file_id, status, created_at)
```

### Test Cases

- Tables are created idempotently.
- Same `report_id` is unique within one scope/module.
- Global and company override can coexist.
- Deleting a semantic file marks its metadata inactive or removes only that file's metadata.

## Phase 3 - Admin Semantic API

### Task 3.1 - Create router

File:

```text
api/routers/admin_semantic.py
```

Register in:

```text
api/main.py
```

Endpoints:

```text
GET    /admin/semantic/stats
GET    /admin/semantic/files
POST   /admin/semantic/upload
GET    /admin/semantic/files/{id}
POST   /admin/semantic/files/{id}/run-now
DELETE /admin/semantic/files/{id}
GET    /admin/semantic/reports
GET    /admin/semantic/reports/{report_id}
POST   /admin/semantic/validate
```

Upload form fields:

```text
file
scope_type = global | company
company_code
masterfn
companyfn
module
admin_user_id
```

Save path:

```text
data/semantic/_global/{module}/{filename}
data/semantic/clients/{company_code}/{module}/{filename}
```

### Task 3.2 - Run ingest in background

Pattern should follow `admin_documents.py`:

```text
upload -> status=pending
run-now -> status=processing
background thread -> ingest_semantic_metadata.py --file ...
success -> status=done
failure -> status=failed + error_message
```

### Test Cases

- Upload without file returns 400.
- Upload invalid extension returns 400. Allowed: `.xlsx`, `.json`.
- Upload invalid module returns 400.
- Company scope without `company_code` returns 400.
- Company scope without `masterfn/companyfn` returns 400 if company-level runtime override is required.
- Global upload writes to `data/semantic/_global/{module}`.
- Company upload writes to `data/semantic/clients/{company_code}/{module}`.
- `run-now` starts background ingest and updates status.
- Failed ingest stores readable `error_message`.
- Admin action log records upload, run-now, success, failure, delete.

## Phase 4 - Semantic Ingest Engine

### Task 4.1 - Create ingest script

File:

```text
ingest/ingest_semantic_metadata.py
```

CLI:

```text
python ingest/ingest_semantic_metadata.py --file path.xlsx --force
python ingest/ingest_semantic_metadata.py --file path.json --dry-run
```

Responsibilities:

```text
1. Read JSON or Excel.
2. Normalize sheet/section names.
3. Validate required fields.
4. Validate report -> output/filter/sample question references.
5. Validate tool_name exists in skills `/tools` result or local allowlist.
6. Store metadata rows.
7. Build searchable text documents.
8. Upsert embeddings for report definitions and sample questions.
9. Write ingest summary.
```

Searchable text example:

```text
Report: Sales Order Listing
Module: sales
Intent: list
Keywords: sales order, SO, customer order
Tool: list_sales_documents
Default filters: tag_table_usage=sal_soe, tag_void_yn=n
Sample questions: list sales order in 7/2026; show sales orders this month
```

### Test Cases

- JSON ingest creates one report, output columns, filters, synonyms, and sample questions.
- Excel ingest creates the same rows as JSON.
- Dry-run validates but does not write rows.
- Force re-ingest replaces old rows from the same file.
- Invalid cross-reference, such as output mapping with unknown `report_id`, fails.
- Invalid JSON gives clear parse error.
- Empty workbook fails.
- Embedding unavailable does not block row ingest; status should mention indexing skipped.

## Phase 5 - Admin CFML Page

### Task 5.1 - Create admin page

File:

```text
cfml-examples/admin_ai_semantic_layer.cfm
```

UI sections:

```text
1. Header and status cards
2. Scope selector
3. Module selector
4. Upload panel
5. Uploaded files table
6. Ingest status / error viewer
7. Reports browser
8. Metadata preview drawer/modal
```

Scope selector:

```text
Global
Company
  company_code
  masterfn
  companyfn
```

Module selector:

```text
sales
purchase
inventory
finance
hr
project
analytics
general
```

Upload:

```text
Accept: .xlsx,.json
Action: semantic_upload
```

### Task 5.2 - Update CFML proxy

File:

```text
cfml-examples/inc_ajax_ai_admin.cfm
```

Add actions:

```text
semantic_upload                 -> POST /admin/semantic/upload
semantic_files                  -> GET  /admin/semantic/files
semantic_run_now                -> POST /admin/semantic/files/{id}/run-now
semantic_delete                 -> DELETE /admin/semantic/files/{id}
semantic_stats                  -> GET  /admin/semantic/stats
semantic_reports                -> GET  /admin/semantic/reports
semantic_validate               -> POST /admin/semantic/validate
```

### Test Cases

- Page loads without breaking existing admin dashboard.
- Scope selector toggles company fields correctly.
- Upload button disabled until module and file are selected.
- Company scope requires company code.
- Upload success shows file in table with `pending` status.
- Run Now changes status to `processing`, then `done` or `failed`.
- Error viewer shows validation errors from API.
- Reports browser shows reports from selected scope/module.
- Global report appears when no company override exists.
- Company override appears before global report for same report ID.

## Phase 6 - Runtime Semantic Retrieval

### Task 6.1 - Create semantic retrieval module

File:

```text
api/semantic/retrieval.py
```

Function:

```python
resolve_semantic_report(query, masterfn, companyfn, company_code, module_hint=None)
```

Return:

```json
{
  "matched": true,
  "confidence": 0.91,
  "scope_used": "company",
  "report_id": "SAL-SO-LIST",
  "module": "sales",
  "intent_type": "list",
  "tool_name": "list_sales_documents",
  "default_filters": {
    "tag_table_usage": "sal_soe",
    "tag_void_yn": "n"
  },
  "required_filters": ["date_from", "date_to"],
  "output_columns": ["dnum_auto", "date_trans", "party_desc", "amount_local"]
}
```

### Task 6.2 - Integrate with data-query flow

Current:

```text
run_data_query -> Gemini chooses skill tool
```

Target:

```text
run_data_query
-> semantic report resolution
-> if high confidence, pass selected report metadata into prompt
-> Gemini chooses/calls matching skill tool
-> execute_skill_tool
-> render answer
```

Do not bypass skills. Semantic metadata decides; skills execute.

### Test Cases

- `list sales order in 7/2026` resolves to `SAL-SO-LIST`.
- `top 10 sales order in 7/2026` resolves to top/ranking report, not list report.
- `sales order by customer in 7/2026` resolves to aggregate-by-customer report.
- Company-specific synonym overrides global synonym.
- Low confidence returns no selected report and falls back to existing skill flow.
- Missing required date filter either asks a safe clarification or applies a safe default preview policy.

## Phase 7 - Query Context Memory

### Task 7.1 - Store last data-query context

After successful query, store:

```text
session_id
user_id
company_id
masterfn
companyfn
report_id
tool_name
tool_args
filters
columns
result_ids
document_numbers
created_at
```

### Task 7.2 - Use context for follow-up

Examples:

```text
User: list sales order in 7/2026
Follow-up: which document numbers?
Follow-up: total amount?
Follow-up: which customers?
Follow-up: compare with August
```

### Test Cases

- Follow-up `which document numbers?` uses previous report/filter context.
- Follow-up `total amount?` reuses filters but calls aggregate tool.
- Follow-up `compare with August` keeps document type and changes date range.
- Context is isolated by session and company scope.

## Phase 8 - Security and Performance

### Task 8.1 - Security validation

Rules:

```text
- Only admins can upload semantic metadata.
- API key remains server-side through CFML proxy.
- Company scope cannot override another company.
- Tool names must be from allowed skills.
- SQL templates, if supported, must pass SELECT-only validator.
- No DELETE/UPDATE/INSERT/ALTER/DROP from metadata.
```

### Task 8.2 - Performance policy

Rules:

```text
- Metadata search uses top K only.
- Runtime prompt includes selected metadata only, not entire catalog.
- List reports enforce limit/pageSize.
- Required filters must be enforced before heavy queries.
- Large export must be async, not chat response.
```

### Test Cases

- Non-admin request rejected.
- Metadata with forbidden SQL rejected.
- Metadata referencing unknown tool rejected.
- List query without limit gets safe default limit.
- Metadata retrieval returns company override plus global fallback without scanning all rows.

## Phase 9 - Demo Acceptance Scenarios

### Scenario 1 - Global Sales Metadata

Steps:

```text
1. Open admin_ai_semantic_layer.cfm.
2. Select Global.
3. Select Sales.
4. Upload sales_metadata.json.
5. Click Run Now.
6. Verify status done.
7. Ask chatbox: list sales order in 7/2026.
```

Expected:

```text
Semantic match: SAL-SO-LIST
Tool: list_sales_documents
Filters: tag_table_usage=sal_soe, date_from=2026-07-01, date_to=2026-08-01
Answer: sales order table with document numbers
```

### Scenario 2 - Company Override

Steps:

```text
1. Upload global Sales metadata.
2. Upload Company ABC Sales metadata with synonym Customer Order = Sales Order.
3. Ask as ABC scope: list customer orders in 7/2026.
```

Expected:

```text
Company metadata wins.
Customer Order maps to Sales Order.
Tool remains sales list skill.
```

### Scenario 3 - Invalid Metadata

Steps:

```text
1. Upload metadata missing report_id.
2. Click Run Now.
```

Expected:

```text
Status failed.
Error viewer shows missing report_id.
No partial active report is created.
```

### Scenario 4 - Follow-Up Context

Steps:

```text
1. Ask: list sales order in 7/2026.
2. Ask: which document numbers?
3. Ask: total amount?
```

Expected:

```text
Step 2 uses previous list context.
Step 3 reuses same filters and calls aggregate/count/summary tool as appropriate.
```

## Suggested Build Order

```text
1. Backend schema + metadata validator.
2. Semantic upload API.
3. Semantic ingest script.
4. CFML admin page and proxy actions.
5. Report browser and status UI.
6. Semantic retrieval function.
7. Runtime data-query integration.
8. Query context memory.
```

## Definition of Done

- `admin_ai_semantic_layer.cfm` can upload JSON/Excel metadata by global/company scope.
- Ingest validates and stores semantic rows.
- Admin can see file status, ingest error, and parsed reports.
- Chatbox can resolve at least Sales Order Listing from semantic metadata.
- Existing skill execution remains unchanged.
- Existing document ingest remains unchanged.
- Tests cover upload, validation, ingest, scope override, semantic report resolution, and follow-up context.
