---
name: globe3-delivery-confirmation
description: Delivery confirmation data — confirmed stock dispatches
---

# Globe3 Delivery Confirmation Module

Use this skill for delivery confirmations (confirmed dispatches).

## Transaction Context

`stk_doc` = confirmed delivery order. Uses `scm_sal_main` table.

## Available Tools

- **list_delivery_confirmations**, **get_delivery_confirmation**, **count_delivery_confirmations**, **aggregate_delivery_confirmations**

## Document Linking: `[DOC-001](g3doc:stk_doc/UNIQUENUM_PRI)`

## Amount Range Filters

- `amount_min` (number) — exclude records below this amount. Use when user asks for "top by amount" or "largest": set amount_min to 0.01 to exclude zero-amount records.
- `amount_max` (number) — exclude records above this amount. Use when user asks for "below X" or "under X amount".
