# SCM Question Coverage Checklist

Goal: track which SCM questions the assistant can answer today, and which ones still need product or data work.

Current coverage:
- Directly answerable now: 3 / 15
- Partial or fallback only: 8 / 15
- Not yet covered: 4 / 15

## 1. SCM Overview (Last 30 Days)

1. [partial] "Summary of SCM performance over the last 30 days."
   - Status: summary exists, but often returns zero metrics and is too generic.
   - Priority: P1
2. [partial] "Which SKUs had the highest sales growth this month?"
   - Status: routed to trend logic, but often returns no rows.
   - Priority: P0
3. [partial] "Which products had high inventory but low sales performance?"
   - Status: currently falls back to overview, not a true ranking.
   - Priority: P1
4. [partial] "Which supplier had the most delivery delays last month?"
   - Status: currently falls back to overview, not a supplier delay ranking.
   - Priority: P1
5. [partial] "Which products experienced a surge in demand in the last 4 weeks?"
   - Status: routed to trend logic, but often returns no rows.
   - Priority: P0

## 2. Market Forecast & Demand Prediction

6. [partial] "Forecast market demand for the next month by product group."
   - Status: route exists, but backend currently errors on some scopes.
   - Priority: P0
7. [partial] "Which products are showing stable growth?"
   - Status: routed to trend logic, but often returns no rows.
   - Priority: P1
8. [partial] "Which product groups should increase inventory for the upcoming season?"
   - Status: route exists, but backend currently errors on some scopes.
   - Priority: P0
9. [unsupported] "Which products have the highest forecast volatility?"
   - Status: no dedicated tool yet.
   - Priority: P2
10. [unsupported] "Compare this month's forecast demand with last month's actual sales."
    - Status: no dedicated tool yet.
    - Priority: P2

## 3. Bestselling Product Analysis

11. [partial] "Display the top 20 bestselling products of the past month."
    - Status: routed to trend logic, but often returns no rows.
    - Priority: P1
12. [partial] "Which products generated the highest revenue?"
    - Status: currently falls back to overview, not a revenue ranking.
    - Priority: P1
13. [partial] "Which SKUs are experiencing the fastest sales growth?"
    - Status: routed to trend logic, but often returns no rows.
    - Priority: P0
14. [unsupported] "Which products are most often purchased together?"
    - Status: no market basket / affinity analysis yet.
    - Priority: P0
15. [partial] "Which best-selling products are running out of stock?"
    - Status: currently falls back to overview, not a true low-stock bestseller list.
    - Priority: P1

## What To Fix Next

### P0

- Fix `run_scm_model` data availability for forecast and trend queries.
- Add explicit support for market basket / purchased-together analysis.
- Make top-growth and fast-growth queries return real rows instead of empty fallback text.

### P1

- Replace generic overview fallback with more specific answer templates for inventory, supplier delay, revenue, and low-stock questions.
- Add regression tests for every partial and supported question.
- Keep the SCM route map aligned with the skills server output.

### P2

- Add forecast volatility ranking.
- Add forecast vs actual comparison.

## Test Expectations

- Supported or partial questions should return a domain-specific SCM answer, not knowledge/manual text.
- Forecast and trend queries should never silently fall back to generic guidance when SCM data exists.
- Unsupported questions should clearly say they are not available yet.
