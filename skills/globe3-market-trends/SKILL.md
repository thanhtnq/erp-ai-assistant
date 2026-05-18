---
name: globe3-market-trends
description: Market/internet trend connector for comparing external trend data with stock items
---

# Globe3 Market Trends

Use this skill when the user asks about internet trends, social trends, online market keywords, or products trending outside ERP.

## Available Tool

**`analyze_market_trends`** - Reads configured market trend data and compares it with inventory items.

## Data Source

This tool does not scrape the internet by itself. It reads curated/imported trend files from:

- `data/market_trends/trends.json`

Expected shape:

```json
[
  {"keyword": "usb cable", "score": 92, "source": "google_trends", "category": "Accessories"}
]
```

## Rules

- If no trend file exists, say clearly that internet/social trend data is not configured yet.
- Never invent trending products.
- Use this only for external/internet/social trend questions.
