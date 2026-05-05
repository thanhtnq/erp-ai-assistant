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
import { readdirSync, statSync } from 'fs';
import { join, dirname }         from 'path';
import { fileURLToPath, pathToFileURL } from 'url';

const __dir = dirname(fileURLToPath(import.meta.url));
const app   = express();
app.use(express.json());

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
  const { name, arguments: args = {}, masterfn, companyfn } = req.body;

  if (!skills[name]) {
    return res.status(404).json({ ok: false, error: `Unknown tool: "${name}"` });
  }
  if (!masterfn || !companyfn) {
    return res.status(400).json({ ok: false, error: 'masterfn and companyfn are required' });
  }

  try {
    const result = await skills[name].func({ ...args, masterfn, companyfn });
    res.json({ ok: true, result });
  } catch (err) {
    console.error(`[${name}] ${err.message}`);
    res.status(500).json({ ok: false, error: err.message });
  }
});

// ── Start ─────────────────────────────────────────────────────────────────────

const PORT = parseInt(process.env.SKILLS_PORT || '3001', 10);
app.listen(PORT, () => {
  console.log(`Skills server listening on http://localhost:${PORT}`);
});
