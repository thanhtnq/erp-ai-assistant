# AI Right Bot Module Tasks

## Goal

Add two ERP desktop modules below `AI CHATBOX` in `wgp_tnorightbot`:

- `FRAUD DETECTION` is an AI alert workspace.
- `DEMAND PLANNING` is a dedicated demand-planning chatbox/workspace.

Both modules must preserve ERP scope through cookies and `inc_ajax_ai_assistant.cfm`.
Browser JavaScript must never call FastAPI with the API key directly.

## Current Status

Done:

- Added `cfml-examples/inc_ai_desktop_links.cfm`.
- Added `cfml-examples/ai_fraud_alerts.cfm`.
- Added `cfml-examples/ai_demand_planning.cfm`.
- Added `cfml-examples/inc_wgp_tnorightbot_11_panel.cfm` — source-controlled include for right bot panel.
- Included `inc_ai_desktop_links.cfm` after `AI CHATBOX` in deployment file `contentadmin/inc_wgp_tnorightbot_11_panel.cfm`.
- Added CFML proxy actions for fraud scan, demand plan, alert review, recommendation action, and demand settings.
- Demand Planning page now has scrollable result table, full-width forecast card, `m8` settings panel, pagination, row detail expansion, and empty states.
- Fraud Detection page now has scrollable findings area, severity/type/status filters, and review controls (status update + note per finding).
- Settings module (`api/routers/admin_settings.py`) with fraud + demand defaults per user/company.
- Alert persistence + deduplication in fraud scan (Task 2).
- Fraud Alert Badge in Right Bot (P1.2) — badge count next to FRAUD DETECTION link, scoped to current ERP company, non-blocking on API failure.
- Recommendation Actions in Demand UI (P2.1) — Accept/Adjust/Reject buttons per row, adjusted quantity input, action state persistence.
- P2.3 - Better Demand Calculation Inputs — on-order (PO), committed (SO), service factor, Z-score safety stock, lead time, missing inputs disclosure.
- Local API direct checks returned data:
  - Fraud scan: 4 findings in demo scope.
  - Demand plan: 86 SKU rows in demo scope.

Important runtime note:

- Remote API `124.155.214.47:8297` did not have the new analytics routes and returned `404`.
- Local FastAPI `http://localhost:8000` must be running for current analytics testing.
- Customer demo runbook and implementation plan: `docs/customer_demo_workflow.md`.

## User Workflow - How To Exploit The Two Modules

### 1. Daily Risk Check - Fraud Detection

Goal:

- Help AP/Finance users find suspicious accounting activity before payment, posting, or month-end close.

User steps:

1. Open Right Bot, click `FRAUD DETECTION`.
2. Select scan scope:
   - `All` for daily check.
   - `Duplicate invoice` when reviewing AP payment runs.
   - `Round amount` or `Weekend posting` when reviewing unusual entries.
3. Select severity:
   - Start with `Critical/High` for daily work.
   - Use `All` for weekly audit review.
4. Click `Run Scan`.
5. Review each card:
   - `Risk score` tells priority.
   - `Reason code` tells why the item was flagged.
   - Evidence fields show document/vendor/date/amount where available.
6. Set review status:
   - `Investigating` when user needs to check source document.
   - `Confirmed issue` when the transaction needs correction or hold.
   - `False positive` when the transaction is valid.
   - `Resolved` when the issue has been handled.
7. Add review note and save.

Data exploited by user:

- Open critical/high alert count in Right Bot badge.
- Persistent alert list in `ai_alerts`.
- Review status, reviewer, and note for audit trail.
- Original finding evidence stored in alert evidence JSON.

Expected outcome:

- Finance can prioritize risky invoices/entries without searching raw ERP tables.
- Repeated scans do not create duplicate open alerts for the same unresolved issue.
- Manager can see which findings are still new/investigating/confirmed/resolved.

### 2. Replenishment Planning - Demand Planning Chatbox

Goal:

- Help purchasing/inventory users estimate replenishment needs by SKU/location and keep discussion history with the forecast.

User steps:

1. Open Right Bot, click `DEMAND PLANNING`.
2. Set filters:
   - `SKU = all` for broad planning.
   - Specific SKU for focused review.
   - `Location = all` or one warehouse/location.
   - `Horizon = 30/60/90/180 days`.
3. User can either click `Generate Forecast` or type a request like `forecast all SKU for 90 days`.
4. Read summary metrics:
   - `Total SKU`: number of SKU rows returned.
   - `Reorder`: items with recommended reorder quantity.
   - `Review`: low-confidence or missing-input items.
   - `OK`: items with enough stock.
5. Scroll the result table and click a row to inspect evidence:
   - historical sales window,
   - historical order count,
   - last order date,
   - on-hand stock,
   - on-order stock,
   - committed stock,
   - service factor and lead time,
   - missing inputs.
6. Decide row action:
   - `Accept` when recommendation is reasonable.
   - `Adjust` when buyer wants a different quantity.
   - `Reject` when user has outside knowledge or an existing order.
7. Use chat history as the planning trail:
   - user request is saved,
   - AI forecast summary is saved,
   - clear only when the user wants a fresh planning thread.

Data exploited by user:

- Forecast rows from `demand_forecasts` and `demand_sku_forecasts`.
- Chat history from `ai_module_chat_messages`.
- Recommendation actions from recommendation action records.
- User/company scoped settings from `ai_settings`.

Expected outcome:

- Buyer can quickly identify which SKU/location combinations need replenishment.
- User can explain why each recommendation exists before creating any ERP purchasing document.
- m8 can tune default horizon/result limit/auto-run for the company workflow.

### 3. m8 Settings Workflow

Goal:

- Let the admin user configure module behavior without changing code.

User steps:

1. Login as `m8`.
2. Open `DEMAND PLANNING`.
3. Click `Settings`.
4. Set default horizon, SKU/location filters, result limit, and auto-run.
5. Save and reload page.

Expected outcome:

- Settings reload automatically by current ERP login/company cookies.
- Non-m8 users can run the module but do not see the Settings control.

### 4. Recommended Operating Rhythm

Daily:

- Run `FRAUD DETECTION` with `Critical/High`.
- Run `DEMAND PLANNING` for 30 or 90 days.
- Review only exceptions: fraud findings and demand rows with `Reorder/Review`.

Weekly:

- Fraud: filter `All severity`, resolve old investigating alerts.
- Demand: review accepted/adjusted recommendations before creating ERP PR/PO.

Month-end:

- Fraud: confirm no critical/high unresolved alerts.
- Demand: compare reorder recommendations with actual purchasing decisions.

## P0 - Make Current Modules Usable

### P0.1 - Right Bot Link Source Control ✅

Task:

- [x] Bring `inc_wgp_tnorightbot_11_panel.cfm` or a minimal patch/include strategy into repo source control.
- [x] Avoid relying on a manual deployment-only edit.

Files:

- `contentadmin/inc_wgp_tnorightbot_11_panel.cfm`
- `cfml-examples/inc_ai_desktop_links.cfm`
- `cfml-examples/inc_wgp_tnorightbot_11_panel.cfm` — **created**

Acceptance:

- [x] Running `.\scripts\sync_cfml_examples.ps1` must not remove the two AI module links.
- [ ] `wgp_tnorightbot.cfm` shows `AI CHATBOX`, `FRAUD DETECTION`, and `DEMAND PLANNING` in the expected order. *(cần kiểm tra trên ERP)*

### P0.2 - Demand Planning UI Polish ✅

Task:

- [x] Keep result table readable at 1366px, 1600px, and 1920px widths.
- [x] Add pagination or virtual paging if result sets exceed the configured `result_limit`.
- [x] Add row detail expansion showing evidence fields from `details_json`.
- [x] Add clear empty states for:
  - no demand rows,
  - no sales history,
  - backend partial errors,
  - API unavailable.

Files:

- `cfml-examples/ai_demand_planning.cfm`

Acceptance:

- [x] Forecast result area scrolls independently without losing header or composer.
- [x] User can inspect all returned rows up to `Result Limit`.
- [x] No text overlaps at desktop width or mobile width.

### P0.3 - Demand Settings for m8 ✅

Task:

- [x] Finish `m8` settings flow.
- [x] Store and apply:
  - `horizon_days`,
  - `sku_filter`,
  - `location_filter`,
  - `result_limit`,
  - `auto_run`,
  - future `service_factor`.
- [x] Add visible saved/failed state.

Files:

- `api/routers/admin_settings.py`
- `cfml-examples/inc_ajax_ai_assistant.cfm`
- `cfml-examples/ai_demand_planning.cfm`
- `tests/test_ai_analytics.py`

Acceptance:

- [x] `m8` sees Settings.
- [x] non-`m8` does not see Settings.
- [x] Saved settings reload on page open.
- [x] `auto_run=y` triggers one forecast after settings load.

### P0.4 - Fraud Detection UI Usability ✅

Task:

- [x] Bring Fraud UI to the same standard as Demand.
- [x] Add scrollable findings area.
- [x] Add severity/type/status filters.
- [x] Add latest scan selector.
- [x] Show partial errors from backend.
- [x] Add review controls on each finding.

Files:

- `cfml-examples/ai_fraud_alerts.cfm`
- `cfml-examples/inc_ajax_ai_assistant.cfm`
- `api/routers/analytics_fraud.py`

Acceptance:

- [x] Fraud scan results are readable and scrollable.
- [x] User can update finding status and note.

## P1 - Persist and Review Alerts

### P1.1 - Persist Fraud Findings into `ai_alerts` ✅

Task:

- [x] When a fraud scan returns findings, create or update durable `ai_alerts`.
- [x] Deduplicate by:
  - `masterfn`,
  - `companyfn`,
  - `alert_type`,
  - `source_id`,
  - `rule_version`,
  - unresolved status.

Files:

- `api/routers/analytics_fraud.py`
- `api/routers/admin_ai_alerts.py`
- `api/database.py`
- `tests/test_ai_analytics.py`

Acceptance:

- [x] Re-running the same scan does not create duplicate open alerts.
- [x] Resolved alerts allow a new alert if the issue appears again.
- [x] Alert evidence includes original finding payload and scan metadata.

### P1.2 - Fraud Alert Badge in Right Bot ✅

Task:

- [x] Show count badge next to `FRAUD DETECTION`.
- [x] Count only open critical/high alerts for current `masterfn/companyfn`.
- [x] Load count through CFML proxy, not direct API.

Files:

- `cfml-examples/inc_ai_desktop_links.cfm`
- `cfml-examples/inc_ajax_ai_assistant.cfm`
- `api/routers/admin_ai_alerts.py`

Acceptance:

- [x] Badge shows `0`, exact count, or `99+`.
- [x] Badge is scoped to current ERP company.
- [x] If API is down, right bot still renders without blocking.

### P1.3 - Fraud Review Workflow ✅

Task:

- [x] Implement review status transitions:
  - `new`,
  - `investigating`,
  - `confirmed_issue`,
  - `false_positive`,
  - `resolved`.
- [x] Capture reviewer and note.
- [x] Add audit log entry for each review.

Files:

- `api/routers/admin_ai_alerts.py`
- `api/routers/admin_action_log.py`
- `cfml-examples/ai_fraud_alerts.cfm`
- `tests/test_ai_analytics.py`

Acceptance:

- [x] Invalid statuses are rejected.
- [x] Every state change is scoped and auditable.
- [x] UI refreshes changed row without requiring full page reload.

## P2 - Demand Recommendation Workflow

### P2.1 - Recommendation Actions in Demand UI ✅

Task:

- [x] Add accept, adjust, reject actions to each recommendation row.
- [x] Save through `recommendation_action`.
- [x] Ask for adjusted quantity when action is `adjusted`.

Files:

- `cfml-examples/ai_demand_planning.cfm`
- `cfml-examples/inc_ajax_ai_assistant.cfm`
- `api/routers/admin_ai_alerts.py` or dedicated recommendation router
- `tests/test_ai_analytics.py`

Acceptance:

- [x] Accepted/rejected/adjusted actions persist.
- [x] Adjusted quantity must be positive.
- [x] UI shows latest action state per recommendation.
- [x] No ERP PR/PO is created.

### P2.2 - Demand Forecast Evidence ✅

Task:

- [x] Show forecast evidence for each row:
  - history window,
  - historical order count,
  - last order date,
  - stock value,
  - missing inputs.
- [x] Add row detail drawer or expansion.

Files:

- `api/routers/analytics_demand.py`
- `cfml-examples/ai_demand_planning.cfm`

Acceptance:

- [x] User can see why a recommendation was made.
- [x] Missing history is shown as low confidence, not hidden.

### P2.3 - Better Demand Calculation Inputs ✅

Task:

- [x] Add on-order and committed stock when source tables are confirmed.
- [x] Add configurable service factor.
- [x] Add lead-time source:
  - actual PO-to-GRN lead time (hardcoded 14 days, configurable later),
  - fallback vendor lead time.

Files:

- `api/services/erp_db.py`
- `api/routers/analytics_demand.py`
- `docs/ai-requirement-data-mapping.md`

Acceptance:

- [x] Response includes calculation basis (service_factor, z_score, lead_time_days, daily_rate in details_json).
- [x] Missing inputs are listed in `details_json.missing_inputs`.
- [x] Formula is deterministic and testable (SMA + Z-score safety stock).

## P3 - Access, Settings, and Deployment

### P3.1 - Separate Access Rights

Task:

- [ ] Confirm with ERP owner whether to keep shared `AiCbDt` or add separate rights:
  - `AiFdDt` for Fraud Detection,
  - `AiDpDt` for Demand Planning.

Files:

- `cfml-examples/inc_ai_desktop_links.cfm`
- access-control source files if new rights are approved

Acceptance:

- [ ] Unauthorized users do not see restricted module links.
- [ ] Existing `AI CHATBOX` behavior does not change.

### P3.2 - API URL Configuration ✅

Task:

- [x] Remove hard-coded analytics local/remote split.
- [x] Read API target from `.env` consistently.
- [x] Add a safe development override for local analytics routes.

Files:

- `cfml-examples/inc_ajax_ai_assistant.cfm`
- `.env`
- `docs/cfml-sync-rules.md`

Acceptance:

- [x] Local dev can use `localhost:8000` (set `AI_ANALYTICS_URL=http://localhost:8000` in `.env`).
- [x] Deployed environment can use hosted API after routes are deployed (set `AI_ANALYTICS_URL` to production URL).

### P3.3 - Browser Smoke Tests

Task:

- [ ] Add repeatable smoke checklist or Playwright tests for:
  - right bot menu links,
  - Fraud scan,
  - Demand forecast,
  - m8 settings,
  - non-m8 hidden settings.

Files:

- `tests/` or `debug/`
- optional Playwright config

Acceptance:

- [ ] Screenshot verifies right bot layout.
- [ ] Demand result table is scrollable.
- [ ] Fraud findings render.
- [ ] Settings visibility matches user.

## F2 - Extended Alert Dispositions ✅

Task:

- [x] Add structured disposition fields to `ai_alerts` table:
  - `disposition_reason` — why the alert was handled (ignored_by_policy, duplicate_alert, needs_rule_tuning, insufficient_evidence).
  - `next_action` — what to do next (hold_payment, check_document, contact_buyer, ignore, create_correction).
  - `rule_feedback` — free-text feedback for rule tuning.
- [x] Add `reject_reason` to `ai_recommendation_actions` table.
- [x] Expose new fields in `AIAlertReview` and `AIRecommendationAction` Pydantic models.
- [x] Add migration helpers for existing databases.
- [x] Show extended disposition UI in Fraud Detection page (collapsible ext-review section).
- [x] Pass new fields through CFML proxy.

Files:

- `api/models.py`
- `api/database.py`
- `api/routers/admin_ai_alerts.py`
- `cfml-examples/ai_fraud_alerts.cfm`
- `cfml-examples/inc_ajax_ai_assistant.cfm`

Acceptance:

- [x] Review PATCH accepts disposition_reason, next_action, rule_feedback.
- [x] Existing alerts without these fields still work (migration).
- [x] Fraud UI shows extended disposition controls.
- [x] Recommendation POST accepts reject_reason.

## F3 - Demo-Friendly Fraud UI ✅

Task:

- [x] Add demo readiness panel (pre-demo health check).
- [x] Add demo badge styling for ready/not-ready states.
- [x] Add CSS classes for demo-panel, demo-ready, demo-not-ready.

Files:

- `cfml-examples/ai_fraud_alerts.cfm`
- `api/routers/admin_health.py`

Acceptance:

- [x] Demo panel CSS is present (hidden by default, shown via JS).
- [x] Demo readiness endpoint returns live row counts.

## D0 - Demo Data Readiness Endpoint ✅

Task:

- [x] Add `/admin/demo-readiness` endpoint that checks live ERP row counts for Fraud and Demand modules.
- [x] Report fraud readiness: duplicate_invoices, new_vendors, inventory_anomalies, finance_anomalies.
- [x] Report demand readiness: sku_master, current_stock, sales_history, on_order, committed.
- [x] Return summary with fraud_ready and demand_ready booleans.

Files:

- `api/routers/admin_health.py`
- `cfml-examples/inc_ajax_ai_assistant.cfm`

Acceptance:

- [x] Endpoint returns counts without running full scan/forecast.
- [x] Timeout is 60s (some queries may be slow on first run).
- [x] Errors per check are reported individually, not blocking the whole response.

## D1 - Forecast Selector and Row Filter ✅

Task:

- [x] Add forecast selector dropdown in Demand UI to switch between saved forecasts.
- [x] Add filter badges (All, Reorder, Review, OK) to filter rows by recommendation status.
- [x] Add `demand_forecasts_list` and `demand_results` CFML proxy actions.
- [x] Add `GET /api/analytics/demand/forecasts` and `GET /api/analytics/demand/results` backend endpoints.

Files:

- `cfml-examples/ai_demand_planning.cfm`
- `cfml-examples/inc_ajax_ai_assistant.cfm`
- `api/routers/analytics_demand.py`

Acceptance:

- [x] Forecast selector loads on forecast completion.
- [x] Selecting a forecast loads its results without re-running.
- [x] Filter badges update the table in real-time.
- [x] Pagination works with filtered results.

## D2 - Reject Reason and Saved Action State ✅

Task:

- [x] Add reject reason dropdown when user clicks Reject on a recommendation.
- [x] Show saved action state (Accepted/Rejected/Adjusted) on page reload.
- [x] Add `GET /admin/ai-recommendations/actions` endpoint to list saved actions.
- [x] Load saved actions on forecast render and apply to matching rows.

Files:

- `cfml-examples/ai_demand_planning.cfm`
- `cfml-examples/inc_ajax_ai_assistant.cfm`
- `api/routers/admin_ai_alerts.py`

Acceptance:

- [x] Reject requires a reason before submission.
- [x] Saved actions persist across page reloads.
- [x] Rejected rows show the reject reason next to the button.
- [x] Matching is done by recommendation_id (forecast_id-sku-location).

## D3 - Review History and Copy Summary ✅

Task:

- [x] Add `GET /admin/ai-alerts/{alert_id}/history` endpoint to return review history for a specific alert.
- [x] Add `alert_review_history` CFML proxy action.
- [x] Add `showReviewHistory()` function in Fraud UI to display review history in an alert dialog.
- [x] Add `GET /api/analytics/demand/summary-text` endpoint to generate a plain-text summary of a demand forecast.
- [x] Add `demand_summary_text` CFML proxy action.
- [x] Add `copySummary()` function in Demand UI to copy forecast summary to clipboard.

Files:

- `api/routers/admin_ai_alerts.py`
- `api/routers/analytics_demand.py`
- `cfml-examples/inc_ajax_ai_assistant.cfm`
- `cfml-examples/ai_fraud_alerts.cfm`
- `cfml-examples/ai_demand_planning.cfm`

Acceptance:

- [x] Fraud UI can show review history for any alert.
- [x] Demand UI can copy a plain-text summary to clipboard.
- [x] Summary includes forecast ID, horizon, totals, reorder items, and review items.
- [x] Both features work through CFML proxy (no direct API calls).

## D4 - Demand Chat Intent Guard ✅

Task:

- [x] Stop treating every chat prompt as a forecast request.
- [x] Only run Demand forecast when prompt contains demand/reorder/SKU/forecast intent.
- [x] Add lightweight chat commands:
  - `help` shows example Demand prompts.
  - `status` summarizes current forecast rows.
  - `show reorder rows` filters current result.
  - `show review rows` filters current result.
  - `show ok rows` filters current result.
  - `copy summary` copies buyer summary.
- [x] Avoid duplicate user messages when a prompt triggers forecast.
- [x] Return scoped out-of-domain answer for unrelated chat.

Files:

- `cfml-examples/ai_demand_planning.cfm`

Acceptance:

- [x] Asking unrelated questions does not call `demand_plan`.
- [x] Forecast prompts still run forecast and persist chat history.
- [x] Result filters can be driven from chat without re-running forecast.

## D5 - Demand Planning Guided Layout ✅

Task:

- [x] Add a visible "Question Lanes" panel outside the chat transcript.
- [x] Split suggested questions into clear lanes:
  - Forecast Demand,
  - Find Reorder Risk,
  - Review Data Quality,
  - Buyer Actions.
- [x] Add clickable prompt chips so users know what to ask.
- [x] Make no-data result state actionable instead of showing four zero metrics.
- [x] Keep chat history as its own scrollable transcript.
- [x] Move prompt examples into the sidebar so old conversations remain visible.
- [x] Prevent `forecast all SKU for 90 days` from being parsed as SKU=`for`.
- [x] Replace empty no-data card with an AI diagnosis surface.
- [x] Show live demand readiness counts when forecast returns zero rows.
- [x] Add next-step buttons for no-data cases:
  - try 180 days,
  - reset to all SKU,
  - show question examples.

Files:

- `cfml-examples/ai_demand_planning.cfm`

Acceptance:

- [x] User can understand what the module detects without typing first.
- [x] Suggested questions can trigger forecast/filter/copy-summary flows.
- [x] Empty forecast state explains what to try next.
- [x] Chat history remains readable after adding guided prompts.
- [x] No-data state explains missing ERP data instead of showing a large blank card.

## D6 - Demand AI Chat Reasoning Summary ✅

Task:

- [x] Return AI processing summaries as chat messages instead of raw panels in the result workspace.
- [x] Make Demand Planning a chat-first workspace.
- [x] Hide the result workspace until forecast rows exist.
- [x] Support natural questions:
  - `Demand là gì?`
  - `Bạn kiểm tra gì phía sau?`
  - `Vì sao không có forecast?`
  - `Reorder là gì?`
  - `Safety stock là gì?`
- [x] Summarize public processing steps:
  - understand request,
  - apply ERP scope,
  - read ERP data,
  - calculate demand,
  - persist forecast/chat trail.
- [x] Show what data sources are checked in the no-data chat response.
- [x] Clarify that missing ERP rows are not fabricated.

Files:

- `cfml-examples/ai_demand_planning.cfm`

Acceptance:

- [x] User can chat with the module and receive a natural Demand Planning answer.
- [x] No-data answer explains what was checked and what data is needed next inside the chat transcript.
- [x] Result workspace is reserved for forecast tables or a minimal placeholder.
- [x] Result workspace does not occupy the main screen when there are no rows.

## D7 - Demand Smart Chat Backend ✅

Task:

- [x] Add backend Demand chat answer endpoint.
- [x] Use latest forecast context and sample rows when answering questions.
- [x] Use Gemini through the existing server-side wrapper when available.
- [x] Add deterministic Demand fallback when model/API is unavailable.
- [x] Route natural Demand questions from the chat UI to the backend instead of hard-coded browser replies.
- [x] Keep forecast/filter workflow commands fast on the frontend.

Files:

- `api/routers/analytics_demand.py`
- `cfml-examples/inc_ajax_ai_assistant.cfm`
- `cfml-examples/ai_demand_planning.cfm`
- `tests/test_ai_analytics.py`

Acceptance:

- [x] `helo`, `Demand?`, `reorder là gì`, `vì sao không có forecast`, and similar questions get contextual chat answers.
- [x] Browser still never calls the API key directly.
- [x] If Gemini is unavailable, fallback answer stays inside Demand Planning scope.

## Release Gate

Run before handoff:

```powershell
codegraph status
.\.venv\Scripts\python.exe -m pytest tests/test_ai_analytics.py -v
.\scripts\sync_cfml_examples.ps1
```

Manual ERP browser checks:

- Open `http://localhost:8119/v50foldersetadmin/v50stringg3new/v50master/contentadmin/wgp_tnorightbot.cfm` in an authenticated ERP session.
- Confirm right bot links appear below `AI CHATBOX`.
- Open `FRAUD DETECTION`, run scan, review rows.
- Open `DEMAND PLANNING`, run forecast, scroll result table.
