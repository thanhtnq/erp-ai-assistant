# 3-Module Progress Report

> **Project:** ERP AI Assistant V2  
> **Date:** 21/07/2026

---

## 1. 🤖 Chatbot AI

### ✅ Done

- **Bilingual chat (Vietnamese / English)** — ask questions about live ERP data
- **RAG Knowledge Base** — ingest documents (docx/pdf) into ChromaDB, hybrid search (vector + keyword)
- **Live ERP queries** — via Skills Server (Node.js) connecting to PostgreSQL, 25+ business modules
- **SSE Streaming** — real-time response, no waiting
- **Session history** — conversation context, smart follow-up (SKU, vendor, location...)
- **Intent detection + Ambiguity check** — classify intent, clarify vague questions
- **Admin APIs** — manage knowledge, documents, alerts, memo, scheduler, settings

### 🔧 In Progress

- **Follow-up context inheritance** — vendor, document, location
- **Expand Finance/SCM questions** — integrate new detection skills

### 🧭 Roadmap

| Direction | Description |
|-----------|-------------|
| Expand business scope | Add HR, Project, CRM queries |
| Improve context | More accurate follow-up, complex multi-turn |
| Performance | Cache, pre-aggregation for large queries |
| UI/UX | Dashboard, customizable widgets per module |

---

## 2. ⚙️ Fraud Detection

### ✅ Done

- **Fraud Engine foundation** — `api/fraud/engine.py` + `rules.py` + `domain.py`
- **8 detection rules:**
  - `HighAmountRule` — transaction > p95
  - `FrequencySpikeRule` — daily count spike
  - `HighRefundRule` — abnormal refund count
  - `AbnormalDiscountRule` — unusual discount ratio
  - `TooManyVoidRule` — excessive voids
  - `OutsideWorkingHoursRule` — after-hours activity
  - `RepeatedInvoiceModificationRule` — multiple invoice edits
  - `BackdatedTransactionRule` — backdated entries
- **Deduplication** — SHA-256 hash, never recreates same alert
- **Full alert lifecycle API:**
  - `GET /api/fraud-alerts` — list
  - `GET /api/fraud-alerts/{id}` — detail
  - `POST .../acknowledge` — acknowledge
  - `POST .../resolve` — resolve
  - `POST .../hide` — hide
- **Scheduled scan** — daily at 01:00, configurable thresholds
- **59 unit tests** passed

### 🔧 In Progress

- **Finance AI Detection integration** — duplicate AP, vendor bank, journal balance, 3-way match, unreconciled payments (6/9 features live)
- **Alert review workflow** — new → investigating → confirmed/false_positive/resolved

### 🧭 Roadmap

| Direction | Description |
|-----------|-------------|
| Complete P0 Finance | Approval bypass, working hours, split transactions |
| Expand P1 | AP/GL outliers, vendor fraud indicators, expanded filters |
| Machine Learning | Add ML detector alongside rule-based engine |
| Admin UI | Fraud dashboard, drill-down evidence, charts |

---

## 3. 📊 Demand Planning

### ✅ Done

- **SKU demand forecasting** — realtime from ERP, no training database required
  - Aggregate Sales Invoice by SKU/week
  - Calculate weekly mean, variability, trend
  - Project to requested horizon (weeks/months)
  - Confidence interval (lower/upper bounds)
- **Replenishment Recommendations:**
  - Safety stock = `service_factor × demand_stddev × √lead_days`
  - Reorder point = `avg_daily_demand × lead_days + safety_stock`
  - Target stock, recommended qty, order date, receipt date
  - MOQ, open PO balance, stockout risk score
- **Backtest & Accuracy:**
  - Rolling expanding-window backtest
  - MAE, WAPE, signed bias
  - Confidence label based on history depth + WAPE
- **15 SCM questions** fully supported:
  - Overview, growth, high-stock-low-sales, delivery delays
  - Demand forecast, stable growth, volatility
  - Top sellers, highest revenue, fastest growth
  - Frequently bought together, running out of stock
- **APIs:**
  - `POST /analytics/demand-plan` — create forecast
  - `GET /analytics/demand/results` — get results
  - `GET /analytics/demand/forecasts` — list forecasts
  - `POST /analytics/demand/chat-answer` — demand planning chat

### 🔧 In Progress

- **Seasonality model** — weekly/monthly seasonality, intermittent demand
- **Forecast backtesting** — add seasonal-model backtest
- **Follow-up context** — SKU, period, top-N inheritance

### 🧭 Roadmap

| Direction | Description |
|-----------|-------------|
| Seasonality | Exponential smoothing, Holt-Winters |
| Replenishment | Pack size, order multiple, committed demand |
| Stock anomaly | Negative balance, transfer rules, shrinkage equation |
| Expiry risk | Batch allocation, consumption projection |
| UI | Forecast charts, SCM dashboard |

---

## 📈 Progress Overview

| Module | Done | In Progress | Next |
|--------|------|-------------|------|
| **Chatbot AI** | Core chat, RAG, Skills, Session, Admin APIs | Follow-up context, expand business scope | UI, cache, multi-turn |
| **Fraud Detection** | Engine, 8 rules, alert lifecycle, scheduler, 59 tests | Finance AI detection (6/9 features) | ML detector, admin dashboard |
| **Demand Planning** | 15 SCM queries, forecast, replenishment, backtest | Seasonality, context inheritance | Charts, dashboard, stock anomaly |
