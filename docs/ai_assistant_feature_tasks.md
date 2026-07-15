# AI Assistant Feature Implementation Plan

## Objective

Deliver three scoped ERP experiences:

1. **General Chat** - the existing manual and realtime ERP assistant.
2. **Fraud Detection** - structured risk indicators with evidence and human review.
3. **Demand Planning** - forecast, stock gap, and replenishment recommendations.

Fraud and demand are operational workspaces, not additional free-form chatbots.
Every request must preserve `masterfn`, `companyfn`, user identity, and language.

## Current implementation status

### General Chat - available

- CFML chat UI, recent sessions, history pagination, feedback, SSE, and step images.
- Server-side CFML proxy keeps the API key outside browser JavaScript.
- FastAPI chat routing supports manual knowledge and realtime ERP tools.

### Fraud analytics - backend foundation available

Existing realtime tools cover:

- Duplicate AP invoices and payments.
- Finance amount anomalies and new-vendor high values.
- Shared vendor bank accounts and vendor risk indicators.
- Stock movement anomalies, shrinkage, negative inventory, and expiry risk.
- Accounting integrity and missing PO/GRN source checks.

Existing workflow storage/API supports scoped alerts and review statuses. Missing work is
the user workspace, scan orchestration, alert deduplication, and scheduled execution.

### Demand planning - backend foundation available

Existing tools cover:

- SKU demand history.
- SKU/location forecast with confidence and backtest evidence.
- Safety stock, reorder point, and recommended quantity.
- Forecast volatility and forecast-versus-actual analysis.

Existing API records recommendation decisions. It does not create an ERP Purchase
Requisition or Purchase Order yet.

## Source mapping

Repository source of truth:

- `cfml-examples/ai_assistant.cfm`
- `cfml-examples/inc_ajax_ai_assistant.cfm`
- `api/`
- `skills/globe3-ai-risk-analytics/`

Deployment copies currently exist under the relevant Globe3 `contentadmin` directory.
Implement and test in this repository first, then sync the reviewed CFML files according
to `docs/cfml-sync-rules.md`.

## Ordered implementation backlog

### P0.1 - Capability document and API contracts [completed]

- Record existing fraud and demand capabilities.
- Define analytics as structured JSON responses, not SSE chat text.
- Keep General Chat behavior unchanged.

Acceptance:

- This document matches the current repository.
- Request and response contracts are represented by backend models.

### P0.2 - Three-mode UI shell [next]

- Add `General Chat`, `Fraud Detection`, and `Demand Planning` tabs.
- Preserve the existing chat DOM and session behavior for General Chat.
- Give fraud and demand independent filters and loading/error/empty states.
- Do not place analytics results into chat bubbles.

Acceptance:

- Switching modes does not destroy the current chat session.
- Each analytics mode restores its own filters and most recent result.
- Layout works at desktop and mobile widths.

### P0.3 - Scoped analytics endpoints

Add dedicated endpoints:

- `POST /analytics/fraud-scan`
- `POST /analytics/demand-plan`

Required scope:

- `masterfn`
- `companyfn`
- authenticated API key

Fraud response:

- Summary counts by severity/type.
- Prioritized findings with risk score, reason code, evidence, and source ID.
- Explicit indicator disclaimer.

Demand response:

- Forecast by SKU/location.
- On-hand, committed, on-order, safety stock, and reorder point evidence.
- Recommended quantity and action with assumptions.

Acceptance:

- Missing scope returns HTTP 400.
- Results cannot include another company scope.
- Upstream tool failures return structured partial-error information.

### P0.4 - CFML proxy routing

Add proxy actions:

- `fraud_scan` -> `/analytics/fraud-scan`
- `demand_plan` -> `/analytics/demand-plan`
- `alert_review` -> existing alert review API
- `recommendation_action` -> existing recommendation action API

Acceptance:

- API key remains server-side.
- ERP cookie/header scope is authoritative; browser parameters cannot override it.
- JSON status and upstream error codes are preserved.

### P1.1 - Fraud review workflow

- Persist selected scan findings into `ai_alerts`.
- Deduplicate by company, rule version, alert type, and source ID.
- Support `new`, `investigating`, `confirmed_issue`, `false_positive`, and `resolved`.
- Record reviewer, note, and timestamps.

Acceptance:

- Re-running the same scan does not create duplicate open alerts.
- Every state change is scoped and auditable.

### P1.2 - Demand recommendation workflow

- Record accepted, adjusted, rejected, and expired decisions.
- Require review before any ERP transaction creation.
- Add a future adapter boundary for Purchase Requisition creation.

Acceptance:

- Recommendation ID and evidence snapshot are retained.
- No endpoint silently creates a PO/PR.
- Adjusted quantity must be positive and auditable.

### P1.3 - Scheduler and observability

- Schedule fraud scans and forecast refreshes by company.
- Add idempotency keys, duration, row count, and failure reason.
- Surface service health without blocking the API event loop.

### P0.5 - Tests and release gate

Required tests:

- Scope required and cross-company isolation.
- Fraud/demand request validation and response contract.
- Alert deduplication and review transitions.
- Recommendation action validation.
- CFML proxy action mapping.
- General Chat SSE regression.
- Desktop/mobile screenshots for all three modes.

## Stakeholder inputs still required

- Risk thresholds and severity policy for each fraud rule.
- Approved source tables/views and document identifiers.
- Forecast horizon, service factor, and lead-time assumptions.
- Required filters by company, vendor, SKU, location, and document type.
- Roles allowed to review alerts and approve replenishment recommendations.
- ERP approval path for future Purchase Requisition creation.

## Safety rules

- Findings are indicators for human review, never definitive fraud verdicts.
- Forecasts must disclose horizon, history window, confidence, and missing data.
- Analytics must use live scoped ERP data, not manual knowledge as evidence.
- No cross-company fallback is allowed.
- No financial or purchasing document is created without explicit approval.
