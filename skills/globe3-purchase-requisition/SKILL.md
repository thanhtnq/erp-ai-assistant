---
name: globe3-purchase-requisition
description: Purchase requisition data — list, search, count, and analyze purchase requests
---

# Globe3 Purchase Requisition Module

Use this skill for purchase requisitions (PR) — internal purchase requests before PO creation.

## Transaction Context

`pur_pr` = Purchase Requisition. First step in procurement:
```
pur_pr (Requisition) → pur_po (Purchase Order) → ...
```

## Available Tools

- **list_purchase_requisitions**, **get_purchase_requisition**, **count_purchase_requisitions**, **aggregate_purchase_requisitions**

## Document Linking: `[PR-001](g3doc:pur_pr/UNIQUENUM_PRI)`

## Amount Range Filters

- `amount_min` (number) — exclude records below this amount. Use when user asks for "top by amount" or "largest": set amount_min to 0.01 to exclude zero-amount records.
- `amount_max` (number) — exclude records above this amount. Use when user asks for "below X" or "under X amount".

## User-Facing Language: Say "Purchase Requisition" or "PR", not `pur_pr`.
