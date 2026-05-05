---
description: Skills architecture for live ERP data queries — skill-based tools and Text-to-SQL fallback
---

# Skills Architecture (`skills/`)

Node.js modules that query the live PostgreSQL ERP database. Complement the Python RAG backend.

## Structure

```
skills/
  package.json                  # deps: pg, node-sql-parser, express
  _shared/
    orm-fetch.js                # unified DB access — list/findById/count/aggregate/runQuery + SQL logger
    query-safety.js             # SQL validation + scope injection for run_query
  globe3-sales/                 # renamed from globe3-sales-order — covers ALL sales types
    SKILL.md                    # tag_table_usage mapping, filter fields, doc-link format
    tools.js                    # list/get/count/aggregate_sales_documents (generic, tag required)
  globe3-analyst/
    SKILL.md                    # schema reference for ad-hoc queries
    tools.js                    # run_query tool
```

## globe3-sales — Multi-type Design

All Globe3 sales documents share `scm_sal_main` table, distinguished by `tag_table_usage`.
LLM must always specify `tag_table_usage` in filters.

| tag | Document |
|---|---|
| `sal_inv` | Sales Invoice |
| `sal_quo` | Sales Quotation |
| `sal_soe` | Sales Order |
| `sal_soc` | SO Confirmation |
| `sal_rta` | Retail Sales |
| `sal_dn` | Debit Note |
| `sal_cn` | Credit Note |
| `sal_fma` | Pro Forma Invoice |

`orm-fetch.js` model key: `sales` (not `sales_order`). `default_filters` has only `tag_void_yn: 'n'`.

## Two Query Paths

```
User question
  ├─ Common query  → skill tool (list/count/aggregate via orm-fetch)
  │                   Fast, safe, returns charts + document links
  └─ Ad-hoc query  → run_query → validateAndSanitize → PostgreSQL
```

## Skill Pattern (per module)

Each module has two files:
- **`SKILL.md`** — instruction card for LLM: when to use, available tools, filter fields, chart format, doc-link format
- **`tools.js`** — tool definitions calling `ormFetch(operation, modelName, args)`

Standard tools per skill: `list_*`, `get_*`, `count_*`, `aggregate_*`

To add a new module: add model to `MODELS` in `orm-fetch.js`, then create `skills/globe3-{module}/`.

## Safety Layer (`_shared/query-safety.js`)

`validateAndSanitize(sql, masterfn, companyfn)` applies 5 layers:
1. Block forbidden keywords (`INSERT/UPDATE/DELETE/DROP/…`)
2. AST parse — confirm it is a `SELECT`
3. Table whitelist (`ALLOWED_TABLES`) — reject unknown tables
4. Inject both scope filters: `masterfn = 'X' AND companyfn = 'Y'`
5. Add `LIMIT 100` if missing

To allow a new table: add to `ALLOWED_TABLES` in `query-safety.js`.

## ORM (`_shared/orm-fetch.js`)

All skill tools route through `ormFetch(operation, modelName, args)`.

`args` must include:
- `masterfn` — from `cookie.cookmfnunique`
- `companyfn` — from `cookie.cookcfnunique`

Model registry in `MODELS` defines per-table: `masterfn_field`, `companyfn_field`, `select_cols`, `allowed_filters`, `allowed_sorts`, `allowed_groups`, `default_filters`.

**SQL Query Logger:** every `db.query()` call is wrapped in `dbQuery(db, label, sql, params)` which prints resolved SQL (params substituted) + row count + execution time to stdout. Colors: cyan `[SQL]`, yellow label, green result.

## Document Linking (in SKILL.md files)

Sales order links use format: `[DOC_NUMBER](g3doc:sal_soe/UNIQUENUM_PRI)`  
Never truncate `uniquenum_pri`. Never output document numbers as plain text.

## Chart Output (in SKILL.md files)

```g3chart
{"type":"bar","title":"Title","labels":[...],"data":[...],"currency":"VND"}
```
Types: `bar` (compare), `line` (trend), `pie` / `doughnut` (proportions).
