---
description: FastAPI endpoints, chat pipeline, admin dashboard backend
alwaysApply: true
---

# API (`api.py`)

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/chat/stream` | SSE streaming chat — requires `X-API-Key` header |
| `POST` | `/greeting` | Welcome message for new sessions |
| `POST` | `/feedback` | Thumbs up/down with optional comment |
| `GET` | `/health` | Liveness check — domain/entry counts + model status |
| `GET\|DELETE` | `/history/{company_id}/{user_id}` | Chat history |
| `GET\|PUT` | `/preferences/{company_id}/{user_id}` | Per-user language + response length |
| `GET` | `/admin/feedback` | List feedback_log (filter: company, rating, flag_status, date) |
| `GET` | `/admin/feedback/stats` | KPI counts (total, thumbs_up/down, flagged counts) |
| `DELETE` | `/admin/feedback/all` | **Demo/test only** — delete all feedback_log rows + reset entry_version scores/flags; logs `clear_feedback` action |
| `POST` | `/admin/entries/{id}/resolve-flag` | Resolve flag + write admin_action_log |
| `POST` | `/admin/entries/{id}/unflag` | Clear flag + write admin_action_log |
| `POST` | `/admin/entries/{id}/flag` | Manual flag + write admin_action_log |
| `GET` | `/admin/action-log` | Full audit trail |
| `GET` | `/admin/documents/stats` | Document registry KPIs (total/done/failed/pending/processing/entries) |
| `GET` | `/admin/documents` | List document_registry (filter: status, company_id, domain, search) |
| `POST` | `/admin/documents/{id}/reingest` | Reset doc to `pending` + log `reingest_queued` action |
| `GET` | `/admin/scheduler/status` | Read scheduler_state.json — all job configs + last run info |
| `POST` | `/admin/scheduler/jobs/{job}/enable` | Enable job + log action |
| `POST` | `/admin/scheduler/jobs/{job}/disable` | Disable job + log action |
| `POST` | `/admin/scheduler/jobs/{job}/run-now` | Spawn ingest subprocess in daemon thread + log action |
| `PUT` | `/admin/scheduler/jobs/{job}/config` | Update interval/time/day in state file + log action |
| `GET` | `/admin/knowledge/stats` | KPI counts — domains, features, entries, versions, flagged, by_type, by_source |
| `GET` | `/admin/knowledge/entries` | Paginated entry list — filters: domain, entry_type, company, flagged, search |
| `GET` | `/admin/knowledge/entries/{id}` | Full entry detail — all current versions with steps, notes, flags |
| `GET` | `/admin/analytics/overview` | KPI: active users, messages, feedback given, positive rate, language dist — params: company_id, days (7/30/90) |
| `GET` | `/admin/analytics/messages` | Daily message + active-user counts — params: company_id, days (7/14/30) |
| `GET` | `/admin/analytics/feedback-trend` | Daily thumbs_up/down series — params: company_id, days (14/30/90) |
| `GET` | `/admin/analytics/top-queries` | Top domains (via feedback), downvote reasons, sample query texts — params: company_id, days, limit |
| `GET` | `/admin/analytics/users` | Paginated per-user activity table — params: company_id, days, limit, offset |

## Chat Pipeline (`POST /chat/stream`)

1. Load chat history (last 6 messages)
2. Detect preference changes (language, response length)
3. `rewrite_query()` — follow-up detection, step navigation, LLM rewrite
4. `detect_intent()` → `error_fix | procedure | faq | reference | any`
5. `check_ambiguity()` — LLM decides if query is clear enough; if not, return clarifying question (skip step navigation)
6. `search_knowledge()` — hybrid vector + SQL search
7. `format_knowledge_context()` — build markdown for LLM
8. Stream LLM response via Gemini SSE
9. Save to `chat_history.db` with `[STEP:N]` markers
10. Map step numbers to images in `document_images/`

## Auto-Flag Rules (`POST /feedback`)

- thumbs_down rate > 30% after 5+ votes → auto-flag
- Immediate flag for reasons: `wrong_answer | incomplete | outdated`
- `log_admin_action()` — writes all mutations to `admin_action_log`, never blocks main action

## Admin Dashboard (`admin_dashboard.cfm`)

Horizontal tab strip: **Feedback** · **Action Log** · [future phases]

Phase roadmap:

| Phase | Name | Status |
|---|---|---|
| 1 | Feedback Dashboard | ✅ Done |
| 2 | Document Management | ✅ Done |
| 3 | Scheduler Management | ✅ Done |
| 4 | Knowledge Base Browser | ✅ Done |
| 5 | System Health Monitor | ✅ Done |
| 6 | User Analytics | ✅ Done |

Feedback tab UI: accordion list, KPI cards, sub-tabs (All / Pending / Resolved), resolve modal with required note textarea. "🗑 Clear All" danger button (red outline) next to Refresh — triggers confirmation dialog, calls `DELETE /admin/feedback/all`, toasts result count.

**Language:** All UI text in English only — no Vietnamese in HTML/JS/CSS.
