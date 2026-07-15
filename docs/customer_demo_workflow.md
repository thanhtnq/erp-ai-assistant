# Customer Demo Workflow - Fraud Detection and Demand Planning

## Demo Goal

Show the customer two useful ERP AI workflows using real ERP data:

- `Fraud Detection`: create reviewable alerts from live accounting/purchasing signals.
- `Demand Planning`: create replenishment recommendations from live SKU, stock, order, and sales history.

No demo step should depend on fake seed data. If a module has no result, the demo must show why the real ERP scope has no matching data and how the user narrows the scope.

## Readiness Gates

Before demo:

- [ ] Confirm FastAPI is running and `AI_ANALYTICS_URL` points to the active API.
- [ ] Confirm browser is logged into the target ERP company.
- [ ] Confirm `masterfn` and `companyfn` from cookies match the customer scope.
- [ ] Run a live Fraud scan and confirm at least one saved alert or a clear zero-result explanation.
- [ ] Run a live Demand forecast and confirm at least one SKU row or a clear missing-data explanation.
- [ ] Confirm all API calls go through `inc_ajax_ai_assistant.cfm`, not direct browser API key calls.

## 15 Minute Customer Demo Script

### 1. Start From Right Bot

Narrative:

- "These modules run inside the existing ERP session, so the AI reads the same company scope as the logged-in user."

Steps:

1. Open `wgp_tnorightbot.cfm`.
2. Show `AI CHATBOX`, `FRAUD DETECTION`, and `DEMAND PLANNING`.
3. Point out that API keys are server-side only.

Expected result:

- Customer sees the two modules as ERP tools, not external dashboards.

### 2. Fraud Detection Demo

Narrative:

- "This is not a fraud verdict. It is a queue of live ERP indicators for human review."

Steps:

1. Open `FRAUD DETECTION`.
2. Set severity to `All` for demo, or `High/Critical` for a shorter manager view.
3. Run scan.
4. Open stored alerts.
5. Pick one alert and review evidence:
   - document/source id,
   - risk score,
   - reason code,
   - amount/vendor/date evidence if available.
6. Mark the alert:
   - `Confirmed issue` if it looks real,
   - `False positive` if valid business reason exists,
   - `Investigating` if user needs source document,
   - `Resolved` after action taken.
7. Add a note like `Demo review - customer confirmed this needs checking`.
8. Reload stored alerts and show the status is retained.

Expected result:

- Every alert from the scan is saved with customer scope.
- The selected alert has a review status and note.
- Re-running the scan does not duplicate unresolved alerts for the same source.

### 3. Demand Planning Demo

Narrative:

- "This helps the buyer identify SKU/location combinations that need reorder, then inspect why."

Steps:

1. Open `DEMAND PLANNING`.
2. Use `SKU = all`, `Location = all`, `Horizon = 90 days`.
3. Click `Generate Forecast`.
4. Show summary cards:
   - total SKU,
   - reorder,
   - review,
   - OK.
5. Sort visually by action or scan the `Reorder/Review` rows.
6. Click one row and explain:
   - sales history window,
   - average demand,
   - on hand,
   - committed stock,
   - on order,
   - service factor,
   - lead time,
   - missing inputs.
7. Take one recommendation action:
   - `Accept` for clean recommendation,
   - `Adjust` if buyer wants a lower/higher quantity,
   - `Reject` if user knows there is already a purchase/order outside current data.
8. Show the chat history above the result area.

Expected result:

- Forecast rows come from live ERP data.
- The customer sees evidence for why a recommendation exists.
- User action is saved but no ERP PR/PO is created automatically.

## Real Data Fallbacks For Demo

If Fraud returns no alerts:

- Switch severity to `All`.
- Increase finding limit to `20`.
- Run by specific scan type:
  - duplicate invoice,
  - round amount,
  - weekend posting,
  - unusual vendor/payment amount.
- If still zero, show stored alert list and explain the current live scope has no matching indicators.

If Demand returns no rows:

- Use `SKU = all` and `Location = all`.
- Try `Horizon = 180 days`.
- Confirm SKU master, stock, sales history, purchase order, and committed order queries return rows for the company.
- If sales history is missing, show low-confidence/missing-input explanation rather than fake recommendations.

## Alert Feedback Lifecycle

Current statuses:

- `new`: AI created alert, not reviewed.
- `investigating`: user is checking source document.
- `confirmed_issue`: user agrees this alert is valid and needs action.
- `false_positive`: alert logic fired, but user says transaction is valid.
- `resolved`: issue is handled.

Recommended additional dispositions:

- `ignored_by_policy`: customer accepts the risk or rule is not relevant for this company.
- `duplicate_alert`: same issue was already reviewed under another source.
- `needs_rule_tuning`: alert is useful but threshold/reason needs adjustment.
- `insufficient_evidence`: AI does not show enough ERP evidence to decide.

Recommended feedback fields:

- `feedback_status`: one of current status values.
- `disposition_reason`: short reason, for example `vendor approved`, `known backorder`, `manual exception`.
- `reviewer_user_id`: ERP login id.
- `reviewed_at`: timestamp.
- `next_action`: `hold payment`, `check document`, `contact buyer`, `ignore`, `create correction`.
- `rule_feedback`: optional text for improving the detection rule.

## Storage Requirement

Customer requirement:

- Each alert must be saved into the customer's own persisted database scope.

Target behavior:

- Alerts are scoped by `masterfn`, `companyfn`, and ERP login.
- Alert rows are durable after refresh/re-login.
- Feedback updates modify the same alert record.
- Scan reruns update or reuse open alerts instead of duplicating them.
- Resolved/false-positive/ignored alerts stay available for audit.

Implementation decision needed:

- Option A: store alerts in the AI server DB, but strictly tenant-scope by `masterfn/companyfn`.
- Option B: write alerts into a customer-owned ERP database table/schema.
- Option C: dual write, with AI DB as cache and customer DB as system of record.

Recommended for customer demo:

- Use Option A for the immediate demo only if the customer accepts server-side tenant DB.
- Move to Option B or C before production if "their DB" means the customer's ERP PostgreSQL database.

## Implementation Task Plan

### D0 - Demo Data Readiness

- [x] Add a pre-demo health check endpoint that reports live row counts for:
  - invoices/AP documents,
  - GL entries,
  - SKU master,
  - stock on hand,
  - sales history,
  - purchase orders/on-order,
  - committed sales/orders.
- [x] Add a small admin-only page or script that shows whether the current ERP scope can produce demo results.
- [x] Add no-fake-data rule: demo scripts can only use live query results.

Acceptance:

- Demo operator can know before the call whether Fraud and Demand will return useful results.

### F1 - Fraud Alert Persistence In Customer Scope

- [x] Persist Fraud scan findings into `ai_alerts`.
- [x] Deduplicate unresolved alerts by company/source.
- [x] Confirm whether `ai_alerts` is acceptable as customer-owned DB storage.
  - Decision: Use Option A (AI server DB with tenant-scope by masterfn/companyfn) for demo.
  - Move to Option B (customer ERP PostgreSQL table) before production if required.
- [x] Create ERP/customer DB table mapping for alerts (ai_alerts schema documented in api/database.py).
- [x] Add migration/bootstrap for customer alert table (auto-created via CREATE TABLE IF NOT EXISTS).
- [x] Add write-through from Fraud scan into customer alert table (implemented in analytics_fraud.py).
- [x] Add failure handling when AI DB save succeeds but customer DB save fails (try/except with partial_errors).

Acceptance:

- Every Fraud alert is durably saved in the customer-approved DB location.

### F2 - Alert Review And Feedback

- [x] Existing review statuses: `new`, `investigating`, `confirmed_issue`, `false_positive`, `resolved`.
- [x] Add dispositions: `ignored_by_policy`, `duplicate_alert`, `needs_rule_tuning`, `insufficient_evidence`.
- [x] Add structured fields: `disposition_reason`, `next_action`, `rule_feedback`.
- [x] Show reviewer user id from ERP cookie instead of hardcoded `user`.
- [x] Show review history/audit log per alert.
- [x] Add filter by status/disposition (status dropdown + disposition dropdown in Fraud UI toolbar).

Acceptance:

- User can say whether an alert is correct, wrong, ignored, duplicate, or needs tuning.
- That feedback is stored and visible after reload.

### F3 - Demo-Friendly Fraud UI

- [x] Add demo readiness panel using live data counts.
- [x] Add one-click filters: `Needs review`, `High risk`, `False positives`, `Confirmed`.
- [x] Add "why this fired" fields for every rule.
- [x] Add empty-state guidance when no alerts are found in real data.

Acceptance:

- A non-technical customer can understand each alert in under one minute.

### D1 - Demand Planning Demo Workflow

- [x] Demand forecast uses real ERP queries.
- [x] Demand result table is scrollable and row details show evidence.
- [x] Chat history persists.
- [x] Add "Demo recommended rows" filter: show `Reorder` and `Review` rows first.
- [x] Add clear empty-state for missing real data category:
  - no SKU master,
  - no sales history,
  - no stock rows,
  - no on-order/committed rows.
- [x] Add "copy summary for buyer" action.
- [x] Add latest forecast selector so customer can reopen a past forecast.

Acceptance:

- Demand demo produces a clear buyer workflow even when many SKUs are `OK`.

### D2 - Demand Recommendation Feedback

- [x] Row actions: `Accept`, `Adjust`, `Reject`.
- [x] Add reason field for reject/adjust:
  - `existing PO`,
  - `known customer order canceled`,
  - `supplier delay`,
  - `seasonal demand`,
  - `data looks wrong`,
  - `other`.
- [x] Show saved action state when reopening a forecast.
- [x] Add review status per forecast row:
  - `new`,
  - `accepted`,
  - `adjusted`,
  - `rejected`,
  - `converted_to_pr_po` later.

Acceptance:

- Buyer feedback becomes training/validation data for improving the demand formula.

### R1 - Customer Demo Runbook

- [x] Build a one-page checklist for the demo operator (`docs/customer_demo_runbook.md`).
- [ ] Add screenshots after browser smoke test (runbook has placeholders).
- [ ] Record one successful live scope (runbook has table with empty fields).

Acceptance:

- The demo can be repeated without guessing which buttons to press.
- Runbook covers: pre-demo readiness, 15-min script, fallback plans, post-demo tasks.
- Runbook has a table to record live scope values (ERP user, company, counts, sample IDs).

