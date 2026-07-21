# Hệ Thống ERP AI Assistant — System Architecture Graph

> **Tài liệu kiến trúc tổng thể** — mô tả toàn bộ components, data flow, và dependencies của hệ thống.
> Cập nhật lần cuối: 2026-07-20

---

## 1. Tổng Quan Kiến Trúc (High-Level Architecture)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (CFML / HTML)                            │
│  cfml-examples/*.cfm  │  chatbox.html  │  three_mode_shell.html             │
│  local_ai_proxy_test.html  │  ai_assistant.cfm  │  admin_dashboard.cfm      │
│  ai_erp_extract_admin.cfm  │  inc_ajax_ai_admin.cfm                        │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │ HTTP / SSE
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        API LAYER (FastAPI - Python)                         │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  api/main.py  (App entry, router registration, CORS, middleware)    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  Chat Router  │  │  Analytics   │  │  Admin       │  │  Auth        │   │
│  │  /chat/*      │  │  /analytics/*│  │  /admin/*    │  │  /auth/*     │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
│         │                 │                 │                 │            │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐   │
│  │  api/chat.py │  │  /analytics/ │  │  /admin/     │  │  api/auth.py │   │
│  │  (handler)   │  │  fraud*.py   │  │  knowledge*  │  │  (verify)    │   │
│  │              │  │  demand*.py  │  │  documents*  │  │              │   │
│  │              │  │              │  │  ai_alerts*  │  │              │   │
│  │              │  │              │  │  memo.py     │  │              │   │
│  │              │  │              │  │  erp_extract*│  │              │   │
│  └──────────────┘  └──────┬───────┘  └──────────────┘  └──────────────┘   │
│                           │                                                 │
│                    ┌──────┴───────┐                                         │
│                    │  api/services │                                         │
│                    │  /erp_db.py  │                                         │
│                    └──────┬───────┘                                         │
└───────────────────────────┼─────────────────────────────────────────────────┘
                            │
          ┌─────────────────┼─────────────────────┐
          ▼                 ▼                      ▼
┌─────────────────┐ ┌──────────────┐ ┌──────────────────────────┐
│  PostgreSQL ERP  │ │  SQLite DB   │ │  ChromaDB (Vector DB)    │
│  (Globe3 Data)   │ │  (Chat/      │ │  (Knowledge Embeddings) │
│                  │ │  Knowledge)  │ │                          │
└─────────────────┘ └──────────────┘ └──────────────────────────┘
          │                 │
          │                 ▼
          │          ┌──────────────────────┐
          │          │  SQLite Extract DB   │
          │          │  data/erp_extract.db │
          │          │  (17 tables, multi-  │
          │          │   company scoped)    │
          │          └──────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SKILLS SERVER (Node.js)                              │
│  skills/server.js  (Express, port 3001)                                     │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  globe3-* skill modules (25+ modules)                               │   │
│  │  Mỗi module có tools.js định nghĩa tool functions                   │   │
│  │  GET /health, GET /tools, POST /execute                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘

          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        LLM LAYER (Gemini API)                               │
│  api/llm.py  →  Google Gemini (generative-ai SDK)                          │
│  Dùng cho: Chat streaming, Greeting, Demand Planning chat                  │
└─────────────────────────────────────────────────────────────────────────────┘

          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        INGESTION PIPELINE                                   │
│  ingest/ingest_knowledge.py  →  Document → Knowledge DB + ChromaDB         │
│  ingest/ingest_tickets.py    →  Support tickets → Knowledge DB             │
│  ingest/ingest_config.py     →  DB config                                   │
│  schedule/scheduler.py       →  Scheduled tasks (docs, tickets, fraud,     │
│                                 erp_extract)                                │
│  schedule/run_erp_extract.py →  ERP extract runner (multi-scope)           │
│  scm_training/               →  SCM model training pipeline                │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. API Router Map (Chi Tiết)

### 2.1 Chat Module (`/chat/*`)

| Endpoint | File | Method | Mô tả |
|----------|------|--------|-------|
| `/chat/stream` | `api/routers/chat.py` | POST | SSE streaming chat với Gemini |
| `/chat/history` | `api/routers/chat.py` | POST | Lấy lịch sử chat |
| `/chat/history/delete` | `api/routers/chat.py` | POST | Xóa lịch sử chat |
| `/chat/greeting` | `api/routers/chat.py` | POST | Tạo lời chào |
| `/chat/preferences` | `api/routers/chat.py` | GET/POST | User preferences |
| `/chat/sessions` | `api/routers/chat.py` | POST | Danh sách sessions |
| `/chat/sessions/create` | `api/routers/chat.py` | POST | Tạo session mới |
| `/chat/sessions/rename` | `api/routers/chat.py` | POST | Đổi tên session |
| `/chat/sessions/delete` | `api/routers/chat.py` | POST | Xóa session |
| `/chat/recent/delete` | `api/routers/chat.py` | POST | Xóa recent conversation |

### 2.2 Analytics Module (`/analytics/*`)

#### Fraud Detection

| Endpoint | File | Method | Mô tả |
|----------|------|--------|-------|
| `/analytics/fraud-scan` | `api/routers/analytics_fraud.py` | POST | Chạy scan phát hiện gian lận |
| `/analytics/fraud/results` | `api/routers/analytics_fraud.py` | GET | Kết quả scan |
| `/analytics/fraud/findings/{id}` | `api/routers/analytics_fraud.py` | PATCH | Cập nhật finding |
| `/analytics/fraud/scans` | `api/routers/analytics_fraud.py` | GET | Danh sách scans |

#### Demand Planning

| Endpoint | File | Method | Mô tả |
|----------|------|--------|-------|
| `/analytics/demand-plan` | `api/routers/analytics_demand.py` | POST | Tạo forecast |
| `/analytics/demand/results` | `api/routers/analytics_demand.py` | GET | Kết quả forecast |
| `/analytics/demand/forecasts` | `api/routers/analytics_demand.py` | GET | Danh sách forecasts |
| `/analytics/demand/chat-history` | `api/routers/analytics_demand.py` | GET/POST/DELETE | Chat history cho demand module |
| `/analytics/demand/chat-answer` | `api/routers/analytics_demand.py` | POST | Trả lời câu hỏi demand planning |

### 2.3 Admin Module (`/admin/*`)

#### Knowledge Management

| Endpoint | File | Method | Mô tả |
|----------|------|--------|-------|
| `/admin/knowledge/stats` | `api/routers/admin_knowledge.py` | GET | Thống kê knowledge base |
| `/admin/knowledge/entries` | `api/routers/admin_knowledge.py` | GET | Danh sách entries |
| `/admin/knowledge/entries/{id}` | `api/routers/admin_knowledge.py` | GET/DELETE | Chi tiết / Xóa entry |
| `/admin/knowledge/entries` | `api/routers/admin_knowledge.py` | DELETE | Xóa tất cả entries |

#### Document Management

| Endpoint | File | Method | Mô tả |
|----------|------|--------|-------|
| `/admin/documents/stats` | `api/routers/admin_documents.py` | GET | Thống kê documents |
| `/admin/documents` | `api/routers/admin_documents.py` | GET | Danh sách documents |
| `/admin/documents/upload` | `api/routers/admin_documents.py` | POST | Upload document |
| `/admin/documents/{id}` | `api/routers/admin_documents.py` | DELETE | Xóa document |
| `/admin/documents/{id}/reingest` | `api/routers/admin_documents.py` | POST | Re-ingest document |
| `/admin/documents/{id}/run-now` | `api/routers/admin_documents.py` | POST | Chạy ingest ngay |

#### AI Alerts & Recommendations

| Endpoint | File | Method | Mô tả |
|----------|------|--------|-------|
| `/admin/ai-alerts` | `api/routers/admin_ai_alerts.py` | POST/GET | Tạo / Danh sách alerts |
| `/admin/ai-alerts/{id}` | `api/routers/admin_ai_alerts.py` | PATCH | Review alert |
| `/admin/ai-alerts/{id}/history` | `api/routers/admin_ai_alerts.py` | GET | Lịch sử review |
| `/admin/ai-alerts/count` | `api/routers/admin_ai_alerts.py` | GET | Đếm open alerts |
| `/admin/ai-recommendations/actions` | `api/routers/admin_ai_alerts.py` | POST/GET | Recommendation actions |

#### Memo

| Endpoint | File | Method | Mô tả |
|----------|------|--------|-------|
| `/admin/memo` | `api/routers/admin_memo.py` | POST | Tạo memo trong ERP PostgreSQL |

#### ERP Extract (MỚI)

| Endpoint | File | Method | Mô tả |
|----------|------|--------|-------|
| `/admin/erp-extract/scopes` | `api/routers/admin_erp_extract.py` | GET/POST | Danh sách / Thêm scope extract |
| `/admin/erp-extract/scopes/{id}` | `api/routers/admin_erp_extract.py` | PUT/DELETE | Sửa / Xóa scope |
| `/admin/erp-extract/run` | `api/routers/admin_erp_extract.py` | POST | Trigger extract (async) |
| `/admin/erp-extract/status` | `api/routers/admin_erp_extract.py` | GET | Trạng thái extract hiện tại |
| `/admin/erp-extract/history` | `api/routers/admin_erp_extract.py` | GET | Lịch sử extract |
| `/admin/erp-extract/stats` | `api/routers/admin_erp_extract.py` | GET | Row counts per table per scope |
| `/admin/erp-extract/health` | `api/routers/admin_erp_extract.py` | GET | Health check (DB size, data age) |
| `/admin/erp-extract/alerts` | `api/routers/admin_erp_extract.py` | GET | Extract system alerts |

---

## 3. Data Flow Diagrams

### 3.1 Chat Flow

```
User (CFML/HTML)
  │
  │ POST /chat/stream  { query, user_id, company_id, session_id }
  ▼
api/routers/chat.py
  │
  ├──► api/auth.py  (verify_api_key)
  ├──► api/chat.py  (get_user_prefs, build_system_prompt, get_session_history)
  ├──► api/database.py  (get_chat_conn → SQLite)
  │
  └──► api/llm.py  (call_gemini_chat → Gemini API)
        │
        └──► skills/server.js  (POST /execute → globe3-* tools)
              │
              └──► PostgreSQL ERP (Globe3 data)
  │
  ▼
SSE Stream → User
```

### 3.2 Fraud Detection Flow

```
User (API/CFML)
  │
  │ POST /analytics/fraud-scan  { masterfn, companyfn, scan_type, date_from, date_to }
  ▼
api/routers/analytics_fraud.py
  │
  ├──► api/auth.py  (verify_api_key)
  ├──► api/database.py  (get_chat_conn → SQLite: fraud_scans, fraud_findings)
  │
  └──► api/services/erp_db.py  (PostgreSQL queries)
        │
        ├──► query_duplicate_ap_invoices()  → scm_pur_main + scm_pur_data
        ├──► query_new_vendor_high_value()  → scm_pur_main + adm_cnt_main
        ├──► query_inventory_anomalies()    → scm_stk_main + scm_stk_data
        └──► query_finance_anomalies()      → gen_ledger_detail
  │
  ▼
Response: { scan_id, summary, findings, partial_errors }
  │
  └──► Also persists to ai_alerts table (durable alerts)
```

### 3.3 Demand Planning Flow

```
User (API/CFML)
  │
  │ POST /analytics/demand-plan  { masterfn, companyfn, horizon_days, sku_filter, location_filter }
  ▼
api/routers/analytics_demand.py
  │
  ├──► api/auth.py  (verify_api_key)
  ├──► api/database.py  (get_chat_conn → SQLite: demand_forecasts, demand_sku_forecasts)
  │
  └──► api/services/erp_db.py  (PostgreSQL queries)
        │
        ├──► query_sales_history()     → scm_sal_main + scm_sal_data
        ├──► query_current_stock()     → scm_stk_data
        ├──► query_on_order_stock()    → scm_pur_main + scm_pur_data
        └──► query_committed_stock()   → scm_sal_main + scm_sal_data
  │
  ▼
Response: { forecast_id, summary, items, assumptions, partial_errors }
```

### 3.4 Document Ingestion Flow

```
User (Admin)
  │
  │ POST /admin/documents/upload  (file + company_code + domain)
  ▼
api/routers/admin_documents.py
  │
  ├──► Save file to data/docs/{_global|clients}/{domain}/
  ├──► Register in document_registry (SQLite Knowledge DB)
  │
  └──► Background thread: ingest_knowledge.py
        │
        ├──► Parse document (PDF, DOCX, TXT)
        ├──► Extract steps/notes → Knowledge DB (SQLite)
        └──► Generate embeddings → ChromaDB
```

### 3.5 AI Alerts & Review Flow

```
Fraud Scan / Other Sources
  │
  │ Creates ai_alerts record
  ▼
api/routers/admin_ai_alerts.py
  │
  ├──► POST /admin/ai-alerts  (create alert)
  ├──► GET  /admin/ai-alerts  (list alerts with filters)
  ├──► PATCH /admin/ai-alerts/{id}  (review: status, disposition, next_action)
  │
  │   Statuses: new → investigating → confirmed_issue | false_positive | resolved
  │   Dispositions: ignored_by_policy, duplicate_alert, needs_rule_tuning, insufficient_evidence
  │   Next Actions: hold_payment, check_document, contact_buyer, ignore, create_correction
  │
  └──► POST /admin/ai-recommendations/actions  (accept/adjust/reject recommendations)
```

### 3.6 ERP Extract Flow (MỚI)

```
Scheduler (schedule/scheduler.py)
  │
  │ Weekly trigger (Chủ nhật 00:00)
  ▼
schedule/run_erp_extract.py
  │
  ├──► Đọc data/erp_extract_scopes.json (danh sách scope)
  │
  └──► Với mỗi scope enabled:
        │
        └──► scripts/extract_erp_to_sqlite.py
              │
              ├──► Kết nối PostgreSQL (masterfn + companyfn filter)
              ├──► Với mỗi table trong TABLE_MAPPINGS (17 tables):
              │     ├──► SELECT ... FROM pg_table WHERE masterfn=? AND companyfn=?
              │     ├──► INSERT OR REPLACE INTO sqlite_table
              │     └──► (Incremental: chỉ fetch data từ last_extract_time)
              │
              └──► Ghi meta vào _extract_meta table

Admin UI (CFML)
  │
  │ POST /admin/erp-extract/run  (trigger manual)
  ▼
api/routers/admin_erp_extract.py
  │
  ├──► Background thread → scripts/extract_erp_to_sqlite.py
  ├──► Ghi admin_action_log (erp_extract_completed / erp_extract_failed)
  └──► Alert nếu 2+ consecutive failures
```

---

## 4. Database Schema Overview

### 4.1 Chat Database (SQLite - `data/chat.db`)

```
chat_history          → user_id, company_id, session_id, role, content, timestamp
user_preferences      → user_id, company_id, language, response_len
chat_sessions         → session_id, user_id, company_id, title, created_at, updated_at
fraud_scans           → masterfn, companyfn, scan results summary
fraud_findings        → scan findings with severity, evidence, status
demand_forecasts      → forecast summary per scope
demand_sku_forecasts  → per-SKU forecast details
ai_alerts             → durable alerts with review workflow
alert_review_history  → audit trail for alert reviews
ai_recommendation_actions → user actions on recommendations
ai_module_chat_messages → persisted chat per module (demand, etc.)
```

### 4.2 Knowledge Database (SQLite - `data/knowledge.db`)

```
domains               → Sales, Purchase, Inventory, Finance, HR, Project, CRM, CM, General
features              → Features within domains
entries               → Knowledge entries (name, type, summary, menu_path)
entry_versions        → Versioned content (steps, notes, score, flags)
companies             → Company codes for scoping
document_registry     → Uploaded document tracking (status, domain, company)
admin_audit_log       → Admin action audit trail
```

### 4.3 PostgreSQL ERP Database (Globe3)

```
scm_sal_main/data     → Sales Orders (headers + lines)
scm_pur_main/data     → Purchase Orders / Invoices (headers + lines)
scm_stk_main/data     → Stock movements (headers + lines)
gen_ledger_detail     → General Ledger entries
adm_cnt_main          → Contact/Vendor master
stk_sku_data          → SKU master data
memo_long_table       → Memo/notes table
```

### 4.4 ERP Extract Database (SQLite - `data/erp_extract.db`) [MỚI]

```
--- Transaction Tables (multi-company, có scope_masterfn + scope_companyfn) ---
scm_sal_main          → Sales headers (SO, Invoice, DO, CN, DN)
scm_sal_data          → Sales line items
scm_pur_main          → Purchase headers (PO, PI, PR, GRN, GN)
scm_pur_data          → Purchase line items
scm_stk_main          → Stock movement headers
scm_stk_data          → Stock movement line items
stk_code_main         → Stock item master (SKU)
stk_code_data         → Stock item vendor data
adm_cnt_main          → Customer/Party master
adm_cnt_data          → Customer bank data
gen_ledger_detail     → General Ledger detail entries
gnl_maint_all         → GL Master (AP/AR aging)
stkm_main_all         → Stock ledger (balance per SKU per location)
memo_long_table       → Memo/notes table
prj_pbill_main        → Project master (CRM tickets)
prj_pbill_body        → Project body (CRM ticket details)
gen_ledger_stk        → GL Stock ledger

--- Meta Table ---
_extract_meta         → key/value store: schema_version, last_extract timestamps,
                        extract summaries per scope
```

---

## 5. Skills Server Modules

```
skills/server.js  (Express, port 3001)
  │
  ├── globe3-accounts-payable/      → AP invoice queries
  ├── globe3-accounts-receivable/   → AR queries
  ├── globe3-ai-risk-analytics/     → Risk scoring
  ├── globe3-analyst/               → General analyst queries
  ├── globe3-customer/              → Customer info
  ├── globe3-delivery-confirmation/ → Delivery confirmation
  ├── globe3-delivery-order/        → Delivery order
  ├── globe3-finance/               → Finance queries
  ├── globe3-general-ledger/        → GL queries
  ├── globe3-goods-received/        → Goods received
  ├── globe3-goods-return/          → Goods return
  ├── globe3-hr/                    → HR queries
  ├── globe3-inventory/             → Inventory queries
  ├── globe3-market-trends/         → Market trends
  ├── globe3-po-confirmation/       → PO confirmation
  ├── globe3-product-info/          → Product info
  ├── globe3-project/               → Project queries
  ├── globe3-project-master/        → Project master
  ├── globe3-purchase-invoice/      → Purchase invoice
  ├── globe3-purchase-order/        → Purchase order
  ├── globe3-purchase-requisition/  → Purchase requisition
  ├── globe3-sales/                 → Sales queries
  ├── globe3-sales-invoice/         → Sales invoice
  ├── globe3-sales-order/           → Sales order
  ├── globe3-sales-quotation/       → Sales quotation
  ├── globe3-scm-overview/          → SCM overview
  ├── globe3-so-confirmation/       → SO confirmation
  ├── globe3-stock-item/            → Stock item
  └── globe3-trained-models/        → Trained ML models
```

---

## 6. Fraud Detection Engine (Chi Tiết)

```
api/fraud/
  │
  ├── domain.py       → Transaction, UserBaseline, AlertCandidate (dataclasses)
  ├── engine.py       → FraudRuleEngine (baseline builder + rule evaluator)
  ├── rules.py        → FraudRule implementations:
  │                      • HighAmountRule          (amount > p95)
  │                      • FrequencySpikeRule      (daily count spike)
  │                      • HighRefundRule          (refund count)
  │                      • AbnormalDiscountRule    (discount ratio)
  │                      • TooManyVoidRule         (void count)
  │                      • OutsideWorkingHoursRule (activity time)
  │                      • RepeatedInvoiceModificationRule
  │                      • BackdatedTransactionRule
  │                      • RuleThresholds (configurable via env vars)
  │
  └── (used by api/routers/analytics_fraud.py for live ERP scans)
```

---

## 7. SCM Training Pipeline

```
scm_training/
  │
  ├── main.py                 → Pipeline orchestrator
  ├── config.py               → Configuration
  ├── mapping.json            → Data mapping
  ├── model_tool.py           → Model utilities
  ├── scheduled_training.py   → Scheduled training jobs
  │
  ├── analysis/               → Data analysis modules
  ├── extractors/             → Data extractors (from ERP)
  ├── query/                  → Query builders
  ├── trainers/               → Model trainers
  └── transformers/           → Data transformers
```

---

## 8. ERP Extract System (MỚI — Chi Tiết)

### 8.1 File Structure

```
scripts/
  ├── create_erp_extract_tables.sql     → SQL schema (17 tables + indexes)
  └── extract_erp_to_sqlite.py          → Multi-scope extract engine

schedule/
  ├── scheduler.py                      → [MODIFIED] Thêm job erp_extract
  └── run_erp_extract.py                → [NEW] Extract runner (gọi từ scheduler)

api/routers/
  └── admin_erp_extract.py              → [NEW] Admin API endpoints

data/
  ├── erp_extract_scopes.json           → [NEW] Scope config (masterfn, companyfn, schedule)
  ├── erp_extract.db                    → [NEW] SQLite extract DB
  └── erp_extract_state.json            → [NEW] Extract state (is_running, last_run, alerts)

cfml-examples/
  └── ai_erp_extract_admin.cfm          → [NEW] CFML admin UI

logs/
  └── erp_extract.log                   → [NEW] Extract log file
```

### 8.2 Scope Config (data/erp_extract_scopes.json)

```json
{
  "scopes": [
    {
      "id": "banleong369878mfn_p23091210332792616",
      "masterfn": "banleong369878mfn",
      "companyfn": "p23091210332792616",
      "name": "Công ty Chính",
      "enabled": true,
      "schedule": { "interval": "weekly", "day": "sunday", "time": "00:00" }
    }
  ],
  "global_config": {
    "enabled": true,
    "sqlite_path": "data/erp_extract.db",
    "max_retries": 3,
    "timeout_minutes": 120,
    "notify_on_failure": true,
    "batch_size": 5000
  }
}
```

### 8.3 Extract Modes

| Mode | Flag | Mô tả |
|------|------|-------|
| **Full** | (default) | Extract tất cả data từ PostgreSQL |
| **Incremental** | `--incremental` | Chỉ fetch data từ `last_extract_time` (dùng `date_col`) |
| **Dry Run** | `--dry-run` | Đếm rows mà không insert |

### 8.4 TABLE_MAPPINGS (17 tables)

| # | SQLite Table | PG Table | Incremental Support | Date Column |
|---|-------------|----------|-------------------|-------------|
| 1 | scm_sal_main | scm_sal_main | ✅ | date_lastupdate |
| 2 | scm_sal_data | scm_sal_data | ✅ | date_trans |
| 3 | scm_pur_main | scm_pur_main | ✅ | date_lastupdate |
| 4 | scm_pur_data | scm_pur_data | ❌ | - |
| 5 | scm_stk_main | scm_stk_main | ✅ | date_trans |
| 6 | scm_stk_data | scm_stk_data | ❌ | - |
| 7 | stk_code_main | stk_code_main | ✅ | date_lastupdate |
| 8 | stk_code_data | stk_code_data | ❌ | - |
| 9 | adm_cnt_main | adm_cnt_main | ❌ | - |
| 10 | adm_cnt_data | adm_cnt_data | ❌ | - |
| 11 | gen_ledger_detail | gen_ledger_detail | ✅ | date_trans |
| 12 | gnl_maint_all | gnl_maint_all | ✅ | date_trans |
| 13 | stkm_main_all | stkm_main_all | ❌ | - |
| 14 | memo_long_table | memo_long_table | ❌ | - |
| 15 | prj_pbill_main | prj_pbill_main | ❌ | - |
| 16 | prj_pbill_body | prj_pbill_body | ❌ | - |
| 17 | gen_ledger_stk | gen_ledger_stk | ✅ | date_trans |

### 8.5 Scheduler Integration

Scheduler hiện tại có 4 jobs:

| Job | Interval | Time | Mô tả |
|-----|----------|------|-------|
| `documents` | Daily | 02:00 | Ingest documents |
| `tickets` | Daily | 03:00 | Ingest tickets |
| `fraud` | Daily | 01:00 | Fraud detection |
| `erp_extract` | Weekly | CN 00:00 | ERP data extraction |

### 8.6 Alerting

- **Consecutive failures ≥ 2:** Ghi alert vào `admin_action_log` với `target_type='erp_extract_alert'`
- **Data age > 7 days:** Warning trong health check
- **Data age > 14 days:** Error status trong health check

---

## 9. Key Dependencies & Data Flow Map

```
                    ┌──────────────────────┐
                    │    Frontend (CFML)    │
                    │  ai_erp_extract_admin │
                    └──────────┬───────────┘
                               │ HTTP
                    ┌──────────▼───────────┐
                    │   api/main.py        │
                    │   (FastAPI App)      │
                    └──────────┬───────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
  ┌───────▼───────┐   ┌───────▼───────┐   ┌───────▼───────────┐
  │  Chat Router  │   │  Analytics    │   │  Admin            │
  │  /chat/*      │   │  /analytics/* │   │  /admin/*         │
  └───────┬───────┘   └───────┬───────┘   └───────┬───────────┘
          │                   │                    │
  ┌───────▼───────┐   ┌───────▼───────┐   ┌───────▼───────────┐
  │  api/chat.py  │   │  erp_db.py    │   │  Knowledge DB     │
  │  (handler)    │   │  (PostgreSQL) │   │  (SQLite)         │
  └───────┬───────┘   └───────────────┘   └───────────────────┘
          │                                        │
  ┌───────▼───────┐                        ┌───────▼───────────┐
  │  api/llm.py   │                        │  admin_erp_extract│
  │  (Gemini)     │                        │  (ERP Extract)    │
  └───────┬───────┘                        └───────┬───────────┘
          │                                        │
  ┌───────▼───────┐                        ┌───────▼───────────┐
  │ Skills Server │                        │  SQLite Extract   │
  │ (Node.js)     │                        │  erp_extract.db   │
  └───────┬───────┘                        └───────────────────┘
          │
  ┌───────▼───────┐
  │  PostgreSQL   │
  │  (ERP Data)   │
  └───────────────┘
```

---

## 10. Environment Variables

| Variable | Default | Mô tả |
|----------|---------|-------|
| `GEMINI_API_KEY` | - | Google Gemini API key |
| `SKILLS_SERVER_URL` | `http://localhost:3001` | Skills server URL |
| `SKILLS_PORT` | `3001` | Skills server port |
| `PG_HOST` | `localhost` | PostgreSQL host |
| `PG_PORT` | `5432` | PostgreSQL port |
| `PG_DBNAME` | `v57udemo2011` | PostgreSQL database |
| `PG_USER` | `postgres` | PostgreSQL user |
| `PG_PASSWORD` | `123` | PostgreSQL password |
| `FRAUD_*` | (various) | Fraud rule thresholds (see rules.py) |
| `FRAUD_ENABLE_OUTSIDE_HOURS` | `false` | Enable outside hours rule |
| `FRAUD_SCHEDULER_ENABLED` | `false` | Enable fraud scheduler |
| `FRAUD_SCHEDULER_SCOPES` | `[]` | JSON array of {masterfn, companyfn} |

---

## 11. Startup Sequence

```
1. PostgreSQL (ERP Database) — must be running
2. Skills Server:
     cd skills && node server.js
     → Listens on port 3001
     → Loads all globe3-* skill modules
3. FastAPI Server:
     cd . && python api/main.py
     → Listens on port 8000
     → Connects to SQLite (chat.db, knowledge.db)
     → Connects to PostgreSQL via erp_db.py
     → Connects to Skills Server via HTTP
4. ChromaDB (optional) — for vector search
5. Frontend (CFML/HTML) — connects to FastAPI
```
