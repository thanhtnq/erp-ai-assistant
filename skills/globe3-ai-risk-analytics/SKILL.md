---
name: globe3-ai-risk-analytics
description: Explainable realtime finance, demand, replenishment, and stock-risk analytics scoped to the current ERP company
---

# Globe3 AI Risk Analytics

All tools query the live ERP PostgreSQL database and require `masterfn` and
`companyfn`. Results are indicators for human review, not proof of fraud/theft
or guaranteed forecasts. Never omit warnings or assumptions.

Tools:

- `detect_duplicate_ap_transactions`
- `get_sku_demand_history`
- `recommend_inventory_replenishment`
- `detect_inventory_movement_anomalies`

