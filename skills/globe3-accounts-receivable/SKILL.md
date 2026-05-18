---
name: globe3-accounts-receivable
description: Accounts Receivable data — list, search, count, and analyze AR outstanding balances and aging
---

# Globe3 Accounts Receivable Module

Use this skill when the user asks about AR, outstanding receivables, customer balances, or aging analysis.

## Key Facts

- AR data uses `gnl_maint_all` with `tag_table_usage = 'recv'`
- `maint_amount_local` = original amount; `tag_closed_yn` = 'n' for open items
- `maint_cslsegm` = source type (sal_inv, csh_recp, etc.)
- For invoice details → use **globe3-sales-invoice** skill

## CRITICAL — Outstanding / Open Balance Queries

When the user asks for **"outstanding"**, **"open"**, **"unpaid"**, or **"overdue"** AR balances, you MUST include `tag_closed_yn: "n"` in the filters. Without this filter, results include already-closed (paid) items, which gives incorrect totals.

- "Show outstanding AR" → `filters: { tag_closed_yn: "n" }`
- "Total unpaid receivables by customer" → `filters: { tag_closed_yn: "n" }`
- "AR aging" → `filters: { tag_closed_yn: "n" }`
- "All AR entries" (no outstanding qualifier) → no filter needed

## Available Tools

- **list_ar_entries** — Search AR entries by customer, date, due date, currency, status.
- **get_ar_entry** — Retrieve a single AR entry by ID.
- **count_ar_entries** — Count matching AR entries.
- **aggregate_ar_entries** — Summarize AR: total by customer, currency, source type, due date. Use for aging analysis.

## Filter Fields

- `party_code`, `party_desc` (text search), `maint_date_trans`, `maint_date_due`, `maint_acctnumdisp`, `maint_curr_short`, `maint_cslsegm`, `date_trans`, `tag_closed_yn`, `tag_void_yn`

## Aggregate Options

- **Measures:** maint_amount_local, maint_amount_forex, maint_amount_orig
- **Group By:** party_code, party_desc, maint_acctnumdisp, maint_curr_short, maint_cslsegm, maint_date_trans, tag_closed_yn

## Amount Range Filters

- `amount_min` (number) — exclude records below this amount. Use when user asks for "top by amount" or "largest": set amount_min to 0.01 to exclude zero-amount records.
- `amount_max` (number) — exclude records above this amount. Use when user asks for "below X" or "under X amount".

## User-Facing Language

Say "Accounts Receivable" or "AR", never mention `gnl_maint_all` or `recv`.
