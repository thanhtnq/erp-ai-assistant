<!---
  Developer diagnostic: verify tenant-scoped realtime Skills queries.
  This page never renders API/DB credentials and only permits whitelisted tools.
--->
<cfsetting showdebugoutput="false">
<cfparam name="cookie.cookuserloginid" default="">
<cfparam name="cookie.cookmfnunique" default="">
<cfparam name="cookie.cookcfnunique" default="">
<cfparam name="form.tool_name" default="get_sku_demand_history">
<cfparam name="form.days" default="30">
<cfparam name="form.top" default="10">
<cfparam name="form.group_by" default="company">

<cfscript>
skillsUrl = "http://localhost:3001";
toolCatalog = {
  "get_sku_demand_history" = {
    label = "SKU Demand History",
    sources = "scm_sal_main + scm_sal_data",
    logic = "Non-void Sales Invoice lines, grouped by SKU/week (optionally location)."
  },
  "forecast_sku_demand_advanced" = {
    label = "Advanced SKU Demand Forecast",
    sources = "scm_sal_main + scm_sal_data",
    logic = "Weekly SKU demand mean, variability and trend projected to the requested horizon."
  },
  "recommend_inventory_replenishment" = {
    label = "Replenishment Recommendations",
    sources = "scm_sal_main + scm_sal_data + stk_code_main + stk_code_data",
    logic = "Demand + lead time + variability + on-hand; returns safety stock, reorder point and quantity."
  },
  "detect_duplicate_ap_transactions" = {
    label = "Potential Duplicate AP Transactions",
    sources = "gnl_maint_all",
    logic = "Non-void AP rows grouped by vendor + normalized reference + currency + absolute local amount."
  },
  "detect_finance_transaction_anomalies" = {
    label = "Finance Transaction Anomalies",
    sources = "gnl_maint_all",
    logic = "Vendor/source amount outliers using historical average and standard deviation."
  },
  "detect_vendor_risk_indicators" = {
    label = "Vendor Risk Indicators",
    sources = "gnl_maint_all",
    logic = "Vendor payment concentration within the selected tenant and period."
  },
  "detect_inventory_movement_anomalies" = {
    label = "Inventory Movement Anomalies",
    sources = "scm_stk_main + scm_stk_data",
    logic = "Adjustment quantity outliers by SKU/location against historical mean and deviation."
  },
  "detect_stock_shrinkage_indicators" = {
    label = "Stock Shrinkage Indicators",
    sources = "scm_stk_main + scm_stk_data",
    logic = "Net negative stock-adjustment indicators by SKU/location; not proof of theft."
  },
  "detect_expiry_writeoff_risk" = {
    label = "Expiry / Write-off Risk",
    sources = "stkm_main_all",
    logic = "Positive batch balances expiring within the horizon, with estimated write-off exposure."
  },
  "analyze_scm_realtime" = {
    label = "SCM Overview",
    sources = "scm_sal_main",
    logic = "Non-void Sales Invoice / SO Confirmation / Sales Order summary for the selected period."
  }
};

masterfn = trim(cookie.cookmfnunique);
companyfn = trim(cookie.cookcfnunique);
userId = trim(cookie.cookuserloginid);
selectedTool = structKeyExists(toolCatalog, form.tool_name) ? form.tool_name : "get_sku_demand_history";
days = min(max(val(form.days), 1), 365);
top = min(max(val(form.top), 1), 100);
requestPayload = {};
rawResponse = "";
httpStatus = "Not executed";
runError = "";

if (structKeyExists(form, "run_check")) {
  if (!len(userId) || !len(masterfn) || !len(companyfn)) {
    runError = "Missing authenticated ERP cookies: cookuserloginid, cookmfnunique or cookcfnunique.";
  } else {
    toolArgs = { "days" = days, "top" = top };
    if (selectedTool == "get_sku_demand_history") {
      toolArgs.group_by = (form.group_by == "location" ? "location" : "company");
    }
    if (selectedTool == "forecast_sku_demand_advanced") {
      toolArgs.horizon_days = days;
    }
    if (selectedTool == "detect_duplicate_ap_transactions") {
      toolArgs.transaction_type = "invoice";
    }
    if (selectedTool == "analyze_scm_realtime") {
      toolArgs.analysis = "overview";
    }
    requestPayload = {
      "name" = selectedTool,
      "arguments" = toolArgs,
      "masterfn" = masterfn,
      "companyfn" = companyfn
    };
  }
}
</cfscript>

<cfif structKeyExists(form, "run_check") AND !len(runError)>
  <cftry>
    <cfhttp url="#skillsUrl#/execute" method="POST" result="skillHttp" timeout="45" throwonerror="false">
      <cfhttpparam type="header" name="Content-Type" value="application/json">
      <cfhttpparam type="body" value="#serializeJSON(requestPayload)#">
    </cfhttp>
    <cfset httpStatus = structKeyExists(skillHttp, "statusCode") ? skillHttp.statusCode : "Unknown">
    <cfset rawResponse = toString(skillHttp.fileContent)>
    <cfcatch>
      <cfset runError = cfcatch.message & (len(cfcatch.detail) ? ": " & cfcatch.detail : "")>
    </cfcatch>
  </cftry>
</cfif>

<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>ERP AI Realtime Query Check</title>
  <style>
    body{font-family:Arial,sans-serif;margin:20px;color:#12345b;background:#f4f7fb}
    .card{background:white;border:1px solid #c9d7e8;border-radius:8px;padding:16px;margin-bottom:14px}
    h1{font-size:21px;margin:0 0 14px} h2{font-size:16px;margin:0 0 10px}
    label{display:block;font-weight:700;margin:9px 0 4px} select,input{padding:7px;border:1px solid #9eb2ca;border-radius:4px}
    select{min-width:360px}.row{display:flex;gap:18px;flex-wrap:wrap}.muted{color:#657890;font-size:12px}
    button{margin-top:14px;padding:8px 16px;background:#073b78;color:white;border:0;border-radius:5px;cursor:pointer}
    pre{white-space:pre-wrap;word-break:break-word;background:#0d1b2a;color:#d9e8f7;padding:14px;border-radius:6px;max-height:520px;overflow:auto}
    .ok{color:#16733b}.error{color:#b42318}.kv{display:grid;grid-template-columns:150px 1fr;gap:5px 10px}
    code{background:#eaf0f7;padding:2px 4px;border-radius:3px}
  </style>
</head>
<body>
<h1>ERP AI Realtime Query Check</h1>

<div class="card">
  <h2>Current ERP scope</h2>
  <div class="kv">
    <div>User</div><div><cfoutput>#htmlEditFormat(userId)#</cfoutput></div>
    <div>masterfn</div><div><cfoutput>#htmlEditFormat(masterfn)#</cfoutput></div>
    <div>companyfn</div><div><cfoutput>#htmlEditFormat(companyfn)#</cfoutput></div>
    <div>Skills endpoint</div><div><code><cfoutput>#htmlEditFormat(skillsUrl)#/execute</cfoutput></code></div>
  </div>
</div>

<div class="card">
  <form method="post">
    <label for="tool_name">Realtime query</label>
    <select id="tool_name" name="tool_name">
      <cfoutput>
      <cfloop collection="#toolCatalog#" item="toolKey">
        <option value="#htmlEditFormat(toolKey)#" #(selectedTool == toolKey ? "selected" : "")#>#htmlEditFormat(toolCatalog[toolKey].label)# — #htmlEditFormat(toolKey)#</option>
      </cfloop>
      </cfoutput>
    </select>
    <div class="row">
      <div><label for="days">Period / horizon (days)</label><input id="days" name="days" type="number" min="1" max="365" value="<cfoutput>#days#</cfoutput>"></div>
      <div><label for="top">Maximum rows</label><input id="top" name="top" type="number" min="1" max="100" value="<cfoutput>#top#</cfoutput>"></div>
      <div><label for="group_by">Demand grouping</label><select id="group_by" name="group_by" style="min-width:150px"><option value="company">Company</option><option value="location" <cfif form.group_by EQ "location">selected</cfif>>Location</option></select></div>
    </div>
    <button type="submit" name="run_check" value="1">Run realtime check</button>
  </form>
</div>

<div class="card">
  <h2>What this tool queries</h2>
  <div class="kv">
    <div>Tool</div><div><code><cfoutput>#htmlEditFormat(selectedTool)#</cfoutput></code></div>
    <div>Source tables</div><div><cfoutput>#htmlEditFormat(toolCatalog[selectedTool].sources)#</cfoutput></div>
    <div>SQL logic</div><div><cfoutput>#htmlEditFormat(toolCatalog[selectedTool].logic)#</cfoutput></div>
    <div>Mandatory scope</div><div><code>masterfn + companyfn</code></div>
  </div>
  <p class="muted">Exact implementation SQL lives in the selected skill's <code>tools.js</code>. This page shows the executed tool, arguments, scope and raw result without exposing credentials.</p>
</div>

<cfif structKeyExists(form, "run_check")>
  <div class="card">
    <h2>Executed request</h2>
    <pre><cfoutput>#htmlEditFormat(serializeJSON(requestPayload))#</cfoutput></pre>
  </div>
  <div class="card">
    <h2>Skills response — HTTP <cfoutput>#htmlEditFormat(httpStatus)#</cfoutput></h2>
    <cfif len(runError)><p class="error"><cfoutput>#htmlEditFormat(runError)#</cfoutput></p></cfif>
    <cfif len(rawResponse)><pre><cfoutput>#htmlEditFormat(rawResponse)#</cfoutput></pre></cfif>
  </div>
</cfif>
</body>
</html>
