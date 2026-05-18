---
name: globe3-stock-item
description: Stock item master data — search, browse, and analyze inventory items
---

# Globe3 Stock Item Module

Use this skill when the user asks about stock items, inventory products, item codes, or item master data.

## Key Facts

- Description column is `stkcode_desc_english` (NOT `stkcode_desc` — that column does NOT exist)
- PK is `stkcode_unique` but queries use `uniquenum_pri`
- This is a master table, not transaction data

## Available Tools

- **lookup_stock_item** — Search stock items by code, name, or status.
- **get_stock_item** — Retrieve a single stock item by ID.
- **count_stock_items** — Count matching stock items.

## Filter Fields

- `stkcode_code` — item code
- `stkcode_desc_english` — item name (text search)
- `tag_active_yn` — active status (y/n)
- `tag_assembly_yn` — is assembly item
- `tag_taxable_yn` — is taxable

## User-Facing Language

Say "Stock Item" or "Product", never mention `stk_code_main`. Say "Item Code" not `stkcode_code`.
