# Delete Knowledge Entries — Design Spec

**Date:** 2026-05-12  
**Feature:** Add delete capability to Knowledge Base Browser tab in admin dashboard  
**Scope:** Medium

---

## Summary

Add the ability to soft-delete individual knowledge entries or all entries from the admin dashboard Knowledge tab. Soft delete sets `is_active = 0` on the `entries` table — entries become invisible to search and the KB browser without removing data from the database. All delete actions are recorded in `admin_action_log` for audit trail consistency.

---

## Decisions

| Question | Decision |
|---|---|
| Delete type | Soft delete (`is_active = 0`) — reversible at DB level |
| Delete All scope | All entries (`is_active = 0` for all), no ChromaDB purge |
| Single delete placement | New Actions column in table row |
| Delete All placement | Top-right of Knowledge tab header |
| Audit trail | Yes — both actions write to `admin_action_log` |

---

## Backend — New Endpoints (`api.py`)

### `DELETE /admin/knowledge/entries/{entry_id}`

- **Auth:** `X-API-Key` header (existing middleware)
- **Query param:** `admin_user_id` (required — for audit log)
- **Logic:**
  1. Fetch entry by `id` where `is_active = 1` — 404 if not found
  2. `UPDATE entries SET is_active = 0 WHERE id = {entry_id}`
  3. `log_admin_action("delete_entry", target_id=entry_id, note=entry_name, admin_user_id=...)`
- **Response:** `{"deleted": true, "entry_id": X, "name": "..."}`
- **Errors:** 404 if entry not found or already deactivated

### `DELETE /admin/knowledge/entries`

- **Auth:** `X-API-Key` header
- **Query param:** `admin_user_id` (required)
- **Logic:**
  1. `UPDATE entries SET is_active = 0 WHERE is_active = 1` — capture rowcount
  2. `log_admin_action("delete_all_entries", note=f"Deactivated {N} entries", admin_user_id=...)`
- **Response:** `{"deleted": true, "count": N}`
- **Edge case:** If count = 0, still return `{"deleted": true, "count": 0}` (idempotent)

---

## Frontend — UI Changes (`admin_dashboard.cfm`)

### 1. Table — Actions column

- Add 8th `<th>Actions</th>` header (centered, narrow width)
- Each rendered row: add `<td>` with a small icon button
  - Icon: `🗑` or trash SVG
  - Style: `--g3-danger` (`#e53935`) outline, small padding
  - On click: confirmation dialog — *"Delete entry '[Name]'? It will be hidden from the knowledge base."*
  - On confirm: `DELETE /admin/knowledge/entries/{id}` with `admin_user_id`
  - Success: toast "Entry deleted", reload table (silent refresh)
  - Error: toast red with API error message

### 2. Tab header — Delete All button

- Position: top-right of `#tab-knowledge` panel, same row as the tab title/heading area
- Button label: `🗑 Delete All`
- Style: danger-outline (red border, red text, white bg — same as Feedback tab "Clear All" button)
- On click: stronger confirmation dialog — *"Delete ALL knowledge entries? All entries will be hidden from the knowledge base. You will need to run ingest to rebuild."*
- On confirm:
  - Show spinner in button while calling `DELETE /admin/knowledge/entries`
  - Success: toast "X entries deleted", reload KPI cards + table
  - Error: toast red with API error message

### 3. Loading / feedback states

- Single delete: row hides immediately on success (optimistic), table reloads to sync count
- Delete All: button shows spinner during API call, disabled to prevent double-click
- All toasts use existing toast pattern from the dashboard

---

## Data Flow

```
User clicks 🗑 (row)
  → Confirmation dialog
    → DELETE /admin/knowledge/entries/{id}?admin_user_id=...
      → UPDATE entries SET is_active = 0
      → log_admin_action("delete_entry", ...)
      → 200 {"deleted": true, "name": "..."}
    → Toast success → reload table

User clicks 🗑 Delete All
  → Confirmation dialog (stronger)
    → DELETE /admin/knowledge/entries?admin_user_id=...
      → UPDATE entries SET is_active = 0 WHERE is_active = 1
      → log_admin_action("delete_all_entries", ...)
      → 200 {"deleted": true, "count": N}
    → Toast "N entries deleted" → reload KPI + table
```

---

## Files Changed

| File | Change |
|---|---|
| `api.py` | Add 2 new DELETE endpoints |
| `cfml-examples/admin_dashboard.cfm` | Add Actions column to KB table, Delete All button to tab header, JS handlers |

---

## Out of Scope

- Hard delete (removing from DB)
- ChromaDB vector cleanup
- Restore/undo soft-deleted entries
- Filtering deleted entries back in
