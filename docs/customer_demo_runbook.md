# Customer Demo Runbook — One-Page Checklist

## Pre-Demo Readiness (15 min before call)

- [ ] FastAPI running: `http://g3rag2.globe3cloud.com:8297/docs`
- [ ] AI_ANALYTICS_URL = `http://g3rag2.globe3cloud.com:8297`
- [ ] Browser logged into target ERP company
- [ ] Run demo readiness check:
  - Open `FRAUD DETECTION` → click `Stored Alerts` → confirm at least 1 alert OR zero-result explanation ready
  - Open `DEMAND PLANNING` → click `Generate Forecast` → confirm at least 1 SKU row OR missing-data explanation ready
- [ ] Confirm `inc_ajax_ai_assistant.cfm` proxies all API calls (no direct browser API keys)

## Demo Script (15 min)

### 1. Right Bot Entry (2 min)

- [ ] Open `wgp_tnorightbot.cfm`
- [ ] Point out `AI CHATBOX`, `FRAUD DETECTION`, `DEMAND PLANNING`
- [ ] Say: "API keys are server-side, never exposed to browser"

### 2. Fraud Detection (6 min)

- [ ] Open `FRAUD DETECTION`
- [ ] Set severity = `All` (or `High/Critical` for manager view)
- [ ] Click `Run Scan`
- [ ] Click `Stored Alerts`
- [ ] Pick one alert → show evidence (source_id, risk_score, reason_code)
- [ ] Mark alert: `Confirmed Issue` / `False Positive` / `Investigating`
- [ ] Add note: "Demo review - customer confirmed"
- [ ] Reload → show status retained
- [ ] Show disposition filter: filter by `Needs Tuning` or `Duplicate`
- [ ] Show review history: click alert → show history dialog

### 3. Demand Planning (7 min)

- [ ] Open `DEMAND PLANNING`
- [ ] SKU = all, Location = all, Horizon = 90 days
- [ ] Click `Generate Forecast`
- [ ] Show summary cards: Total, Reorder, Review, OK
- [ ] Click a Reorder row → show detail (sales history, on-hand, committed, on-order, safety stock)
- [ ] Take action: `Accept` / `Adjust` / `Reject` with reason
- [ ] Show chat history above result area
- [ ] Click `Copy Summary for Buyer` → paste into Notepad to show plain-text output
- [ ] Show forecast selector: switch to a past forecast

## Recorded Live Scope

| Field | Value |
|-------|-------|
| ERP User | |
| Company | |
| Fraud Result Count | |
| Demand SKU Count | |
| Sample Alert ID | |
| Sample SKU Row | |

## Fallback Plans

### If Fraud returns no alerts:
- [ ] Switch severity to `All`
- [ ] Increase max findings to `20`
- [ ] Try specific scan type: `duplicate invoice`, `round amount`, `weekend posting`
- [ ] If still zero: show stored alert list, explain "current scope has no matching indicators"

### If Demand returns no rows:
- [ ] Try `Horizon = 180 days`
- [ ] Confirm SKU master, stock, sales history, PO, committed orders return rows
- [ ] If sales history missing: show low-confidence/missing-input explanation

## Post-Demo

- [ ] Save this runbook with recorded live scope values
- [ ] Take screenshots of:
  - Right Bot with Fraud/Demand links
  - Fraud scan results with one alert expanded
  - Demand forecast with one row detail expanded
  - Copy Summary output
