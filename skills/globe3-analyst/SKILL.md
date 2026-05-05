---
name: globe3-analyst
description: Ad-hoc SQL analysis across ERP tables when no specific skill covers the question
---

# Globe3 Analyst

Use this skill for **cross-module or ad-hoc analysis** questions that no specific skill tool covers.

## When to Use

- Cross-module questions: "Compare sales vs purchase by customer this year"
- Line-item analysis: "Top selling products", "revenue by category/brand"
- Complex multi-condition queries not expressible via standard skill filters
- Customer retention / RFM analysis, churn indicators

## When NOT to Use

- A dedicated skill exists → use that skill instead (faster, has charts + document links)
- User asks **how to do something** in ERP → use the RAG knowledge base, not this skill
- Simple single-table lookups covered by list/count/aggregate tools

## Available Tool

**`run_query`** — Executes a custom SELECT query. The server automatically:
1. Validates it is a SELECT statement
2. Injects `masterfn = '<client>'` AND `companyfn = '<entity>'` as mandatory scope filters
3. Caps results at 100 rows if no LIMIT is specified

**Scope model:**
- `masterfn` — client-level identifier (one per customer)
- `companyfn` — entity/subsidiary identifier (one client can have many entities)
- Both are required together to prevent cross-entity data leakage

**Rules for writing SQL:**
- Write standard PostgreSQL syntax
- Do NOT include `masterfn` or `companyfn` in your WHERE clause — both are injected automatically
- Always include a `LIMIT` (max 100)
- Use exact column names from the schema below
- For text search use `ILIKE '%value%'`
- Always filter `tag_void_yn = 'n'` to exclude voided records
- Use table aliases when joining (e.g. `m` for scm_sal_main, `d` for scm_sal_data)

---

## Database Schema

### `scm_sal_main` — Sales Transaction Headers

All sales document types share this table, discriminated by `tag_table_usage`:

| tag_table_usage | Meaning |
|---|---|
| `sal_soe` | Sales Order Entry (quotation/order) |
| `sal_soc` | Sales Order Confirmation |
| `sal_inv` | Sales Invoice |
| `sal_quo` | Sales Quotation (legacy) |
| `sal_cn`  | Sales Credit Note |
| `stk_do`  | Delivery Order |
| `stk_doc` | Delivery Order Confirmation |

**Columns:**
```
uniquenum_pri          TEXT     Business primary key (links to scm_sal_data)
dnum_auto              TEXT     Document number (e.g. "SOE00123", "INV00456")
date_trans             DATE     Transaction date (YYYY-MM-DD)
date_due               DATE     Due / payment date
party_unique           TEXT     Customer ID (unique key)
party_code             TEXT     Customer code
party_desc             TEXT     Customer name
amount_local           DECIMAL  Total in local currency
amount_forex           DECIMAL  Total in foreign currency
curr_short_forex       TEXT     Currency code (VND, USD, SGD, ...)
curr_rate_forex_f_calc DECIMAL  Exchange rate
staff_code             TEXT     Salesperson code
staff_unique           TEXT     Salesperson ID
deptunit_code          TEXT     Business unit code
deptunit_desc          TEXT     Business unit name
location_code          TEXT     Warehouse / location code
creditterm_desc        TEXT     Payment terms (e.g. "Net 30")
delivtype_desc         TEXT     Delivery type
sendby_desc            TEXT     Shipping method
notes_memo             TEXT     Header notes / remarks
salestaxpct            DECIMAL  Tax percentage
tag_void_yn            CHAR(1)  'y' = voided — always filter: tag_void_yn = 'n'
tag_table_usage        TEXT     Document type (see mapping above)
masterfn               TEXT     Client identifier — DO NOT filter, auto-injected
companyfn              TEXT     Entity/subsidiary identifier — DO NOT filter, auto-injected
```

---

### `scm_sal_data` — Sales Line Items

One row per product line in each sales document. Links to `scm_sal_main` via `uniquenum_pri`.

**Join pattern:**
```sql
FROM scm_sal_main m
JOIN scm_sal_data d ON d.uniquenum_pri = m.uniquenum_pri
                   AND d.tag_table_usage = m.tag_table_usage
                   AND d.companyfn = m.companyfn
```

**Columns:**
```
uniquenum_uniq         TEXT     Line item business key
uniquenum_pri          TEXT     FK → scm_sal_main
row_item_num           DECIMAL  Line sequence number
stkcode_code           TEXT     Product code
stkcode_unique         TEXT     Product ID
stkcode_desc           TEXT     Product name
skucode_code           TEXT     SKU code
brand_code             TEXT     Brand code
brand_desc             TEXT     Brand name
stkcate_code           TEXT     Product category code
stkcate_desc           TEXT     Product category name
stkvendor_code         TEXT     Vendor code
stkvendor_desc         TEXT     Vendor name
qnty_total             DECIMAL  Ordered quantity
qnty_uomstk            DECIMAL  Quantity in stock UOM
bal_qnty_total         DECIMAL  Remaining / unfulfilled quantity
uom_stk_code           TEXT     Unit of measure
price_unitlist_local   DECIMAL  List price (local currency)
price_unitrate_local   DECIMAL  Actual unit price (local currency)
price_unitrate_forex   DECIMAL  Actual unit price (foreign currency)
discount_pct           DECIMAL  Discount percentage
amount_local           DECIMAL  Line total (local currency)
amount_forex           DECIMAL  Line total (foreign currency)
amount_tax_local       DECIMAL  Tax amount (local currency)
gst_taxa_code          TEXT     Tax code
party_code             TEXT     Customer code (denormalized)
party_desc             TEXT     Customer name (denormalized)
staff_code             TEXT     Salesperson code (denormalized)
deptunit_code          TEXT     Business unit code (denormalized)
location_code          TEXT     Warehouse code (denormalized)
date_trans             DATE     Transaction date (denormalized)
tag_void_yn            CHAR(1)  'y' = voided — always filter: tag_void_yn = 'n'
tag_item_taxable_yn    CHAR(1)  'y' = taxable item
tag_closedmain_yn      TEXT     'y' = parent document closed
tag_table_usage        TEXT     Matches parent document type
masterfn               TEXT     Client identifier — DO NOT filter, auto-injected
companyfn              TEXT     Entity/subsidiary identifier — DO NOT filter, auto-injected
```

---

### `prj_pbill_main` — CRM Tickets / Support Cases

```
uniquenum_pri       TEXT    Primary key
dnum_auto           TEXT    Ticket number
acctnumdesc_disc    TEXT    Ticket subject / title
notes_memo          TEXT    Issue description
date_trans          DATE    Created date
tag_closed03_yn     CHAR(1) 'y' = resolved/closed
tag_void_yn         CHAR(1) 'y' = voided
tag_table_usage     TEXT    'crm_int' for CRM tickets
masterfn            TEXT    Client identifier — DO NOT filter, auto-injected
companyfn           TEXT    Entity/subsidiary identifier — DO NOT filter, auto-injected
```

To get ticket solutions, JOIN with `memo_long_table`:
```sql
LEFT JOIN memo_long_table memo
  ON  memo.companyfn       = p.companyfn
  AND memo.uniquenum_pri   = p.uniquenum_pri
  AND memo.tag_table_usage = p.tag_table_usage
  AND memo.tag_memo_type   = 'norm_notes'
```

---

### `memo_long_table` — Long-text Memos

```
uniquenum_pri   TEXT  Links to parent document
tag_table_usage TEXT  Must match parent
tag_memo_type   TEXT  'norm_notes' = main solution/notes field
notes_memo      TEXT  The actual text content
companyfn       TEXT  Company identifier
```

---

## Example Queries

**Revenue by month (invoices only):**
```sql
SELECT DATE_TRUNC('month', date_trans) AS month,
       SUM(amount_local)               AS revenue,
       COUNT(*)                        AS invoice_count
FROM scm_sal_main
WHERE tag_table_usage = 'sal_inv'
  AND tag_void_yn = 'n'
  AND date_trans >= DATE_TRUNC('year', CURRENT_DATE)
GROUP BY 1
ORDER BY 1
LIMIT 12
```

**Top 10 products by revenue (join header + line items):**
```sql
SELECT d.stkcode_code,
       d.stkcode_desc                  AS product,
       d.stkcate_desc                  AS category,
       d.brand_desc                    AS brand,
       SUM(d.qnty_total)              AS qty_sold,
       SUM(d.amount_local)            AS revenue,
       AVG(d.price_unitrate_local)    AS avg_price
FROM scm_sal_main m
JOIN scm_sal_data d ON d.uniquenum_pri   = m.uniquenum_pri
                   AND d.tag_table_usage = m.tag_table_usage
                   AND d.companyfn       = m.companyfn
WHERE m.tag_table_usage = 'sal_inv'
  AND m.tag_void_yn = 'n'
  AND d.tag_void_yn = 'n'
GROUP BY d.stkcode_code, d.stkcode_desc, d.stkcate_desc, d.brand_desc
ORDER BY revenue DESC
LIMIT 10
```

**Customer retention (RFM — invoices):**
```sql
SELECT party_code,
       party_desc                                      AS customer,
       MIN(date_trans)                                 AS first_purchase,
       MAX(date_trans)                                 AS last_purchase,
       CURRENT_DATE - MAX(date_trans)                 AS days_since_last,
       COUNT(*)                                        AS total_invoices,
       SUM(amount_local)                              AS total_spent,
       ROUND(AVG(amount_local), 2)                   AS avg_order_value
FROM scm_sal_main
WHERE tag_table_usage = 'sal_inv'
  AND tag_void_yn = 'n'
GROUP BY party_code, party_desc
ORDER BY last_purchase DESC
LIMIT 50
```

**Revenue by category and brand:**
```sql
SELECT d.stkcate_desc  AS category,
       d.brand_desc    AS brand,
       SUM(d.amount_local) AS revenue,
       SUM(d.qnty_total)   AS qty_sold
FROM scm_sal_data d
WHERE d.tag_table_usage = 'sal_inv'
  AND d.tag_void_yn = 'n'
GROUP BY d.stkcate_desc, d.brand_desc
ORDER BY revenue DESC
LIMIT 20
```

**Discount analysis by salesperson:**
```sql
SELECT m.staff_code,
       m.deptunit_desc                    AS business_unit,
       COUNT(DISTINCT m.uniquenum_pri)    AS order_count,
       ROUND(AVG(d.discount_pct), 2)     AS avg_discount_pct,
       SUM(d.amount_local)               AS net_revenue
FROM scm_sal_main m
JOIN scm_sal_data d ON d.uniquenum_pri   = m.uniquenum_pri
                   AND d.tag_table_usage = m.tag_table_usage
                   AND d.companyfn       = m.companyfn
WHERE m.tag_table_usage IN ('sal_inv', 'sal_soc')
  AND m.tag_void_yn = 'n'
  AND d.discount_pct > 0
GROUP BY m.staff_code, m.deptunit_desc
ORDER BY avg_discount_pct DESC
LIMIT 20
```

---

## Output Format

Present results as a clean markdown table. For numerical data, also include a chart:

```g3chart
{"type":"bar","title":"Top 10 Products by Revenue","labels":["Product A","Product B"],"data":[150000,95000],"currency":"VND"}
```

Chart types: `bar` (compare categories), `line` (trend over time), `pie` / `doughnut` (proportions).

## User-Facing Language

Never mention table names, column names, or SQL. Say "Sales Invoice" not `sal_inv`. Say "Product" not `stkcode_desc`. Say "Category" not `stkcate_desc`.
