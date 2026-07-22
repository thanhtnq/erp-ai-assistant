<!---@ ###########################################################################################################
Version 5.0.1
File Description:
No	Modified Date	Modified By		Change Log
1.	20240722	Lopper		Creation Of File 
################################################################################################################# @--->
<cfparam name="action" default="">
<cfparam name="cookie.cookuserloginid" default="">
<cfparam name="cookie.cookmfnunique"   default="">
<cfparam name="cookie.cookcfnunique"   default="">

<cfinclude template="inc_syspathname.cfm">
<cfinclude template="sym_meta_lang_a.cfm">
<cfinclude template="inc_qs_set_co_main.cfm">

<cfscript>
    host_api_url = "http://localhost:8000";
    ai_api_key = "YJfgXD-P5WF9p3VCT1XN_ehsnB2KK_OfIYedBxz_J8M";
</cfscript>
<cftry>
    <cfinclude template="inc_ai_host_config.cfm">
    <cfcatch></cfcatch>
</cftry>

<cfswitch expression="#Trim(action)#">

    <!--- ─── Dashboard ──────────────────────────────────────────────── --->
    <cfcase value="get_dashboard">
        <cfhttp url="#host_api_url#/admin/erp-extract/stats" method="GET" timeout="30">
            <cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
        </cfhttp>
        <cfset stats_data = DeserializeJSON(cfhttp.FileContent)>

        <cfhttp url="#host_api_url#/admin/erp-extract/status" method="GET" timeout="10">
            <cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
        </cfhttp>
        <cfset status_data = DeserializeJSON(cfhttp.FileContent)>

        <cfhttp url="#host_api_url#/admin/erp-extract/history" method="GET" timeout="10">
            <cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
        </cfhttp>
        <cfset history_data = DeserializeJSON(cfhttp.FileContent)>

        <cfhttp url="#host_api_url#/admin/erp-extract/alerts" method="GET" timeout="10">
            <cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
        </cfhttp>
        <cfset alerts_data = DeserializeJSON(cfhttp.FileContent)>

        <cfoutput>
        <div class="erp-extract-dashboard">
            <style>
                .erp-extract-dashboard { font-family: Arial, sans-serif; padding: 20px; }
                .erp-extract-dashboard h2 { color: ##333; border-bottom: 2px solid ##4CAF50; padding-bottom: 10px; }
                .erp-extract-dashboard .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
                .erp-extract-dashboard .stat-card { background: ##f5f5f5; border-radius: 8px; padding: 15px; text-align: center; }
                .erp-extract-dashboard .stat-card h3 { margin: 0 0 5px 0; font-size: 14px; color: ##666; }
                .erp-extract-dashboard .stat-card .value { font-size: 24px; font-weight: bold; color: ##333; }
                .erp-extract-dashboard .stat-card .value.ok { color: ##4CAF50; }
                .erp-extract-dashboard .stat-card .value.warn { color: ##FF9800; }
                .erp-extract-dashboard .stat-card .value.err { color: ##f44336; }
                .erp-extract-dashboard table { width: 100%; border-collapse: collapse; margin: 15px 0; }
                .erp-extract-dashboard th, .erp-extract-dashboard td { padding: 10px; text-align: left; border-bottom: 1px solid ##ddd; }
                .erp-extract-dashboard th { background: ##4CAF50; color: white; }
                .erp-extract-dashboard tr:hover { background: ##f1f1f1; }
                .erp-extract-dashboard .btn { padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; }
                .erp-extract-dashboard .btn-primary { background: ##4CAF50; color: white; }
                .erp-extract-dashboard .btn-danger { background: ##f44336; color: white; }
                .erp-extract-dashboard .btn-warning { background: ##FF9800; color: white; }
                .erp-extract-dashboard .badge { padding: 3px 8px; border-radius: 12px; font-size: 12px; }
                .erp-extract-dashboard .badge-ok { background: ##e8f5e9; color: ##2e7d32; }
                .erp-extract-dashboard .badge-warn { background: ##fff3e0; color: ##e65100; }
                .erp-extract-dashboard .badge-err { background: ##ffebee; color: ##c62828; }
                .erp-extract-dashboard .log-entry { padding: 5px 0; border-bottom: 1px solid ##eee; font-size: 13px; }
            </style>

            <h2>🔄 ERP Extract Manager</h2>

            <!--- Global Status --->
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>Total Scopes</h3>
                    <div class="value">#StructFindValue(stats_data, "scope").count#</div>
                </div>
                <div class="stat-card">
                    <h3>Total Rows</h3>
                    <div class="value">#NumberFormat(StructFindValue(stats_data, "total_rows").value, "_,_")#</div>
                </div>
                <div class="stat-card">
                    <h3>Last Run</h3>
                    <div class="value #status_data.is_running ? 'warn' : 'ok'#">
                        #status_data.is_running ? 'Running...' : (status_data.last_run_at ? Left(status_data.last_run_at, 16) : 'Never')#
                    </div>
                </div>
                <div class="stat-card">
                    <h3>Status</h3>
                    <div class="value #status_data.is_running ? 'warn' : 'ok'#">
                        #status_data.is_running ? '⏳ Running' : '✅ Idle'#
                    </div>
                </div>
            </div>

            <!--- Scope Table --->
            <h3>📋 Scope List</h3>
            <table>
                <tr>
                    <th>##</th>
                    <th>Scope Name</th>
                    <th>Masterfn</th>
                    <th>Companyfn</th>
                    <th>Status</th>
                    <th>Total Rows</th>
                    <th>Schedule</th>
                    <th>Action</th>
                </tr>
                <cfloop index="i" from="1" to="#ArrayLen(stats_data)#">
                    <cfset s = stats_data[i]>
                    <tr>
                        <td>#i#</td>
                        <td><b>#s.scope#</b></td>
                        <td>#s.masterfn#</td>
                        <td>#s.companyfn#</td>
                        <td>
                            <cfif s.total_rows gt 0>
                                <span class="badge badge-ok">✅ OK</span>
                            <cfelse>
                                <span class="badge badge-warn">⚠️ Empty</span>
                            </cfif>
                        </td>
                        <td>#NumberFormat(s.total_rows, "_,_")#</td>
                        <td>Weekly (Sun 00:00)</td>
                        <td>
                            <button class="btn btn-primary" onclick="runScopeExtract('#s.masterfn#', '#s.companyfn#')">▶ Run</button>
                        </td>
                    </tr>
                </cfloop>
            </table>

            <div style="margin: 15px 0;">
                <button class="btn btn-primary" onclick="runAllExtract()">▶ Run All Scopes</button>
                <button class="btn btn-warning" onclick="refreshDashboard()">🔄 Refresh</button>
            </div>

            <!--- Recent Logs --->
            <h3>📝 Recent Logs</h3>
            <div id="extract-logs">
                <cfloop index="i" from="1" to="#Min(10, ArrayLen(history_data))#">
                    <cfset h = history_data[i]>
                    <div class="log-entry">
                        <cfif h.status eq "success">
                            <span style="color:##4CAF50">✅</span>
                        <cfelseif h.status eq "running">
                            <span style="color:##FF9800">⏳</span>
                        <cfelse>
                            <span style="color:##f44336">❌</span>
                        </cfif>
                        <b>#h.scope#</b> — #h.status# (#h.duration_sec#s, #h.rows_extracted# rows)
                        <span style="color:##999; float:right">#h.timestamp#</span>
                    </div>
                </cfloop>
            </div>
        </div>

        <script>
        function runAllExtract() {
            if (!confirm('Run extract for ALL scopes?')) return;
            var btn = event.target; btn.disabled = true; btn.textContent = '⏳ Running...';
            fetch('#host_api_url#/admin/erp-extract/run', {
                method: 'POST',
                headers: { 'X-API-Key': '#ai_api_key#', 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode: 'incremental' })
            }).then(r => r.json()).then(d => {
                alert('Extract started: ' + (d.message || 'OK'));
                setTimeout(refreshDashboard, 2000);
            }).catch(e => { alert('Error: ' + e); }).finally(() => { btn.disabled = false; btn.textContent = '▶ Run All Scopes'; });
        }
        function runScopeExtract(mfn, cfn) {
            if (!confirm('Run extract for ' + mfn + '?')) return;
            fetch('#host_api_url#/admin/erp-extract/run', {
                method: 'POST',
                headers: { 'X-API-Key': '#ai_api_key#', 'Content-Type': 'application/json' },
                body: JSON.stringify({ masterfn: mfn, companyfn: cfn, mode: 'incremental' })
            }).then(r => r.json()).then(d => {
                alert('Extract started: ' + (d.message || 'OK'));
                setTimeout(refreshDashboard, 2000);
            }).catch(e => alert('Error: ' + e));
        }
        function refreshDashboard() {
            fetch('/contentadmin/ai_erp_extract_admin.cfm?action=get_dashboard')
                .then(r => r.text()).then(html => {
                    document.querySelector('.erp-extract-dashboard').outerHTML = html;
                });
        }
        </script>
        </cfoutput>
    </cfcase>

    <!--- ─── Get Scopes ─────────────────────────────────────────────── --->
    <cfcase value="get_scopes">
        <cfhttp url="#host_api_url#/admin/erp-extract/scopes" method="GET" timeout="15">
            <cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
        </cfhttp>
        <cfoutput>#cfhttp.FileContent#</cfoutput>
    </cfcase>

    <!--- ─── Add Scope ──────────────────────────────────────────────── --->
    <cfcase value="add_scope">
        <cfparam name="form.masterfn" default="">
        <cfparam name="form.companyfn" default="">
        <cfparam name="form.name" default="">
        <cfhttp url="#host_api_url#/admin/erp-extract/scopes" method="POST" timeout="15">
            <cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
            <cfhttpparam type="header" name="Content-Type" value="application/json">
            <cfhttpparam type="body" value='{"masterfn":"#JSStringFormat(form.masterfn)#","companyfn":"#JSStringFormat(form.companyfn)#","name":"#JSStringFormat(form.name)#"}'>
        </cfhttp>
        <cfoutput>#cfhttp.FileContent#</cfoutput>
    </cfcase>

    <!--- ─── Update Scope ───────────────────────────────────────────── --->
    <cfcase value="update_scope">
        <cfparam name="form.scope_id" default="">
        <cfparam name="form.masterfn" default="">
        <cfparam name="form.companyfn" default="">
        <cfparam name="form.name" default="">
        <cfhttp url="#host_api_url#/admin/erp-extract/scopes/#URLEncodedFormat(form.scope_id)#" method="PUT" timeout="15">
            <cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
            <cfhttpparam type="header" name="Content-Type" value="application/json">
            <cfhttpparam type="body" value='{"masterfn":"#JSStringFormat(form.masterfn)#","companyfn":"#JSStringFormat(form.companyfn)#","name":"#JSStringFormat(form.name)#"}'>
        </cfhttp>
        <cfoutput>#cfhttp.FileContent#</cfoutput>
    </cfcase>

    <!--- ─── Delete Scope ───────────────────────────────────────────── --->
    <cfcase value="delete_scope">
        <cfparam name="form.scope_id" default="">
        <cfhttp url="#host_api_url#/admin/erp-extract/scopes/#URLEncodedFormat(form.scope_id)#" method="DELETE" timeout="15">
            <cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
        </cfhttp>
        <cfoutput>#cfhttp.FileContent#</cfoutput>
    </cfcase>

    <!--- ─── Run Extract ────────────────────────────────────────────── --->
    <cfcase value="run_extract">
        <cfparam name="form.masterfn" default="">
        <cfparam name="form.companyfn" default="">
        <cfparam name="form.mode" default="incremental">
        <cfset body = '{"mode":"#form.mode#"}'>
        <cfif form.masterfn neq "">
            <cfset body = '{"masterfn":"#JSStringFormat(form.masterfn)#","companyfn":"#JSStringFormat(form.companyfn)#","mode":"#form.mode#"}'>
        </cfif>
        <cfhttp url="#host_api_url#/admin/erp-extract/run" method="POST" timeout="30">
            <cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
            <cfhttpparam type="header" name="Content-Type" value="application/json">
            <cfhttpparam type="body" value="#body#">
        </cfhttp>
        <cfoutput>#cfhttp.FileContent#</cfoutput>
    </cfcase>

    <!--- ─── Run Scope Extract ──────────────────────────────────────── --->
    <cfcase value="run_scope_extract">
        <cfparam name="form.scope_id" default="">
        <cfhttp url="#host_api_url#/admin/erp-extract/run" method="POST" timeout="30">
            <cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
            <cfhttpparam type="header" name="Content-Type" value="application/json">
            <cfhttpparam type="body" value='{"scope_id":"#JSStringFormat(form.scope_id)#","mode":"incremental"}'>
        </cfhttp>
        <cfoutput>#cfhttp.FileContent#</cfoutput>
    </cfcase>

    <!--- ─── Get Logs ───────────────────────────────────────────────── --->
    <cfcase value="get_logs">
        <cfhttp url="#host_api_url#/admin/erp-extract/history" method="GET" timeout="15">
            <cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
        </cfhttp>
        <cfoutput>#cfhttp.FileContent#</cfoutput>
    </cfcase>

    <!--- ─── Update Config ──────────────────────────────────────────── --->
    <cfcase value="update_config">
        <cfparam name="form.enabled" default="true">
        <cfparam name="form.interval" default="weekly">
        <cfparam name="form.time" default="00:00">
        <cfparam name="form.day" default="sunday">
        <cfhttp url="#host_api_url#/admin/erp-extract/config" method="PUT" timeout="15">
            <cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
            <cfhttpparam type="header" name="Content-Type" value="application/json">
            <cfhttpparam type="body" value='{"enabled":#form.enabled#,"interval":"#form.interval#","time":"#form.time#","day":"#form.day#"}'>
        </cfhttp>
        <cfoutput>#cfhttp.FileContent#</cfoutput>
    </cfcase>

    <!--- ─── Default: Show Dashboard ────────────────────────────────── --->
    <cfdefaultcase>
        <cfhttp url="#host_api_url#/admin/erp-extract/stats" method="GET" timeout="30">
            <cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
        </cfhttp>
        <cfset stats_data = DeserializeJSON(cfhttp.FileContent)>

        <cfhttp url="#host_api_url#/admin/erp-extract/status" method="GET" timeout="10">
            <cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
        </cfhttp>
        <cfset status_data = DeserializeJSON(cfhttp.FileContent)>

        <cfoutput>
        <div class="erp-extract-dashboard">
            <style>
                .erp-extract-dashboard { font-family: Arial, sans-serif; padding: 20px; }
                .erp-extract-dashboard h2 { color: ##333; border-bottom: 2px solid ##4CAF50; padding-bottom: 10px; }
                .erp-extract-dashboard .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
                .erp-extract-dashboard .stat-card { background: ##f5f5f5; border-radius: 8px; padding: 15px; text-align: center; }
                .erp-extract-dashboard .stat-card h3 { margin: 0 0 5px 0; font-size: 14px; color: ##666; }
                .erp-extract-dashboard .stat-card .value { font-size: 24px; font-weight: bold; color: ##333; }
                .erp-extract-dashboard .stat-card .value.ok { color: ##4CAF50; }
                .erp-extract-dashboard .stat-card .value.warn { color: ##FF9800; }
                .erp-extract-dashboard .stat-card .value.err { color: ##f44336; }
                .erp-extract-dashboard table { width: 100%; border-collapse: collapse; margin: 15px 0; }
                .erp-extract-dashboard th, .erp-extract-dashboard td { padding: 10px; text-align: left; border-bottom: 1px solid ##ddd; }
                .erp-extract-dashboard th { background: ##4CAF50; color: white; }
                .erp-extract-dashboard tr:hover { background: ##f1f1f1; }
                .erp-extract-dashboard .btn { padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; }
                .erp-extract-dashboard .btn-primary { background: ##4CAF50; color: white; }
                .erp-extract-dashboard .btn-danger { background: ##f44336; color: white; }
                .erp-extract-dashboard .btn-warning { background: ##FF9800; color: white; }
                .erp-extract-dashboard .badge { padding: 3px 8px; border-radius: 12px; font-size: 12px; }
                .erp-extract-dashboard .badge-ok { background: ##e8f5e9; color: ##2e7d32; }
                .erp-extract-dashboard .badge-warn { background: ##fff3e0; color: ##e65100; }
                .erp-extract-dashboard .badge-err { background: ##ffebee; color: ##c62828; }
            </style>

            <h2>🔄 ERP Extract Manager</h2>

            <div class="stats-grid">
                <div class="stat-card">
                    <h3>Total Scopes</h3>
                    <div class="value">#ArrayLen(stats_data)#</div>
                </div>
                <div class="stat-card">
                    <h3>Total Rows</h3>
                    <div class="value">
                        <cfset total = 0>
                        <cfloop index="i" from="1" to="#ArrayLen(stats_data)#">
                            <cfset total = total + stats_data[i].total_rows>
                        </cfloop>
                        #NumberFormat(total, "_,_")#
                    </div>
                </div>
                <div class="stat-card">
                    <h3>Last Run</h3>
                    <div class="value #status_data.is_running ? 'warn' : 'ok'#">
                        #status_data.is_running ? 'Running...' : (status_data.last_run_at ? Left(status_data.last_run_at, 16) : 'Never')#
                    </div>
                </div>
                <div class="stat-card">
                    <h3>Status</h3>
                    <div class="value #status_data.is_running ? 'warn' : 'ok'#">
                        #status_data.is_running ? '⏳ Running' : '✅ Idle'#
                    </div>
                </div>
            </div>

            <h3>📋 Scope List</h3>
            <table>
                <tr>
                    <th>##</th>
                    <th>Scope Name</th>
                    <th>Masterfn</th>
                    <th>Companyfn</th>
                    <th>Status</th>
                    <th>Total Rows</th>
                    <th>Action</th>
                </tr>
                <cfloop index="i" from="1" to="#ArrayLen(stats_data)#">
                    <cfset s = stats_data[i]>
                    <tr>
                        <td>#i#</td>
                        <td><b>#s.scope#</b></td>
                        <td>#s.masterfn#</td>
                        <td>#s.companyfn#</td>
                        <td>
                            <cfif s.total_rows gt 0>
                                <span class="badge badge-ok">✅ OK</span>
                            <cfelse>
                                <span class="badge badge-warn">⚠️ Empty</span>
                            </cfif>
                        </td>
                        <td>#NumberFormat(s.total_rows, "_,_")#</td>
                        <td>
                            <button class="btn btn-primary" onclick="runScopeExtract('#s.masterfn#', '#s.companyfn#')">▶ Run</button>
                        </td>
                    </tr>
                </cfloop>
            </table>

            <div style="margin: 15px 0;">
                <button class="btn btn-primary" onclick="runAllExtract()">▶ Run All Scopes</button>
                <button class="btn btn-warning" onclick="refreshDashboard()">🔄 Refresh</button>
            </div>
        </div>

        <script>
        function runAllExtract() {
            if (!confirm('Run extract for ALL scopes?')) return;
            var btn = event.target; btn.disabled = true; btn.textContent = '⏳ Running...';
            fetch('#host_api_url#/admin/erp-extract/run', {
                method: 'POST',
                headers: { 'X-API-Key': '#ai_api_key#', 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode: 'incremental' })
            }).then(r => r.json()).then(d => {
                alert('Extract started: ' + (d.message || 'OK'));
                setTimeout(refreshDashboard, 2000);
            }).catch(e => { alert('Error: ' + e); }).finally(() => { btn.disabled = false; btn.textContent = '▶ Run All Scopes'; });
        }
        function runScopeExtract(mfn, cfn) {
            if (!confirm('Run extract for ' + mfn + '?')) return;
            fetch('#host_api_url#/admin/erp-extract/run', {
                method: 'POST',
                headers: { 'X-API-Key': '#ai_api_key#', 'Content-Type': 'application/json' },
                body: JSON.stringify({ masterfn: mfn, companyfn: cfn, mode: 'incremental' })
            }).then(r => r.json()).then(d => {
                alert('Extract started: ' + (d.message || 'OK'));
                setTimeout(refreshDashboard, 2000);
            }).catch(e => alert('Error: ' + e));
        }
        function refreshDashboard() {
            fetch('/contentadmin/ai_erp_extract_admin.cfm?action=get_dashboard')
                .then(r => r.text()).then(html => {
                    document.querySelector('.erp-extract-dashboard').outerHTML = html;
                });
        }
        </script>
        </cfoutput>
    </cfdefaultcase>

</cfswitch>
