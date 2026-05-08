---
name: Admin Dashboard — Phases & Architecture
description: Admin dashboard phase status, clear-feedback utility, health monitor, scheduler/knowledge browser implementation, API endpoints, UI patterns
type: project
---

Admin dashboard is in `admin_dashboard.cfm` — full-width, horizontal tab strip, no sidebar. CSS from `globe3-ui.css`.

**Language rule:** All UI text (HTML labels, JS strings, CSS comments) must be in English only. No Vietnamese anywhere in the dashboard files.

## Clear Feedback (Test/Demo Utility)

**API:** `DELETE /admin/feedback/all` — body: `{ admin_user_id }`, requires `X-API-Key`.

What it does:
1. Deletes all rows from `feedback_log` (chat_history.db)
2. Resets `thumbs_up=0, thumbs_down=0, score=NULL, is_flagged=0, flag_status=NULL, flag_reason=NULL, flag_resolved_at=NULL, flag_resolved_by=NULL, flag_resolution_note=NULL` on ALL `entry_versions` (knowledge.db)
3. Logs `clear_feedback` action in `admin_action_log` with meta: `{deleted_count, reset_count}`

**Returns:** `{ status, deleted_count, reset_count }`

**UI:** "🗑 Clear All" button (`.btn-sm.danger` — red outline) next to Refresh in the Feedback tab sub-tab bar. Shows a multi-line `confirm()` dialog listing the 3 consequences. On success, toasts `"Cleared N feedback records · reset N entry versions"` and reloads stats + list.

**Action log badge:** `clear_feedback` → red badge (same style as `unflag`). Filterable in Action Log dropdown.

**Why:** Central ops UI for managing the AI assistant — feedback quality, document pipeline, scheduler, knowledge browsing, system health.

**How to apply:** When building new admin phases, follow the established tab/panel pattern and reuse existing CSS classes (kpi-card, content-card, sub-tab, log-tbl, job-card).

## Phase Status

| Phase | Name | Status |
|---|---|---|
| 1 | Feedback Dashboard | ✅ Done |
| 2 | Document Management | ✅ Done |
| 3 | Scheduler Management | ✅ Done |
| 4 | Knowledge Base Browser | ✅ Done |
| 5 | System Health Monitor | ✅ Done |
| 6 | User Analytics | ✅ Done |

## Phase 6 — User Analytics

### API endpoints (all require X-API-Key)
| Method | Path | Params | Action |
|---|---|---|---|
| GET | `/admin/analytics/overview` | company_id, days (7/30/90) | KPI: active_users, total_messages, feedback_given, positive_rate, companies[], language_dist, response_len_dist |
| GET | `/admin/analytics/messages` | company_id, days (7/14/30) | Daily series: labels[], messages[], users[] |
| GET | `/admin/analytics/feedback-trend` | company_id, days (14/30/90) | Daily series: labels[], thumbs_up[], thumbs_down[] |
| GET | `/admin/analytics/top-queries` | company_id, days, limit | domains[], reasons[], queries[] — top queried domains via feedback, downvote reasons, sample query texts |
| GET | `/admin/analytics/users` | company_id, days, limit, offset | Paginated: total, items[{user_id, company_id, messages, last_seen, feedback_count, positive_rate, language, response_len}] |

Data sources (no schema changes needed):
- `chat_history.db`: `chat_history` (message counts, active users), `feedback_log` (feedback trend, reasons, queries), `user_preferences` (language/len distribution)
- `erp_knowledge.db`: `entry_versions → entries → features → domains` (top queried domains, via feedback.entry_version_id)

**Note:** message counts reflect stored history only (last 6 messages/session retained by the chat pipeline). UI displays "based on stored history" note.

Helper `_anl_date_threshold(days)` in `api.py` returns ISO date N days ago for SQLite WHERE clauses.

### UI components (tab `#tab-analytics`)
- **4 KPI cards**: Active Users · Total Messages · Feedback Given · Positive Rate (green ≥70%, red <50%)
- **Filter bar**: Company dropdown (auto-populated from overview.companies) · Range select (7/30/90d) · Refresh button
- **3 sub-tabs**: Overview · Users · Query Insights

**Overview sub-panel:**
- `chart-activity` — line chart (dual y-axis): messages (navy fill) + active users (dashed light blue)
- `chart-feedback` — stacked bar: thumbs_up (green) + thumbs_down (red)
- `chart-language` — doughnut: language preference distribution

**Users sub-panel:**
- `#anl-users-body` table: User | Company | Messages | Last Seen | Feedback | Pos. Rate | Language | Resp. Len
- Rate badge: green ≥70% / red <50% / navy otherwise
- Pagination via `anlUsersPage(dir)`, 20/page

**Query Insights sub-panel:**
- `chart-domains` — horizontal bar: top domains by feedback count
- `chart-reasons` — doughnut: downvote reason distribution
- `#anl-queries-list` — `<ol>` of top 10 query texts with occurrence count

### Chart library
**Chart.js 4.4.0** loaded from CDN (`https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js`). Navy palette: `ANL_NAVY = ['#1e3a6e','#2c5282','#4a7fc1','#8fafd8','#c5d5ec','#dde6f5']`. Grid color: `rgba(208,217,234,0.5)`.

### Key JS state & functions
- `anlPage`, `anlTotal`, `anlTab`, `anlCharts` — pagination + active sub-tab + Chart.js instances map
- `loadAnalytics()` — called on `switchTab('analytics')`: fetches overview + fires messages/feedback-trend async; Users/Queries loaded lazily on sub-tab switch
- `renderChart(id, config)` — destroys existing Chart.js instance before re-creating (prevents canvas reuse error)
- `setAnlTab(tab)` — toggles panel visibility, triggers lazy load for users/queries
- `anlApplyFilters()` — resets page to 0, calls `loadAnalytics()`
- `escHtml(s)` — XSS-safe HTML encoding used in table rows

## Phase 5 — System Health Monitor

### API endpoint (requires X-API-Key)
| Method | Path | Action |
|---|---|---|
| GET | `/admin/health` | Full system health snapshot — services, models, databases, scheduler |

Response shape:
```json
{
  "checked_at": "2026-04-28T10:00:00Z",
  "services": {
    "api":           {"status": "ok"},
    "gemini":        {"status": "ok|down", "response_ms": 45},
    "chromadb":      {"status": "ok|down"},
    "postgres":      {"status": "ok|down|skip", "response_ms": 12},
    "skills_server": {"status": "ok|down", "url": "...", "response_ms": 30}
  },
  "models": [
    {"role": "Chat|Ingest|Embedding|Reranker", "name": "...", "available": true|false|null}
  ],
  "databases": {
    "knowledge":   {"exists": true, "size_mb": 5.2, "entries": 450, "versions": 523, "flagged": 3, "path": "..."},
    "chat_history": {"exists": true, "size_mb": 0.8, "messages": 120, "path": "..."}
  },
  "scheduler": {
    "documents": {"enabled": true, "is_running": false, "last_run_status": "success", "last_run_at": "...", "last_run_duration_sec": 45},
    "tickets":   { ... }
  }
}
```

- `postgres` status is `"skip"` when `psycopg2` is not installed
- Reranker `available` uses `get_reranker() is not None` (in-process check)

### UI components (tab `#tab-health`)
- **4 KPI cards**: Overall Status (Healthy/Issues) · Services Up (x/5) · Models Ready (x/4) · Issues count
- **Services grid** (`#h-services-grid`): 5 cards — API Server, Gemini API, ChromaDB, PostgreSQL, Skills Server — each with color dot + OK/Down badge + latency ms
- **Models table** (`#h-models-body`): Role / Model name / Ready|Missing|N/A badge
- **Databases table** (`#h-db-body`): Name / Path (shortened) / Size MB / Records / Status
- **Scheduler table** (`#h-sched-body`): Job / Enabled / Running / Last run / Last status / Duration

### Key JS state & functions
- `hAutoTimer` — interval handle for auto-refresh (30s toggle via `toggleHAutoRefresh()`)
- `loadHealth()` — calls `/admin/health`, renders all sections; hooked to `switchTab('health')`
- `H_SVC_LABELS`, `H_SVC_ICONS` — display maps for service keys

## Phase 4 — Knowledge Base Browser

### API endpoints (all require X-API-Key)
| Method | Path | Action |
|---|---|---|
| GET | `/admin/knowledge/stats` | KPI counts — domains, features, entries, versions, flagged, by_type, by_source |
| GET | `/admin/knowledge/entries` | Paginated list — params: domain, entry_type, company, flagged (1), search, limit, offset |
| GET | `/admin/knowledge/entries/{id}` | Full entry detail — all current versions with steps/notes (JSON parsed) |

`/admin/knowledge/entries` also returns `domains` array in response for populating the filter dropdown (loaded once, guarded by `kbDomainsLoaded` flag).

### UI components
- **4 KPI cards**: Domains & Features count · Indexed Entries & Versions · By Type breakdown (procedure/error_fix/faq/reference) · Flagged Versions (red if > 0)
- **Filter bar**: Domain dropdown (auto-populated) · Type select · Flagged toggle · Search text (Enter triggers apply) · Apply/Reset buttons
- **Entries table** (`#kb-tbody`): Domain › Feature | Entry Name + summary preview | Type badge | Source badges | Version count | Score (color-coded) | Flagged count
- **Entry detail drawer** (`#kb-drawer`): slides in from the right (500px), backdrop click to close. Shows all current `entry_versions` — each version card has company badge (Global / company code), source badge, flag status, steps as `<ol>`, notes as `<ul>`, source_ref link, flag resolution note.

### Key JS state & functions
- `kbPage`, `kbTotal`, `kbDomainsLoaded` — pagination + one-time dropdown population
- `loadKbStats()` — loads KPIs
- `loadKbEntries()` — loads table, populates domain dropdown on first call
- `openKbDetail(id, name)` — fetches and opens drawer
- `closeKbDrawer()` — removes `.open` class; backdrop click also closes
- `KB_TYPE_BADGE`, `KB_SRC_BADGE` — badge class maps for type/source

### CSS
Drawer uses `#kb-drawer` (fixed overlay, pointer-events none until `.open`), `#kb-drawer-panel` (right:-500px → right:0 on open), `#kb-drawer-backdrop` (opacity 0 → 1). All transitions 0.25s ease.

## Phase 3 — Scheduler Management

### State file contract: `schedule/scheduler_state.json`
Single JSON file shared between the API and the scheduler daemon. Written by both.

```json
{
  "documents": {
    "enabled": true,
    "interval": "daily",   // hourly | daily | weekly
    "time": "02:00",       // HH:MM
    "day": "monday",       // for weekly only
    "last_run_at": "2025-01-15T02:00:05",
    "last_run_status": "success",  // success | failed | null
    "last_run_duration_sec": 45,
    "is_running": false
  },
  "tickets": { ... }
}
```

- **API** reads on every `/admin/scheduler/status` GET; writes on enable/disable/run-now/config PUT.
- **scheduler.py** reads at `setup_schedule()` (startup); writes `is_running=true` before each run, then updates `last_run_*` fields after.
- Falls back to `ingest/ingest_config.py` SCHEDULE defaults if state file doesn't exist yet.

### API endpoints (all require X-API-Key)
| Method | Path | Action |
|---|---|---|
| GET | `/admin/scheduler/status` | Returns full state dict |
| POST | `/admin/scheduler/jobs/{job}/enable` | Sets enabled=true |
| POST | `/admin/scheduler/jobs/{job}/disable` | Sets enabled=false |
| POST | `/admin/scheduler/jobs/{job}/run-now` | Spawns daemon thread → `_run_ingest_background()` |
| PUT | `/admin/scheduler/jobs/{job}/config` | Updates interval/time/day |

Valid `{job}` values: `documents`, `tickets`.

### Run-now thread model
`_run_ingest_background(job, admin_user_id)` — runs in a `threading.Thread(daemon=True)`. Uses `_sched_lock` (threading.Lock) to prevent double-starts. After completion writes `ingest_completed` or `ingest_failed` to `admin_action_log`.

### Action log actions used by scheduler
- `scheduler_enable`, `scheduler_disable` — toggle events
- `scheduler_run_now` — manual trigger (admin_user_id set to triggering admin)
- `scheduler_update_time` — config change with meta: {interval, time, day}
- `ingest_completed`, `ingest_failed` — post-run results with meta: {job, duration_sec, trigger}

### UI: job cards
Each job has a card with:
- Status badge: Enabled (green) / Disabled (gray) / Running (navy pulse)
- Schedule description (e.g. "Daily at 02:00")
- Last run result + duration
- Inline edit form (interval select + time input + weekday select for weekly)
- Run Now / Edit Schedule / Enable/Disable buttons

Run History sub-tab reuses `GET /admin/action-log?target_type=scheduler_job`.
