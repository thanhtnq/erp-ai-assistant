---
name: globe3-so-confirmation
description: SO Confirmation data — list, search, count, and analyze confirmed sales orders
---

# Globe3 SO Confirmation Module

Use this skill when the user asks about SO confirmations, confirmed orders, or the SOC stage.

## Transaction Context

SO Confirmations (`sal_soc`) are the confirmed order stage:
```
sal_soe (Sales Order) → sal_soc (SO Confirmation) → sal_inv (Sales Invoice)
```
- SOC represents a confirmed/approved sales order before invoicing.

## Available Tools

- **list_so_confirmations** — Search SO confirmations by customer, date, document number, staff, currency.
- **get_so_confirmation** — Retrieve a single SO confirmation by its unique ID.
- **count_so_confirmations** — Count matching SO confirmations.
- **aggregate_so_confirmations** — Summarize SO confirmations: total/avg/min/max/count grouped by customer, staff, currency, or date.

## Filter Fields

- `party_code`, `party_desc` (text search), `date_trans`, `staff_code`, `dnum_auto`, `dnum_reference`, `curr_short_forex`, `tag_void_yn`

## Aggregate Options

- **Measures:** amount_forex, amount_local
- **Group By:** party_code, party_desc, staff_code, curr_short_forex, date_trans

## Amount Range Filters

- `amount_min` (number) — exclude records below this amount. Use when user asks for "top by amount" or "largest": set amount_min to 0.01 to exclude zero-amount records.
- `amount_max` (number) — exclude records above this amount. Use when user asks for "below X" or "under X amount".

## Document Number Linking

CRITICAL: ALWAYS format every SO confirmation document number as a clickable link. NEVER output a document number as plain text.

Format: `[DOC_NUMBER](g3doc:sal_soc/UNIQUENUM_PRI)` — replace UNIQUENUM_PRI with the actual uniquenum_pri from tool results.

Example: If tool returns `{ "dnum_auto": "SOC00456", "uniquenum_pri": "p240403143005199005408" }`, output:
```
[SOC00456](g3doc:sal_soc/p240403143005199005408)
```
NEVER truncate uniquenum_pri. Copy the COMPLETE value from tool results. Never write "p240403..." — always the full ID.

## User-Facing Language

Say "SO Confirmation" not `sal_soc`. Never mention table names.
