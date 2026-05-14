const cfg = document.getElementById("training-dashboard-config")?.dataset || {};
const API = cfg.api || "http://localhost:8001";
const API_KEY = cfg.apiKey || "erp-ai-secret-key-change-me";
const ADMIN = cfg.admin || "admin";
const HEADERS = {"Content-Type": "application/json", "X-API-Key": API_KEY};

function esc(v) {
  return String(v ?? "").replace(/[&<>"']/g, ch => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[ch]));
}

function qs() {
  const p = new URLSearchParams();
  const masterfn = document.getElementById("masterfn").value.trim();
  const companyfn = document.getElementById("companyfn").value.trim();
  const route = document.getElementById("route").value;
  if (masterfn) p.set("masterfn", masterfn);
  if (companyfn) p.set("companyfn", companyfn);
  if (route) p.set("route", route);
  return p;
}

async function apiGet(path) {
  const res = await fetch(API + path, {headers: HEADERS});
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function apiPost(path, body) {
  const res = await fetch(API + path, {
    method: "POST",
    headers: HEADERS,
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function routePill(route) {
  const cls = route === "scm_training" ? "ok" : route === "data_query" ? "info" : route === "rag" ? "warn" : "";
  return `<span class="pill ${cls}">${esc(route)}</span>`;
}

function trainedPill(item) {
  if (item.used_training) return `<span class="pill ok">${esc(item.trained_status || "used")}</span>`;
  return `<span class="pill">${esc(item.trained_status || "not training")}</span>`;
}

async function loadStatus() {
  const p = qs();
  p.delete("route");
  const d = await apiGet("/admin/training/status?" + p.toString());
  document.getElementById("artifact-root").textContent = d.artifact_root || "";
  document.getElementById("m-scopes").textContent = d.scope_count || 0;
  document.getElementById("m-datasets").textContent = (d.dataset_names || []).length;
  document.getElementById("m-models").textContent = (d.model_names || []).length;
  renderScopes(d.scopes || []);
  renderJobs(d.jobs || []);
}

function renderScopes(scopes) {
  const box = document.getElementById("scopes-box");
  if (!scopes.length) {
    box.className = "state";
    box.textContent = "No SCM training artifacts found for this filter.";
    return;
  }
  box.className = "";
  box.innerHTML = `<table>
    <thead><tr><th>Scope</th><th>Datasets</th><th>Models</th><th>Analysis</th><th>Updated</th></tr></thead>
    <tbody>${scopes.map(s => `
      <tr>
        <td><div class="mono">${esc(s.masterfn)} / ${esc(s.companyfn)}</div><div class="muted">${esc(s.database)}</div></td>
        <td>${(s.datasets || []).map(d => `<div><span class="pill info">${esc(d.name)}</span> ${esc(d.rows ?? "?")} rows</div>`).join("") || "-"}</td>
        <td>${(s.models || []).map(m => `<div><span class="pill ok">${esc(m.name)}</span> <span class="muted">${esc(m.updated_at || "")}</span></div>`).join("") || "-"}</td>
        <td>${(s.analysis || []).slice(0, 3).map(a => `<div class="mono">${esc(a.name)}</div>`).join("") || "-"}</td>
        <td class="muted">${esc(s.updated_at || "")}</td>
      </tr>`).join("")}</tbody>
  </table>`;
}

async function loadTraces() {
  const p = qs();
  p.set("limit", "100");
  const d = await apiGet("/admin/training/query-traces?" + p.toString());
  document.getElementById("m-traces").textContent = d.total || 0;
  const box = document.getElementById("trace-box");
  const items = d.items || [];
  if (!items.length) {
    box.className = "state";
    box.textContent = "No query traces yet. Ask a chat question first.";
    return;
  }
  box.className = "";
  box.innerHTML = `<table>
    <thead><tr><th>Time</th><th>Route</th><th>Question</th><th>Rewritten / Scope</th><th>Model</th><th>Training</th></tr></thead>
    <tbody>${items.map(i => `
      <tr>
        <td class="muted">${esc(i.created_at)}</td>
        <td>${routePill(i.route)}</td>
        <td>${esc(i.original_query)}</td>
        <td><div>${esc(i.rewritten_query || "")}</div><div class="mono muted">${esc(i.masterfn)} / ${esc(i.companyfn)}</div></td>
        <td><div>${esc(i.model || "-")}</div><div class="muted">${esc(i.intent || "")} ${i.duration_ms ? "(" + esc(i.duration_ms) + "ms)" : ""}</div></td>
        <td>${trainedPill(i)}<div class="muted">${esc(i.training_scope || "")}</div></td>
      </tr>`).join("")}</tbody>
  </table>`;
}

function renderJobs(jobs) {
  const box = document.getElementById("jobs-box");
  if (!jobs.length) {
    box.className = "state";
    box.textContent = "No training jobs in this API process.";
    return;
  }
  box.className = "";
  box.innerHTML = `<table>
    <thead><tr><th>Job</th><th>Status</th><th>Scope</th><th>Action</th><th>Started</th><th>Error</th></tr></thead>
    <tbody>${jobs.map(j => `
      <tr>
        <td class="mono">${esc(j.id)}</td>
        <td>${j.status === "done" ? '<span class="pill ok">done</span>' : j.status === "failed" ? '<span class="pill warn">failed</span>' : '<span class="pill info">' + esc(j.status) + '</span>'}</td>
        <td class="mono">${esc(j.masterfn)} / ${esc(j.companyfn)}</td>
        <td>${esc(j.action)} / ${esc(j.model)}</td>
        <td class="muted">${esc(j.started_at)}</td>
        <td class="muted">${esc(j.error || "")}</td>
      </tr>`).join("")}</tbody>
  </table>`;
}

async function runTraining() {
  const masterfn = document.getElementById("masterfn").value.trim();
  if (!masterfn) {
    alert("masterfn is required.");
    return;
  }
  const body = {
    admin_user_id: ADMIN,
    action: document.getElementById("action").value,
    masterfn,
    companyfn: document.getElementById("companyfn").value.trim(),
    model: document.getElementById("model").value,
    note: "Started from training_dashboard.cfm",
  };
  await apiPost("/admin/training/run", body);
  await loadStatus();
}

async function refreshAll() {
  try {
    await Promise.all([loadStatus(), loadTraces()]);
  } catch (e) {
    alert("Dashboard load failed: " + e.message);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("refresh-btn")?.addEventListener("click", refreshAll);
  document.getElementById("apply-btn")?.addEventListener("click", refreshAll);
  document.getElementById("run-training-btn")?.addEventListener("click", runTraining);
  refreshAll();
  setInterval(loadStatus, 10000);
});
