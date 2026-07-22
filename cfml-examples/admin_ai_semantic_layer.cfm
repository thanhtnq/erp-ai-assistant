<!---@ ###########################################################################################################
Version 5.0.1
File Description:
No	Modified Date	Modified By		Change Log
1.	20240722	Lopper		Creation Of File 
################################################################################################################# @--->
<cfparam name="cookie.cookuserloginid" default="admin">
<cfparam name="cookie.cookmfnunique" default="">
<cfparam name="cookie.cookcfnunique" default="">
<cfparam name="cookie.cookcompanycode" default="">
<cfparam name="url.embedded" default="0">

<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Semantic Layer Admin</title>
  <style>
    :root {
      --g3-primary:#1f4b7a;
      --g3-accent:#2f7dbd;
      --g3-border:#d8e1ea;
      --g3-bg:#f5f7fa;
      --g3-text:#182433;
      --g3-muted:#66788a;
      --g3-danger:#b42318;
      --g3-ok:#16794f;
    }
    * { box-sizing:border-box; }
    body { margin:0; font-family:Arial, sans-serif; background:var(--g3-bg); color:var(--g3-text); }
    .shell { max-width:1320px; margin:0 auto; padding:22px; }
    .topbar { display:flex; justify-content:space-between; gap:16px; align-items:center; margin-bottom:18px; }
    h1 { margin:0; font-size:22px; color:var(--g3-primary); }
    .sub { color:var(--g3-muted); font-size:13px; margin-top:4px; }
    .grid { display:grid; grid-template-columns:320px minmax(0,1fr); gap:16px; align-items:start; }
    .card { background:#fff; border:1px solid var(--g3-border); border-radius:8px; padding:16px; box-shadow:0 1px 3px rgba(20,40,70,.06); }
    .card h2 { margin:0 0 12px; font-size:15px; color:var(--g3-primary); }
    label { display:block; font-size:12px; font-weight:700; margin:12px 0 6px; }
    input, select { width:100%; padding:9px 10px; border:1px solid var(--g3-border); border-radius:6px; font-size:13px; background:#fff; }
    input[type=file] { padding:8px; }
    .row { display:flex; gap:8px; align-items:center; }
    .row > * { flex:1; }
    .radio-row { display:flex; gap:12px; margin:8px 0; font-size:13px; }
    .radio-row label { margin:0; font-weight:400; display:flex; gap:6px; align-items:center; }
    .radio-row input { width:auto; }
    .btn { border:1px solid var(--g3-primary); background:var(--g3-primary); color:#fff; border-radius:6px; padding:9px 12px; font-size:13px; cursor:pointer; }
    .btn.secondary { background:#fff; color:var(--g3-primary); }
    .btn.danger { border-color:var(--g3-danger); background:var(--g3-danger); }
    .btn:disabled { opacity:.55; cursor:not-allowed; }
    .actions { display:flex; gap:8px; flex-wrap:wrap; margin-top:14px; }
    .kpis { display:grid; grid-template-columns:repeat(4, minmax(0,1fr)); gap:10px; margin-bottom:14px; }
    .kpi { background:#fff; border:1px solid var(--g3-border); border-radius:8px; padding:12px; }
    .kpi .value { font-size:22px; font-weight:700; color:var(--g3-primary); }
    .kpi .label { font-size:12px; color:var(--g3-muted); }
    .table-wrap { overflow-x:auto; }
    table { width:100%; border-collapse:collapse; font-size:13px; table-layout:fixed; }
    th, td { text-align:left; padding:9px 8px; border-bottom:1px solid var(--g3-border); vertical-align:top; }
    th { background:#f7f9fc; color:var(--g3-primary); font-size:12px; }
    .files-table col:nth-child(1) { width:42px; }
    .files-table col:nth-child(2) { width:38%; }
    .files-table col:nth-child(3) { width:80px; }
    .files-table col:nth-child(4) { width:72px; }
    .files-table col:nth-child(5) { width:76px; }
    .files-table col:nth-child(6) { width:66px; }
    .files-table col:nth-child(7) { width:22%; }
    .files-table col:nth-child(8) { width:96px; }
    .file-cell, .error { overflow-wrap:anywhere; word-break:break-word; }
    .badge { display:inline-block; border-radius:999px; padding:3px 8px; font-size:12px; background:#eef3f8; color:var(--g3-primary); }
    .badge.done { background:#e8f6ef; color:var(--g3-ok); }
    .badge.failed { background:#fdecec; color:var(--g3-danger); }
    .badge.processing { background:#fff6df; color:#8a5a00; }
    .error { white-space:pre-wrap; color:var(--g3-danger); }
    .action-stack { display:flex; flex-direction:column; gap:6px; align-items:stretch; min-width:82px; }
    .action-stack .btn { width:100%; padding:7px 8px; white-space:nowrap; line-height:1.15; }
    .muted { color:var(--g3-muted); }
    .tabs { display:flex; gap:8px; margin:0 0 12px; }
    .tab { border:1px solid var(--g3-border); background:#fff; color:var(--g3-primary); border-radius:6px; padding:8px 11px; cursor:pointer; }
    .tab.active { background:var(--g3-primary); color:#fff; border-color:var(--g3-primary); }
    .panel { display:none; }
    .panel.active { display:block; }
    @media (max-width:900px) {
      .grid { grid-template-columns:1fr; }
      .kpis { grid-template-columns:repeat(2, minmax(0,1fr)); }
    }
    body.embedded { background:transparent; }
    body.embedded .shell { max-width:none; width:100%; padding:16px 18px 24px; }
    body.embedded .topbar { display:none; }
    body.embedded .kpis {
      display:flex;
      gap:14px;
      margin-bottom:18px;
      align-items:stretch;
      flex-wrap:wrap;
    }
    body.embedded .kpi {
      width:240px;
      min-height:102px;
      border-radius:8px;
      padding:16px 18px;
      box-shadow:0 3px 12px rgba(20,40,70,.08);
    }
    body.embedded .kpi .label {
      text-transform:uppercase;
      font-weight:700;
      letter-spacing:.04em;
      color:var(--g3-primary);
      margin-bottom:12px;
    }
    body.embedded .kpi .value {
      font-size:30px;
      line-height:1;
    }
    body.embedded .grid {
      display:block;
    }
    body.embedded .grid > .card {
      margin-bottom:12px;
      padding:14px 16px;
    }
    body.embedded .grid > .card h2,
    body.embedded .panel.card h2 {
      font-size:13px;
      text-transform:none;
      color:var(--g3-primary);
      margin-bottom:12px;
    }
    body.embedded .grid > .card label {
      margin-top:8px;
    }
    body.embedded .grid > .card .actions {
      margin-top:10px;
    }
    body.embedded .grid > .card {
      max-width:none;
    }
    body.embedded .grid > .card select,
    body.embedded .grid > .card input[type=file],
    body.embedded .grid > .card input[type=text],
    body.embedded .grid > .card input:not([type]) {
      max-width:300px;
    }
    body.embedded .panel.card {
      width:100%;
      border-radius:8px;
      padding:16px;
      box-shadow:0 1px 3px rgba(20,40,70,.06);
    }
    body.embedded .tabs {
      margin:0 0 10px;
    }
    body.embedded .tab {
      padding:7px 12px;
      font-size:12px;
    }
    body.embedded .registry-head {
      display:flex;
      align-items:center;
      justify-content:space-between;
      gap:12px;
      margin-bottom:12px;
    }
    body.embedded .registry-head h2 {
      margin:0;
    }
    body.embedded .registry-actions {
      display:flex;
      gap:8px;
      align-items:center;
    }
    body.embedded .upload-panel {
      display:none;
      margin-bottom:12px;
    }
    body.embedded .upload-panel.open {
      display:block;
    }
  </style>
</head>
<body class="<cfif url.embedded EQ '1'>embedded</cfif>">
<div class="shell">
  <div class="topbar">
    <div>
      <h1>AI Semantic Layer Admin</h1>
      <div class="sub">Upload scoped ERP report metadata, ingest it, and let chat select the right skill/tool.</div>
    </div>
    <div class="actions">
      <button class="btn secondary" onclick="loadAll()">Refresh</button>
    </div>
  </div>

  <div class="kpis">
    <div class="kpi"><div class="value" id="kpi-files">-</div><div class="label">Metadata Files</div></div>
    <div class="kpi"><div class="value" id="kpi-reports">-</div><div class="label">Active Reports</div></div>
    <div class="kpi"><div class="value" id="kpi-done">-</div><div class="label">Done Files</div></div>
    <div class="kpi"><div class="value" id="kpi-failed">-</div><div class="label">Failed Files</div></div>
  </div>

  <div class="grid">
    <div class="card upload-panel" id="upload-panel">
      <h2>Upload Metadata</h2>
      <label>Scope</label>
      <div class="radio-row">
        <label><input type="radio" name="scope_type" value="global" checked onchange="toggleCompany()"> Global</label>
        <label><input type="radio" name="scope_type" value="company" onchange="toggleCompany()"> Company</label>
      </div>

      <div id="company-fields" style="display:none">
        <label>Company Code</label>
        <input id="company_code" maxlength="20" value="<cfoutput>#HTMLEditFormat(cookie.cookcompanycode)#</cfoutput>" placeholder="ABC">
        <div class="row">
          <div>
            <label>Master FN</label>
            <input id="masterfn" value="<cfoutput>#HTMLEditFormat(cookie.cookmfnunique)#</cfoutput>">
          </div>
          <div>
            <label>Company FN</label>
            <input id="companyfn" value="<cfoutput>#HTMLEditFormat(cookie.cookcfnunique)#</cfoutput>">
          </div>
        </div>
      </div>

      <label>Business Module</label>
      <select id="module">
        <option value="sales">Sales</option>
        <option value="purchase">Purchase</option>
        <option value="inventory">Inventory</option>
        <option value="finance">Finance</option>
        <option value="hr">HR</option>
        <option value="project">Project</option>
        <option value="analytics">Analytics</option>
        <option value="general">General</option>
      </select>

      <label>Metadata File</label>
      <input id="semantic-file" type="file" accept=".json,.xlsx">
      <div class="muted" style="font-size:12px;margin-top:7px">Accepted: .json, .xlsx</div>

      <div class="actions">
        <button class="btn" onclick="uploadSemantic()">Upload</button>
        <button class="btn secondary" onclick="validateSelected()">Validate Selected File</button>
      </div>
      <div id="upload-msg" class="muted" style="margin-top:12px;font-size:13px"></div>
    </div>

    <div>
      <div class="tabs">
        <button class="tab active" onclick="showPanel('files')">Files</button>
        <button class="tab" onclick="showPanel('reports')">Reports</button>
        <button class="tab" onclick="showPanel('learned')">Learned</button>
      </div>

      <div id="panel-files" class="panel active card">
        <div class="registry-head">
          <h2>Semantic Metadata Registry</h2>
          <div class="registry-actions">
            <button class="btn" onclick="toggleUploadPanel()">+ Upload</button>
            <button class="btn secondary" onclick="loadAll()">Refresh</button>
          </div>
        </div>
        <div class="table-wrap">
        <table class="files-table">
          <colgroup><col><col><col><col><col><col><col><col></colgroup>
          <thead>
            <tr>
              <th>ID</th><th>File</th><th>Scope</th><th>Module</th><th>Status</th><th>Reports</th><th>Error</th><th>Actions</th>
            </tr>
          </thead>
          <tbody id="files-body"><tr><td colspan="8">Loading...</td></tr></tbody>
        </table>
        </div>
      </div>

      <div id="panel-reports" class="panel card">
        <h2>Parsed Reports</h2>
        <table>
          <thead>
            <tr>
              <th>Report ID</th><th>Name</th><th>Module</th><th>Scope</th><th>Intent</th><th>Tool</th><th>Default Filters</th>
            </tr>
          </thead>
          <tbody id="reports-body"><tr><td colspan="7">Loading...</td></tr></tbody>
        </table>
      </div>

      <div id="panel-learned" class="panel card">
        <h2>Learned Query Memory</h2>
        <table>
          <thead>
            <tr>
              <th>Question Template</th><th>Report</th><th>Tool</th><th>Verified</th><th>Feedback</th><th>Last Question</th>
            </tr>
          </thead>
          <tbody id="learned-body"><tr><td colspan="6">Loading...</td></tr></tbody>
        </table>
      </div>
    </div>
  </div>
</div>

<script>
const ADMIN = "<cfoutput>#JSStringFormat(cookie.cookuserloginid)#</cfoutput>" || "admin";
const PROXY = "inc_ajax_ai_admin.cfm";

function esc(v) {
  return String(v ?? "").replace(/[&<>"']/g, s => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[s]));
}

async function apiFetch(path, method = "GET", body = null) {
  const fd = new URLSearchParams();
  fd.append("action", "admin_call");
  fd.append("path", path);
  fd.append("method", method);
  if (body) fd.append("body", JSON.stringify(body));
  const res = await fetch(PROXY, {
    method: "POST",
    headers: {"Content-Type": "application/x-www-form-urlencoded"},
    body: fd
  });
  const text = await res.text();
  let data;
  try { data = JSON.parse(text); } catch(e) { data = {error:text}; }
  if (!res.ok) throw new Error(data.detail || data.error || text);
  return data;
}

function selectedScope() {
  return document.querySelector("input[name='scope_type']:checked").value;
}

function toggleCompany() {
  document.getElementById("company-fields").style.display = selectedScope() === "company" ? "block" : "none";
}

function showPanel(name) {
  document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
  document.querySelectorAll(".panel").forEach(p => p.classList.remove("active"));
  event.target.classList.add("active");
  document.getElementById("panel-" + name).classList.add("active");
}

function toggleUploadPanel(forceOpen) {
  const panel = document.getElementById("upload-panel");
  const shouldOpen = forceOpen === true || !panel.classList.contains("open");
  panel.classList.toggle("open", shouldOpen);
}

async function loadStats() {
  const s = await apiFetch("admin/semantic/stats");
  document.getElementById("kpi-files").textContent = s.files ?? 0;
  document.getElementById("kpi-reports").textContent = s.reports ?? 0;
  document.getElementById("kpi-done").textContent = (s.files_by_status || {}).done || 0;
  document.getElementById("kpi-failed").textContent = (s.files_by_status || {}).failed || 0;
}

async function loadFiles() {
  const d = await apiFetch("admin/semantic/files?limit=100");
  const body = document.getElementById("files-body");
  const items = d.items || [];
  if (!items.length) {
    body.innerHTML = '<tr><td colspan="8" class="muted">No semantic metadata files yet.</td></tr>';
    return;
  }
  body.innerHTML = items.map(row => {
    const scope = row.scope_type === "company" ? `${esc(row.company_code)}<br><span class="muted">${esc(row.masterfn)} / ${esc(row.companyfn)}</span>` : "Global";
    const statusClass = ["done","failed","processing"].includes(row.status) ? row.status : "";
    return `<tr>
      <td>${row.id}</td>
      <td class="file-cell">${esc(row.filename)}<br><span class="muted">${esc(row.file_path)}</span></td>
      <td>${scope}</td>
      <td>${esc(row.module)}</td>
      <td><span class="badge ${statusClass}">${esc(row.status)}</span></td>
      <td>${row.reports_parsed || 0}</td>
      <td class="error">${esc(row.error_message || "")}</td>
      <td>
        <div class="action-stack">
        <button class="btn secondary" onclick="runNow(${row.id})">Re-Ingest</button>
        <button class="btn secondary" onclick="validateFile(${row.id})">Validate</button>
        <button class="btn danger" onclick="deleteFile(${row.id})">Delete</button>
        </div>
      </td>
    </tr>`;
  }).join("");
}

async function loadReports() {
  const module = document.getElementById("module").value;
  const d = await apiFetch(`admin/semantic/reports?module=${encodeURIComponent(module)}`);
  const body = document.getElementById("reports-body");
  const items = d.items || [];
  if (!items.length) {
    body.innerHTML = '<tr><td colspan="7" class="muted">No reports parsed for this module.</td></tr>';
    return;
  }
  body.innerHTML = items.map(row => `<tr>
    <td>${esc(row.report_id)}</td>
    <td>${esc(row.report_name)}<br><span class="muted">${esc(row.description || "")}</span></td>
    <td>${esc(row.module)}</td>
    <td>${row.scope_type === "company" ? esc(row.company_code) : "Global"}</td>
    <td>${esc(row.intent_type)}</td>
    <td>${esc(row.tool_name)}</td>
    <td><code>${esc(JSON.stringify(row.default_filters || {}))}</code></td>
  </tr>`).join("");
}

async function loadLearned() {
  const module = document.getElementById("module").value;
  const d = await apiFetch(`admin/semantic/learned?module=${encodeURIComponent(module)}`);
  const body = document.getElementById("learned-body");
  const items = d.items || [];
  if (!items.length) {
    body.innerHTML = '<tr><td colspan="6" class="muted">No learned query mappings yet.</td></tr>';
    return;
  }
  body.innerHTML = items.map(row => `<tr>
    <td><code>${esc(row.normalized_question)}</code></td>
    <td>${esc(row.report_id)}<br><span class="muted">${esc(row.module)}</span></td>
    <td>${esc(row.tool_name)}</td>
    <td>${row.verified ? '<span class="badge done">verified</span>' : '<span class="badge">candidate</span>'}</td>
    <td>Up: ${row.feedback_up_count || 0}<br>Down: ${row.feedback_down_count || 0}</td>
    <td>${esc(row.question_text)}</td>
  </tr>`).join("");
}

async function uploadSemantic() {
  const fileInput = document.getElementById("semantic-file");
  const msg = document.getElementById("upload-msg");
  if (!fileInput.files.length) { msg.textContent = "Please choose a metadata file."; return; }
  const scope = selectedScope();
  const fd = new FormData();
  fd.append("action", "semantic_upload");
  fd.append("file", fileInput.files[0]);
  fd.append("scope_type", scope);
  fd.append("company_code", document.getElementById("company_code").value.trim().toUpperCase());
  fd.append("masterfn", document.getElementById("masterfn").value.trim());
  fd.append("companyfn", document.getElementById("companyfn").value.trim());
  fd.append("module", document.getElementById("module").value);
  fd.append("admin_user_id", ADMIN);
  msg.textContent = "Uploading...";
  const res = await fetch(PROXY, {method:"POST", body:fd});
  const text = await res.text();
  let data;
  try { data = JSON.parse(text); } catch(e) { data = {error:text}; }
  if (!res.ok || data.error || data.detail) {
    msg.textContent = data.detail || data.error || "Upload failed.";
    return;
  }
  msg.textContent = `Uploaded ${data.filename || fileInput.files[0].name}. Status: ${data.status}`;
  fileInput.value = "";
  toggleUploadPanel(false);
  await loadAll();
}

async function runNow(id) {
  await apiFetch(`admin/semantic/files/${id}/run-now`, "POST", {admin_user_id: ADMIN});
  await loadAll();
  setTimeout(loadAll, 1500);
}

async function validateFile(id) {
  try {
    const d = await apiFetch("admin/semantic/validate", "POST", {file_id:id});
    alert("Valid metadata:\\n" + JSON.stringify(d.sections, null, 2));
  } catch(e) {
    alert("Validation failed:\\n" + e.message);
  }
}

async function validateSelected() {
  alert("Upload the file first, then use Validate from the file row.");
}

async function deleteFile(id) {
  if (!confirm("Delete this semantic metadata file and parsed metadata?")) return;
  await apiFetch(`admin/semantic/files/${id}?admin_user_id=${encodeURIComponent(ADMIN)}`, "DELETE");
  await loadAll();
}

async function loadAll() {
  try {
    await Promise.all([loadStats(), loadFiles(), loadReports(), loadLearned()]);
  } catch(e) {
    document.getElementById("upload-msg").textContent = e.message;
  }
}

document.getElementById("module").addEventListener("change", () => { loadReports(); loadLearned(); });
toggleCompany();
loadAll();
</script>
</body>
</html>
