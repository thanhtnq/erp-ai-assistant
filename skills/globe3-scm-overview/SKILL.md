---
name: globe3-scm-overview
description: SCM 30-day overview combining sales, inventory, reorder, overstock, purchase, and supplier delivery KPIs
---

# Globe3 SCM Overview

Use this skill when the user asks for an SCM overview, supply chain performance summary, or cross-module SCM health check.

## Available Tool

**`get_scm_overview`** - Returns a structured SCM snapshot for the current `masterfn/companyfn` scope.

## What It Covers

- Sales revenue and transaction count
- Top selling products
- Items below reorder level
- Overstock or high-stock/low-sales items
- Late supplier deliveries from GRN records
- Chart-ready data blocks

## Rules

- Use this for broad questions like "Tóm tắt hiệu suất SCM 30 ngày gần nhất".
- Use `days=30` unless the user asks for another period.
- If the result is empty, state that there is no data for the selected scope/period.

## User-Facing Language

Never mention table names, SQL, or internal document codes.
