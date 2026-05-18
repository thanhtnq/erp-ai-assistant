---
name: globe3-finance
description: Finance module knowledge — general ledger, accounts receivable, accounts payable, bank reconciliation
---

# Globe3 Finance Module

Use this skill when the user asks about GL accounts, journal entries, AR/AP balances, bank reconciliation, or financial reporting.

## Related Skills (for data queries)

- For **invoice data** (AR analysis, revenue) → use **globe3-sales-invoice** skill
- For **customer/supplier records** (credit limits, credit terms) → use **globe3-customer** skill
- For **purchase data** (AP analysis) → use **globe3-purchase-order** skill

## Key Architecture (internal reference)

- `gen_ledger_detail` — GL transaction detail. Uses `amount_local` with sign = direction (positive = debit, negative = credit). Do NOT use `amt_debit_local` or `amt_credit_local` — these do not exist.
- `gnl_maint_all` — AR/AP bridge table. `tag_table_usage` = `recv` (AR) or `paya` (AP), `cslsegm` = source transaction type.
- `set_co_main` — Company master. Use `co_code` (NOT `setco_code`).

## AR/AP Pattern

`gnl_maint_all` uses dual discriminators:
- `tag_table_usage` = `recv` or `paya` (which side)
- `cslsegm` = originating transaction type (e.g., `sal_inv`, `pur_inv`)

## Financial Year

- Current FY in `cookie.cookfyearnow`.
- Period closing via `tag_closed01_yn` through `tag_closed03_yn`.

## Common Queries (knowledge only — GL/AP tools not yet available)

- GL balance: SUM(amount_local) from gen_ledger_detail by account_code
- Outstanding AR: gnl_maint_all where tag_table_usage = 'recv' and outstanding != 0
- Outstanding AP: gnl_maint_all where tag_table_usage = 'paya' and outstanding != 0

## User-Facing Language

Say "General Ledger" not gen_ledger_detail. Say "Accounts Receivable" not gnl_maint_all. Never mention table names or SQL.

## Internal Rules

1. GL uses `amount_local` only — sign = direction.
2. `gnl_maint_all` is the ONLY table for AR/AP balances.
3. Always filter by `companyfn` for multi-company.
4. Warn users before changes to posted financial documents.
