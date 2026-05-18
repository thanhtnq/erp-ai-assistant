---
name: globe3-sales-invoice
description: Sales invoice data — list, search, count, and analyze sales invoices for revenue and AR analysis
---

# Globe3 Sales Invoice Module

Use this skill when the user asks about sales invoices, billing, revenue, or accounts receivable data.

## Transaction Context

Sales Invoices (`sal_inv`) are the billing/invoicing stage:
```
sal_soe (Sales Order) → sal_soc (SO Confirmation) → sal_inv (Sales Invoice)
```
- Invoices link to Accounts Receivable (AR).
- Outstanding invoices: `tag_closed03_yn = 'n'`.

## Available Tools

- **list_sales_invoices** — Search sales invoices by customer, date, document number, staff, currency. Returns paginated results.
- **get_sales_invoice** — Retrieve a single sales invoice by its unique ID.
- **count_sales_invoices** — Count matching invoices without fetching rows.
- **aggregate_sales_invoices** — Summarize invoices: total/avg/min/max/count grouped by customer, staff, currency, date, or credit term. Use for revenue analysis and AR reporting.

## Filter Fields

- `party_code` — exact match by customer code
- `party_desc` — text search by customer name (e.g., "GENERAL" matches "GENERAL PARTY")
- `date_trans` — invoice date
- `staff_code` — sales person code
- `dnum_auto` — invoice document number
- `dnum_reference` — reference number
- `dnum_invoice` — invoice number
- `amount_forex` — amount in foreign currency
- `curr_short_forex` — currency (SGD, USD, etc.)
- `tag_void_yn` — voided status (n = active)

## Aggregate Options

- **Measures:** amount_forex, amount_local
- **Group By:** party_code, party_desc, staff_code, curr_short_forex, date_trans, creditterm_desc

## Amount Range Filters

- `amount_min` (number) — exclude records below this amount. Use when user asks for "top by amount" or "largest": set amount_min to 0.01 to exclude zero-amount records.
- `amount_max` (number) — exclude records above this amount. Use when user asks for "below X" or "under X amount".

## Tool Usage Guidelines

1. For "how many invoices" → use `count_sales_invoices`.
2. For revenue analysis (total by customer, monthly trend) → use `aggregate_sales_invoices`.
3. Always filter to narrow results.
4. For customer lookup → use **globe3-customer** skill.
5. For AR/AP context → see **globe3-finance** skill knowledge.
6. Present aggregate results as markdown tables + g3chart.

## Chart Output Format

```g3chart
{"type":"bar","title":"Invoice Total by Customer","labels":["Cust A","Cust B"],"data":[50000,30000],"currency":"SGD"}
```

## Document Number Linking

CRITICAL: ALWAYS format every sales invoice document number as a clickable link. NEVER output a document number as plain text.

Format: `[DOC_NUMBER](g3doc:sal_inv/UNIQUENUM_PRI)` — replace UNIQUENUM_PRI with the actual uniquenum_pri from tool results.

Example: If tool returns `{ "dnum_auto": "SIV12376", "uniquenum_pri": "p240403143128199005414" }`, output:
```
[SIV12376](g3doc:sal_inv/p240403143128199005414)
```

## User-Facing Language

Say "Sales Invoice" not `sal_inv`. Say "Customer" not `party_code`. Never mention table names.
