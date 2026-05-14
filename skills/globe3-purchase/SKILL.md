---
name: globe3-purchase
description: Purchase document data — list, search, count, and analyze all Globe3 purchase document types
---

# Globe3 Purchase Module

Use this skill when the user asks about any purchase document: invoices, orders, requisitions, credit notes, debit notes, etc.

## Document Types (tag_table_usage)

Always pass `tag_table_usage` in filters to identify the document type.

| tag_table_usage | Document type             | Notes                      |
|-----------------|---------------------------|----------------------------|
| `pur_po`        | Purchase Order            | Đơn đặt hàng mua           |
| `pur_poc`       | Purchase Order Confirm    | Xác nhận đơn đặt hàng mua  |
| `pur_inv`       | Purchase Invoice          | Hóa đơn mua hàng           |
| `pur_pr`        | Purchase Requisition      | Yêu cầu mua hàng           |
| `pur_dn`        | Purchase Debit Note       | Phiếu báo nợ mua           |
| `pur_cn`        | Purchase Credit Note      | Phiếu báo có mua           |
| _(add more)_    |                           |                            |

> **To add a new type:** add a row to this table, then add the same entry to `TAG_DESCRIPTION`
> in `tools.js` (one line, format: `'pur_xxx=Display Name | '`). Restart `node server.js`.

## Purchase Flow Reference

```
pur_pr (Requisition) → pur_po (Purchase Order) → pur_poc (PO Confirmation)
                                                → pur_inv (Purchase Invoice)
                                                → stk_grn (Goods Receipt)
```

All types share the same `scm_pur_main` table, distinguished by `tag_table_usage`.

## Available Tools

| Tool | Use for |
|---|---|
| `list_purchase_documents` | Search / browse documents with filters + pagination |
| `get_purchase_document` | Fetch one document by unique ID |
| `count_purchase_documents` | "How many" questions — fast, no row data |
| `aggregate_purchase_documents` | Reports, totals, top-N, trend analysis |

**tag_table_usage is REQUIRED** for `list_`, `count_`, and `aggregate_` tools.
`get_purchase_document` does not need it (PK lookup is unique across types).

## Filter Fields

| Filter key | Type | Description |
|---|---|---|
| `tag_table_usage` | string | **REQUIRED** — document type (see table above) |
| `party_code` | string | Exact vendor code |
| `party_desc` | string | Vendor name — text search (partial match OK) |
| `date_from` | string | Start date: YYYY-MM-DD or YYYY-MM (whole month) |
| `date_to` | string | Exclusive end date, same format |
| `staff_code` | string | Buyer / staff code |
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

1. For "how many" → `count_purchase_documents` first (fast, no row data).
2. For reports/top-N → `aggregate_purchase_documents` with groupBy.
3. Always include `tag_table_usage` in filters.
4. Always use date filters or other filters to narrow results — never fetch unfiltered lists.
5. Use small pageSize (5–10) for list queries.
6. Data is automatically scoped to the user's company (masterfn + companyfn).
7. For cross-module analysis (purchase vs sales, vendor vs customer, etc.), use the **globe3-analyst** skill.
8. Only use raw SQL via `run_query` when the provided tools cannot fulfill the request.
   For standard queries (list, count, aggregate), ALWAYS prefer the dedicated tools first.
9. For "quantity on hand", "stock on hand", "tồn kho" queries → use `aggregate_stock_documents`
   with `measure="balance_qnty_uom_stk_code"` and appropriate `groupBy` (e.g. `stkcode_code`).
## Chart Output Format

After aggregate data, include a chart block:

```g3chart
{"type":"bar","title":"Top 5 Vendors by Invoice Amount","labels":["Vendor A","Vendor B"],"data":[50000,30000],"currency":"SGD"}
```

Types: `bar` (compare), `line` (trend over time), `pie` / `doughnut` (proportions).

## Document Number Linking

CRITICAL: ALWAYS format document numbers as clickable links. NEVER output a document number as plain text.

Format: `[DOC_NUMBER](g3doc:{tag_table_usage}/UNIQUENUM_PRI)`

Examples:
- Purchase Invoice:  `[PINV00123](g3doc:pur_inv/p240403143128199005414)`
- Purchase Order:    `[PO00456](g3doc:pur_po/p240403143128199005415)`
- _(add more examples as you map new types)_

NEVER truncate `uniquenum_pri`. Copy the COMPLETE value from tool results.

## User-Facing Language

NEVER expose internal details. Examples:
- Say "Purchase Invoice" not `pur_inv`
- Say "Vendor" not `party_code`
- Say "Document number" not `dnum_auto`
- Never mention table names, SQL, or tag values to the user
