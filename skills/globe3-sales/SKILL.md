---
name: globe3-sales
description: Sales document data — list, search, count, and analyze all Globe3 sales document types
---

# Globe3 Sales Module

Use this skill when the user asks about any sales document: invoices, orders, quotations, credit notes, delivery orders, etc.

## Document Types (tag_table_usage)

Always pass `tag_table_usage` in filters to identify the document type.

| tag_table_usage | Document type               | Notes                    |
|-----------------|-----------------------------|--------------------------|
| `sal_inv`       | Sales Invoice               | Hóa đơn bán hàng         |
| `sal_quo`       | Sales Quotation             | Báo giá bán hàng         |
| `sal_soe`       | Sales Order                 | Đơn đặt hàng bán hàng    |
| `sal_soc`       | Sales Order Confirmation    | Xác nhận đơn đặt hàng    |
| `sal_rta`       | Retail Sales                | Doanh số bán lẻ          |
| `sal_dn`        | Sales Debit Note            | Phiếu báo nợ             |
| `sal_cn`        | Sales Credit Note           | Phiếu báo có             |
| `sal_fma`       | Pro Forma Invoice           | Hóa đơn chiếu lệ         |
| _(add more)_    |                             |                          |

> **To add a new type:** add a row to this table, then add the same entry to `TAG_DESCRIPTION`
> in `tools.js` (one line, format: `'sal_xxx=Display Name | '`). Restart `node server.js`.

## Sales Flow Reference

```
sal_quo (Quotation) → sal_soe (Sales Order) → sal_soc (SO Confirmation)
                                             → sal_inv (Sales Invoice)
                                             → stk_do  (Delivery Order)
                                             → stk_doc (DO Confirmation)
```

All types share the same `scm_sal_main` table, distinguished by `tag_table_usage`.

## Available Tools

| Tool | Use for |
|---|---|
| `list_sales_documents` | Search / browse documents with filters + pagination |
| `get_sales_document` | Fetch one document by unique ID |
| `count_sales_documents` | "How many" questions — fast, no row data |
| `aggregate_sales_documents` | Reports, totals, top-N, trend analysis |

**tag_table_usage is REQUIRED** for `list_`, `count_`, and `aggregate_` tools.
`get_sales_document` does not need it (PK lookup is unique across types).

## Filter Fields

| Filter key | Type | Description |
|---|---|---|
| `tag_table_usage` | string | **REQUIRED** — document type (see table above) |
| `party_code` | string | Exact customer code |
| `party_desc` | string | Customer name — text search (partial match OK) |
| `date_from` | string | Start date: YYYY-MM-DD or YYYY-MM (whole month) |
| `date_to` | string | Exclusive end date, same format |
| `staff_code` | string | Salesperson code |
| `dnum_auto` | string | Document number — text search |
| `dnum_reference` | string | Reference number |
| `location_code` | string | Warehouse / location |
| `curr_short_forex` | string | Currency: SGD, USD, VND… |
| `tag_void_yn` | string | `"n"` = active (default), `"y"` = voided |
| `amount_min` | number | Exclude amounts below this value |
| `amount_max` | number | Exclude amounts above this value |

## Aggregate Options

- **func:** sum, count, avg, min, max (default: sum)
- **measure:** amount_local, amount_forex (default: amount_local)
- **groupBy:** party_code, party_desc, staff_code, staff_desc, location_code, deptunit_code, curr_short_forex, date_trans, creditterm_desc

## Tool Usage Guidelines

1. For pure "how many" questions → `count_sales_documents` first (fast, count only, no document numbers or rows).
2. If the user asks "which documents", "document numbers", "list", or "show details", use `list_sales_documents` with the same filters.
3. For reports/top-N → `aggregate_sales_documents` with groupBy.
4. Always include `tag_table_usage` in filters.
5. Always use date filters or other filters to narrow results — never fetch unfiltered lists.
6. Use small pageSize (5–10) for list queries.
7. Data is automatically scoped to the user's company (masterfn + companyfn).
8. For cross-module analysis (sales vs purchase, etc.), use the **globe3-analyst** skill.

## Chart Output Format

After aggregate data, include a chart block:

```g3chart
{"type":"bar","title":"Top 5 Customers by Invoice Amount","labels":["Customer A","Customer B"],"data":[50000,30000],"currency":"SGD"}
```

Types: `bar` (compare), `line` (trend over time), `pie` / `doughnut` (proportions).

## Document Number Linking

CRITICAL: ALWAYS format document numbers as clickable links. NEVER output a document number as plain text.

Format: `[DOC_NUMBER](g3doc:{tag_table_usage}/UNIQUENUM_PRI)`

Examples:
- Sales Invoice: `[INV00123](g3doc:sal_inv/p240403143128199005414)`
- _(add more examples as you map new types)_

NEVER truncate `uniquenum_pri`. Copy the COMPLETE value from tool results.

## User-Facing Language

NEVER expose internal details. Examples:
- Say "Sales Invoice" not `sal_inv`
- Say "Customer" not `party_code`
- Say "Document number" not `dnum_auto`
- Never mention table names, SQL, or tag values to the user
