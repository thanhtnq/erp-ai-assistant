# Context-First LLM Query Engine Tasks

## Goal

Make the ERP AI chatbox understand user intent from conversation context before choosing a semantic report, skill, SQL template, or manual-search answer.

## Current Implementation Status

Completed in this branch:

- Follow-up query rewrite before routing for Sales Order header, Detail Items, and Driver Info.
- Dedicated `api/conversation_state.py` state extractor for compact session context.
- Generic Globe3 document number detection, including visible numbers like `SOB10344933`.
- Driver Info routing accepts typo-style input such as `driver infor tab SOB10344933`.
- Data-query intent detection now recognizes standalone ERP document follow-ups like `SOB10344933 this one`.
- Chat stream uses the context-resolved query before intent detection and semantic/tool routing.
- Semantic matches now prefer deterministic Sales Order tab runners before generic SQL templates.
- Semantic resolver accepts `context_state` and boosts the report/tab used in the current conversation.
- Internal ERP keys are redacted from direct output paths.
- Chat/session DB indexes were added for session-scoped history lookup.
- Frontend chart follow-up now restores chartable context from visible history or per-session browser storage.
- Server-side chart follow-up fallback avoids raw/irrelevant LLM answers when no chartable table context exists.
- Added regression coverage for multi-user/session chat-history isolation.
- Server-side `chat_result_context` stores compact result metadata for the latest table/chartable result.
- Legacy monolith entrypoint `api.py` now has the same session-aware context rewrite and result-context save path for `uvicorn api:app`.
- Legacy monolith `api.py` also has deterministic Sales Order Header, Detail Items, and Driver Info runners before LLM tool selection.
- Added `scripts/context_scale_smoke.py` for a 1,000+ user/session isolation smoke test.
- Added `scripts/chat_http_load_smoke.py` for concurrent HTTP smoke testing against `/chat/stream`.
- Added `docs/context-first-deploy-checklist.md` for server deployment and QA steps.

Still to do:

- Run true concurrent HTTP load testing against the deployed FastAPI service after deployment.

Current problem:

- The assistant often routes by keyword too early.
- Follow-up questions like `this one`, `SOB10344933`, `show that tab`, or `convert to chart` are not always resolved from prior context.
- Semantic metadata exists, but the orchestration layer does not consistently merge chat context with the current user message before tool selection.

Target behavior:

```text
User: list of sale order 6/2026
AI: shows sales order list
User: driver infor tab SOB10344933
AI: shows Driver Info tab for Sales Order SOB10344933
User: SOB10344932 this one
AI: shows Driver Info tab for Sales Order SOB10344932
User: chart this
AI: renders chart from the last result
```

---

## Phase 1 - Conversation State Foundation

### Task 1.1 - Define Conversation State Object

Add a normalized state object generated from recent chat history.

Fields:

```json
{
  "last_module": "sales",
  "last_document_type": "sales_order",
  "last_document_no": "SOB10344933",
  "last_report_id": "SAL-SO-DRIVER-INFO",
  "last_tab": "Driver Info",
  "last_filters": {
    "date_from": "2026-06-01",
    "date_to": "2026-07-01",
    "tag_table_usage": "sal_soe"
  },
  "last_result_shape": "table",
  "last_result_columns": ["document_no", "customer", "amount_local"],
  "last_successful_tool": "run_query"
}
```

Implementation area:

- `api/chat.py`
- `api/llm.py`
- optionally new file: `api/conversation_state.py`

Done when:

- State can be built from the last N messages.
- State ignores raw internal fields like `uniquenum_pri`.
- State prefers latest user intent over assistant table content when there is conflict.

Tests:

- History contains Sales Order list, state returns `last_document_type=sales_order`.
- History contains Driver Info clarification, state returns `last_tab=Driver Info`.
- History contains several document numbers, latest explicit user document wins.

---

## Phase 2 - Contextual Query Rewriter

### Task 2.1 - Rewrite Follow-Up Before Routing

Before semantic matching or deterministic tool routing, rewrite the current query using conversation state.

Examples:

| Current User Message | Context | Rewritten Query |
|---|---|---|
| `this one` | last tab = Driver Info, current doc = SOB10344933 | `show Driver Info for Sales Order SOB10344933` |
| `SOB10344933 this one` | last tab = Driver Info | `show Driver Info for Sales Order SOB10344933` |
| `show detail` | last doc = SOB10344933 | `show Detail Items for Sales Order SOB10344933` |
| `convert to chart` | last result = sales order table | `render chart from last sales order result` |
| `which document numbers?` | last query = count sales orders in 7/2026 | `list sales orders in 7/2026 document numbers` |

Implementation area:

- `api/llm.py`
- `api/chat.py`

Done when:

- All data-query routing uses `effective_query`, not raw `q.text`.
- Logs show:

```text
[context] data query: 'SOB10344933 this one' -> 'show Driver Info for Sales Order SOB10344933'
```

Tests:

- `driver infor tab SOB10344933` routes to Driver Info.
- `SOB10344932 this one` after Driver Info context routes to Driver Info.
- `show detail` after Sales Order header routes to Detail Items.
- `convert this to pie chart` after a table returns chart JSON/render event.

---

## Phase 3 - Intent Classifier Upgrade

### Task 3.1 - Separate Intent From Tool Selection

Introduce a small internal classification result before choosing a report/tool.

Output:

```json
{
  "intent": "erp_data_query",
  "action": "show_detail_tab",
  "module": "sales",
  "document_type": "sales_order",
  "document_no": "SOB10344933",
  "requested_view": "driver_info",
  "needs_clarification": false
}
```

Classifier should combine:

- rules for stable ERP entities
- semantic metadata report catalog
- optional LLM classification only when rules are not enough

Done when:

- Tool selection no longer depends only on keyword matching.
- If multiple reports match, user gets clickable suggestions.
- If one report is obvious from context, it runs directly.

Tests:

- `info of SOB10344933` returns suggestions if no tab context exists.
- `this one` returns Driver Info if previous assistant asked for Driver Info document number.
- `driver tab` asks for document number if no doc exists anywhere in context.

---

## Phase 4 - Semantic Report Resolver Upgrade

### Task 4.1 - Semantic Match Uses Context

Semantic resolver should accept both the current query and conversation state.

Input:

```python
resolve_semantic_report(
    query=effective_query,
    context_state=state,
    masterfn=...,
    companyfn=...,
    company_code=...
)
```

Ranking rules:

- Company-specific metadata wins over global.
- Exact report/tab from context wins over generic report.
- Current explicit user request wins over context.
- If confidence is low and more than one report matches, return options instead of guessing.

Done when:

- Adding a new child tab in Excel is enough for suggestions.
- Asking follow-up about that tab uses the same report without keyword repetition.

Tests:

- Upload metadata with `Driver Info`, then ask `what tabs are supported?`.
- Click/use `Driver Info`, then ask `SOB... this one`.
- Add a second child tab and verify clarification shows both options.

---

## Phase 5 - Result Memory And Chart Conversion

### Task 5.1 - Store Last Query Result Metadata

Do not store huge row data in chat memory. Store only safe result metadata and a short result cache key.

Example:

```json
{
  "last_result_id": "res_abc123",
  "shape": "table",
  "row_count": 10,
  "columns": ["document_no", "customer", "amount_local"],
  "chartable": true,
  "default_chart": "bar"
}
```

Done when:

- `show chart`, `pie chart`, `convert this to chart` uses the previous result.
- No chart option appears when there is no row data.
- No chart option appears for empty result.

Tests:

- Sales order table -> `show pie chart` renders chart.
- Empty result -> no chart suggestion.
- Manual/procedure answer -> no chart suggestion.

---

## Phase 6 - Guardrails And Response Quality

### Task 6.1 - Never Leak Internal Fields

Block internal ERP keys from all render paths.

Never show:

- `uniquenum_pri`
- `uniquenum_uniq`
- `masterfn`
- `companyfn`
- `party_unique`
- `tag_void_yn`
- `tag_deleted_yn`

Done when:

- Formatter redacts internal fields even if tool result contains them.

Tests:

- Tool returns `uniquenum_pri`; chat output must not contain it.
- `show full info` does not expose internal identifiers.

### Task 6.2 - Better Clarification

When missing required data, ask a precise question.

Bad:

```text
Please provide the document number.
```

Good:

```text
Which Sales Order should I open Driver Info for?
```

Done when:

- Missing document number asks for the right document type and tab.
- Ambiguous report returns clickable options.

---

## Phase 7 - Performance And Scale

### Task 7.1 - Keep Context Small

For thousands of users, never send full chat history or huge table rows to the LLM.

Use:

- last 10-20 messages
- compressed conversation state
- result cache references
- semantic metadata lookup by module/company

Done when:

- Context builder is O(last messages), not O(all history).
- Semantic resolver queries indexed SQLite/PostgreSQL tables.
- Large ERP result sets are paginated and aggregated server-side.

Tests:

- 1,000 users with separate sessions do not cross-leak context.
- 10,000 learned query rows still resolve under target latency.
- Large Sales Order table returns first page/top N only.

Recommended indexes:

```sql
CREATE INDEX IF NOT EXISTS idx_chat_session_user_company
ON chat_history(user_id, company_id, session_id, created_at);

CREATE INDEX IF NOT EXISTS idx_semantic_learned_scope
ON semantic_learned_queries(scope_type, company_code, module, verified);

CREATE INDEX IF NOT EXISTS idx_semantic_reports_scope
ON semantic_reports(scope_type, company_code, module, report_id);
```

---

## Phase 8 - Test Suite

### Unit Tests

Files:

- `tests/test_context_state.py`
- `tests/test_ai_analytics.py`
- `tests/test_admin_semantic.py`

Must cover:

- document number extraction
- follow-up rewrite
- semantic report selection
- child tab routing
- chart conversion
- internal-field redaction

### Integration Tests

Use FastAPI TestClient:

- Upload semantic Excel.
- Run ingest.
- Ask chat query.
- Ask follow-up.
- Validate final answer uses correct tool.

### Manual QA Script

Run these in chat:

```text
list of sale order 6/2026
driver infor tab SOB10344933
SOB10344932 this one
show detail for this one
show chart
info of SOB10344933
```

Expected:

- No manual answer when ERP data exists.
- No repeated request for document number when it is present in current message or context.
- No internal IDs in answer.
- Chart only appears when previous result has chartable data.

### Scale Smoke Script

```bash
python scripts/context_scale_smoke.py --users 1000 --messages 4
```

Expected:

- Prints `OK users=1000`.
- Target user/session returns only its own messages.
- Latest result context is chartable and session-scoped.

### HTTP Load Smoke Script

Run this after the FastAPI server is already running:

```bash
python scripts/chat_http_load_smoke.py --url http://127.0.0.1:8000/chat/stream --requests 50 --concurrency 10
```

Expected:

- `failed=0`
- Each response contains `event: done`
- The default query uses the chart fallback path, so it should not require Gemini or the skills server.

Local note:

- A small local run with the correct API key passed at `requests=5`, `concurrency=2`, `failed=0`.

---

## Scale Answer

Can this support thousands of users?

Yes, if the design avoids sending everything to the LLM and avoids querying huge ERP data directly in chat.

Required:

- Session-isolated conversation state.
- Indexed semantic metadata tables.
- Cached short result summaries.
- Paginated ERP queries.
- Background ingest jobs.
- No per-request full Excel parsing.
- No full chat history in prompt.
- API workers behind a process manager or load balancer.

Risk if not fixed:

- Higher LLM cost.
- Slow response under concurrent usage.
- Wrong context between users if session scope is weak.
- Random answers if tool selection stays keyword-only.
