/**
 * Globe3 Skills Server
 * Exposes all globe3-* skill tools as HTTP endpoints for api.py to call.
 *
 * Routes:
 *   GET  /health   — liveness check + loaded tool names
 *   GET  /tools    — Ollama-compatible tool definitions (array)
 *   POST /execute  — execute a named tool { name, arguments, masterfn, companyfn }
 *
 * Start: node skills/server.js
 * Port:  SKILLS_PORT env var (default 3001)
 */

import express    from 'express';
import { mkdirSync, readdirSync, statSync } from 'fs';
import { appendFile, rename, stat, unlink } from 'fs/promises';
import { join, dirname }         from 'path';
import { fileURLToPath, pathToFileURL } from 'url';
import { randomUUID } from 'crypto';

const __dir = dirname(fileURLToPath(import.meta.url));
const app   = express();
app.use(express.json({ limit: '64kb' }));
const auditDir = join(__dir, '..', 'logs');
const auditPath = join(auditDir, 'skills-audit.log');
const auditPreviousPath = join(auditDir, 'skills-audit-previous.log');
const auditMaxBytes = Math.max(1024 * 1024, Number(process.env.SKILLS_AUDIT_MAX_BYTES || 10 * 1024 * 1024));
mkdirSync(auditDir, { recursive: true });
let auditQueue = Promise.resolve();

const cleanScope = (value) => {
  const text = String(value ?? '').trim();
  if (!text || text.length > 128 || /[\u0000-\u001f\u007f]/.test(text)) return '';
  return text;
};

const audit = (event) => {
  const line = JSON.stringify({ event:'skill_execution', timestamp:new Date().toISOString(), ...event });
  console.log(line);
  auditQueue = auditQueue.then(async () => {
    try {
      const info = await stat(auditPath).catch(() => null);
      if (info && info.size >= auditMaxBytes) {
        await unlink(auditPreviousPath).catch(() => {});
        await rename(auditPath, auditPreviousPath);
      }
      await appendFile(auditPath, `${line}\n`, { encoding:'utf8', mode:0o600 });
    } catch (error) {
      console.error(`[audit] ${error.message}`);
    }
  });
};

// ── Load all globe3-* skill modules ──────────────────────────────────────────

const skills = {};

const skillDirs = readdirSync(__dir).filter(name =>
  name.startsWith('globe3-') && statSync(join(__dir, name)).isDirectory()
);

for (const dir of skillDirs) {
  const toolsPath = pathToFileURL(join(__dir, dir, 'tools.js')).href;
  try {
    const { default: tools } = await import(toolsPath);
    for (const tool of tools) {
      skills[tool.name] = tool;
    }
    console.log(`[OK] ${dir}: ${tools.map(t => t.name).join(', ')}`);
  } catch (e) {
    console.error(`[FAIL] ${dir}/tools.js — ${e.message}`);
  }
}

console.log(`\nLoaded ${Object.keys(skills).length} tools total.\n`);

// ── Routes ────────────────────────────────────────────────────────────────────

app.get('/health', (_req, res) => {
  res.json({ status: 'ok', tools: Object.keys(skills) });
});

/**
 * GET /tools
 * Returns all tool definitions in Ollama's tool calling format.
 */
app.get('/tools', (_req, res) => {
  const tools = Object.values(skills).map(t => ({
    type: 'function',
    function: {
      name:        t.name,
      description: t.description,
      parameters:  t.parameters,
    },
  }));
  res.json(tools);
});

/**
 * POST /execute
 * Body: { name: string, arguments: object, masterfn: string, companyfn: string }
 */
app.post('/execute', async (req, res) => {
  const requestId = randomUUID();
  const started = Date.now();
  const { name, arguments: args = {} } = req.body || {};
  const masterfn = cleanScope(req.body?.masterfn);
  const companyfn = cleanScope(req.body?.companyfn);

  if (!skills[name]) {
    audit({ request_id: requestId, tool: String(name || ''), masterfn, companyfn, status: 'unknown_tool', duration_ms: Date.now()-started });
    return res.status(404).json({ ok: false, error: `Unknown tool: "${name}"` });
  }
  if (!masterfn || !companyfn) {
    audit({ request_id: requestId, tool: name, masterfn, companyfn, status: 'invalid_scope', duration_ms: Date.now()-started });
    return res.status(400).json({ ok: false, error: 'valid masterfn and companyfn are required', request_id: requestId });
  }
  if (!args || typeof args !== 'object' || Array.isArray(args)) {
    audit({ request_id: requestId, tool: name, masterfn, companyfn, status: 'invalid_arguments', duration_ms: Date.now()-started });
    return res.status(400).json({ ok: false, error: 'arguments must be an object', request_id: requestId });
  }

  try {
    const result = await skills[name].func({ ...args, masterfn, companyfn });
    const rowCount = Array.isArray(result?.rows) ? result.rows.length : null;
    audit({ request_id: requestId, tool: name, masterfn, companyfn, status: 'ok', duration_ms: Date.now()-started, row_count: rowCount });
    res.set('X-Request-ID', requestId).json({ ok: true, result, request_id: requestId });
  } catch (err) {
    audit({ request_id: requestId, tool: name, masterfn, companyfn, status: 'error', duration_ms: Date.now()-started, error_type: err?.code || err?.name || 'Error' });
    console.error(`[${requestId}] [${name}] ${err.message}`);
    res.status(500).json({ ok: false, error: err.message, request_id: requestId });
  }
});

app.use((err, _req, res, next) => {
  if (!err) return next();
  if (err.type === 'entity.too.large') return res.status(413).json({ ok:false, error:'request body too large' });
  if (err instanceof SyntaxError) return res.status(400).json({ ok:false, error:'invalid JSON body' });
  return next(err);
});

// ── Start ─────────────────────────────────────────────────────────────────────

const PORT = parseInt(process.env.SKILLS_PORT || '3001', 10);
app.listen(PORT, () => {
  console.log(`Skills server listening on http://localhost:${PORT}`);
});
