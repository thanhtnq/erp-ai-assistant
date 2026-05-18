---
name: globe3-trained-models
description: Run trained SCM ML models for sales forecast and customer churn, plus product trend scoring
---

# Globe3 Trained SCM Models

Use this skill when the user asks for predictions that should use trained SCM artifacts instead of raw SQL only.

## Available Tool

**`run_scm_model`** - Runs a Python SCM model/analyzer for the chat scope.

## When to Use

- Demand or sales forecast for the next days/month.
- Forecast comparison or expected growth.
- Customer churn / retention risk.
- Product trend / potential product scoring.

## Tasks

| task | Uses persisted trained model? | Purpose |
|---|---:|---|
| `forecast` | Yes | Uses `sales_forecaster.pkl` and `sales_trend.parquet` |
| `churn` | Yes | Uses `churn_predictor.pkl` and `customer_retention.parquet` |
| `demand_forecast` | No | Uses extracted product artifacts with moving-average demand forecast by product/category |
| `product_trend` | No | Uses live sales-history scoring from `ProductTrendAnalyzer` |
| `auto` | Depends | Infers from the user question |

## Rules

- Always pass the user's original question in `query`.
- Use `forecast` for demand/sales prediction questions.
- Use `demand_forecast` when the user asks by product, SKU, item, or product category.
- Use `churn` for customer retention/churn-risk questions.
- Use `product_trend` for potential products or growth trend scoring.
- If the tool returns `ok=false`, tell the user which trained artifact is missing and suggest running training for that `masterfn/companyfn` scope.

## User-Facing Language

Never mention Python files, table names, or internal artifact paths unless explaining a missing training artifact.
