# SCM Question Coverage Checklist

Goal: track which SCM questions the assistant can answer today, and which ones still need product or data work.

Current coverage:
- Directly answerable from realtime ERP data: 15 / 15
- Requires trained/extracted SCM data: 0 / 15
- Not yet covered: 0 / 15

All questions below now route to scoped PostgreSQL queries through the Skills
server. Forecast values use rolling ERP sales history; they do not use persisted
training artifacts or model files.

## 1. SCM Overview (Last 30 Days)

1. [realtime] "Summary of SCM performance over the last 30 days."
   - Status: realtime sales summary query.
   - Priority: P1
2. [realtime] "Which SKUs had the highest sales growth this month?"
   - Status: compares current and previous half-period quantities.
   - Priority: P0
3. [realtime] "Which products had high inventory but low sales performance?"
   - Status: ranks current stock against period sales.
   - Priority: P1
4. [realtime] "Which supplier had the most delivery delays last month?"
   - Status: ranks suppliers by late deliveries and days late.
   - Priority: P1
5. [realtime] "Which products experienced a surge in demand in the last 4 weeks?"
   - Status: realtime half-period demand growth ranking.
   - Priority: P0

## 2. Market Forecast & Demand Prediction

6. [realtime] "Forecast market demand for the next month by product group."
   - Status: rolling weekly demand projection by product group.
   - Priority: P0
7. [realtime] "Which products are showing stable growth?"
   - Status: ranks products with positive, consistent period growth.
   - Priority: P1
8. [realtime] "Which product groups should increase inventory for the upcoming season?"
   - Status: rolling category demand projection from live sales.
   - Priority: P0
9. [realtime] "Which products have the highest forecast volatility?"
   - Status: ranks coefficient of variation from weekly live demand.
   - Priority: P2
10. [realtime] "Compare this month's forecast demand with last month's actual sales."
    - Status: compares rolling-history projection with prior-month actual revenue.
    - Priority: P2

## 3. Bestselling Product Analysis

11. [realtime] "Display the top 20 bestselling products of the past month."
    - Status: realtime quantity ranking with requested top limit.
    - Priority: P1
12. [realtime] "Which products generated the highest revenue?"
    - Status: realtime product revenue ranking.
    - Priority: P1
13. [realtime] "Which SKUs are experiencing the fastest sales growth?"
    - Status: realtime current-vs-previous period growth ranking.
    - Priority: P0
14. [realtime] "Which products are most often purchased together?"
    - Status: realtime document-line pair frequency analysis.
    - Priority: P0
15. [realtime] "Which best-selling products are running out of stock?"
    - Status: joins bestseller sales with current stock and reorder level.
    - Priority: P1

## What To Verify Next

- Validate the business definitions for “sales”, “late delivery”, and stock level with ERP owners.
- Add automated regression tests for all 15 routes and empty-data scopes.
- Review indexes and query plans on large customer databases.

## Test Expectations

- Supported or partial questions should return a domain-specific SCM answer, not knowledge/manual text.
- Forecast and trend queries should never silently fall back to generic guidance when SCM data exists.
- Unsupported questions should clearly say they are not available yet.

---

# AI Requirement Implementation Backlog

Scope: tender requirements highlighted in red: `100.06`, `102.06`, `102.07`, and `102.08`.

Implementation rule: use tenant-scoped realtime ERP queries through the Skills
server (`masterfn` + `companyfn`). Do not depend on the old SCM training database
or persisted model artifacts. Persisted alert history is allowed, but source
transactions and stock balances must come from the live ERP database.

## Current Gap Assessment

| Requirement | Current status | What exists | Main gap |
|---|---|---|---|
| 100.06 Anomaly Detection and Fraud Prevention | Not covered | AP, GL, purchase, and generic SQL skills can read transactions. | No detection rules, risk score, evidence, alert workflow, or duplicate-payment/vendor-fraud analysis. |
| 102.06 Demand Forecasting | Partial | Realtime rolling weekly demand projection by product/category. | Not yet SKU + location level; seasonality, lead time, confidence range, backtesting, and forecast accuracy are missing. |
| 102.07 Replenishment Recommendations | Partial | Current reorder-level and stock-on-hand queries exist. | No dynamic safety stock, lead-time demand, carrying-cost/stockout-risk balance, location scope, or recommended order date. |
| 102.08 Stock Anomaly Detection | Not covered | Stock totals, sales velocity, and demand volatility can be queried. | No movement anomaly, shrinkage/theft indicator, negative stock, expiry risk, write-off risk, or alert workflow. |

## Shared Foundation Tasks

### AI-FOUND-01 — Confirm business definitions and source fields

- Priority: P0
- Map document types used as posted sales, purchases, receipts, returns, payments, and journals.
- Confirm stock-on-hand source of truth by SKU, warehouse, location, and bin.
- Confirm supplier lead-time fields and whether actual lead time should be calculated from PO to GRN.
- Identify batch/lot expiry fields and stock adjustment/write-off transaction types.
- Define what counts as duplicate payment, unusual transaction, vendor fraud, theft indicator, and expiry risk.
- Acceptance: signed field/rule mapping with sample records for every required signal.

### AI-FOUND-02 — Add a common realtime analytics response contract

- Priority: P0
- Standard fields: scope, analysis period, generated time, rows, risk/score, reason codes, evidence, and data-quality warnings.
- Never return a confident recommendation when required inputs are missing.
- Empty datasets must return a clear no-data reason instead of zero-filled insights.
- Acceptance: all four requirement tools return the same metadata and error structure.

### AI-FOUND-03 — Add performance and tenant-scope safeguards

- Priority: P0
- Enforce `masterfn/companyfn` in every query and joined table.
- Review query plans and required indexes for date, document type, SKU, supplier, warehouse/location, and transaction reference.
- Add query timeout, row limits, pagination, and audit logging.
- Acceptance: cross-tenant tests fail closed; agreed large-client benchmark completes within the target response time.

## 100.06 — Anomaly Detection and Fraud Prevention

### FIN-AI-01 — Duplicate vendor invoice and payment detection

- Priority: P0
- Detect exact duplicates using vendor + invoice/reference number + amount + currency.
- Detect near duplicates using normalized reference, close dates, repeated amount, and same bank/payee where available.
- Exclude voided/reversed transactions and link legitimate credit/reversal documents.
- Output risk score, matched transactions, triggered rules, values, dates, and vendor.
- Acceptance: seeded exact and near duplicates are flagged; legitimate recurring payments can be explained and dismissed.

### FIN-AI-02 — Unusual AP/GL transaction detection

- Priority: P1
- Rules: amount outlier versus vendor/account history, unusual posting time, unusual account/cost-centre combination, round-amount spike, rapid split transactions, and first-time vendor/high-value payment.
- Start with explainable statistical/rule scoring; do not label an item as fraud without evidence.
- Acceptance: every alert contains reproducible evidence and a human-readable reason.

### FIN-AI-03 — Vendor fraud indicators

- Priority: P1
- Detect shared bank/tax/contact details across vendors where these fields are available.
- Detect recent vendor-master changes followed by payment, abnormal bank-detail changes, and payment concentration.
- Record missing source fields as coverage gaps.
- Acceptance: vendor risk result distinguishes confirmed data signals from unavailable checks.

### FIN-AI-04 — Finance alert review workflow

- Priority: P1
- Add alert statuses: new, investigating, confirmed issue, false positive, resolved.
- Store reviewer, note, timestamps, evidence snapshot, and rule version.
- Add admin filters by risk, company, vendor, account, date, status, and rule.
- Acceptance: reviewers can trace an alert to source transactions without modifying ERP accounting data.

## 102.06 — SKU-Level Demand Forecasting

### SCM-AI-01 — Realtime SKU/location demand history

- Priority: P0
- Aggregate posted demand by SKU, warehouse/location, day/week, and requested horizon.
- Handle returns/cancellations consistently and distinguish zero demand from missing data.
- Include supplier lead time and stockout periods where available.
- Acceptance: totals reconcile to ERP sales lines for sampled SKU/location/date scopes.

### SCM-AI-02 — Seasonality-aware forecast

- Priority: P0
- Add weekly/monthly seasonality, recent trend, intermittent-demand handling, and lead-time horizon.
- Return point forecast plus lower/upper confidence range.
- Provide fallback hierarchy: SKU/location -> SKU/company -> category -> insufficient data.
- Acceptance: no trained database dependency; forecast is computed from current scoped ERP history.

### SCM-AI-03 — Forecast backtesting and accuracy

- Priority: P1
- Backtest rolling historical windows and calculate MAE, WAPE/MAPE where valid, bias, and data sufficiency.
- Show forecast method, history window, last actual date, and accuracy warning.
- Acceptance: user can distinguish reliable forecasts from low-confidence estimates.

### SCM-AI-04 — Forecast query and UI output

- Priority: P1
- Support SKU, product group, location, horizon, top-N, and comparison with prior actuals.
- Use friendly headings, sortable tables, pagination, and optional chart output.
- Acceptance: follow-up questions retain scope, horizon, SKU/category, and location from conversation history.

## 102.07 — Replenishment Recommendations

### SCM-AI-05 — Dynamic reorder point and safety stock

- Priority: P0
- Calculate lead-time demand, safety stock, reorder point, and target stock per SKU/location.
- Inputs: forecast demand, demand variability, supplier lead time/variability, service-level policy, on-hand, committed, on-order, and backorder quantities.
- Acceptance: calculation breakdown is visible and reproducible for each recommendation.

### SCM-AI-06 — Recommended order quantity and date

- Priority: P0
- Recommend order quantity, required-by date, and order-by date.
- Respect pack size, MOQ, order multiple, maximum level, existing open PO, and available stock where configured.
- Prevent negative recommendations and duplicate replenishment against open supply.
- Acceptance: recommendation explains every constraint that changed the raw quantity.

### SCM-AI-07 — Carrying-cost versus stockout-risk scoring

- Priority: P1
- Rank recommendations using expected shortage, days of cover, demand confidence, carrying cost, and stockout impact.
- If cost/service-level inputs are unavailable, state that the result is operational priority rather than optimized cost.
- Acceptance: priority score contains named components and no invented cost values.

### SCM-AI-08 — Replenishment approval handoff

- Priority: P2
- Provide recommendation/export first; do not create or post purchase requisitions automatically without explicit authorization and ERP approval controls.
- Track accepted, adjusted, rejected, and expired recommendations.
- Acceptance: no recommendation bypasses the existing ERP approval workflow.

## 102.08 — Stock Anomaly Detection

### SCM-AI-09 — Inventory movement anomaly rules

- Priority: P0
- Detect negative stock, unusual adjustment quantity/value, repeated adjustment, movement outside normal hours, unexpected warehouse/bin transfer, and sales/issue without expected source flow.
- Compare each signal with SKU/location history and peer activity.
- Acceptance: alert includes movement documents, before/after quantity, user/time/location, and triggered rule.

### SCM-AI-10 — Consumption and shrinkage indicators

- Priority: P1
- Compare stock depletion with sales, production/issue, receipt, return, and adjustment records.
- Flag unexplained shrinkage and persistent book-versus-movement inconsistencies.
- Label results as indicators requiring investigation, not proven theft.
- Acceptance: stock equation and unexplained variance are shown per SKU/location.

### SCM-AI-11 — Expiry and write-off risk

- Priority: P1
- For batch/expiry-controlled items, calculate days to expiry, projected consumption before expiry, at-risk quantity, and estimated write-off value.
- Exclude expired/voided batches according to confirmed ERP rules.
- Acceptance: result identifies batch, SKU, location, expiry date, at-risk quantity, and calculation basis.

### SCM-AI-12 — Stock anomaly alert workflow

- Priority: P1
- Reuse the shared alert lifecycle and audit trail.
- Add filters by SKU, warehouse/location/bin, anomaly type, severity, date, and review status.
- Acceptance: alert can be investigated from summary to source stock movements.

## Delivery Order

1. `AI-FOUND-01` to `AI-FOUND-03`
2. `SCM-AI-01`, `SCM-AI-05`, `FIN-AI-01`, `SCM-AI-09`
3. `SCM-AI-02`, `SCM-AI-06`, `FIN-AI-02`, `SCM-AI-10`
4. Accuracy, cost-risk, expiry, vendor-risk, and review workflows
5. UI polish, regression suite, performance validation, and tender evidence pack

## Tender Evidence / Definition of Done

- Demonstrate each requirement on tenant-scoped ERP data with documented sample scenarios.
- Show query inputs, source records, calculation/rule explanation, and output evidence.
- Include empty-data, missing-field, false-positive, and cross-tenant security tests.
- Document limitations explicitly; “AI” wording must not imply fraud confirmation or guaranteed forecasts.
- Provide screenshots/API samples and a requirement-to-test traceability matrix for `100.06`, `102.06`, `102.07`, and `102.08`.
