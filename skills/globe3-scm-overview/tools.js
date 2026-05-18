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

export default [
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
