import os

path = r'D:\tnosystems\v50foldersetadmin\v50stringg3new\v50master\contentadmin\ai_erp_extract_admin.cfm'

# Read the current file
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the truncation point
marker = '.erp-extract-dashboard .scope-desc { font-size: 13px; color'
idx = content.find(marker)
if idx < 0:
    print("ERROR: Could not find truncation marker")
    exit(1)

# Keep everything up to the marker
content = content[:idx]

# Append the complete rest of the file
rest = """##666; margin: 5px 0 10px 0; }
                .erp-extract-dashboard .action-bar { margin: 15px 0; display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
                .erp-extract-dashboard .helper-text { font-size: 12px; color: ##666; }
                .erp-extract-dashboard .form-row { display: flex; gap: 10px; align-items: center; margin: 5px 0; flex-wrap: wrap; }
                .erp-extract-dashboard .form-row input, .erp-extract-dashboard .form-row textarea { padding: 6px 10px; border: 1px solid ##ccc; border-radius: 4px; font-size: 13px; }
                .erp-extract-dashboard .form-row input { width: 180px; }
                .erp-extract-dashboard .form-row textarea { width: 300px; height: 40px; }
                .erp-extract-dashboard .tab-bar { display: flex; gap: 0; margin-bottom: 15px; }
                .erp-extract-dashboard .tab-bar .tab { padding: 10px 20px; cursor: pointer; border: 1px solid ##ddd; background: ##f5f5f5; border-radius: 6px 6px 0 0; font-size: 14px; }
                .erp-extract-dashboard .tab-bar .tab.active { background: ##2196F3; color: white; border-color: ##2196F3; }
                .erp-extract-dashboard .tab-bar .tab:not(.active):hover { background: ##e0e0e0; }
                .erp-extract-dashboard .config-form-box { background: ##f9f9f9; padding: 15px; border-radius: 8px; margin: 15px 0; }
                .erp-extract-dashboard .config-form-title { margin: 0 0 10px 0; }
                .erp-extract-dashboard .notes-cell { font-size: 12px; color: ##666; }
            </style>

            <div class="tab-bar">
                <div class="tab" onclick="showDashboardTab()">📊 Dashboard</div>
                <div class="tab active">⚙️ Cài đặt Công ty</div>
            </div>

            <h2>⚙️ Cài đặt Công ty cần Train</h2>
            <p class="scope-desc">
                Quản lý danh sách công ty cần extract dữ liệu. Mỗi công ty có masterfn + companyfn + API key riêng.
                Dữ liệu được lưu trong database để query sau này.
            </p>

            <!--- Form thêm mới --->
            <div class="config-form-box">
                <h4 class="config-form-title">➕ Thêm Công ty mới</h4>
                <div class="form-row">
                    <input type="text" id="cfg_masterfn" placeholder="Masterfn (VD: banleong369878mfn)">
                    <input type="text" id="cfg_companyfn" placeholder="Companyfn (VD: p23091210332792616)">
                    <input type="text" id="cfg_name" placeholder="Tên công ty (VD: Công ty Chính)">
                    <input type="text" id="cfg_api_key" placeholder="API Key (nếu có)">
                </div>
                <div class="form-row">
                    <textarea id="cfg_notes" placeholder="Ghi chú (VD: Công ty có 1,116,605 sales)"></textarea>
                    <button class="btn btn-primary" onclick="addCompanyConfig()">➕ Thêm</button>
                </div>
            </div>

            <!--- Danh sách config --->
            <table>
                <tr>
                    <th>ID</th>
                    <th>Tên Công ty</th>
                    <th>Masterfn</th>
                    <th>Companyfn</th>
                    <th>API Key</th>
                    <th>Trạng thái</th>
                    <th>Ghi chú</th>
                    <th>Thao tác</th>
                </tr>
                <cfloop index="i" from="1" to="#ArrayLen(cfg_list)#">
                    <cfset c = cfg_list[i]>
                    <tr>
                        <td>#c.id#</td>
                        <td><b>#c.company_name#</b></td>
                        <td class="code-cell">#c.masterfn#</td>
                        <td class="code-cell">#c.companyfn#</td>
                        <td class="code-cell">#c.api_key neq '' ? '••••' & Right(c.api_key, 4) : '—'#</td>
                        <td>
                            <cfif c.enabled>
                                <span class="badge badge-ok">✅ Bật</span>
                            <cfelse>
                                <span class="badge badge-err">⛔ Tắt</span>
                            </cfif>
                        </td>
                        <td class="notes-cell">#c.notes#</td>
                        <td>
                            <button class="btn btn-warning" onclick="toggleCompanyConfig(#c.id#, #c.enabled#)" title="Bật/Tắt config này">#c.enabled ? '⛔ Tắt' : '✅ Bật'#</button>
                            <button class="btn btn-danger" onclick="deleteCompanyConfig(#c.id#)" title="Xóa config này">🗑 Xóa</button>
                        </td>
                    </tr>
                </cfloop>
            </table>

            <div class="action-bar">
                <button class="btn btn-info" onclick="showDashboardTab()">📊 Về Dashboard</button>
                <span class="helper-text">(Quay lại màn hình chính)</span>
            </div>
        </div>
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
        <!--- Nếu không có masterfn/companyfn từ form, lấy từ cookie --->
        <cfif form.masterfn eq "">
            <cfset form.masterfn = cookie.cookmfnunique>
        </cfif>
        <cfif form.companyfn eq "">
            <cfset form.companyfn = cookie.cookcfnunique>
        </cfif>
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

    <!--- ─── Default: Redirect to Dashboard ─────────────────────────── --->
    <cfdefaultcase>
        <cftry>
        <cfhttp url="#host_api_url#/admin/erp-extract/dashboard" method="GET" timeout="30">
            <cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
        </cfhttp>
        <cfset dash_raw = DeserializeJSON(cfhttp.FileContent)>
        <cfset dash = dash_raw>
        <cfcatch type="any">
            <cfset dash = {summary={}, companies=[], history=[], alerts=[], ai_insights=[], charts={}}>
        </cfcatch>
        </cftry>

        <cfoutput>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>

        <div class="erp-extract-dashboard">
        <style>
            .erp-extract-dashboard { font-family: 'Segoe UI', system-ui, sans-serif; padding: 20px; background: ##f8f9fa; min-height: 100vh; }
            .erp-extract-dashboard .card { border: none; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); transition: transform .15s, box-shadow .15s; }
            .erp-extract-dashboard .card:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,0.1); }
            .erp-extract-dashboard .stat-icon { width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px; }
            .erp-extract-dashboard .stat-value { font-size: 1.6rem; font-weight: 700; line-height: 1.2; }
            .erp-extract-dashboard .stat-label { font-size: .8rem; color: ##6c757d; margin-top: 2px; }
            .erp-extract-dashboard .table-container { border-radius: 12px; overflow: hidden; }
            .erp-extract-dashboard .table { margin-bottom: 0; }
            .erp-extract-dashboard .table thead th { background: ##f1f3f5; color: ##495057; font-weight: 600; font-size: .8rem; text-transform: uppercase; letter-spacing: .5px; border-bottom: 2px solid ##dee2e6; position: sticky; top: 0; z-index: 2; }
            .erp-extract-dashboard .table tbody tr { transition: background .1s; }
            .erp-extract-dashboard .table tbody tr:hover { background: ##f8f9fa; }
            .erp-extract-dashboard .badge-status { padding: 4px 10px; border-radius: 20px; font-size: .75rem; font-weight: 500; }
            .erp-extract-dashboard .health-bar { height: 6px; border-radius: 3px; background: ##e9ecef; overflow: hidden; }
            .erp-extract-dashboard .health-bar-fill { height: 100%; border-radius: 3px; transition: width .5s; }
            .erp-extract-dashboard .timeline { position: relative; padding-left: 30px; }
            .erp-extract-dashboard .timeline::before { content: ''; position: absolute; left: 12px; top: 0; bottom: 0; width: 2px; background: ##dee2e6; }
            .erp-extract-dashboard .timeline-item { position: relative; margin-bottom: 16px; }
            .erp-extract-dashboard .timeline-dot { position: absolute; left: -22px; top: 4px; width: 12px; height: 12px; border-radius: 50%; border: 2px solid ##fff; }
            .erp-extract-dashboard .timeline-time { font-size: .75rem; color: ##6c757d; }
            .erp-extract-dashboard .insight-card { border-left: 4px solid; border-radius: 8px; }
            .erp-extract-dashboard .expand-row { cursor: pointer; }
            .erp-extract-dashboard .expand-row .expand-icon { transition: transform .2s; }
            .erp-extract-dashboard .expand-row[aria-expanded="true"] .expand-icon { transform: rotate(90deg); }
            .erp-extract-dashboard .detail-row { background: ##f8f9fa; }
            .erp-extract-dashboard .filter-bar { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
            .erp-extract-dashboard .filter-bar select, .erp-extract-dashboard .filter-bar input { font-size: .85rem; border-radius: 8px; border: 1px solid ##dee2e6; padding: 6px 12px; }
            .erp-extract-dashboard .empty-state { text-align: center; padding: 60px 20px; color: ##6c757d; }
            .erp-extract-dashboard .empty-state i { font-size: 4rem; color: ##dee2e6; margin-bottom: 16px; }
            .erp-extract-dashboard .progress-thin { height: 6px; border-radius: 3px; }
            .erp-extract-dashboard .code-cell { font-family: 'SF Mono', 'Consolas', monospace; font-size: .8rem; }
            .erp-extract-dashboard .tab-bar { display: flex; gap: 0; margin-bottom: 20px; }
            .erp-extract-dashboard .tab-bar .tab { padding: 10px 24px; cursor: pointer; border: 1px solid ##dee2e6; background: ##fff; border-radius: 8px 8px 0 0; font-size: 14px; font-weight: 500; }
            .erp-extract-dashboard .tab-bar .tab.active { background: ##0d6efd; color: white; border-color: ##0d6efd; }
            .erp-extract-dashboard .tab-bar .tab:not(.active):hover { background: ##e9ecef; }
            .erp-extract-dashboard .chart-container { height: 200px; }
        </style>

        <div class="tab-bar">
            <div class="tab active">📊 Dashboard</div>
            <div class="tab" onclick="showConfigTab()">⚙️ Cài đặt Công ty</div>
        </div>

        <!--- ─── Summary Cards ─── --->
        <div class="row g-3 mb-4">
            <div class="col-6 col-md-3 col-xl">
                <div class="card p-3 h-100">
                    <div class="d-flex align-items-center gap-3">
                        <div class="stat-icon bg-primary bg-opacity-10 text-primary"><i class="bi bi-building"></i></div>
                        <div>
                            <div class="stat-value">#dash.summary.total_companies#</div>
                            <div class="stat-label">Tổng công ty</div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-6 col-md-3 col-xl">
                <div class="card p-3 h-100">
                    <div class="d-flex align-items-center gap-3">
                        <div class="stat-icon bg-success bg-opacity-10 text-success"><i class="bi bi-check-circle"></i></div>
                        <div>
                            <div class="stat-value">#dash.summary.completed#</div>
                            <div class="stat-label">Hoàn thành</div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-6 col-md-3 col-xl">
                <div class="card p-3 h-100">
                    <div class="d-flex align-items-center gap-3">
                        <div class="stat-icon bg-warning bg-opacity-10 text-warning"><i class="bi bi-arrow-repeat"></i></div>
                        <div>
                            <div class="stat-value">#dash.summary.running#</div>
                            <div class="stat-label">Đang chạy</div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-6 col-md-3 col-xl">
                <div class="card p-3 h-100">
                    <div class="d-flex align-items-center gap-3">
                        <div class="stat-icon bg-danger bg-opacity-10 text-danger"><i class="bi bi-exclamation-triangle"></i></div>
                        <div>
                            <div class="stat-value">#dash.summary.failed#</div>
                            <div class="stat-label">Thất bại</div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-6 col-md-3 col-xl">
                <div class="card p-3 h-100">
                    <div class="d-flex align-items-center gap-3">
                        <div class="stat-icon bg-secondary bg-opacity-10 text-secondary"><i class="bi bi-dash-circle"></i></div>
                        <div>
                            <div class="stat-value">#dash.summary.never_extracted#</div>
                            <div class="stat-label">Chưa extract</div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-6 col-md-3 col-xl">
                <div class="card p-3 h-100">
                    <div class="d-flex align-items-center gap-3">
                        <div class="stat-icon bg-info bg-opacity-10 text-info"><i class="bi bi-database"></i></div>
                        <div>
                            <div class="stat-value">#NumberFormat(dash.summary.total_rows, "_,_")#</div>
                            <div class="stat-label">Tổng dòng</div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-6 col-md-3 col-xl">
                <div class="card p-3 h-100">
                    <div class="d-flex align-items-center gap-3">
                        <div class="stat-icon bg-info bg-opacity-10 text-info"><i class="bi bi-hdd-stack"></i></div>
                        <div>
                            <div class="stat-value">#dash.summary.sqlite_size_mb# MB</div>
                            <div class="stat-label">Dung lượng</div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-6 col-md-3 col-xl">
                <div class="card p-3 h-100">
                    <div class="d-flex align-items-center gap-3">
                        <div class="stat-icon bg-success bg-opacity-10 text-success"><i class="bi bi-robot"></i></div>
                        <div>
                            <div class="stat-value">#dash.summary.ai_ready#</div>
                            <div class="stat-label">AI sẵn sàng</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!--- ─── AI Insights ─── --->
        <cfif ArrayLen(dash.ai_insights) gt 0>
        <div class="card p-3 mb-4">
            <h6 class="fw-bold mb-3"><i class="bi bi-lightbulb text-warning me-2"></i>AI Insights & Recommendations</h6>
            <div class="row g-2">
                <cfloop index="ii" from="1" to="#ArrayLen(dash.ai_insights)#">
                    <cfset ins = dash.ai_insights[ii]>
                    <div class="col-md-6">
                        <div class="insight-card p-2 px-3 d-flex align-items-center gap-2 
                            #ins.severity eq 'high' ? 'border-danger bg-danger bg-opacity-10' : (ins.severity eq 'medium' ? 'border-warning bg-warning bg-opacity-10' : 'border-info bg-info bg-opacity-10')#">
                            <i class="bi #ins.severity eq 'high' ? 'bi-exclamation-circle text-danger' : (ins.severity eq 'medium' ? 'bi-exclamation-diamond text-warning' : 'bi-info-circle text-info')#"></i>
                            <div class="small">
                                <b>#ins.company#</b>: #ins.message#
                                <br><span class="text-muted">→ #ins.recommendation#</span>
                            </div>
                        </div>
                    </div>
                </cfloop>
            </div>
        </div>
        </cfif>

        <!--- ─── Charts Row ─── --->
        <div class="row g-3 mb-4">
            <div class="col-md-4">
                <div class="card p-3">
                    <h6 class="fw-bold mb-2"><i class="bi bi-bar-chart me-2"></i>Extracts / Ngày</h6>
                    <div class="chart-container"><canvas id="chartExtractsPerDay"></canvas></div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card p-3">
                    <h6 class="fw-bold mb-2"><i class="bi bi-pie-chart me-2"></i>Success vs Failed</h6>
                    <div class="chart-container"><canvas id="chartSuccessFailed"></canvas></div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card p-3">
                    <h6 class="fw-bold mb-2"><i class="bi bi-trophy me-2"></i>Top Companies (Rows)</h6>
                    <div class="chart-container"><canvas id="chartTopCompanies"></canvas></div>
                </div>
            </div>
        </div>

        <!--- ─── Filter Bar ─── --->
        <div class="card p-3 mb-3">
            <div class="filter-bar">
                <select id="filterStatus" class="form-select form-select-sm" style="width:auto" onchange="applyFilters()">
                    <option value="">All Status</option>
                    <option value="completed">✅ Completed</option>
                    <option value="running">🟡 Running</option>
                    <option value="failed">🔴 Failed</option>
                    <option value="never">⚪ Never</option>
                    <option value="empty">🔵 Empty</option>
                </select>
                <select id="filterAiStatus" class="form-select form-select-sm" style="width:auto" onchange="applyFilters()">
                    <option value="">All AI Status</option>
                    <option value="ai_ready">🤖 AI Ready</option>
                    <option value="embedding_pending">⏳ Embedding Pending</option>
                    <option value="extracting">🔄 Extracting</option>
                    <option value="failed">❌ Failed</option>
                    <option value="waiting">⏸ Waiting</option>
                </select>
                <input type="text" id="filterSearch" class="form-control form-control-sm" style="width:200px" placeholder="🔍 Search company..." onkeyup="applyFilters()">
                <button class="btn btn-sm btn-outline-primary" onclick="refreshDashboard()"><i class="bi bi-arrow-clockwise"></i> Refresh</button>
                <button class="btn btn-sm btn-outline-success" onclick="runAllExtract()"><i class="bi bi-play-fill"></i> Run All</button>
                <span class="badge bg-light text-dark ms-auto" id="filterCount"></span>
            </div>
        </div>

        <!--- ─── Company Table ─── --->
        <div class="card table-container">
            <div class="table-responsive">
            <table class="table table-hover align-middle mb-0" id="companyTable">
                <thead>
                    <tr>
                        <th style="width:30px"></th>
                        <th>Công ty</th>
                        <th>MasterFN</th>
                        <th>CompanyFN</th>
                        <th>Extract Status</th>
                        <th>AI Status</th>
                        <th>Rows</th>
                        <th>Last Extract</th>
                        <th>Duration</th>
                        <th>Health</th>
                        <th style="width:180px">Actions</th>
                    </tr>
                </thead>
                <tbody>
                <cfif ArrayLen(dash.companies) eq 0>
                    <tr>
                        <td colspan="11">
                            <div class="empty-state">
                                <i class="bi bi-building-slash"></i>
                                <h5>No company configured.</h5>
                                <p class="text-muted">Add a company in the Settings tab to get started.</p>
                                <button class="btn btn-primary" onclick="showConfigTab()"><i class="bi bi-gear"></i> Go to Settings</button>
                            </div>
                        </td>
                    </tr>
                </cfif>
                <cfloop index="ci" from="1" to="#ArrayLen(dash.companies)#">
                    <cfset comp = dash.companies[ci]>
                    <cfset statusBadge = "">
                    <cfset statusIcon = "">
                    <cfif comp.extract_status eq "completed">
                        <cfset statusBadge = "bg-success"><cfset statusIcon = "✅">
                    <cfelseif comp.extract_status eq "running">
                        <cfset statusBadge = "bg-warning text-dark"><cfset statusIcon = "🟡">
                    <cfelseif comp.extract_status eq "failed">
                        <cfset statusBadge = "bg-danger"><cfset statusIcon = "🔴">
                    <cfelseif comp.extract_status eq "empty">
                        <cfset statusBadge = "bg-info"><cfset statusIcon = "🔵">
                    <cfelse>
                        <cfset statusBadge = "bg-secondary"><cfset statusIcon = "⚪">
                    </cfif>
                    <cfset aiBadge = "">
                    <cfset aiIcon = "">
                    <cfif comp.ai_status eq "ai_ready">
                        <cfset aiBadge = "bg-success"><cfset aiIcon = "🤖">
                    <cfelseif comp.ai_status eq "embedding_pending">
                        <cfset aiBadge = "bg-info"><cfset aiIcon = "⏳">
                    <cfelseif comp.ai_status eq "extracting">
                        <cfset aiBadge = "bg-warning text-dark"><cfset aiIcon = "🔄">
                    <cfelseif comp.ai_status eq "failed">
                        <cfset aiBadge = "bg-danger"><cfset aiIcon = "❌">
                    <cfelse>
                        <cfset aiBadge = "bg-secondary"><cfset aiIcon = "⏸">
                    </cfif>
                    <cfset healthColor = "bg-danger">
                    <cfif comp.health_score gte 80><cfset healthColor = "bg-success">
                    <cfelseif comp.health_score gte 60><cfset healthColor = "bg-warning">
                    <cfelseif comp.health_score gte 40><cfset healthColor = "bg-info">
                    </cfif>
                    <tr class="expand-row" data-bs-toggle="collapse" data-bs-target="#detail_#ci#" aria-expanded="false">
                        <td><i class="bi bi-chevron-right expand-icon"></i></td>
                        <td><b>#comp.company_name#</b></td>
                        <td class="code-cell">#comp.masterfn#</td>
                        <td class="code-cell">#comp.companyfn#</td>
                        <td><span class="badge-status #statusBadge#">#statusIcon# #comp.extract_status#</span></td>
                        <td><span class="badge-status #aiBadge#">#aiIcon# #comp.ai_status#</span></td>
                        <td><b>#NumberFormat(comp.total_rows, "_,_")#</b></td>
                        <td class="small text-muted">#comp.last_extract neq "" ? Left(comp.last_extract, 16) : "—"#</td>
                        <td class="small">#comp.last_duration neq "" ? comp.last_duration & "s" : "—"#</td>
                        <td>
                            <div class="health-bar" style="width:60px">
                                <div class="health-bar-fill #healthColor#" style="width:#comp.health_score#%"></div>
                            </div>
                            <small class="text-muted">#comp.health_score#</small>
                        </td>
                        <td>
                            <div class="btn-group btn-group-sm">
                                <button class="btn btn-outline-success" onclick="runScopeExtract('#comp.masterfn#','#comp.companyfn#')" title="Run Extract"><i class="bi bi-play-fill"></i></button>
                                <button class="btn btn-outline-danger" onclick="if(confirm('Delete SQLite for #comp.company_name#?'))deleteCompanyConfig(#comp.id#)" title="Delete SQLite"><i class="bi bi-trash"></i></button>
                                <button class="btn btn-outline-info" onclick="viewCompanyDetail('#comp.masterfn#','#