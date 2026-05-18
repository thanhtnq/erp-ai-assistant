---
name: globe3-purchase-order
description: Purchase order data — list, search, count, and analyze purchase orders for procurement
---

# Globe3 Purchase Order Module

Use this skill when the user asks about purchase orders, procurement, or supplier spending.

## Transaction Context

Purchase Orders (`pur_po`) are the procurement stage:
```
pur_pr (Requisition) → pur_po (Purchase Order) → pur_poc (PO Confirmation)
                                                → stk_gvn (Goods Received)
                                                → pur_inv (Purchase Invoice)
```

## Available Tools

- **list_purchase_orders** — Search POs by supplier, date, document number, location, currency.
- **get_purchase_order** — Retrieve a single PO by its unique ID.
- **count_purchase_orders** — Count matching POs.
- **aggregate_purchase_orders** — Summarize POs: total/avg/min/max/count grouped by supplier, staff, location, currency, or date.

## Filter Fields

- `party_code`, `party_desc` (text search, e.g. "HD Metal" matches "HD Metal Pte Ltd"), `date_trans`, `dnum_auto`, `dnum_docnum`, `dnum_reference`, `location_code`, `curr_short_forex`, `tag_void_yn`

## Aggregate Options

- **Measures:** amount_forex, amount_local, subtot_forex, subtot_local, nettot_forex, nettot_local
- **Group By:** party_code, party_desc, staff_code, location_code, curr_short_forex, date_trans

## Amount Range Filters

- `amount_min` (number) — exclude records below this amount. Use when user asks for "top by amount" or "largest": set amount_min to 0.01 to exclude zero-amount records.
- `amount_max` (number) — exclude records above this amount. Use when user asks for "below X" or "under X amount".

## Tool Usage Guidelines

1. For PO Confirmations → use **globe3-po-confirmation** skill.
2. For supplier lookup → use **globe3-customer** skill (suppliers are also in customer master).

## Document Number Linking

CRITICAL: ALWAYS format every purchase order document number as a clickable link. NEVER output a PO number as plain text.

Format: `[DOC_NUMBER](g3doc:pur_po/UNIQUENUM_PRI)` — replace UNIQUENUM_PRI with the actual uniquenum_pri from tool results.

Example: If tool returns `{ "dnum_auto": "POM1315", "uniquenum_pri": "p240403143005199005408" }`, output:
```
[POM1315](g3doc:pur_po/p240403143005199005408)
```

## User-Facing Language

Say "Purchase Order" not `pur_po`. Say "Supplier" not `party_code`. Never mention table names.
