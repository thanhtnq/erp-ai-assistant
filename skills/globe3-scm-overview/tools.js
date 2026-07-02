import pg from 'pg';
import { existsSync, readFileSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const { Pool } = pg;
const __dir = dirname(fileURLToPath(import.meta.url));

loadRepoEnv();

function loadRepoEnv() {
  const envPath = join(__dir, '..', '..', '.env');
  if (!existsSync(envPath)) return;
  for (const raw of readFileSync(envPath, 'utf8').split(/\r?\n/)) {
    const line = raw.trim();
    if (!line || line.startsWith('#') || !line.includes('=')) continue;
    const idx = line.indexOf('=');
    const key = line.slice(0, idx).trim();
    let value = line.slice(idx + 1).trim();
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }
    if (!(key in process.env)) process.env[key] = value;
  }
}

let _pool = null;
function pool() {
  if (!_pool) {
    _pool = new Pool({
      host: process.env.PG_HOST || 'localhost',
      port: +(process.env.PG_PORT || 5432),
      database: process.env.PG_DBNAME || 'v57udemo2011_tno',
      user: process.env.PG_USER || 'postgres',
      password: process.env.PG_PASSWORD || '123',
      max: 5,
      statement_timeout: 8000,
      connectionTimeoutMillis: 3000,
    });
  }
  return _pool;
}

async function q(db, sql, params) {
  const res = await db.query(sql, params);
  return res.rows;
}

const clamp = (value, fallback, max) => Math.min(Math.max(Number(value || fallback), 1), max);

async function runRealtimeAnalysis(args) {
  const { masterfn, companyfn } = args;
  if (!masterfn || !companyfn) throw new Error('masterfn and companyfn are required');

  const analysis = String(args.analysis || 'overview');
  const days = clamp(args.days, 30, 365);
  const top = clamp(args.top, 10, 50);
  const db = pool();
  const params = [masterfn, companyfn, days, top];
  const salesWhere = `m.masterfn = $1 AND m.companyfn = $2
    AND m.tag_void_yn = 'n' AND d.tag_void_yn = 'n'
    AND m.tag_table_usage IN ('sal_inv', 'sal_soc', 'sal_soe')`;

  let rows;
  let total = null;
  if (analysis === 'overview') {
    rows = await q(db, `
      SELECT COUNT(*)::int AS transaction_count,
             COALESCE(SUM(amount_local),0)::float AS revenue_local,
             COALESCE(AVG(amount_local),0)::float AS avg_transaction_value,
             COUNT(DISTINCT party_code)::int AS customer_count
      FROM scm_sal_main
      WHERE masterfn=$1 AND companyfn=$2 AND tag_void_yn='n'
        AND tag_table_usage IN ('sal_inv','sal_soc','sal_soe')
        AND date_trans >= CURRENT_DATE - ($3::int * INTERVAL '1 day')`, params.slice(0, 3));
  } else if (analysis === 'sales_invoices') {
    const [countRows, invoiceRows] = await Promise.all([
      q(db, `SELECT COUNT(*)::int AS total
        FROM scm_sal_main
        WHERE masterfn=$1 AND companyfn=$2 AND tag_void_yn='n'
          AND tag_table_usage='sal_inv'
          AND date_trans >= CURRENT_DATE - ($3::int * INTERVAL '1 day')`, params.slice(0, 3)),
      q(db, `SELECT dnum_auto AS invoice_no, TO_CHAR(date_trans, 'YYYY-MM-DD') AS invoice_date,
                    party_code AS customer_code, party_desc AS customer,
                    amount_local::float AS amount_local, curr_short_forex AS currency
        FROM scm_sal_main
        WHERE masterfn=$1 AND companyfn=$2 AND tag_void_yn='n'
          AND tag_table_usage='sal_inv'
          AND date_trans >= CURRENT_DATE - ($3::int * INTERVAL '1 day')
        ORDER BY date_trans DESC, dnum_auto DESC LIMIT $4`, params),
    ]);
    total = countRows[0]?.total || 0;
    rows = invoiceRows;
  } else if (analysis === 'growth' || analysis === 'demand_surge' || analysis === 'stable_growth') {
    rows = await q(db, `
      WITH product_sales AS (
        SELECT d.stkcode_code AS code, MAX(d.stkcode_desc) AS product,
               MAX(d.stkcate_desc) AS category,
               SUM(CASE WHEN m.date_trans >= CURRENT_DATE - (($3::int / 2) * INTERVAL '1 day')
                        THEN d.qnty_total ELSE 0 END)::float AS current_qty,
               SUM(CASE WHEN m.date_trans < CURRENT_DATE - (($3::int / 2) * INTERVAL '1 day')
                         AND m.date_trans >= CURRENT_DATE - ($3::int * INTERVAL '1 day')
                        THEN d.qnty_total ELSE 0 END)::float AS previous_qty,
               SUM(CASE WHEN m.date_trans >= CURRENT_DATE - (($3::int / 2) * INTERVAL '1 day')
                        THEN d.amount_local ELSE 0 END)::float AS current_revenue
        FROM scm_sal_main m JOIN scm_sal_data d
          ON d.masterfn=m.masterfn AND d.companyfn=m.companyfn
         AND d.uniquenum_pri=m.uniquenum_pri AND d.tag_table_usage=m.tag_table_usage
        WHERE ${salesWhere} AND m.date_trans >= CURRENT_DATE - ($3::int * INTERVAL '1 day')
        GROUP BY d.stkcode_code
      )
      SELECT *, CASE WHEN previous_qty = 0 THEN CASE WHEN current_qty > 0 THEN 100 ELSE 0 END
                     ELSE ((current_qty - previous_qty) / ABS(previous_qty) * 100) END::float AS growth_pct
      FROM product_sales
      WHERE current_qty > 0 ${analysis === 'stable_growth' ? 'AND previous_qty > 0 AND current_qty >= previous_qty' : ''}
      ORDER BY ${analysis === 'stable_growth' ? 'ABS((current_qty - previous_qty) / NULLIF(previous_qty, 0)) ASC, current_qty DESC' : 'growth_pct DESC, current_qty DESC'}
      LIMIT $4`, params);
  } else if (analysis === 'revenue' || analysis === 'bestselling') {
    rows = await q(db, `
      SELECT d.stkcode_code AS code, MAX(d.stkcode_desc) AS product,
             MAX(d.stkcate_desc) AS category, SUM(d.qnty_total)::float AS qty_sold,
             SUM(d.amount_local)::float AS revenue
      FROM scm_sal_main m JOIN scm_sal_data d
        ON d.masterfn=m.masterfn AND d.companyfn=m.companyfn
       AND d.uniquenum_pri=m.uniquenum_pri AND d.tag_table_usage=m.tag_table_usage
      WHERE ${salesWhere} AND m.date_trans >= CURRENT_DATE - ($3::int * INTERVAL '1 day')
      GROUP BY d.stkcode_code
      ORDER BY ${analysis === 'revenue' ? 'revenue' : 'qty_sold'} DESC LIMIT $4`, params);
  } else if (analysis === 'stock_low_sales' || analysis === 'low_stock_bestsellers') {
    rows = await q(db, `
      WITH sales AS (
        SELECT d.stkcode_code, SUM(d.qnty_total)::float qty_sold, SUM(d.amount_local)::float revenue
        FROM scm_sal_main m JOIN scm_sal_data d
          ON d.masterfn=m.masterfn AND d.companyfn=m.companyfn
         AND d.uniquenum_pri=m.uniquenum_pri AND d.tag_table_usage=m.tag_table_usage
        WHERE ${salesWhere} AND m.date_trans >= CURRENT_DATE - ($3::int * INTERVAL '1 day')
        GROUP BY d.stkcode_code
      )
      SELECT i.stkcode_code AS code, i.stkcode_desc_english AS product, i.stkcate_desc AS category,
             COALESCE(i.stkm_qnty_total,0)::float AS stock_on_hand,
             COALESCE(i.level_reorder,0)::float AS reorder_level,
             COALESCE(s.qty_sold,0)::float AS qty_sold, COALESCE(s.revenue,0)::float AS revenue
      FROM stk_code_main i LEFT JOIN sales s ON s.stkcode_code=i.stkcode_code
      WHERE i.masterfn=$1 AND i.companyfn=$2 AND i.tag_void_yn='n'
        AND COALESCE(i.tag_active_yn,'y')='y'
        ${analysis === 'low_stock_bestsellers'
          ? "AND COALESCE(s.qty_sold,0)>0 AND COALESCE(i.stkm_qnty_total,0)<=GREATEST(COALESCE(i.level_reorder,0),0)"
          : 'AND COALESCE(i.stkm_qnty_total,0)>0'}
      ORDER BY ${analysis === 'low_stock_bestsellers' ? 'qty_sold DESC, stock_on_hand ASC' : 'stock_on_hand DESC, qty_sold ASC'}
      LIMIT $4`, params);
  } else if (analysis === 'supplier_delay') {
    rows = await q(db, `
      SELECT party_code AS code, party_desc AS supplier, COUNT(*)::int AS late_deliveries,
             AVG(date_delivery::date-date_due::date)::float AS avg_days_late,
             MAX(date_delivery::date-date_due::date)::int AS max_days_late
      FROM scm_pur_main WHERE masterfn=$1 AND companyfn=$2 AND tag_void_yn='n'
        AND date_due IS NOT NULL AND date_delivery IS NOT NULL AND date_delivery::date>date_due::date
        AND date_trans >= CURRENT_DATE - ($3::int * INTERVAL '1 day')
      GROUP BY party_code, party_desc ORDER BY late_deliveries DESC, avg_days_late DESC LIMIT $4`, params);
  } else if (analysis === 'basket') {
    rows = await q(db, `
      SELECT a.stkcode_code AS code_a, MAX(a.stkcode_desc) AS product_a,
             b.stkcode_code AS code_b, MAX(b.stkcode_desc) AS product_b,
             COUNT(DISTINCT a.uniquenum_pri)::int AS together_count
      FROM scm_sal_data a JOIN scm_sal_data b
        ON b.masterfn=a.masterfn AND b.companyfn=a.companyfn
       AND b.uniquenum_pri=a.uniquenum_pri AND b.tag_table_usage=a.tag_table_usage
       AND b.stkcode_code>a.stkcode_code
      WHERE a.masterfn=$1 AND a.companyfn=$2 AND a.tag_void_yn='n' AND b.tag_void_yn='n'
        AND a.tag_table_usage IN ('sal_inv','sal_soc','sal_soe')
        AND a.date_trans >= CURRENT_DATE - ($3::int * INTERVAL '1 day')
      GROUP BY a.stkcode_code,b.stkcode_code ORDER BY together_count DESC LIMIT $4`, params);
  } else if (analysis === 'demand_forecast' || analysis === 'forecast_volatility') {
    const groupExpr = args.group_by === 'category' ? "COALESCE(d.stkcate_desc,'Uncategorized')" : 'd.stkcode_code';
    rows = await q(db, `
      WITH weekly AS (
        SELECT ${groupExpr} AS code, MAX(${args.group_by === 'category' ? 'd.stkcate_desc' : 'd.stkcode_desc'}) AS product,
               date_trunc('week',m.date_trans) AS week, SUM(d.qnty_total)::float AS qty,
               SUM(d.amount_local)::float AS revenue
        FROM scm_sal_main m JOIN scm_sal_data d
          ON d.masterfn=m.masterfn AND d.companyfn=m.companyfn
         AND d.uniquenum_pri=m.uniquenum_pri AND d.tag_table_usage=m.tag_table_usage
        WHERE ${salesWhere} AND m.date_trans >= CURRENT_DATE - GREATEST($3::int,90) * INTERVAL '1 day'
        GROUP BY ${groupExpr},date_trunc('week',m.date_trans)
      )
      SELECT code, MAX(product) AS product, AVG(qty)::float * ($3::float/7) AS forecast_qty,
             AVG(revenue)::float * ($3::float/7) AS forecast_revenue,
             COALESCE(STDDEV_SAMP(qty),0)::float AS weekly_volatility,
             CASE WHEN AVG(qty)=0 THEN 0 ELSE COALESCE(STDDEV_SAMP(qty),0)/AVG(qty)*100 END::float AS volatility_pct
      FROM weekly GROUP BY code
      ORDER BY ${analysis === 'forecast_volatility' ? 'volatility_pct' : 'forecast_qty'} DESC LIMIT $4`, params);
  } else if (analysis === 'forecast_vs_actual') {
    rows = await q(db, `
      WITH actual AS (
        SELECT SUM(amount_local)::float AS last_month_actual
        FROM scm_sal_main WHERE masterfn=$1 AND companyfn=$2 AND tag_void_yn='n'
          AND tag_table_usage IN ('sal_inv','sal_soc','sal_soe')
          AND date_trans>=date_trunc('month',CURRENT_DATE)-INTERVAL '1 month'
          AND date_trans<date_trunc('month',CURRENT_DATE)
      ), history AS (
        SELECT COALESCE(SUM(amount_local),0)::float/90 AS avg_daily
        FROM scm_sal_main WHERE masterfn=$1 AND companyfn=$2 AND tag_void_yn='n'
          AND tag_table_usage IN ('sal_inv','sal_soc','sal_soe')
          AND date_trans>=CURRENT_DATE-INTERVAL '90 days'
      )
      SELECT actual.last_month_actual,
             history.avg_daily*EXTRACT(day FROM (date_trunc('month',CURRENT_DATE)+INTERVAL '1 month'-INTERVAL '1 day'))::float AS this_month_forecast,
             (history.avg_daily*EXTRACT(day FROM (date_trunc('month',CURRENT_DATE)+INTERVAL '1 month'-INTERVAL '1 day'))-actual.last_month_actual)::float AS variance
      FROM actual CROSS JOIN history`, params.slice(0, 2));
  } else {
    throw new Error(`Unsupported realtime SCM analysis: ${analysis}`);
  }

  return { analysis, period_days: days, scope: { masterfn, companyfn }, total, rows };
}

export default [
  {
    name: 'analyze_scm_realtime',
    description: 'Run scoped realtime SCM analytics directly against PostgreSQL sales, purchase, and stock data. No trained model or extracted artifact is used.',
    parameters: {
      type: 'object',
      properties: {
        analysis: { type: 'string', description: 'overview, sales_invoices, growth, demand_surge, stable_growth, revenue, bestselling, stock_low_sales, low_stock_bestsellers, supplier_delay, basket, demand_forecast, forecast_volatility, or forecast_vs_actual' },
        days: { type: 'number' },
        top: { type: 'number' },
        group_by: { type: 'string', description: 'product or category' },
      },
      required: ['analysis'],
    },
    func: runRealtimeAnalysis,
  },
  {
    name: 'get_scm_overview',
    description: 'Return a cross-module SCM overview for sales, inventory health, replenishment, overstock, and supplier late delivery.',
    parameters: {
      type: 'object',
      properties: {
        days: { type: 'number', description: 'Lookback period in days. Default 30, max 365.' },
        top: { type: 'number', description: 'Number of ranked rows to return. Default 10, max 50.' },
      },
      required: [],
    },

    async func(args) {
      const masterfn = args.masterfn;
      const companyfn = args.companyfn;
      if (!masterfn || !companyfn) throw new Error('masterfn and companyfn are required');

      const days = Math.min(Math.max(Number(args.days || 30), 1), 365);
      const top = Math.min(Math.max(Number(args.top || 10), 1), 50);
      const periodOnlyParams = [masterfn, companyfn, days];
      const periodParams = [masterfn, companyfn, days, top];
      const rankParams = [masterfn, companyfn, top];
      const db = pool();

      const [salesSummary, topProducts, reorderItems, overstockItems, lateSuppliers] = await Promise.all([
        q(db, `
          SELECT COUNT(*)::int AS transaction_count,
                 COALESCE(SUM(amount_local), 0)::float AS revenue_local,
                 COALESCE(AVG(amount_local), 0)::float AS avg_transaction_value
          FROM scm_sal_main
          WHERE masterfn = $1 AND companyfn = $2
            AND tag_void_yn = 'n'
            AND tag_table_usage IN ('sal_inv', 'sal_soc', 'sal_soe')
            AND date_trans >= CURRENT_DATE - ($3::int * INTERVAL '1 day')
        `, periodOnlyParams),

        q(db, `
          SELECT d.stkcode_code,
                 d.stkcode_desc AS product,
                 d.stkcate_desc AS category,
                 COALESCE(SUM(d.qnty_total), 0)::float AS qty_sold,
                 COALESCE(SUM(d.amount_local), 0)::float AS revenue_local
          FROM scm_sal_main m
          JOIN scm_sal_data d
            ON d.uniquenum_pri = m.uniquenum_pri
           AND d.tag_table_usage = m.tag_table_usage
           AND d.companyfn = m.companyfn
           AND d.masterfn = m.masterfn
          WHERE m.masterfn = $1 AND m.companyfn = $2
            AND m.tag_void_yn = 'n' AND d.tag_void_yn = 'n'
            AND m.tag_table_usage IN ('sal_inv', 'sal_soc', 'sal_soe')
            AND m.date_trans >= CURRENT_DATE - ($3::int * INTERVAL '1 day')
          GROUP BY d.stkcode_code, d.stkcode_desc, d.stkcate_desc
          ORDER BY qty_sold DESC, revenue_local DESC
          LIMIT $4
        `, periodParams),

        q(db, `
          SELECT stkcode_code,
                 stkcode_desc_english AS product,
                 stkcate_desc AS category,
                 COALESCE(stkm_qnty_total, 0)::float AS stock_on_hand,
                 COALESCE(level_reorder, 0)::float AS reorder_level,
                 GREATEST(COALESCE(level_reorder, 0) - COALESCE(stkm_qnty_total, 0), 0)::float AS suggested_reorder_qty
          FROM stk_code_main
          WHERE masterfn = $1 AND companyfn = $2
            AND tag_void_yn = 'n'
            AND COALESCE(tag_active_yn, 'y') = 'y'
            AND COALESCE(level_reorder, 0) > 0
            AND COALESCE(stkm_qnty_total, 0) <= COALESCE(level_reorder, 0)
          ORDER BY suggested_reorder_qty DESC
          LIMIT $3
        `, rankParams),

        q(db, `
          SELECT i.stkcode_code,
                 i.stkcode_desc_english AS product,
                 i.stkcate_desc AS category,
                 COALESCE(i.stkm_qnty_total, 0)::float AS stock_on_hand,
                 COALESCE(i.level_max, 0)::float AS max_level,
                 COALESCE(SUM(s.qnty_total), 0)::float AS qty_sold_period
          FROM stk_code_main i
          LEFT JOIN scm_sal_data s
            ON s.masterfn = i.masterfn
           AND s.companyfn = i.companyfn
           AND s.stkcode_code = i.stkcode_code
           AND s.tag_void_yn = 'n'
           AND s.tag_table_usage IN ('sal_inv', 'sal_soc', 'sal_soe')
           AND s.date_trans >= CURRENT_DATE - ($3::int * INTERVAL '1 day')
          WHERE i.masterfn = $1 AND i.companyfn = $2
            AND i.tag_void_yn = 'n'
            AND COALESCE(i.tag_active_yn, 'y') = 'y'
            AND COALESCE(i.stkm_qnty_total, 0) > 0
          GROUP BY i.stkcode_code, i.stkcode_desc_english, i.stkcate_desc, i.stkm_qnty_total, i.level_max
          HAVING (COALESCE(i.level_max, 0) > 0 AND COALESCE(i.stkm_qnty_total, 0) > COALESCE(i.level_max, 0))
              OR COALESCE(SUM(s.qnty_total), 0) = 0
          ORDER BY stock_on_hand DESC, qty_sold_period ASC
          LIMIT $4
        `, periodParams),

        q(db, `
          SELECT party_code,
                 party_desc AS supplier,
                 COUNT(*)::int AS late_delivery_count,
                 AVG(date_delivery::date - date_due::date)::float AS avg_days_late
          FROM scm_pur_main
          WHERE masterfn = $1 AND companyfn = $2
            AND tag_void_yn = 'n'
            AND tag_table_usage IN ('stk_grn', 'stk_gvn')
            AND date_due IS NOT NULL
            AND date_delivery IS NOT NULL
            AND date_delivery::date > date_due::date
            AND date_trans >= CURRENT_DATE - ($3::int * INTERVAL '1 day')
          GROUP BY party_code, party_desc
          ORDER BY late_delivery_count DESC, avg_days_late DESC
          LIMIT $4
        `, periodParams),
      ]);

      return {
        period_days: days,
        scope: { masterfn, companyfn },
        sales_summary: salesSummary[0] || { transaction_count: 0, revenue_local: 0, avg_transaction_value: 0 },
        top_products: topProducts,
        reorder_items: reorderItems,
        overstock_or_slow_items: overstockItems,
        late_suppliers: lateSuppliers,
        charts: [
          {
            type: 'bar',
            title: `Top products by quantity (${days} days)`,
            labels: topProducts.map(r => r.product || r.stkcode_code),
            data: topProducts.map(r => Number(r.qty_sold || 0)),
          },
          {
            type: 'bar',
            title: 'Suggested reorder quantity',
            labels: reorderItems.map(r => r.product || r.stkcode_code),
            data: reorderItems.map(r => Number(r.suggested_reorder_qty || 0)),
          },
        ],
      };
    },
  },
];
