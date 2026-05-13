import pg from 'pg';
import { validateAndSanitize } from './query-safety.js';
import { existsSync, readFileSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const { Pool } = pg;
const __dir = dirname(fileURLToPath(import.meta.url));

loadRepoEnv();

function loadRepoEnv() {
  const envPath = join(__dir, '..', '..', '.env');
  if (!existsSync(envPath)) return;

  const lines = readFileSync(envPath, 'utf8').split(/\r?\n/);
  for (const raw of lines) {
    const line = raw.trim();
    if (!line || line.startsWith('#') || !line.includes('=')) continue;

    const idx = line.indexOf('=');
    const key = line.slice(0, idx).trim();
    let value = line.slice(idx + 1).trim();

    if (
      value.length >= 2 &&
      ((value.startsWith('"') && value.endsWith('"')) ||
       (value.startsWith("'") && value.endsWith("'")))
    ) {
      value = value.slice(1, -1);
    }

    if (!(key in process.env)) process.env[key] = value;
  }
}

// ── Connection pool (mirrors ingest_config.py PG_CONFIG) ─────────────────────

let _pool = null;
function pool() {
  if (!_pool) _pool = new Pool({
    host:     process.env.PG_HOST     || 'localhost',
    port:    +(process.env.PG_PORT    || 5432),
    database: process.env.PG_DBNAME   || 'v57udemo2011_tno',
    user:     process.env.PG_USER     || 'postgres',
    password: process.env.PG_PASSWORD || '123',
    max: 5,
    statement_timeout:        5000,
    connectionTimeoutMillis:  3000,
  });
  return _pool;
}

// ── Model registry ────────────────────────────────────────────────────────────
// Add a new entry here whenever a new ERP module skill is added.

const MODELS = {
  sales: {
    table:           'scm_sal_main',
    masterfn_field:  'masterfn',   // client-level scope  (cookie: cookmfnunique)
    companyfn_field: 'companyfn',  // entity-level scope  (cookie: cookcfnunique)
    pk:              'uniquenum_pri',
    default_filters: { tag_void_yn: 'n' },  // tag_table_usage NOT defaulted — LLM must specify
    select_cols: [
      'uniquenum_pri', 'dnum_auto', 'dnum_reference', 'date_trans', 'date_due',
      'party_code', 'party_desc', 'party_unique',
      'amount_forex', 'amount_local', 'curr_short_forex', 'curr_rate_forex_f_calc',
      'staff_code', 'staff_desc', 'staff_unique',
      'location_code', 'deptunit_code', 'deptunit_desc',
      'creditterm_desc', 'delivtype_desc', 'sendby_desc',
      'tag_void_yn', 'tag_table_usage',
    ],
    text_search:    new Set(['party_desc', 'dnum_auto', 'dnum_reference', 'staff_desc', 'location_desc']),
    date_field:     'date_trans',
    amount_field:   'amount_local',
    allowed_filters: new Set([
      'party_code', 'party_desc', 'date_trans', 'date_from', 'date_to',
      'staff_code', 'dnum_auto', 'dnum_reference',
      'location_code', 'curr_short_forex', 'tag_void_yn', 'tag_table_usage',
      'amount_min', 'amount_max',
    ]),
    allowed_sorts: new Set([
      'date_trans', 'dnum_auto', 'party_code',
      'amount_forex', 'amount_local', 'date_lastupdate',
    ]),
    allowed_groups: new Set([
      'party_code', 'party_desc', 'staff_code', 'staff_desc',
      'location_code', 'deptunit_code', 'deptunit_desc',
      'curr_short_forex', 'date_trans', 'creditterm_desc',
      'delivtype_desc', 'sendby_desc', 'tag_table_usage',
    ]),
  },
};

// ── WHERE clause builder ──────────────────────────────────────────────────────

function buildWhere(model, filters, params) {
  const conds = [];

  // Model-level defaults (skip if user already filtering that column)
  for (const [col, val] of Object.entries(model.default_filters || {})) {
    if (col in filters) continue;
    params.push(val);
    conds.push(`${col} = $${params.length}`);
  }

  // User-supplied filters
  for (const [key, val] of Object.entries(filters)) {
    if (!model.allowed_filters.has(key)) continue;

    if (key === 'date_from') {
      const d = val.length === 7 ? `${val}-01` : val;
      params.push(d);
      conds.push(`${model.date_field} >= $${params.length}`);

    } else if (key === 'date_to') {
      if (val.length === 7) {
        params.push(`${val}-01`);
        conds.push(`${model.date_field} < (DATE $${params.length} + INTERVAL '1 month')`);
      } else {
        params.push(val);
        conds.push(`${model.date_field} < $${params.length}`);
      }

    } else if (key === 'amount_min') {
      params.push(+val);
      conds.push(`${model.amount_field} >= $${params.length}`);

    } else if (key === 'amount_max') {
      params.push(+val);
      conds.push(`${model.amount_field} <= $${params.length}`);

    } else if (model.text_search.has(key)) {
      params.push(`%${val}%`);
      conds.push(`${key} ILIKE $${params.length}`);

    } else {
      params.push(val);
      conds.push(`${key} = $${params.length}`);
    }
  }

  return conds.join(' AND ');
}

// ── Query logger ──────────────────────────────────────────────────────────────

function resolveSql(sql, params) {
  return sql.replace(/\$(\d+)/g, (_, n) => {
    const v = params[+n - 1];
    if (v === null || v === undefined) return 'NULL';
    if (typeof v === 'string') return `'${v.replace(/'/g, "''")}'`;
    return String(v);
  });
}

async function dbQuery(db, label, sql, params = []) {
  const resolved = resolveSql(sql, params);
  process.stdout.write(`\x1b[36m[SQL]\x1b[0m \x1b[33m${label}\x1b[0m\n  ${resolved}\n`);
  const t0  = Date.now();
  const res = await db.query(sql, params);
  const ms  = Date.now() - t0;
  process.stdout.write(`  \x1b[32m→ ${res.rowCount} row(s)  ${ms}ms\x1b[0m\n`);
  return res;
}

// ── Main export ───────────────────────────────────────────────────────────────

/**
 * Unified data access function for all skill tools.
 *
 * @param {'list'|'findById'|'count'|'aggregate'|'runQuery'} operation
 * @param {string} modelName  Key in MODELS registry (ignored for runQuery)
 * @param {object} args       Tool arguments from the LLM
 */
export async function ormFetch(operation, modelName, args) {
  const db        = pool();
  // masterfn = client scope (cookie: cookmfnunique)
  // companyfn = entity scope (cookie: cookcfnunique)
  const masterfn  = args.masterfn  || process.env.DEFAULT_MASTERFN;
  const companyfn = args.companyfn || process.env.DEFAULT_COMPANYFN;

  if (!masterfn || !companyfn) {
    throw new Error('masterfn and companyfn are required for scoped ERP queries');
  }

  // ── Text-to-SQL path ──────────────────────────────────────────────────────
  if (operation === 'runQuery') {
    const safe = validateAndSanitize(args.sql, masterfn, companyfn);
    const res  = await dbQuery(db, 'runQuery', safe);
    return {
      columns:  res.fields.map(f => f.name),
      rows:     res.rows,
      rowCount: res.rowCount,
    };
  }

  // ── Skill-based path ──────────────────────────────────────────────────────
  const model = MODELS[modelName];
  if (!model) throw new Error(`Unknown model: ${modelName}`);

  // $1 = masterfn, $2 = companyfn — consistent position across all queries
  const params     = [masterfn, companyfn];
  const scopeExpr  = `${model.masterfn_field} = $1 AND ${model.companyfn_field} = $2`;
  const filterExpr = buildWhere(model, args.filters || {}, params);
  const where      = filterExpr ? `${scopeExpr} AND ${filterExpr}` : scopeExpr;
  const cols        = model.select_cols.join(', ');

  // list ─────────────────────────────────────────────────────────────────────
  if (operation === 'list') {
    const sortF = model.allowed_sorts.has(args.sortField) ? args.sortField : model.date_field;
    const sortD = args.sortDir === 'ASC' ? 'ASC' : 'DESC';
    const page  = Math.max(1, args.page || 1);
    const size  = Math.min(20, args.pageSize || 10);

    const dataParams = [...params, size, (page - 1) * size];
    const label = `list/${modelName} p${page}`;
    const [countRes, dataRes] = await Promise.all([
      dbQuery(db, `${label} [count]`, `SELECT COUNT(*) FROM ${model.table} WHERE ${where}`, params),
      dbQuery(db, `${label} [data]`,
        `SELECT ${cols} FROM ${model.table} WHERE ${where}` +
        ` ORDER BY ${sortF} ${sortD}` +
        ` LIMIT $${dataParams.length - 1} OFFSET $${dataParams.length}`,
        dataParams,
      ),
    ]);

    return {
      data:     dataRes.rows,
      total:   +countRes.rows[0].count,
      page,
      pageSize: size,
    };
  }

  // findById ─────────────────────────────────────────────────────────────────
  if (operation === 'findById') {
    const res = await dbQuery(db, `findById/${modelName}`,
      `SELECT ${cols} FROM ${model.table} WHERE ${scopeExpr} AND ${model.pk} = $3`,
      [masterfn, companyfn, args.id],
    );
    return res.rows[0] ?? null;
  }

  // count ────────────────────────────────────────────────────────────────────
  if (operation === 'count') {
    const res = await dbQuery(db, `count/${modelName}`,
      `SELECT COUNT(*) AS count FROM ${model.table} WHERE ${where}`,
      params,
    );
    return { count: +res.rows[0].count };
  }

  // aggregate ────────────────────────────────────────────────────────────────
  if (operation === 'aggregate') {
    const VALID_FN = new Set(['SUM', 'COUNT', 'AVG', 'MIN', 'MAX']);
    const fn      = VALID_FN.has((args.func || 'SUM').toUpperCase())
                    ? args.func.toUpperCase() : 'SUM';
    const measure = args.measure || model.amount_field;
    const grp     = model.allowed_groups.has(args.groupBy) ? args.groupBy : null;
    const sortD   = args.sortDir === 'ASC' ? 'ASC' : 'DESC';
    const lim     = Math.min(50, args.limit || 10);

    const valueExpr  = (fn === 'COUNT' && !args.measure) ? 'COUNT(*)' : `${fn}(${measure})`;
    const selectExpr = grp ? `${grp}, ${valueExpr} AS value` : `${valueExpr} AS value`;
    const groupClause = grp ? `GROUP BY ${grp}` : '';

    const res = await dbQuery(db, `aggregate/${modelName}`,
      `SELECT ${selectExpr} FROM ${model.table} WHERE ${where}` +
      ` ${groupClause} ORDER BY value ${sortD} LIMIT ${lim}`,
      params,
    );
    return res.rows;
  }

  throw new Error(`Unknown operation: ${operation}`);
}
