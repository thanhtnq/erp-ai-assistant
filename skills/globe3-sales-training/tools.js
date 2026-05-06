import { execFileSync } from 'child_process';
import { writeFileSync, unlinkSync, mkdtempSync } from 'fs';
import { join, dirname } from 'path';
import { tmpdir } from 'os';
import { fileURLToPath } from 'url';

const __dir = dirname(fileURLToPath(import.meta.url));
const BRIDGE_SCRIPT = join(__dir, '..', '..', 'sales-training', 'analyze_sales_bridge.py');

/**
 * Call the Python sales bridge via subprocess with a temp file (Windows-safe).
 * @param {object} args  { query, companyfn, date_from?, date_to? }
 * @returns {object}     { ok, result } or { ok, error }
 */
function callBridge(args) {
  const python = process.platform === 'win32' ? 'python' : 'python3';
  const tmpDir  = mkdtempSync(join(tmpdir(), 'sales-bridge-'));
  const tmpFile = join(tmpDir, 'input.json');

  try {
    writeFileSync(tmpFile, JSON.stringify(args), 'utf-8');
    const stdout = execFileSync(python, [BRIDGE_SCRIPT], {
      input: JSON.stringify(args),
      encoding: 'utf-8',
      timeout: 30_000,
      maxBuffer: 10 * 1024 * 1024,
    });
    const jsonStart = stdout.indexOf('{');
    if (jsonStart === -1) {
      throw new Error(`No JSON in bridge output: ${stdout.slice(0, 200)}`);
    }
    return JSON.parse(stdout.slice(jsonStart));
  } catch (err) {
    return { ok: false, error: `Sales bridge error: ${err.message}` };
  } finally {
    try { unlinkSync(tmpFile); } catch (_) { /* ignore */ }
    try { unlinkSync(tmpDir);  } catch (_) { /* ignore */ }
  }
}

export default [
  {
    name: 'analyze_sales',
    description: `Run in-depth sales analysis queries against the ERP PostgreSQL database.

Use this tool when the user asks about:
- Customer insights: top customers, repeat rate, customer segments, churn risk
- Product insights: bestsellers, sales by category/brand, product trends, top potential products
- Sales trends: monthly/quarterly sales, day-of-week patterns, growth rates
- Revenue reports: revenue by month/year, comparison periods
- Product trend analysis: top 10 potential products for future sales
- Vietnamese queries: doanh thu, khách hàng, sản phẩm, xu hướng, triển vọng, tiềm năng

This runs analysis queries directly on the ERP database tables (scm_sal_main, scm_sal_data)
and returns structured data for the LLM to interpret.`,
    parameters: {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          description: 'The user question about sales data. Include keywords like: customer, product, revenue, trend, churn, potential, top, bestseller, monthly. Supports Vietnamese too.',
        },
        companyfn: {
          type: 'string',
          description: 'Entity scope (cookie: cookcfnunique). Auto-filled from request.',
        },
        date_from: {
          type: 'string',
          description: 'Start date YYYY-MM-DD (optional). Use when user specifies a time range.',
        },
        date_to: {
          type: 'string',
          description: 'End date YYYY-MM-DD (optional). Use when user specifies a time range.',
        },
      },
      required: ['query'],
    },
    async func(args) {
      const result = callBridge({
        query: args.query,
        companyfn: args.companyfn,
        date_from: args.date_from || undefined,
        date_to: args.date_to || undefined,
      });

      if (!result.ok) {
        throw new Error(result.error || 'Sales analysis failed');
      }
      return result.result;
    },
  },
];