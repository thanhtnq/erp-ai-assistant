---
name: globe3-purchase-invoice
description: Purchase invoice data — list, search, count, and analyze supplier invoices for AP analysis
---

# Globe3 Purchase Invoice Module

Use this skill for purchase invoices (supplier invoices), accounts payable analysis.

## Transaction Context

`pur_inv` = Purchase Invoice (supplier billing). Links to Accounts Payable.
```
pur_po → pur_poc → stk_grn → pur_inv (Purchase Invoice)
```

## Available Tools

- **list_purchase_invoices**, **get_purchase_invoice**, **count_purchase_invoices**, **aggregate_purchase_invoices**

## Filter Fields

- `party_code`, `party_desc` (text search), `date_trans`, `staff_code`, `dnum_auto`, `curr_short_forex`, `tag_void_yn`

## Document Linking: `[PI-001](g3doc:pur_inv/UNIQUENUM_PRI)`

## Amount Range Filters

- `amount_min` (number) — exclude records below this amount. Use when user asks for "top by amount" or "largest": set amount_min to 0.01 to exclude zero-amount records.
- `amount_max` (number) — exclude records above this amount. Use when user asks for "below X" or "under X amount".

## User-Facing Language: Say "Purchase Invoice" or "Supplier Invoice", not `pur_inv`.
