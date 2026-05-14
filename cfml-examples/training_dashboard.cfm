<!---
  Globe3 ERP AI Assistant - SCM Training Dashboard
  Tracks whether chat questions route to trained SCM artifacts, live ERP tools, or RAG.
--->
<cfset adminUserId = (structKeyExists(cookie, "cookuserloginid") ? cookie.cookuserloginid : "admin")>
<cfset defaultMasterfn = (structKeyExists(cookie, "cookmfnunique") ? cookie.cookmfnunique : "")>
<cfset defaultCompanyfn = (structKeyExists(cookie, "cookcfnunique") ? cookie.cookcfnunique : "")>
<cfscript>
aiApiUrl = "http://localhost:8001";
aiApiKey = "erp-ai-secret-key-change-me";
envPath = "D:\tnosystems\v50foldersetadmin\v50stringg3new\v50master\contentadmin\erp-ai-assistant\.env";
if (!FileExists(envPath)) {
  envPath = ExpandPath("../.env");
}

if (FileExists(envPath)) {
  envText = FileRead(envPath);
  envLines = ListToArray(envText, Chr(10));
  for (envLine in envLines) {
    line = Trim(Replace(envLine, Chr(13), "", "all"));
    if (!Len(line) || Left(line, 1) == "##" || !Find("=", line)) {
      continue;
    }
    key = Trim(ListFirst(line, "="));
    value = Trim(Mid(line, Find("=", line) + 1, Len(line)));
    if (Len(value) >= 2) {
      quote = Left(value, 1);
      if ((quote == """" || quote == "'") && Right(value, 1) == quote) {
        value = Mid(value, 2, Len(value) - 2);
      }
    }
    if (key == "CHAT_API_KEY") {
      aiApiKey = value;
    } else if (key == "AI_API_URL") {
      aiApiUrl = value;
    }
  }
}
</cfscript>
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SCM Training Dashboard</title>
  <link rel="stylesheet" href="globe3-ui.css">
  <link rel="stylesheet" href="training_dashboard.css">
</head>
<body>
<cfoutput>
<div class="page">
  <div class="page-head">
    <div>
      <h1>SCM Training Dashboard</h1>
      <div class="sub">Track trained artifacts, chat routing, model usage, and run extract/train jobs.</div>
    </div>
    <div class="actions">
      <button class="secondary" id="refresh-btn">Refresh</button>
    </div>
  </div>

  <div class="toolbar">
    <div>
      <label>masterfn</label>
      <input id="masterfn" value="#EncodeForHTMLAttribute(defaultMasterfn)#" placeholder="cookmfnunique">
    </div>
    <div>
      <label>companyfn</label>
      <input id="companyfn" value="#EncodeForHTMLAttribute(defaultCompanyfn)#" placeholder="cookcfnunique">
    </div>
    <div>
      <label>trace route</label>
      <select id="route">
        <option value="">All routes</option>
        <option value="scm_training">SCM training</option>
        <option value="data_query">Live ERP tools</option>
        <option value="rag">RAG knowledge</option>
        <option value="ambiguity">Clarification</option>
      </select>
    </div>
    <div>
      <label>training action</label>
      <select id="action">
        <option value="extract_train">Extract + train</option>
        <option value="extract">Extract only</option>
        <option value="train">Train only</option>
        <option value="trend">Trend analysis</option>
      </select>
    </div>
    <div>
      <label>model</label>
      <select id="model">
        <option value="all">All</option>
        <option value="churn">Churn</option>
        <option value="forecast">Forecast</option>
      </select>
    </div>
    <div class="actions">
      <button id="apply-btn">Apply</button>
      <button class="secondary" id="run-training-btn">Run</button>
    </div>
  </div>

  <div class="grid">
    <div class="metric"><div class="n" id="m-scopes">-</div><div class="l">trained scopes</div></div>
    <div class="metric"><div class="n" id="m-datasets">-</div><div class="l">dataset types</div></div>
    <div class="metric"><div class="n" id="m-models">-</div><div class="l">model files</div></div>
    <div class="metric"><div class="n" id="m-traces">-</div><div class="l">tracked questions</div></div>
  </div>

  <div class="section">
    <div class="section-head"><h2>Training Artifacts</h2><span class="muted" id="artifact-root"></span></div>
    <div id="scopes-box" class="state">Loading artifacts...</div>
  </div>

  <div class="section">
    <div class="section-head"><h2>Recent Query Routing</h2><span class="muted">Shows which engine answered each question.</span></div>
    <div id="trace-box" class="state">Loading traces...</div>
  </div>

  <div class="section">
    <div class="section-head"><h2>Training Jobs</h2><span class="muted">Jobs run in the API process background.</span></div>
    <div id="jobs-box" class="state">No jobs loaded.</div>
  </div>
</div>

<div id="training-dashboard-config"
     data-api="#EncodeForHTMLAttribute(aiApiUrl)#"
     data-api-key="#EncodeForHTMLAttribute(aiApiKey)#"
     data-admin="#EncodeForHTMLAttribute(adminUserId)#"></div>
<script src="training_dashboard.js"></script>
</cfoutput>
</body>
</html>
