# ERP AI Assistant — Task Tracker

Tracking rule: unfinished work stays at the top. Completed work moves to the
`Done` section at the bottom. Tasks are ordered by dependency, then priority.

## Status Summary

| Status | Count |
|---|---:|
| In progress / awaiting confirmation | 1 |
| Open P0 | 5 |
| Open P1 | 11 |
| Open P2 | 1 |
| Done | 15 SCM queries + 2 foundation tasks |

## In Progress / Awaiting Confirmation

### AI-FOUND-01 — Confirm business definitions and source fields

- Priority: P0
- Status: Awaiting ERP-owner confirmation.
- Technical schema and population audit: done.
- Evidence: `docs/ai-requirement-data-mapping.md`.
- Remaining:
  - Confirm posted demand document types.
  - Confirm PO → GRN → invoice → payment/reversal links.
  - Confirm authoritative stock balance by location/bin/batch.
  - Confirm expiry sentinel handling (`1899-12-31`, `2099-01-01`).
  - Confirm MOQ, pack size, service level, carrying cost and committed stock sources.
  - Confirm vendor bank/tax/contact and master-change audit sources.
- Done when: field/rule mapping is signed off and validated on at least one additional client database.

## Open — P0 / Build Next

### AI-FOUND-03 — Performance and tenant-scope safeguards

- Requirement: Shared foundation.
- Enforce `masterfn/companyfn` on every table and join.
- Add query timeout, row limit, pagination and audit logging.
- Review indexes for date, document type, SKU, supplier, location and reference.
- Done when: cross-tenant tests fail closed and large-client queries meet the agreed response-time target.

### FIN-AI-01 — Duplicate vendor invoice and payment detection

- Requirement: `100.06` Anomaly Detection and Fraud Prevention.
- Detect exact duplicates by vendor + normalized reference + amount + currency.
- Detect near duplicates by similar reference, repeated amount and close dates.
- Exclude or link voids, credits and legitimate reversals.
- Return risk score, matched records, rules and evidence.
- Implementation: exact duplicate detector is live with shared evidence/contract; near-duplicate similarity and signed credit/reversal linkage remain open.
- Done when: seeded duplicates are detected and legitimate recurring transactions can be explained/dismissed.

### SCM-AI-01 — Realtime SKU/location demand history

- Requirement: `102.06` Demand Forecasting.
- Aggregate posted demand by SKU, warehouse/location and day/week.
- Handle returns/cancellations and distinguish zero demand from missing data.
- Include supplier lead time and stockout periods where available.
- Implementation: live SKU/week and optional location history are available; return/cancellation netting awaits signed mapping.
- Done when: sampled totals reconcile with ERP sales lines by SKU/location/date.

### SCM-AI-05 — Dynamic reorder point and safety stock

- Requirement: `102.07` Replenishment Recommendations.
- Calculate lead-time demand, safety stock, reorder point and target stock by SKU/location.
- Inputs: forecast, demand variability, lead time, service level, on-hand,
  committed, on-order and backorder quantities.
- Do not rely on configured `level_reorder`; sampled values are all zero.
- Implementation: dynamic lead-time demand, safety stock, reorder point, quantity, dates, days of cover, order value and stockout score are live; open supply/commitments/MOQ remain open.
- Done when: every result includes a reproducible calculation breakdown.

### SCM-AI-09 — Inventory movement anomaly rules

- Requirement: `102.08` Stock Anomaly Detection.
- Detect negative stock, unusual adjustment, repeated adjustment, unexpected
  transfer, unusual user/time and issue without expected source flow.
- Compare with SKU/location history and peer activity.
- Implementation: explainable adjustment-quantity outlier detection is live; transfer/negative-balance/user-time rules remain open.
- Done when: each alert includes source documents, before/after quantity,
  user, time, location and triggered rule.

## Open — P1 / After P0 Foundation

### FIN-AI-02 — Unusual AP/GL transaction detection

- Requirement: `100.06`.
- Detect amount outliers, unusual posting time/account/cost centre, round-amount
  spikes, split transactions and first-time high-value vendors.
- Use explainable rule/statistical scoring; never declare fraud without evidence.
- Implementation: AP vendor/source amount outliers and new-vendor high-value indicators are live; GL/time/account/split rules remain open.
- Done when: every alert has reproducible evidence and a human-readable reason.

### FIN-AI-03 — Vendor fraud indicators

- Requirement: `100.06`.
- Detect shared vendor bank/tax/contact details where fields exist.
- Detect master-data changes followed by payment and payment concentration.
- Report unavailable checks as data-coverage gaps.
- Implementation: payment concentration indicator is live; bank/tax/contact and master-change sources remain unconfirmed.
- Done when: output separates confirmed signals from unavailable signals.

### FIN-AI-04 — Finance alert review workflow

- Requirement: `100.06`.
- Statuses: new, investigating, confirmed issue, false positive, resolved.
- Store reviewer, notes, timestamps, evidence snapshot and rule version.
- Filter by risk, vendor, account, date, status and rule.
- Implementation: scoped create/list/review lifecycle and evidence snapshot storage are live; expanded filters/admin UI remain open.
- Done when: alerts trace to source transactions without modifying accounting data.

### SCM-AI-02 — Seasonality-aware forecast

- Requirement: `102.06`.
- Add weekly/monthly seasonality, recent trend, intermittent demand and lead-time horizon.
- Return point forecast plus lower/upper confidence range.
- Fallback: SKU/location → SKU/company → category → insufficient data.
- No training database or persisted model dependency.
- Implementation: realtime weekly trend/variability forecast and confidence range are live; explicit seasonal/intermittent-demand models remain open.
- Done when: output is computed from current tenant-scoped ERP history.

### SCM-AI-03 — Forecast backtesting and accuracy

- Requirement: `102.06`.
- Calculate MAE, WAPE/MAPE where valid, bias and data sufficiency.
- Show method, history window, last actual date and confidence warning.
- Implementation: observed weeks, confidence and last-week APE baseline are live; rolling MAE/WAPE/bias remain open.
- Done when: users can distinguish reliable forecasts from weak estimates.

### SCM-AI-04 — Forecast query and UI output

- Requirement: `102.06`.
- Support SKU, category, location, horizon, top-N and forecast-vs-actual.
- Add friendly headings, sorting, pagination and optional charts.
- Preserve scope/horizon/SKU/location in conversation follow-ups.
- Done when: all forecast follow-up tests retain prior context correctly.

### SCM-AI-06 — Recommended order quantity and date

- Requirement: `102.07`.
- Recommend quantity, required-by date and order-by date.
- Respect MOQ, pack size, order multiple, max level and existing open PO.
- Prevent negative recommendations and duplicate supply.
- Implementation: quantity, order date and receipt date are live; MOQ/pack/open-PO constraints await confirmed fields.
- Done when: output explains every constraint that changes raw quantity.

### SCM-AI-07 — Carrying-cost versus stockout-risk scoring

- Requirement: `102.07`.
- Rank expected shortage, days of cover, demand confidence, carrying cost and stockout impact.
- If policy/cost inputs are missing, label output as operational priority—not cost optimization.
- Implementation: unit cost, estimated order value, days of cover and stockout-risk score are live; policy-based carrying cost is open.
- Done when: scores contain named components and no invented cost values.

### SCM-AI-10 — Consumption and shrinkage indicators

- Requirement: `102.08`.
- Reconcile receipts, sales/issues, production, returns, transfers and adjustments.
- Flag unexplained shrinkage and persistent movement/balance inconsistencies.
- Label results as investigation indicators, not proven theft.
- Implementation: net negative adjustment indicator is live with an explicit partial-coverage warning; signed full stock equation remains open.
- Done when: stock equation and unexplained variance are shown per SKU/location.

### SCM-AI-11 — Expiry and write-off risk

- Requirement: `102.08`.
- Calculate days to expiry, projected consumption, at-risk quantity and estimated write-off value.
- Filter confirmed sentinel/invalid expiry dates.
- Implementation: batch balance, horizon, risk and write-off exposure query is live with conservative sentinel filtering; sentinel meaning remains awaiting confirmation.
- Done when: output includes batch, SKU, location, expiry, quantity and calculation basis.

### SCM-AI-12 — Stock anomaly alert workflow

- Requirement: `102.08`.
- Reuse the shared alert lifecycle and audit trail.
- Filter by SKU, location/bin, anomaly type, severity, date and review status.
- Implementation: shared scoped alert lifecycle is live; stock-specific UI/filter expansion remains open.
- Done when: reviewers can drill from alert summary to source movements.

## Open — P2 / Later

### SCM-AI-08 — Replenishment approval handoff

- Requirement: `102.07`.
- Export/recommend first; never create or post purchase requisitions without
  explicit authorization and existing ERP approvals.
- Track accepted, adjusted, rejected and expired recommendations.
- Implementation: local audited actions are live and explicitly return `erp_document_created=false`; ERP UI/export integration remains open.
- Done when: no recommendation bypasses the ERP approval workflow.

## Verification Required Across Open Tasks

- Validate business definitions for sales, delivery delay, stock balance, payment and reversal.
- Add regression tests for successful, empty-data, missing-field and cross-tenant cases.
- Review query plans on large client databases.
- Produce screenshots/API evidence and requirement-to-test traceability for
  `100.06`, `102.06`, `102.07` and `102.08`.
- Document limitations; AI output must not imply confirmed fraud, theft or guaranteed forecasts.

## Question-to-Query Catalog — Highlighted AI Requirements

All queries below must include:

```sql
masterfn = :masterfn AND companyfn = :companyfn
```

They must also exclude void records unless the question explicitly concerns
voids/reversals. `:days`, `:top`, `:sku`, `:location`, and similar values come
from the question or conversation context.

### 100.06 — Anomaly Detection and Fraud Prevention

| # | Example question | Skill tool | Query mapping |
|---:|---|---|---|
| 1 | Which vendor invoices may be duplicates? / Hóa đơn nhà cung cấp nào có khả năng bị trùng? | `detect_duplicate_ap_transactions` | `gnl_maint_all`, AP rows (`tag_table_usage='paya'`, source `pur_pi`); group by vendor + normalized reference + currency + absolute local amount; return groups having `COUNT(*) > 1`. |
| 2 | Are there duplicate payments in the last 90 days? / Có thanh toán nào bị trùng trong 90 ngày qua? | `detect_duplicate_ap_transactions` | Same duplicate key, limited to payment source such as `maint_cslsegm='csh_paym'` after payment/reversal mapping is approved. |
| 3 | Show unusual high-value AP transactions. / Hiển thị giao dịch AP có giá trị cao bất thường. | `detect_finance_transaction_anomalies` | Calculate vendor/source average and standard deviation; flag amount greater than `AVG + 3 × STDDEV`. |
| 4 | Which transactions differ significantly from vendor history? / Giao dịch nào khác biệt lớn so với lịch sử nhà cung cấp? | `detect_finance_transaction_anomalies` | Window statistics partitioned by `party_code, maint_cslsegm`; rank by explainable risk score. |
| 5 | Which vendors receive an unusually high share of payments? / Nhà cung cấp nào nhận tỷ trọng thanh toán bất thường? | `detect_vendor_risk_indicators` | Sum absolute AP/payment amount by vendor, divide by scoped total, order by payment share descending. |
| 6 | Show split transactions with similar amounts. / Hiển thị giao dịch bị chia thành nhiều khoản tương tự. | Planned extension of `detect_finance_transaction_anomalies` | Group same vendor/date-window/rounded amount; flag multiple records whose combined value exceeds the approved threshold. |
| 7 | Show first-time vendors with high-value transactions. / Hiển thị nhà cung cấp mới có giao dịch giá trị cao. | `detect_finance_transaction_anomalies` | Count vendor history and compare current amount; flag low-history vendors with amounts above their baseline/approved threshold. |
| 8 | Explain why this transaction was flagged. / Vì sao giao dịch này bị cảnh báo? | Alert detail API | Read stored `reason_code`, `risk_score`, evidence snapshot, rule version and source IDs from `ai_alerts`. |
| 9 | List unresolved finance alerts. / Liệt kê cảnh báo tài chính chưa xử lý. | `GET /admin/ai-alerts` | Filter local alert store by tenant, finance alert type and status in `new, investigating`. |

#### Duplicate AP reference query shape

```sql
SELECT party_code,
       normalized_reference,
       currency,
       ABS(local_amount) AS local_amount,
       COUNT(*) AS match_count
FROM scoped_ap_transactions
WHERE transaction_date >= CURRENT_DATE - (:days * INTERVAL '1 day')
GROUP BY party_code, normalized_reference, currency, ABS(local_amount)
HAVING COUNT(*) > 1
ORDER BY match_count DESC, local_amount DESC
LIMIT :top;
```

### 102.06 — Demand Forecasting

| # | Example question | Skill tool | Query mapping |
|---:|---|---|---|
| 1 | Forecast demand for each SKU next month. / Dự báo nhu cầu từng SKU tháng tới. | `forecast_sku_demand_advanced` | Aggregate non-void Sales Invoice quantities by SKU/week; calculate weekly mean, variability and trend; project to requested horizon. |
| 2 | Which products will have the highest demand? / Sản phẩm nào có nhu cầu dự báo cao nhất? | `forecast_sku_demand_advanced` | Same forecast, ordered by `forecast_qty DESC`, limited by `:top`. |
| 3 | Forecast demand by product category. / Dự báo nhu cầu theo nhóm sản phẩm. | `analyze_scm_realtime` (`demand_forecast`, category) | Group `scm_sal_data` by `stkcate_code/stkcate_desc` and weekly period before projection. |
| 4 | Forecast demand by warehouse or location. / Dự báo nhu cầu theo kho hoặc location. | Planned location extension of `forecast_sku_demand_advanced` | Add `location_code` to grouping after authoritative location mapping is approved. |
| 5 | Which SKUs have increasing demand? / SKU nào có nhu cầu đang tăng? | `analyze_scm_realtime` (`growth`) | Compare quantity in current half-period with previous half-period; order by growth percentage. |
| 6 | Which products have unstable demand? / Sản phẩm nào có nhu cầu biến động cao? | `analyze_scm_realtime` (`forecast_volatility`) | Calculate weekly `STDDEV_SAMP(qty) / AVG(qty) × 100`; rank descending. |
| 7 | Compare forecast demand with last month's actual sales. / So sánh dự báo với doanh số thực tế tháng trước. | `analyze_scm_realtime` (`forecast_vs_actual`) | Compare rolling-history daily projection for current month against prior calendar-month actual amount. |
| 8 | Show forecast confidence ranges. / Hiển thị khoảng tin cậy dự báo. | `forecast_sku_demand_advanced` | Return point forecast and variability-based lower/upper bounds; include observed weeks and confidence label. |
| 9 | Which forecasts have low confidence? / Dự báo nào có độ tin cậy thấp? | `forecast_sku_demand_advanced` | Filter/rank rows where observed history is below the approved minimum or backtest error exceeds threshold. |
| 10 | Show forecast accuracy. / Hiển thị độ chính xác dự báo. | Baseline in `forecast_sku_demand_advanced`; rolling backtest planned | Current query returns last-week APE; final query must calculate rolling MAE, WAPE and bias. |

#### SKU weekly demand query shape

```sql
SELECT d.stkcode_code AS sku,
       DATE_TRUNC('week', m.date_trans) AS week,
       SUM(d.qnty_total) AS demand_qty
FROM scm_sal_main m
JOIN scm_sal_data d
  ON d.masterfn = m.masterfn
 AND d.companyfn = m.companyfn
 AND d.uniquenum_pri = m.uniquenum_pri
 AND d.tag_table_usage = m.tag_table_usage
WHERE m.masterfn = :masterfn
  AND m.companyfn = :companyfn
  AND m.tag_void_yn = 'n'
  AND d.tag_void_yn = 'n'
  AND m.tag_table_usage = 'sal_inv'
  AND m.date_trans >= CURRENT_DATE - (:days * INTERVAL '1 day')
GROUP BY d.stkcode_code, DATE_TRUNC('week', m.date_trans);
```

### 102.07 — Replenishment Recommendations

| # | Example question | Skill tool | Query/calculation mapping |
|---:|---|---|---|
| 1 | Which products should be reordered now? / Sản phẩm nào cần đặt thêm ngay? | `recommend_inventory_replenishment` | Join forecast demand, `stk_code_main` on-hand and `stk_code_data.vendor_leadtime_days`; select rows where recommended quantity is positive. |
| 2 | Recommend reorder quantities for each SKU. / Đề xuất số lượng đặt lại cho từng SKU. | `recommend_inventory_replenishment` | `MAX(0, target_stock - stock_on_hand)` using lead-time demand + safety stock + target coverage. |
| 3 | What is the safety stock for this product? / Tồn kho an toàn của sản phẩm này là bao nhiêu? | `recommend_inventory_replenishment` | `service_factor × daily_demand_stddev × SQRT(lead_days)`. |
| 4 | Calculate the dynamic reorder point. / Tính điểm đặt hàng động. | `recommend_inventory_replenishment` | `avg_daily_demand × lead_days + safety_stock`. |
| 5 | Which items may run out before the next delivery? / Mặt hàng nào có thể hết trước lần giao tiếp theo? | `recommend_inventory_replenishment` | Compare `days_of_cover` against lead days; rank by stockout-risk score. |
| 6 | Show products with the lowest days of cover. / Hiển thị sản phẩm có số ngày đủ hàng thấp nhất. | `recommend_inventory_replenishment` | `stock_on_hand / NULLIF(avg_daily_demand,0)`, ordered ascending. |
| 7 | When should the next order be placed? / Khi nào cần đặt đơn tiếp theo? | `recommend_inventory_replenishment` | Baseline returns current date for already-triggered rows; future trigger date requires projected stock trajectory. |
| 8 | What is the expected receipt date? / Ngày dự kiến nhận hàng là ngày nào? | `recommend_inventory_replenishment` | `suggested_order_date + lead_days`. |
| 9 | Rank recommendations by stockout risk. / Xếp hạng đề xuất theo nguy cơ hết hàng. | `recommend_inventory_replenishment` | Score coverage relative to lead-time demand; order score descending. |
| 10 | Explain the recommended quantity. / Giải thích số lượng đề xuất. | `recommend_inventory_replenishment` | Return demand, variability, lead days, safety stock, reorder point, on-hand, target coverage, quantity and warnings. |
| 11 | Show estimated recommended-order value. / Hiển thị giá trị đơn hàng đề xuất. | `recommend_inventory_replenishment` | `recommended_qty × most_recent_or_standard_unit_cost`. |
| 12 | Which recommendations were accepted or rejected? / Đề xuất nào đã được chấp nhận hoặc từ chối? | Recommendation action API | Query `ai_recommendation_actions` by tenant, recommendation ID and action. No ERP document is created automatically. |

#### Replenishment formula

```text
safety_stock   = service_factor × demand_stddev_daily × √lead_days
reorder_point  = avg_daily_demand × lead_days + safety_stock
target_stock   = avg_daily_demand × (lead_days + target_cover_days) + safety_stock
recommended_qty = MAX(0, CEIL(target_stock - available_stock - open_supply))
```

`open_supply`, committed stock, MOQ, pack multiple and location-level available
stock remain mandatory inputs before the recommendation can be called fully optimized.

### 102.08 — Stock Anomaly Detection

| # | Example question | Skill tool | Query mapping |
|---:|---|---|---|
| 1 | Show unusual inventory movements. / Hiển thị biến động kho bất thường. | `detect_inventory_movement_anomalies` | Query stock adjustment documents and flag SKU/location quantities above historical mean + two standard deviations. |
| 2 | Which stock adjustments are abnormally large? / Điều chỉnh kho nào lớn bất thường? | `detect_inventory_movement_anomalies` | Filter `stk_adji`, `stk_adjd`, `stk_badji`, `stk_badjd`; rank by deviation/risk score. |
| 3 | Are there products with negative stock? / Có sản phẩm nào tồn kho âm không? | Planned negative-balance rule | Query authoritative `stkm_*` balance or approved location balance where quantity `< 0`. |
| 4 | Show repeated adjustments by SKU or location. / Hiển thị điều chỉnh lặp lại theo SKU hoặc location. | Planned frequency rule | Group adjustment documents by SKU/location/user/time window and apply approved count threshold. |
| 5 | Which locations have unusual stock reductions? / Location nào có lượng tồn giảm bất thường? | `detect_stock_shrinkage_indicators` | Sum negative versus positive adjustments by SKU/location and rank net decrease. |
| 6 | Show possible inventory shrinkage. / Hiển thị dấu hiệu hao hụt kho. | `detect_stock_shrinkage_indicators` | Current baseline reports net negative adjustments; final stock equation must include receipts, issues, sales, returns and transfers. |
| 7 | Which batches are approaching expiry? / Lô nào sắp hết hạn? | `detect_expiry_writeoff_risk` | Query valid positive batch balances with expiry within `:days`; exclude conservative sentinel range. |
| 8 | Estimate expiry write-off value. / Ước tính giá trị hàng có nguy cơ hủy do hết hạn. | `detect_expiry_writeoff_risk` | `positive_batch_balance × unit_cost`, ordered by risk and exposure. |
| 9 | Show unusual warehouse/bin transfers. / Hiển thị chuyển kho hoặc bin bất thường. | Planned transfer rule | Query `stk_btrn` and source/destination locations/bins; compare route, quantity, user and frequency with history. |
| 10 | Explain why this movement was flagged. / Vì sao biến động này bị cảnh báo? | Alert detail API | Return reason, threshold/baseline, risk score, source document, SKU, quantity, location, user and rule version. |
| 11 | List unresolved stock alerts. / Liệt kê cảnh báo kho chưa xử lý. | `GET /admin/ai-alerts` | Filter scoped alerts by stock type and status `new` or `investigating`. |
| 12 | Which users performed unusual adjustments? / User nào thực hiện nhiều điều chỉnh bất thường? | Planned user aggregation | Group flagged source movements by `userid_cookie`, count and risk-weight the results. |

#### Stock adjustment anomaly query shape

```sql
SELECT sku,
       location_code,
       document_no,
       quantity,
       historical_avg,
       historical_stddev
FROM scoped_stock_adjustments
WHERE ABS(quantity) > historical_avg + (2 * historical_stddev)
ORDER BY risk_score DESC
LIMIT :top;
```

---

# Done

## DONE-FOUND-02 — Common realtime analytics contract and local review storage

- All new finance/SCM AI tools return scope, generated time, period, rows,
  warnings, assumptions, evidence and data-quality status.
- Missing inputs are disclosed; empty results are not converted into fake insights.
- Added tenant-scoped local alert lifecycle and replenishment action audit without writing to ERP accounting/stock data.
- Automated unit and live-contract tests pass.

## DONE-FOUND-01 — Technical schema and data-population audit

- Mapped live sources for sales, purchase/receipt, AP, stock movement,
  location/bin, vendor lead time, batch and expiry.
- Recorded data-quality findings and decisions requiring business sign-off.
- Evidence: `docs/ai-requirement-data-mapping.md`.

## DONE-SCM — Realtime SCM Question Coverage (15/15)

All questions below query tenant-scoped PostgreSQL through the Skills server.
They do not require the old SCM training database or persisted model files.

### SCM Overview

1. [done] Summary of SCM performance over the last 30 days.
2. [done] Which SKUs had the highest sales growth this month?
3. [done] Which products had high inventory but low sales performance?
4. [done] Which supplier had the most delivery delays last month?
5. [done] Which products experienced a surge in demand in the last 4 weeks?

### Forecast and Demand Analysis

6. [done] Forecast market demand for the next month by product group.
7. [done] Which products are showing stable growth?
8. [done] Which product groups should increase inventory for the upcoming season?
9. [done] Which products have the highest forecast volatility?
10. [done] Compare this month's forecast demand with last month's actual sales.

### Product Analysis

11. [done] Display the top 20 bestselling products of the past month.
12. [done] Which products generated the highest revenue?
13. [done] Which SKUs are experiencing the fastest sales growth?
14. [done] Which products are most often purchased together?
15. [done] Which best-selling products are running out of stock?

### Completed Supporting Improvements

- Arbitrary periods such as 60 days, weeks and months are parsed correctly.
- SCM tables use friendly business headings and horizontal overflow handling.
- Technical labels such as `[Realtime SCM: ...]` were removed from user output.
- Sales Invoice follow-up can inherit the prior period and drill down to a paged list.
- Empty data returns a clear reason rather than fabricated generic text.
