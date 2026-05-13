import pkg from 'node-sql-parser';
const { Parser } = pkg;

const parser = new Parser();

// Tables the LLM is allowed to query
export const ALLOWED_TABLES = new Set([
  'scm_sal_main',      // Sales header: orders, invoices, deliveries (tag_table_usage discriminates)
  'scm_sal_data',      // Sales line items: products, qty, price, discount per order
  'prj_pbill_main',    // CRM Tickets / Projects
  'memo_long_table',   // Long-text memos / notes attached to transactions
]);

const DANGEROUS = /\b(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE|GRANT|REVOKE|EXECUTE|CALL|MERGE|COPY|VACUUM)\b/i;

/**
 * Validate SQL is a safe SELECT, check table whitelist,
 * then inject mandatory masterfn + companyfn scope filters and a LIMIT cap.
 *
 * Scope model:
 *   masterfn  = customer/client identifier  (cookie: cookmfnunique)
 *   companyfn = subsidiary entity of that client (cookie: cookcfnunique)
 * Both are required together to prevent cross-entity data leakage.
 *
 * @param {string} sql        Raw SQL from LLM
 * @param {string} masterfn   Client-level scope value
 * @param {string} companyfn  Entity-level scope value
 * @returns {string} Safe, sanitized SQL ready to execute
 * @throws  if SQL is invalid, non-SELECT, or uses disallowed tables
 */
export function validateAndSanitize(sql, masterfn, companyfn) {
  if (!sql?.trim())   throw new Error('Empty SQL');
  if (!masterfn)      throw new Error('masterfn is required for scoping');
  if (!companyfn)     throw new Error('companyfn is required for scoping');

  const clean = sql.trim().replace(/;+$/, '');

  // Layer 1: fast keyword block
  if (DANGEROUS.test(clean)) throw new Error('Only SELECT statements are allowed');

  // Layer 2: AST parse — verify SELECT only
  let ast, tableList;
  try {
    ast       = parser.astify(clean, { database: 'PostgreSQL' });
    tableList = parser.tableList(clean, { database: 'PostgreSQL' });
  } catch (e) {
    throw new Error(`Invalid SQL: ${e.message}`);
  }

  const stmts = Array.isArray(ast) ? ast : [ast];
  if (stmts.some(s => s.type !== 'select')) {
    throw new Error('Only SELECT statements are allowed');
  }

  // Layer 3: table whitelist — tableList entries look like "select::null::table_name"
  for (const entry of tableList) {
    const tbl = entry.split('::')[2];
    if (tbl && !ALLOWED_TABLES.has(tbl)) {
      throw new Error(`Table not allowed: "${tbl}". Allowed: ${[...ALLOWED_TABLES].join(', ')}`);
    }
  }

  // Layer 4: inject both scope filters
  const withScope = injectScopeFilter(clean, masterfn, companyfn);

  // Layer 5: cap result size
  return ensureLimit(withScope, 100);
}

function injectScopeFilter(sql, masterfn, companyfn) {
  const esc   = v => v.replace(/'/g, "''");
  // Both conditions injected together as one atomic block
  const qualifier = scopeQualifier(sql);
  const filter = `${qualifier}masterfn = '${esc(masterfn)}' AND ${qualifier}companyfn = '${esc(companyfn)}'`;

  const whereMatch = /\bWHERE\b/i.exec(sql);
  if (whereMatch) {
    // Inject as the first conditions right after WHERE
    const pos = whereMatch.index + whereMatch[0].length;
    return `${sql.slice(0, pos)} ${filter} AND${sql.slice(pos)}`;
  }

  // No WHERE — inject before ORDER BY / GROUP BY / HAVING / LIMIT
  const clauseMatch = /\b(ORDER\s+BY|GROUP\s+BY|HAVING|LIMIT)\b/i.exec(sql);
  if (clauseMatch) {
    return `${sql.slice(0, clauseMatch.index)}WHERE ${filter} ${sql.slice(clauseMatch.index)}`;
  }

  return `${sql} WHERE ${filter}`;
}

function scopeQualifier(sql) {
  const tableAliasPatterns = [
    /\bscm_sal_main\s+(?:AS\s+)?([a-zA-Z_][\w]*)/i,
    /\bscm_sal_data\s+(?:AS\s+)?([a-zA-Z_][\w]*)/i,
    /\bprj_pbill_main\s+(?:AS\s+)?([a-zA-Z_][\w]*)/i,
    /\bmemo_long_table\s+(?:AS\s+)?([a-zA-Z_][\w]*)/i,
  ];

  for (const pattern of tableAliasPatterns) {
    const match = sql.match(pattern);
    if (match && !/^(where|join|on|group|order|limit|having)$/i.test(match[1])) {
      return `${match[1]}.`;
    }
  }

  return '';
}

function ensureLimit(sql, max) {
  if (/\bLIMIT\b/i.test(sql)) return sql;
  return `${sql} LIMIT ${max}`;
}
