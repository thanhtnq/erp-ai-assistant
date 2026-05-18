---
name: globe3-project
description: Project management expert — project costing, budgets, progress claims, project dashboard
---
# Globe3 Project Management Module

Use this skill when the user asks about project costing, project budgets, progress claims, certified claims, or project dashboard.

## Key Tables

- `set_cnpj_main` — Project master. Description column is `desc_english` (NOT `projcode_desc`).

## Capabilities

- Project Dashboard — overview of all active projects
- Progress Claims and Certified Claims — construction billing cycles
- Tender BQ (Bill of Quantities)
- Project Budget — allocation and transfer
- Enterprise Project Accounting — cost tracking across modules

## Industry Focus: Construction

- Progress Claims / Certified Claims
- Construction WIP Accounting
- Project Budget Transfer / Allocation
- Maincon Backcharge and Allocation
- Project Costing and Budgeting
- Vendor / Subcon Approval
- Sub-Con Portal for e-Submission

## CRITICAL: User-Facing Language

NEVER expose internal technical details to the user. Table names, column names, and field references are for YOUR internal use only. Say "Project" not `set_cnpj_main`. Never mention table names or SQL.

## Internal Rules (do not share with user)

1. Project description is `desc_english` in `set_cnpj_main`, never `projcode_desc`.
2. Project costs may span multiple modules (purchasing, inventory, finance).
3. Always filter by `companyfn` for multi-company environments.
