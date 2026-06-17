# CodeGraph First Workflow

> **Mandatory development rule** — applies to all AI agents and human developers working on this project.

---

## Table of Contents

- [Mandatory Startup Procedure](#mandatory-startup-procedure)
- [CodeGraph First Workflow Rule](#codegraph-first-workflow-rule)
- [Workflow Examples](#workflow-examples)
  - [Bug Fixing](#bug-fixing)
  - [Feature Development](#feature-development)
  - [Refactoring](#refactoring)
  - [UI / Layout Issues](#ui--layout-issues)
- [Related Documentation](#related-documentation)

---

## Mandatory Startup Procedure

Before performing **any** task on this project:

1. **Read AGENTS.md** — if it exists, follow its instructions first
2. **Read all documentation in `/docs`** — understand the project rules, architecture decisions, and sync procedures
3. **Use CodeGraph to understand the relevant area** — run `codegraph scan` or open CodeGraph in VS Code to visualize the code structure
4. **Map dependencies** — identify which files, modules, and services are related to the task
5. **Explain findings** — document the root cause, impact analysis, and proposed approach before writing any code
6. **Only then modify code** — propose the smallest possible patch

> ⚠️ **Never start coding immediately.** Always follow the procedure above.

---

## CodeGraph First Workflow Rule

Before any code modification, the AI agent **must**:

1. **Read all documentation in `/docs`**
   - `cfml-sync-rules.md` — CFML sync procedures and API key rules
   - `erp-shell-asset-fixes.md` — ERP shell asset fix procedures
   - `codegraph-workflow.md` — this file
   - `superpowers/specs/*.md` — design specifications

2. **Read AGENTS.md and other AI instruction files**
   - `ROLE.md` — LLM system prompt, behavior rules, guardrails
   - `README.md` — project architecture, setup, daily operation

3. **Use CodeGraph to understand architecture**
   - Open CodeGraph in VS Code (`Ctrl+Shift+P` → `CodeGraph: Generate Diagram`)
   - Visualize class hierarchies, module dependencies, and data flow
   - Identify the relevant components before making changes

4. **Identify related files**
   - Trace imports, includes, and references
   - Check both Python (`api/`) and Node.js (`skills/`) sides
   - Review CFML frontend files (`cfml-examples/`) if UI changes are needed

5. **Check dependencies and impact**
   - API endpoints → router files → service layer → database/models
   - Frontend templates → API calls → data flow
   - Sync rules between `cfml-examples/` and ColdFusion server

6. **Explain root cause before editing**
   - State what the problem is
   - State why it happens (root cause)
   - State what the smallest fix is

7. **Propose the smallest possible patch**
   - One change at a time
   - No scope creep — fix only what is requested
   - No refactoring unrelated code

8. **Avoid blind repository-wide searching** when CodeGraph can provide the answer
   - Use CodeGraph's graph visualization to navigate the codebase
   - Only fall back to text search (`search_files`) when CodeGraph cannot resolve the dependency

---

## Workflow Examples

### Bug Fixing

**Scenario:** User reports that the chat stream returns a 500 error when querying sales data.

**Correct workflow:**

1. Read `/docs/cfml-sync-rules.md` — understand the API key and cookie rules
2. Read `ROLE.md` — understand assistant behavior constraints
3. Open CodeGraph → generate diagram of `api/routers/chat.py` and `api/chat.py`
4. Trace the chat pipeline: `router → chat handler → LLM call → skills server`
5. Identify that the error originates from the skills server connection
6. Check `SKILLS_SERVER_URL` in `.env` and verify the skills server is running
7. **Root cause:** Skills server not started or wrong URL configured
8. **Smallest patch:** Update `.env` or start the skills server — no code change needed

**Incorrect workflow (DO NOT do this):**

1. ❌ Immediately open `api.py` and start searching for "500"
2. ❌ Blindly grep the entire codebase for "error"
3. ❌ Start rewriting error handling without understanding the pipeline

---

### Feature Development

**Scenario:** Add a new endpoint to list all feedback entries with pagination.

**Correct workflow:**

1. Read `/docs/superpowers/specs/*.md` — check if a design spec already exists
2. Read `ROLE.md` — understand guardrails
3. Open CodeGraph → generate diagram of `api/routers/feedback.py` and `api/routers/admin_feedback.py`
4. Study existing patterns: how other list endpoints are structured (pagination, response format, auth)
5. Check `api/models.py` for the feedback database schema
6. Identify that the pattern follows: `router → database query → Pydantic response`
7. **Root cause:** No list endpoint exists for feedback — need to add one
8. **Smallest patch:** Add one new route following the exact pattern of `admin_feedback.py`

**Incorrect workflow (DO NOT do this):**

1. ❌ Start writing the new endpoint without studying existing patterns
2. ❌ Invent a new response format different from all other endpoints
3. ❌ Skip documentation and design review

---

### Refactoring

**Scenario:** Rename the `admin_knowledge` router to `admin_kb` for consistency.

**Correct workflow:**

1. Read `/docs/cfml-sync-rules.md` — check if CFML files reference this router
2. Open CodeGraph → generate a dependency graph showing all files that import or reference `admin_knowledge`
3. Identify all touch points:
   - `api/main.py` — router registration
   - `api/routers/__init__.py` — import
   - `cfml-examples/admin_dashboard.cfm` — API calls to `/admin/knowledge/...`
4. **Root cause:** Inconsistent naming across the project
5. **Smallest patch:** Rename the file, update imports in `main.py` and `__init__.py`, add a redirect or update CFML calls

**Incorrect workflow (DO NOT do this):**

1. ❌ Rename the file and hope nothing breaks
2. ❌ Forget to update CFML frontend references
3. ❌ Skip dependency analysis

---

### UI / Layout Issues

**Scenario:** The admin dashboard knowledge tab table is not responsive on mobile.

**Correct workflow:**

1. Read `/docs/cfml-sync-rules.md` — understand the sync workflow (edit in `cfml-examples/`, sync to ColdFusion)
2. Open CodeGraph → locate `cfml-examples/admin_dashboard.cfm` and its CSS dependencies
3. Check `cfml-examples/globe3-ui.css` for existing responsive patterns
4. Identify that the table uses fixed-width columns that don't stack on small screens
5. **Root cause:** No responsive table breakpoint in the CSS
6. **Smallest patch:** Add a CSS media query in `globe3-ui.css` that switches the table to stacked cards on screens < 768px
7. Run `.\scripts\sync_cfml_examples.ps1` to sync the change

**Incorrect workflow (DO NOT do this):**

1. ❌ Edit the ColdFusion server files directly instead of `cfml-examples/`
2. ❌ Forget to run the sync script after making changes
3. ❌ Rewrite the entire table layout instead of adding a targeted CSS fix

---

## Related Documentation

| File | Purpose |
|---|---|
| `ROLE.md` | LLM system prompt — assistant behavior, guardrails, response format |
| `README.md` | Project architecture, setup, daily operation, configuration |
| `docs/cfml-sync-rules.md` | CFML sync procedures, API key rules, ERP cookie context |
| `docs/erp-shell-asset-fixes.md` | ERP shell asset fix procedures |
| `docs/superpowers/specs/*.md` | Design specifications for features |
| `.codegraph/` | CodeGraph local data directory (gitignored) |
