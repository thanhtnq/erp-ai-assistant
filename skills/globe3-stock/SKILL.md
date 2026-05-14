---
name: globe3-stock
description: Stock/inventory movement data — list, search, count, and analyze all Globe3 stock document types
---

# Globe3 Stock Module

Use this skill when the user asks about any stock or inventory transaction: delivery orders, goods receipts, stock adjustments, transfers, returns, work orders, stock takes, etc.

## Document Types (tag_table_usage)

Always pass `tag_table_usage` in filters to identify the movement type.

| tag_table_usage | Document type                   | Notes                         |
|-----------------|---------------------------------|-------------------------------|
| `stk_do`        | Delivery Order                  | Phiếu xuất kho giao hàng      |
| `stk_doc`       | Delivery Order Confirm          | Xác nhận phiếu xuất kho       |
| `stk_grn`       | Goods Receipt                   | Phiếu nhập kho                |
| `stk_gvn`       | Goods Valuation                 | Định giá hàng tồn             |
| `stk_adji`      | Stock Adjustment (Incr Qnty)    | Điều chỉnh tồn kho (tăng)     |
| `stk_adjd`      | Stock Adjustment (Decr Qnty)    | Điều chỉnh tồn kho (giảm)     |
| `stk_trnc`      | Transfer Confirmation           | Xác nhận chuyển kho           |
| `stk_trnr`      | Transfer Request                | Yêu cầu chuyển kho            |
| `stk_retc`      | Sales Return                    | Hàng bán trả lại              |
| `stk_retv`      | Return To Vendor                | Hàng mua trả lại              |
| `stk_asma`      | Work Order In Progress          | Lệnh sản xuất đang thực hiện  |
| `stk_asmc`      | Work Order Completion           | Hoàn thành lệnh sản xuất      |
| `stk_asmr`      | Work Order Request              | Yêu cầu lệnh sản xuất         |
| `stk_reclas`    | Item Reclassification With Cost | Phân loại lại hàng hóa        |
| `stk_mi`        | Material Stock In               | Nhập nguyên vật liệu          |
| `stk_mw`        | Material Stock Out              | Xuất nguyên vật liệu          |
| `stk_open`      | Stock Opening Balance           | Tồn kho đầu kỳ                |
| `stk_take`      | Stock Take                      | Kiểm kê kho                   |
| `stk_unm`       | Reverse BOM / Unassemble        | Tháo rời thành phẩm           |
| _(add more)_    |                                 |                               |

> **To add a new type:** add a row to this table, then add the same entry to `TAG_DESCRIPTION`
> in `tools.js` (one line, format: `'stk_xxx=Display Name | '`). Restart `node server.js`.

## Stock Flow Reference

```
── Outbound ──────────────────────────────────────────────────────────
sal_soe (Sales Order) → stk_do (Delivery Order) → stk_doc (DO Confirm)
                      → stk_retc (Sales Return)

── Inbound ───────────────────────────────────────────────────────────
pur_po (Purchase Order) → stk_grn (Goods Receipt)
                        → stk_retv (Return To Vendor)

── Internal ──────────────────────────────────────────────────────────
stk_trnr (Transfer Request) → stk_trnc (Transfer Confirm)
stk_asmr (WO Request) → stk_asma (WO In Progress) → stk_asmc (WO Complete)
stk_adji / stk_adjd  — manual quantity adjustments
stk_take             — periodic stock take / cycle count
stk_open             — opening balance (one-time per item)
```

All types share the same `stkm_main_all` table, distinguished by `tag_table_usage`.

## Available Tools

| Tool | Use for |
|---|---|
| `list_stock_documents` | Search / browse stock movements with filters + pagination |
| `get_stock_document` | Fetch one document by unique ID |
| `count_stock_documents` | "How many" questions — fast, no row data |
| `aggregate_stock_documents` | tag_table_usage is OPTIONAL — omit for QOH / cross-type queries |

**tag_table_usage is REQUIRED** for `list_`, `count_`, and `aggregate_` tools.

`get_stock_document` does not need it (PK lookup is unique across types).

## Filter Fields

| Filter key | Type | Description |
|---|---|---|
| `tag_table_usage` | string | **REQUIRED** — movement type (see table above) |
| `stkcode_code` | string | Stock item code (exact match) |
| `location_code` | string | Warehouse / location code |
| `party_code` | string | Exact party code (customer or vendor depending on type) |
| `party_desc` | string | Party name — text search (partial match OK) |
| `date_from` | string | Start date: YYYY-MM-DD or YYYY-MM (whole month) |
| `date_to` | string | Exclusive end date, same format |
| `staff_code` | string | Staff / handler code |
| `dnum_auto` | string | Document number — text search |
| `dnum_reference` | string | Reference number |
| `curr_short_forex` | string | Currency: SGD, USD, VND… |
| `tag_void_yn` | string | `"n"` = active (default), `"y"` = voided |
| `amount_min` | number | Exclude amounts below this value |
| `amount_max` | number | Exclude amounts above this value |

## Aggregate Options

- **func:** sum, count, avg, min, max (default: sum)
- **measure:** `amount_local`, `amount_forex`, `balance_qnty_uom_stk_code` (default: amount_local)
- **groupBy:** stkcode_code, location_code, party_code, party_desc, staff_code, tag_table_usage, curr_short_forex, date_trans

> Use `balance_qnty_uom_stk_code` as measure to aggregate quantities (e.g. total units received, total units delivered).

## Tool Usage Guidelines

1. For "how many" → `count_stock_documents` first (fast, no row data).
2. For inventory reports/top items → `aggregate_stock_documents` with groupBy.
3. Always include `tag_table_usage` in filters **only when the user asks about a specific document type** (e.g. "how many Delivery Orders", "total GRN quantity").
4. **For quantity on hand / tồn kho / current stock queries → NEVER add `tag_table_usage`**. Query `stkm_main_all` without it to sum across all movement types. Adding any `tag_table_usage` (including `stk_open`) will give wrong results.
5. Always use date or location filters to narrow results — never fetch unfiltered lists.
6. Use small pageSize (5–10) for list queries.
7. Data is automatically scoped to the user's company (masterfn + companyfn).
8. For cross-module analysis (stock vs sales, stock vs purchase), use the **globe3-analyst** skill.
9. Only use raw SQL via `run_query` when the provided tools cannot fulfill the request. For standard queries (list, count, aggregate), ALWAYS prefer the dedicated tools first.
10. For "quantity on hand", "stock on hand", "tồn kho" queries → use `aggregate_stock_documents` with `measure="balance_qnty_uom_stk_code"` and appropriate `groupBy` (e.g. `stkcode_code`). Do NOT add `tag_table_usage`.

## Chart Output Format

After aggregate data, include a chart block:

```g3chart
{"type":"bar","title":"Top 10 Items by Goods Receipt Quantity","labels":["ITEM-001","ITEM-002"],"data":[500,320],"currency":""}
```

Types: `bar` (compare), `line` (trend over time), `pie` / `doughnut` (proportions).

> For quantity-based charts, omit `currency` or set it to `""`.

## Document Number Linking

CRITICAL: ALWAYS format document numbers as clickable links. NEVER output a document number as plain text.

Format: `[DOC_NUMBER](g3doc:{tag_table_usage}/UNIQUENUM_PRI)`

Examples:
- Delivery Order:   `[DO00123](g3doc:stk_do/p240403143128199005414)`
- Goods Receipt:    `[GRN00456](g3doc:stk_grn/p240403143128199005415)`
- Stock Take:       `[TAKE00789](g3doc:stk_take/p240403143128199005416)`
- _(add more examples as you map new types)_

NEVER truncate `uniquenum_pri`. Copy the COMPLETE value from tool results.

## User-Facing Language

NEVER expose internal details. Examples:
- Say "Delivery Order" not `stk_do`
- Say "Item code" not `stkcode_code`
- Say "Quantity" not `balance_qnty_uom_stk_code`
- Say "Warehouse" not `location_code`
- Say "Document number" not `dnum_auto`
- Never mention table names, SQL, or tag values to the user
