---
name: globe3-inventory
description: Inventory module expert - stock items, stock-on-hand, reorder, overstock, stock movements, purchase receipts, and supplier delivery analysis
---

# Globe3 Inventory Module

Use this skill when the user asks about stock items, stock-on-hand, overstock, slow-moving items, reorder suggestions, stock movements, transfers, adjustments, assemblies, purchase receipts, supplier delivery, or goods received.

## Available Tool

**`run_inventory_query`** - Executes a custom SELECT query for inventory/purchase analysis. The server automatically:
1. Validates it is a SELECT statement
2. Injects `masterfn = '<client>'` AND `companyfn = '<entity>'` as mandatory scope filters
3. Caps results at 100 rows if no LIMIT is specified

**Rules for writing SQL:**
- Write standard PostgreSQL syntax.
- Do NOT include `masterfn` or `companyfn`; both are injected automatically.
- Always filter `tag_void_yn = 'n'` on transaction/detail tables.
- Use table aliases in joins.
- Always include a `LIMIT` (max 100).
- Never expose table names, column names, or SQL to the user.

## Key Tables

- `stk_code_main` - Stock item master and current total stock. Description column is `stkcode_desc_english` (NOT `stkcode_desc`).
- `stk_code_data` - Stock item vendor/location detail. Joins to `stk_code_main` via `uniquenum_pri` (NOT `stkcode_unique`).
- `scm_stk_main` - Stock transaction header for: `stk_trnr`, `stk_trnc`, `stk_reclas`, `stk_adj*`, `stk_asm*`.
- `scm_stk_data` - Stock transaction line items.
- `scm_pur_main` - Purchase transaction header for purchase orders, PO confirmation, goods received, purchase invoice.
- `scm_pur_data` - Purchase transaction line items.

## Transaction Types

| Code | Description | Header Table |
|------|-------------|-------------|
| `stk_trnr` | Stock Transfer Request | `scm_stk_main` |
| `stk_trnc` | Stock Transfer Confirm | `scm_stk_main` |
| `stk_reclas` | Stock Reclassification | `scm_stk_main` |
| `stk_adj*` | Stock Adjustment | `scm_stk_main` |
| `stk_asm*` | Stock Assembly | `scm_stk_main` |
| `stk_do` / `stk_doc` | Delivery Order | `scm_sal_main` (NOT `scm_stk_main`) |
| `pur_po` | Purchase Order | `scm_pur_main` |
| `pur_poc` | Purchase Order Confirmation | `scm_pur_main` |
| `stk_grn` / `stk_gvn` | Goods Received Note | `scm_pur_main` |
| `pur_inv` | Purchase Invoice | `scm_pur_main` |

## Important Columns

### `stk_code_main` - Stock Item Master / Current Stock

```
uniquenum_pri          TEXT     Stock item primary key
stkcode_code           TEXT     Item code
stkcode_unique         TEXT     Item ID
stkcode_desc_english   TEXT     Item name
stkcate_desc           TEXT     Category
brand_desc             TEXT     Brand
uom_stk_code           TEXT     Stock unit
stkm_qnty_total        DECIMAL  Current total stock quantity
level_min              DECIMAL  Minimum stock level
level_max              DECIMAL  Maximum stock level
level_reorder          DECIMAL  Reorder level
level_slowdays         DECIMAL  Slow-moving threshold in days
tag_active_yn          CHAR(1)  Active item flag
tag_void_yn            CHAR(1)  'y' = voided
masterfn               TEXT     Client identifier - DO NOT filter, auto-injected
companyfn              TEXT     Entity identifier - DO NOT filter, auto-injected
```

### `stk_code_data` - Vendor / Location Detail

```
uniquenum_pri          TEXT     FK to stock item master
stkcode_code           TEXT     Item code
stkcode_desc           TEXT     Item name
location_code          TEXT     Warehouse/location
party_code             TEXT     Vendor code
party_desc             TEXT     Vendor name
vendor_leadtime_days   TEXT     Vendor lead time
amount_unitcost_local  DECIMAL  Unit cost in local currency
tag_active_yn          CHAR(1)  Active row flag
tag_void_yn            CHAR(1)  'y' = voided
masterfn               TEXT     Client identifier - DO NOT filter, auto-injected
companyfn              TEXT     Entity identifier - DO NOT filter, auto-injected
```

### `scm_pur_main` - Purchase Headers

```
uniquenum_pri          TEXT     Business primary key
dnum_auto              TEXT     Document number
date_trans             DATE     Transaction date
date_due               DATE     Due/required date
date_eta               DATE     ETA
date_delivery          DATE     Delivery date
party_code             TEXT     Supplier code
party_desc             TEXT     Supplier name
location_code          TEXT     Warehouse/location
amount_local           DECIMAL  Header amount in local currency
amount_forex           DECIMAL  Header amount in foreign currency
tag_void_yn            CHAR(1)  'y' = voided
tag_table_usage        TEXT     Document type
masterfn               TEXT     Client identifier - DO NOT filter, auto-injected
companyfn              TEXT     Entity identifier - DO NOT filter, auto-injected
```

### `scm_pur_data` - Purchase Lines

```
uniquenum_pri          TEXT     FK to purchase header
uniquenum_uniq         TEXT     Line item key
date_trans             DATE     Transaction date
date_due               DATE     Due/required date
party_code             TEXT     Supplier code
party_desc             TEXT     Supplier name
stkcode_code           TEXT     Item code
stkcode_unique         TEXT     Item ID
stkcode_desc           TEXT     Item name
skucode_code           TEXT     SKU code
stkcate_desc           TEXT     Category
brand_desc             TEXT     Brand
location_code          TEXT     Warehouse/location
qnty_total             DECIMAL  Ordered/received quantity
qnty_uomstk            DECIMAL  Quantity in stock UOM
bal_qnty_total         DECIMAL  Remaining/open quantity
bal_qnty_uomstk        DECIMAL  Remaining/open stock UOM quantity
amount_local           DECIMAL  Line amount in local currency
price_unitrate_local   DECIMAL  Unit price in local currency
tag_void_yn            CHAR(1)  'y' = voided
tag_table_usage        TEXT     Document type
masterfn               TEXT     Client identifier - DO NOT filter, auto-injected
companyfn              TEXT     Entity identifier - DO NOT filter, auto-injected
```

### `scm_stk_main` / `scm_stk_data` - Stock Movements

Use these for transfers, adjustments, reclassification, and assembly. For stock-on-hand questions prefer `stk_code_main.stkm_qnty_total`.

Important columns: `uniquenum_pri`, `dnum_auto`, `date_trans`, `location_code`, `location_desc`, `stkcode_code`, `stkcode_desc`, `qnty_total`, `qnty_uomstk`, `amount_local`, `tag_void_yn`, `tag_table_usage`.

## Critical Warnings

1. `stk_do` and `stk_doc` use `scm_sal_main`; querying `scm_stk_main` returns 0 rows.
2. `stk_grn` / `stk_gvn` use `scm_pur_main`; querying `scm_stk_main` returns 0 rows.
3. Stock item description in `stk_code_main` is `stkcode_desc_english`, never `stkcode_desc`.
4. `stk_code_data` joins via `uniquenum_pri`, not `stkcode_unique`.
5. For stock-on-hand, use `stk_code_main.stkm_qnty_total`.
6. For reorder questions, compare `stkm_qnty_total` with `level_reorder` and `level_min`.
7. For overstock questions, compare `stkm_qnty_total` with `level_max`.

## Example Queries

**Products that need replenishment:**
```sql
SELECT stkcode_code,
       stkcode_desc_english AS product,
       stkcate_desc AS category,
       stkm_qnty_total AS stock_on_hand,
       level_reorder AS reorder_level,
       level_min AS minimum_level,
       GREATEST(level_reorder - stkm_qnty_total, 0) AS suggested_reorder_qty
FROM stk_code_main
WHERE tag_void_yn = 'n'
  AND tag_active_yn = 'y'
  AND level_reorder > 0
  AND stkm_qnty_total <= level_reorder
ORDER BY suggested_reorder_qty DESC
LIMIT 20
```

**High stock but low sales in the last 90 days:**
```sql
SELECT i.stkcode_code,
       i.stkcode_desc_english AS product,
       i.stkcate_desc AS category,
       i.stkm_qnty_total AS stock_on_hand,
       COALESCE(SUM(s.qnty_total), 0) AS qty_sold_90d
FROM stk_code_main i
LEFT JOIN scm_sal_data s
  ON s.stkcode_code = i.stkcode_code
 AND s.companyfn = i.companyfn
 AND s.tag_table_usage = 'sal_inv'
 AND s.tag_void_yn = 'n'
 AND s.date_trans >= CURRENT_DATE - INTERVAL '90 days'
WHERE i.tag_void_yn = 'n'
  AND i.tag_active_yn = 'y'
  AND i.stkm_qnty_total > 0
GROUP BY i.stkcode_code, i.stkcode_desc_english, i.stkcate_desc, i.stkm_qnty_total
ORDER BY i.stkm_qnty_total DESC, qty_sold_90d ASC
LIMIT 20
```

**Suppliers with late deliveries:**
```sql
SELECT party_code,
       party_desc AS supplier,
       COUNT(*) AS late_delivery_count,
       AVG(date_delivery::date - date_due::date) AS avg_days_late
FROM scm_pur_main
WHERE tag_table_usage IN ('stk_grn', 'stk_gvn')
  AND tag_void_yn = 'n'
  AND date_due IS NOT NULL
  AND date_delivery IS NOT NULL
  AND date_delivery::date > date_due::date
  AND date_trans >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY party_code, party_desc
ORDER BY late_delivery_count DESC, avg_days_late DESC
LIMIT 10
```

## Output Format

Present results as a clean markdown table. For numerical data, also include a chart:

```g3chart
{"type":"bar","title":"Products Needing Replenishment","labels":["Product A","Product B"],"data":[50,25]}
```

Chart types: `bar` (compare categories), `line` (trend over time), `pie` / `doughnut` (proportions).

## User-Facing Language

NEVER expose internal technical details to the user. Table names, column names, and transaction codes are for internal use only. Say "Stock Transfer" not `stk_trnr`, say "Delivery Order" not `stk_do`, say "Goods Received Note" not `stk_grn`. Never mention table names or SQL.
