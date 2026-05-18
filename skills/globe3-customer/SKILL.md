---
name: globe3-customer
description: Customer and supplier records — lookup, search, and analyze party data
---

# Globe3 Customer / Party Module

Use this skill when the user asks about customers, suppliers, parties, or needs to look up a party before querying their transactions.

## Context

The customer/party master (`adm_cnt_main`) stores all business partners:
- Customers (clients)
- Suppliers (vendors)
- Both can exist as the same party

## Available Tools

- **lookup_customer** — Search customers/suppliers by code, name, or status. Use to find a party before querying their transactions.
- **get_customer** — Retrieve a single customer/supplier record by ID.
- **aggregate_customers** — Summarize customers: count by type (client/vendor), active status, country, or state. Analyze credit limits.

## Filter Fields

- `party_code` — exact match by party code
- `party_desc` — text search by party name (e.g., "GENERAL" matches "GENERAL PARTY")
- `tag_client_vendor` — "c" for client, "v" for vendor
- `tag_active_yn` — "y" for active, "n" for inactive

## Aggregate Options

- **Measures:** creditlimit_client
- **Group By:** tag_client_vendor, tag_active_yn, addr_main_nation, addr_main_state

## Tool Usage Guidelines

1. Use `lookup_customer` to find a party code/name before querying transactions.
2. After finding the customer, use their `party_code` to filter in other skills:
   - Sales invoices → **globe3-sales-invoice** skill
   - Sales orders → **globe3-sales-order** skill
   - Purchase orders → **globe3-purchase-order** skill

## User-Facing Language

Say "Customer" or "Supplier" not `party_code`. Never mention table names.
