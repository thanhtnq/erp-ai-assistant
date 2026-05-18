---
name: globe3-accounts-payable
description: Accounts Payable data — list, search, count, and analyze AP outstanding balances and aging
---

# Globe3 Accounts Payable Module

Use this skill when the user asks about AP, outstanding payables, supplier balances, or AP aging.

## Key Facts

- AP data uses `gnl_maint_all` with `tag_table_usage = 'paya'`
- `maint_amount_local` = original amount; `tag_closed_yn` = 'n' for open items
- `maint_cslsegm` = source type (pur_pi, csh_paym, sub_jour, etc.)
- For purchase invoice details → use **globe3-purchase-invoice** skill

## CRITICAL — Outstanding / Open Balance Queries

When the user asks for **"outstanding"**, **"open"**, **"unpaid"**, or **"overdue"** AP balances, you MUST include `tag_closed_yn: "n"` in the filters. Without this filter, results include already-closed (paid) items, which gives incorrect totals.

- "Show outstanding AP" → `filters: { tag_closed_yn: "n" }`
- "Total unpaid payables by supplier" → `filters: { tag_closed_yn: "n" }`
- "AP aging" → `filters: { tag_closed_yn: "n" }`
- "All AP entries" (no outstanding qualifier) → no filter needed

## Available Tools

- **list_ap_entries** — Search AP entries by supplier, date, due date, currency, status.
- **get_ap_entry** — Retrieve a single AP entry by ID.
- **count_ap_entries** — Count matching AP entries.
- **aggregate_ap_entries** — Summarize AP: total by supplier, currency, source type, due date.

## Filter Fields

- `party_code`, `party_desc` (text search), `maint_date_trans`, `maint_date_due`, `maint_acctnumdisp`, `maint_curr_short`, `maint_cslsegm`, `date_trans`, `tag_closed_yn`, `tag_void_yn`

## Aggregate Options

- **Measures:** maint_amount_local, maint_amount_forex, maint_amount_orig
- **Group By:** party_code, party_desc, maint_acctnumdisp, maint_curr_short, maint_cslsegm, maint_date_trans, tag_closed_yn

## Amount Range Filters

- `amount_min` (number) — exclude records below this amount. Use when user asks for "top by amount" or "largest": set amount_min to 0.01 to exclude zero-amount records.
- `amount_max` (number) — exclude records above this amount. Use when user asks for "below X" or "under X amount".

## User-Facing Language

Say "Accounts Payable" or "AP", never mention `gnl_maint_all` or `paya`.
