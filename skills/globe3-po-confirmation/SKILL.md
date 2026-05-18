---
name: globe3-po-confirmation
description: PO Confirmation data — list, search, count, and analyze confirmed purchase orders
---

# Globe3 PO Confirmation Module

Use this skill when the user asks about PO confirmations or confirmed purchase orders.

## Transaction Context

PO Confirmations (`pur_poc`) are the confirmed purchase order stage:
```
pur_po (Purchase Order) → pur_poc (PO Confirmation) → stk_gvn (Goods Received)
```
- PO Confirmation IDs have a `c` prefix — strip `c` to get the parent PO ID.

## Available Tools

- **list_po_confirmations** — Search PO confirmations by supplier, date, document number, currency.
- **get_po_confirmation** — Retrieve a single PO confirmation by its unique ID.
- **count_po_confirmations** — Count matching PO confirmations.
- **aggregate_po_confirmations** — Summarize PO confirmations grouped by supplier, staff, currency, or date.

## Filter Fields

- `party_code`, `party_desc` (text search), `date_trans`, `dnum_auto`, `dnum_docnum`, `dnum_reference`, `curr_short_forex`, `tag_void_yn`

## Aggregate Options

- **Measures:** amount_forex, amount_local
- **Group By:** party_code, party_desc, staff_code, curr_short_forex, date_trans

## Amount Range Filters

- `amount_min` (number) — exclude records below this amount. Use when user asks for "top by amount" or "largest": set amount_min to 0.01 to exclude zero-amount records.
- `amount_max` (number) — exclude records above this amount. Use when user asks for "below X" or "under X amount".

## Document Number Linking

CRITICAL: ALWAYS format every PO confirmation document number as a clickable link. NEVER output a document number as plain text.

Format: `[DOC_NUMBER](g3doc:pur_poc/UNIQUENUM_PRI)` — replace UNIQUENUM_PRI with the actual uniquenum_pri from tool results.

Example: If tool returns `{ "dnum_auto": "POM1315", "uniquenum_pri": "p240403143005199005408" }`, output:
```
[POM1315](g3doc:pur_poc/p240403143005199005408)
```

## User-Facing Language

Say "PO Confirmation" not `pur_poc`. Never mention table names.
