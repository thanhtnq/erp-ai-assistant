---
name: globe3-general-ledger
description: General Ledger journal entries — list, search, count, and analyze GL transactions
---

# Globe3 General Ledger Module

Use this skill when the user asks about GL accounts, journal entries, ledger balances, or accounting transactions.

## Key Facts

- `amount_local` is a **single signed column**: positive = debit, negative = credit
- Do NOT use `amt_debit_local` or `amt_credit_local` — these columns do NOT exist
- High-volume table (500K+ rows) — always filter by date or account

## Available Tools

- **list_gl_entries** — Search GL journal entries by account, date, period, party, department.
- **get_gl_entry** — Retrieve a single GL entry by ID.
- **count_gl_entries** — Count matching GL entries.
- **aggregate_gl_entries** — Summarize GL: total/balance by account, party, department, period, date. Use for trial balance, account analysis.

## Filter Fields

- `acctnumdisp` — GL account code (e.g., "1100-001")
- `party_code`, `party_desc` (text search)
- `date_trans`, `date_post` — transaction/posting date
- `fyearcfn` — fiscal year
- `periodmth_cfn` — fiscal period (P01, P02, etc.)
- `staff_code`, `deptunit_code`, `location_code`
- `cslsegm` — source transaction type
- `tag_void_yn`, `tag_wflow_app_yn`

## Aggregate Options

- **Measures:** amount_local, amount_forex
- **Group By:** acctnumdisp, party_code, party_desc, staff_code, deptunit_code, location_code, cslsegm, date_trans, fyearcfn, periodmth_cfn

## Amount Range Filters

- `amount_min` (number) — exclude records below this amount. Use when user asks for "top by amount" or "largest": set amount_min to 0.01 to exclude zero-amount records.
- `amount_max` (number) — exclude records above this amount. Use when user asks for "below X" or "under X amount".

## User-Facing Language

Say "General Ledger" or "Journal Entry", never mention `gen_ledger_detail`. Say "Account" not `acctnumdisp`.
