---
name: globe3-sales-quotation
description: Sales quotation data — list, search, count, and analyze historical quotations
---

# Globe3 Sales Quotation Module

Use this skill for sales quotations (historical). Note: `sal_quo` has near-zero active records in most environments. Active quotations use `sal_soe` (Sales Orders) instead.

## Transaction Context

`sal_quo` = Historical sales quotation. In modern Globe3, quotations are created as Sales Orders (`sal_soe`).

## Available Tools

- **list_sales_quotations**, **get_sales_quotation**, **count_sales_quotations**, **aggregate_sales_quotations**

## Document Linking: `[QUO-001](g3doc:sal_quo/UNIQUENUM_PRI)`

## Amount Range Filters

- `amount_min` (number) — exclude records below this amount. Use when user asks for "top by amount" or "largest": set amount_min to 0.01 to exclude zero-amount records.
- `amount_max` (number) — exclude records above this amount. Use when user asks for "below X" or "under X amount".

## User-Facing Language: Say "Sales Quotation" or "Quote", not `sal_quo`.
