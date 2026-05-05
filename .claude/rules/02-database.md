---
description: SQLite knowledge schema, PostgreSQL config, and chat history DB
alwaysApply: true
---

# Database

## SQLite — Knowledge Base (`data/erp_knowledge.db`)

4-tier hierarchy: `companies → domains → features → entries → entry_versions`

| Table | Purpose |
|---|---|
| `companies` | Tenant registry — code, name |
| `domains` | Top-level ERP areas (Sales, Purchase, Finance, …) |
| `features` | Specific module within a domain |
| `entries` | Knowledge article — type: `procedure\|error_fix\|faq\|reference` |
| `entry_versions` | Versioned content per company — steps (JSON), notes (JSON), source_type, feedback scores |
| `feedback_log` | User thumbs + comment, LLM-normalized, actionable flag |
| `document_registry` | Ingest tracking — file hash, status, error_message |
| `admin_action_log` | Audit trail — flag/resolve/unflag actions |

**Flag lifecycle:**
```
auto-flag (wrong_answer/incomplete/outdated) → is_flagged=1, flag_status='pending'
  ├─ Mark Resolved → flag_status='resolved', flag_resolved_at/by/note
  └─ Unflag        → is_flagged=0, flag_status=NULL
```

**Source types:** `document | ticket | augmented | manual`

## SQLite — Chat History (`data/chat_history.db`)

| Table | Purpose |
|---|---|
| `chat_history` | user_id, company_id, role, content, timestamp (last 6 per session) |
| `user_preferences` | language (auto\|en\|vi), response_len (short\|normal\|detailed) |
| `feedback_log` | duplicate of knowledge DB feedback, linked to chat session |

## PostgreSQL — Source ERP Database

Config in `ingest/ingest_config.py` (override via env vars):

```python
PG_CONFIG = {
    "host":     os.getenv("PG_HOST",     "localhost"),
    "port":     int(os.getenv("PG_PORT", "5432")),
    "dbname":   os.getenv("PG_DBNAME",   "v57udemo2011_tno"),
    "user":     os.getenv("PG_USER",     "postgres"),
    "password": os.getenv("PG_PASSWORD", "123"),
}
```

**Key ERP tables (used by skills/):**

| Table | Content | Company field |
|---|---|---|
| `scm_sal_main` | Sales headers — orders, invoices, deliveries (`tag_table_usage` discriminates) | `companyfn` + `masterfn` |
| `scm_sal_data` | Sales line items — product, qty, price, discount | `companyfn` + `masterfn` |
| `prj_pbill_main` | CRM tickets / support cases (`tag_table_usage = 'crm_int'`) | `companyfn` + `masterfn` |
| `memo_long_table` | Long-text memos/solutions for tickets | `companyfn` |

**`tag_table_usage` values for `scm_sal_main`:**

| Value | Meaning |
|---|---|
| `sal_soe` | Sales Order Entry |
| `sal_soc` | Sales Order Confirmation |
| `sal_inv` | Sales Invoice |
| `sal_quo` | Sales Quotation |
| `sal_cn` | Sales Credit Note |
| `stk_do` | Delivery Order |
| `stk_doc` | Delivery Order Confirmation |
