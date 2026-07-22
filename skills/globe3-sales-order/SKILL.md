---
name: globe3-sales-order
description: Sales order data — list, search, count, and analyze sales orders (quotations)
---

# Globe3 Sales Order Module

Use this skill when the user asks about sales orders, quotations, or the SO stage of the sales flow.

## Transaction Context

Sales Orders (`sal_soe`) are the active quotation/order stage in Globe3:
```
sal_soe (Sales Order) → sal_soc (SO Confirmation) → sal_inv (Sales Invoice)
                                                   → stk_do (Delivery Order)
```
- `sal_quo` is historical with near-zero active records. Use `sal_soe` for active quotations.
- All sales order data is in `scm_sal_main` with `tag_table_usage = 'sal_soe'`.

## Available Tools

- **list_sales_orders** — Search sales orders by customer, date, document number, staff, location, currency. Returns paginated results.
- **get_sales_order** — Retrieve a single sales order by its unique ID.
- **count_sales_orders** — Count matching sales orders without fetching rows. Use for "how many" questions.
- **aggregate_sales_orders** — Summarize sales orders: total/avg/min/max/count grouped by customer, staff, location, currency, date, or credit term. Use for reports and analysis.

## Filter Fields

Available filter keys for list/count/aggregate:
- `party_code` — exact match by customer code
- `party_desc` — text search by customer name (e.g., "GENERAL" matches "GENERAL PARTY")
- `date_trans` — transaction date
- `staff_code` — sales person code
- `dnum_auto` — document number
- `dnum_reference` — reference number
- `location_code` — warehouse/location
- `curr_short_forex` — currency (SGD, USD, etc.)
- `tag_void_yn` — voided status (n = active)

## Aggregate Options

- **Measures:** amount_forex, amount_local
- **Group By:** party_code, party_desc, staff_code, location_code, curr_short_forex, date_trans, creditterm_desc

## Amount Range Filters

- `amount_min` (number) — exclude records below this amount. Use when user asks for "top by amount" or "largest": set amount_min to 0.01 to exclude zero-amount records.
- `amount_max` (number) — exclude records above this amount. Use when user asks for "below X" or "under X amount".

## Tool Usage Guidelines

1. For pure "how many" questions, use `count_sales_orders` first — fast, count only, no document numbers or rows.
2. If the user asks "which sales orders", "document numbers", "list", or "show details", use `list_sales_orders` with the same filters.
3. For analysis/report (top customers, total by month), use `aggregate_sales_orders`.
4. Always use filters to narrow results — never fetch unfiltered full lists.
5. Start with small pageSize (5-10).
6. Data is automatically scoped to the user's company.
7. For customer lookup, use the **globe3-customer** skill.
8. For SO Confirmations, use the **globe3-so-confirmation** skill.
9. For Sales Invoices, use the **globe3-sales-invoice** skill.
10. Present aggregate results as clean markdown tables + g3chart.

## Chart Output Format

After aggregate data, ALWAYS include a chart:
```g3chart
{"type":"bar","title":"Top 5 Customers by Sales Order Amount","labels":["Customer A","Customer B"],"data":[50000,30000],"currency":"SGD"}
```
Types: `bar` (compare), `pie` (proportion), `doughnut` (distribution), `line` (trend over time).

## Document Number Linking

CRITICAL: ALWAYS format every sales order document number as a clickable link. NEVER output a document number as plain text.

Format: `[DOC_NUMBER](g3doc:sal_soe/UNIQUENUM_PRI)` — replace UNIQUENUM_PRI with the actual uniquenum_pri from tool results.

Example: If tool returns `{ "dnum_auto": "SOE00123", "uniquenum_pri": "p240403143128199005414" }`, output:
```
[SOE00123](g3doc:sal_soe/p240403143128199005414)
```
NEVER truncate uniquenum_pri. Copy the COMPLETE value from tool results. Never write "p240403..." — always the full ID.

## User-Facing Language

NEVER expose internal details. Say "Sales Order" not `sal_soe`. Say "Customer" not `party_code`. Never mention table names or SQL.
