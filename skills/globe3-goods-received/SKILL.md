---
name: globe3-goods-received
description: Goods received note data — list, search, count, and analyze GRN records
---

# Globe3 Goods Received Module

Use this skill for goods received notes (GRN) — stock received from suppliers.

## Transaction Context

`stk_grn` = Goods Received Note. Lives in `scm_pur_main` (NOT scm_stk_main).
```
pur_po (Purchase Order) → pur_poc (PO Confirmation) → stk_grn (Goods Received)
```

## Available Tools

- **list_goods_received**, **get_goods_received**, **count_goods_received**, **aggregate_goods_received**

## Filter Fields

- `party_code`, `party_desc` (text search), `date_trans`, `staff_code`, `dnum_auto`, `curr_short_forex`, `tag_void_yn`

## Document Linking: `[GRN-001](g3doc:stk_grn/UNIQUENUM_PRI)`

## Amount Range Filters

- `amount_min` (number) — exclude records below this amount. Use when user asks for "top by amount" or "largest": set amount_min to 0.01 to exclude zero-amount records.
- `amount_max` (number) — exclude records above this amount. Use when user asks for "below X" or "under X amount".

## User-Facing Language: Say "Goods Received Note" or "GRN", not `stk_grn`.
