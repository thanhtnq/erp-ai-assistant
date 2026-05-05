---
name: Skills Architecture
description: Node.js skills server structure, globe3-sales multi-type design, orm-fetch SQL logging
type: project
originSessionId: f63f54d9-5d34-44e5-9bb2-c7fa26764c3f
---
Node.js skills server in `skills/` — queries live PostgreSQL ERP DB.

**Why:** Python api.py handles RAG; Node.js handles live SQL queries with type safety per module.

**How to apply:** When adding new ERP modules, modifying tools, or debugging DB queries.

## globe3-sales (refactored from globe3-sales-order)
- Single skill covers ALL sales document types via `tag_table_usage` parameter
- `tag_table_usage` is REQUIRED in filters for list/count/aggregate tools
- Tag mapping (full list in `skills/globe3-sales/SKILL.md`):
  - `sal_inv` Sales Invoice, `sal_quo` Quotation, `sal_soe` Sales Order
  - `sal_soc` SO Confirmation, `sal_rta` Retail Sales
  - `sal_dn` Debit Note, `sal_cn` Credit Note, `sal_fma` Pro Forma Invoice
- All tools: `list_sales_documents`, `get_sales_document`, `count_sales_documents`, `aggregate_sales_documents`

## orm-fetch.js Key Points
- Model key: `sales` (not `sales_order`)
- `default_filters`: only `tag_void_yn: 'n'` — LLM must specify `tag_table_usage`
- `tag_table_usage` is in `allowed_filters`
- Demo defaults: masterfn=`demo2011mfn`, companyfn=`p11011004464072155`
- **SQL query logger**: every `db.query()` wrapped in `dbQuery()` — prints resolved SQL + row count + ms to stdout

## SQL Logger Output Format
```
[SQL] count/sales
  SELECT COUNT(*) AS count FROM scm_sal_main WHERE masterfn = 'demo2011mfn' AND ...
  → 1 row(s)  12ms
```
Colors: cyan=[SQL], yellow=label, green=result

## ERP Table Join Pattern
- `scm_sal_main` — sales headers (orders, invoices, deliveries) — `tag_table_usage` discriminates type
- `scm_sal_data` — sales line items (product, qty, price, discount, brand, category)
- Join key: `scm_sal_data.uniquenum_pri = scm_sal_main.uniquenum_pri` + same `tag_table_usage` + `companyfn`
- Always add `tag_void_yn = 'n'` to exclude voided documents

## Adding a New Module
1. Add model entry to `MODELS` in `orm-fetch.js`
2. Create `skills/globe3-{module}/tools.js` and `SKILL.md`
3. Add table to `ALLOWED_TABLES` in `query-safety.js` if using run_query
