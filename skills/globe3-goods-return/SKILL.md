---
name: globe3-goods-return
description: Goods return data — list, search, count, and analyze return records
---

# Globe3 Goods Return Module

Use this skill for goods returns — stock returned to/from suppliers.

## Available Tools

- **list_goods_returns**, **get_goods_return**, **count_goods_returns**, **aggregate_goods_returns**

## Document Linking: `[RET-001](g3doc:stk_retc/UNIQUENUM_PRI)`

## Amount Range Filters

- `amount_min` (number) — exclude records below this amount. Use when user asks for "top by amount" or "largest": set amount_min to 0.01 to exclude zero-amount records.
- `amount_max` (number) — exclude records above this amount. Use when user asks for "below X" or "under X amount".

## User-Facing Language: Say "Goods Return", not internal codes.
