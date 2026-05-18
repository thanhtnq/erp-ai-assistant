---
name: globe3-delivery-order
description: Delivery order data — list, search, count, and analyze delivery orders (stock dispatches)
---

# Globe3 Delivery Order Module

Use this skill when the user asks about delivery orders, stock dispatches, or shipments to customers.

## Transaction Context

Delivery Orders (`stk_do`) are the stock dispatch stage:
```
sal_soe (Sales Order) → sal_soc (SO Confirmation) → stk_do (Delivery Order)
                                                   → sal_inv (Sales Invoice)
```
- Delivery orders use `scm_sal_main` table (NOT scm_stk_main).

## Available Tools

- **list_delivery_orders** — Search delivery orders by customer, date, document number, location, currency.
- **get_delivery_order** — Retrieve a single delivery order by its unique ID.
- **count_delivery_orders** — Count matching delivery orders.
- **aggregate_delivery_orders** — Summarize delivery orders grouped by customer, staff, location, currency, or date.

## Filter Fields

- `party_code`, `party_desc` (text search), `date_trans`, `staff_code`, `dnum_auto`, `location_code`, `curr_short_forex`, `tag_void_yn`

## Amount Range Filters

- `amount_min` (number) — exclude records below this amount. Use when user asks for "top by amount" or "largest": set amount_min to 0.01 to exclude zero-amount records.
- `amount_max` (number) — exclude records above this amount. Use when user asks for "below X" or "under X amount".

## Document Number Linking

CRITICAL: ALWAYS format every delivery order document number as a clickable link. NEVER output a document number as plain text.

Format: `[DOC_NUMBER](g3doc:stk_do/UNIQUENUM_PRI)` — replace UNIQUENUM_PRI with the actual uniquenum_pri from tool results.

Example: If tool returns `{ "dnum_auto": "DO00789", "uniquenum_pri": "p240403143005199005408" }`, output:
```
[DO00789](g3doc:stk_do/p240403143005199005408)
```
NEVER truncate uniquenum_pri. Copy the COMPLETE value from tool results. Never write "p240403..." — always the full ID.

## User-Facing Language

Say "Delivery Order" not `stk_do`. Never mention table names.
