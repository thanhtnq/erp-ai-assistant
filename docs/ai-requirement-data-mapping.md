# AI Requirement Data Mapping

Technical schema audit for requirements `100.06`, `102.06`, `102.07`, and
`102.08`. This document records what is available in the current ERP database;
business meanings still require confirmation from the ERP owner.

## Scope and Safety

- Every query must filter `masterfn` and `companyfn` on all participating tables.
- Only non-void source records are eligible unless a detector explicitly needs
  void/reversal evidence.
- Detection output is an indicator for review, not proof of fraud or theft.
- Forecast/replenishment output must disclose missing inputs and calculation basis.

## Confirmed Technical Sources

| Capability | Primary source | Confirmed fields | Notes |
|---|---|---|---|
| Sales demand | `scm_sal_main` + `scm_sal_data` | document type, transaction date, SKU, category, location, quantity, local amount, customer | Posted/eligible sales document types still require business confirmation. |
| Purchase and receipt lead time | `scm_pur_main` + `scm_pur_data` | supplier, SKU, location, due date, delivery date, quantity, amount, linked document identifiers | Current sample has due and delivery dates populated on all 68,611 non-void purchase headers. |
| Vendor-configured lead time | `stk_code_data` | SKU, supplier, location, bin, `vendor_leadtime_days`, unit cost | 26,792 non-empty lead-time values across 136,827 sampled rows. Validate units and precedence versus actual PO-to-GRN lead time. |
| Item stock policy | `stk_code_main` | on-hand total, min/max/reorder level, slow days, cost, batch/serial flags | In the sampled company all 13,616 reorder-level fields exist but every value is zero. Dynamic replenishment cannot rely on configured reorder level alone. |
| Stock movements | `scm_stk_main` + `scm_stk_data` | movement type, date/user, source/destination location, bin, SKU, quantity, cost, batch, serial, expiry | 405,020 non-void headers, 15 locations and 15 movement types in the sampled company. |
| Stock ledger/balance | `stkm_main_all`, `stkm_main_qnty`, `stkm_batch_qnty` | in/out direction, quantity, balance, unit/total cost, location, bin, batch, serial, expiry, source document | Preferred technical source for movement reconciliation and batch-level evidence; exact balance semantics require validation. |
| Batch expiry | `scm_stk_data`, `stkm_main_all`, `stkm_main_qnty` | batch number, expiry date, quantity/balance, SKU, location/bin | 379,931 movement rows contain expiry dates, but sentinel dates range from `1899-12-31` to `2099-01-01`; sentinel filtering rules are mandatory. |
| Accounts payable | `gnl_maint_all` | vendor, source segment, document/reference numbers, transaction/due date, amount/balance/currency, account, open/closed, void state | 59,170 AP rows and 181 vendors in the sampled company. Source segments include `pur_pi`, `pur_cn`, `csh_paym`, and opening/journal records. |
| General ledger | Existing `general_ledger` skill/model | account, transaction date, document/reference, debit/credit/local amount, dimensions | Physical source table and reversal linkage must be confirmed before anomaly rules are implemented. |

## Candidate Document-Type Mapping

These values are observed or already documented, but must be signed off before
they become detector logic.

| Domain | Candidate code | Candidate meaning |
|---|---|---|
| Sales | `sal_inv` | Sales Invoice |
| Sales | `sal_soc` | Sales Order Confirmation |
| Sales | `sal_soe` | Sales Order Entry |
| Purchase/AP | `pur_pi` | Purchase Invoice source in AP |
| Purchase/AP | `pur_cn` | Purchase Credit Note source in AP |
| Payment | `csh_paym` | Cash/payment source in AP |
| Receipt | `stk_grn`, `stk_gvn` | Goods receipt/vendor note candidates |
| Stock | `stk_adji`, `stk_adjd` | Stock adjustment increase/decrease candidates |
| Stock | `stk_badji`, `stk_badjd` | Batch adjustment increase/decrease candidates |
| Stock | `stk_btrn` | Stock/bin transfer candidate |
| Stock | `stk_put`, `stk_pck` | Put-away and picking candidates |
| Stock | `stk_reclas` | Stock reclassification candidate |

## Requirement Mapping

### 100.06 Finance anomaly and fraud prevention

Immediately feasible signals:

- Exact duplicate AP candidate: tenant + vendor + normalized invoice/reference + amount + currency.
- Near duplicate: same vendor/amount within a configurable date window with similar reference.
- Amount outlier by vendor/source/account.
- Split-payment/invoice pattern in a short period.
- First-time or dormant vendor with unusually high value.

Blocked or conditional signals:

- Shared vendor bank/tax/contact detection requires confirmed vendor-master tables and fields.
- Bank-detail-change-before-payment requires vendor-master audit history.
- Payment reversal/credit linkage requires signed document-link rules.

### 102.06 Demand forecasting

Realtime SKU/location history is technically feasible from sales lines. Forecast
must exclude invalid/void documents and distinguish missing history from zero
demand. Supplier lead time can use actual PO/receipt dates with configured vendor
lead time as a fallback after precedence is confirmed.

### 102.07 Replenishment recommendations

Dynamic calculation is required because sampled `level_reorder` values are all
zero. Feasible inputs are forecast demand, actual/configured lead time, on-hand,
stock-ledger balance, unit cost, location/bin and open purchase quantities.
Committed stock, open-PO balance semantics, MOQ, pack size, service level and
carrying-cost policy still require confirmation.

### 102.08 Stock anomaly detection

Immediately feasible signals:

- Negative balance and unexpected in/out direction.
- Large adjustment relative to SKU/location history.
- Repeated adjustment by SKU, location, user or time window.
- Transfer/source-destination inconsistencies.
- Expiry/write-off risk after filtering sentinel dates.

Conditional signals:

- Theft/shrinkage requires a signed stock equation across receipts, issues,
  transfers, sales, returns and adjustments.
- “Outside normal hours” requires company working-hours/time-zone policy.

## Decisions Required From ERP Owner

1. Which document states count as posted/actual demand?
2. Which purchase documents represent ordered, received, returned and invoiced quantities?
3. Which field/link connects PO, GRN, purchase invoice, payment, credit and reversal?
4. Are `date_due` and `date_delivery` planned/actual dates for every relevant document type?
5. What do `1899-12-31` and `2099-01-01` mean for expiry processing?
6. Which stock-ledger quantity is the authoritative location/bin/batch balance?
7. Where are MOQ, pack size, service level, carrying cost and committed stock stored?
8. Which vendor-master and audit tables contain bank, tax, contact and change history?
9. What severity thresholds and review workflow are acceptable for finance and stock alerts?

## AI-FOUND-01 Status

- Technical schema discovery: complete for current database.
- Data-population sampling: complete for one active tenant/company.
- Candidate field/document mapping: complete.
- Business sign-off and cross-client validation: pending.

