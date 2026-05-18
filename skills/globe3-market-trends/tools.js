import pg from 'pg';
import { existsSync, readFileSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const { Pool } = pg;
const __dir = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(__dir, '..', '..');

loadRepoEnv();

function loadRepoEnv() {
  const envPath = join(repoRoot, '.env');
  if (!existsSync(envPath)) return;
  for (const raw of readFileSync(envPath, 'utf8').split(/\r?\n/)) {
    const line = raw.trim();
    if (!line || line.startsWith('#') || !line.includes('=')) continue;
    const idx = line.indexOf('=');
    const key = line.slice(0, idx).trim();
    let value = line.slice(idx + 1).trim();
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) value = value.slice(1, -1);
    if (!(key in process.env)) process.env[key] = value;
  }
}

let _pool = null;
function pool() {
  if (!_pool) _pool = new Pool({
    host: process.env.PG_HOST || 'localhost',
    port: +(process.env.PG_PORT || 5432),
    database: process.env.PG_DBNAME || 'v57udemo2011_tno',
    user: process.env.PG_USER || 'postgres',
    password: process.env.PG_PASSWORD || '123',
    max: 5,
    statement_timeout: 8000,
    connectionTimeoutMillis: 3000,
  });
  return _pool;
}

function loadTrendRows() {
  const path = join(repoRoot, 'data', 'market_trends', 'trends.json');
  if (!existsSync(path)) return { configured: false, path, rows: [] };
  const parsed = JSON.parse(readFileSync(path, 'utf8'));
  return { configured: true, path, rows: Array.isArray(parsed) ? parsed : [] };
}

export default [
  {
    name: 'analyze_market_trends',
    description: 'Compare configured external market/internet trend keywords with Globe3 inventory items. Does not scrape the internet.',
    parameters: {
      type: 'object',
      properties: {
        top: { type: 'number', description: 'Max trends to return. Default 10.' },
      },
      required: [],
    },

    async func(args) {
      const masterfn = args.masterfn;
      const companyfn = args.companyfn;
      if (!masterfn || !companyfn) throw new Error('masterfn and companyfn are required');

      const top = Math.min(Math.max(Number(args.top || 10), 1), 50);
      const trends = loadTrendRows();
      if (!trends.configured) {
        return {
          ok: false,
          configured: false,
          message: 'External market trend data is not configured yet. Add data/market_trends/trends.json before answering internet/social trend questions.',
          expected_file: 'data/market_trends/trends.json',
        };
      }

      const ranked = trends.rows
        .map(r => ({ ...r, score: Number(r.score || 0), keyword: String(r.keyword || '').trim() }))
        .filter(r => r.keyword)
        .sort((a, b) => b.score - a.score)
        .slice(0, top);

      const db = pool();
      const checked = [];
      for (const trend of ranked) {
        const res = await db.query(`
          SELECT stkcode_code, stkcode_desc_english, stkm_qnty_total
          FROM stk_code_main
          WHERE masterfn = $1 AND companyfn = $2
            AND tag_void_yn = 'n'
            AND COALESCE(tag_active_yn, 'y') = 'y'
            AND (
              stkcode_code ILIKE $3 OR
              stkcode_desc_english ILIKE $3 OR
              stkcate_desc ILIKE $3 OR
              brand_desc ILIKE $3
            )
          ORDER BY COALESCE(stkm_qnty_total, 0) DESC
          LIMIT 5
        `, [masterfn, companyfn, `%${trend.keyword}%`]);
        checked.push({
          ...trend,
          in_inventory: res.rows.length > 0,
          matched_items: res.rows,
        });
      }

      return {
        ok: true,
        configured: true,
        source_file: 'data/market_trends/trends.json',
        trends_checked: checked,
        missing_from_inventory: checked.filter(r => !r.in_inventory),
        charts: [{
          type: 'bar',
          title: 'External trend scores',
          labels: checked.map(r => r.keyword),
          data: checked.map(r => r.score),
        }],
      };
    },
  },
];
