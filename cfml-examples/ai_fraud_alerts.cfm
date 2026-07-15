<!--- Fraud Detection alert workspace for the ERP AI assistant. --->
<cfparam name="cookie.cookuserloginid" default="user_001">
<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="utf-8">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<title>Fraud Detection - Globe3 ERP AI</title>
	<link href="../../folder_style_j/font-awesome.min.css" rel="stylesheet">
	<style>
		* { box-sizing: border-box; }
		body { margin: 0; background: #eaeff7; color: #14325f; font-family: "Century Gothic", Arial, sans-serif; }
		.shell { min-height: 100vh; display: grid; grid-template-rows: auto auto 1fr; }
		header { padding: 18px 24px; background: #fff; border-bottom: 1px solid #d8e1f1; display: flex; align-items: center; gap: 14px; }
		header .icon { width: 42px; height: 42px; display: grid; place-items: center; color: #fff; background: #d83b35; border-radius: 8px; font-size: 22px; }
		h1 { margin: 0; font-size: 22px; letter-spacing: .08em; }
		header p { margin: 4px 0 0; color: #667b9b; font-size: 13px; }
		.toolbar { padding: 14px; background: #f8fbff; display: flex; gap: 10px; flex-wrap: wrap; align-items: end; }
		label { display: grid; gap: 5px; color: #506985; font-size: 11px; font-weight: 700; letter-spacing: .04em; text-transform: uppercase; }
		select, input { min-width: 138px; height: 34px; border: 1px solid #b9c8de; border-radius: 6px; background: #fff; color: #14325f; padding: 0 9px; font: inherit; font-size: 13px; }
		button { height: 34px; border: 0; border-radius: 6px; background: #0a65b6; color: #fff; padding: 0 14px; font-weight: 700; letter-spacing: .04em; cursor: pointer; }
		button.secondary { background: #fff; color: #0a65b6; border: 1px solid #b9c8de; }
		button.small { height: 28px; font-size: 11px; padding: 0 9px; }
		main { padding: 14px 24px 28px; overflow: auto; }
		.compact-status { display:grid; grid-template-columns: repeat(5, minmax(120px, 1fr)); gap:10px; margin-bottom:14px; }
		.compact-pill { background:#fff; border:1px solid #d8e1f1; border-left:4px solid #0a65b6; border-radius:8px; padding:9px 11px; min-height:52px; }
		.compact-pill b { display:block; font-size:19px; color:#0a2c61; line-height:1; }
		.compact-pill span { display:block; margin-top:5px; color:#667b9b; font-size:10px; text-transform:uppercase; letter-spacing:.06em; }
		.compact-pill.high { border-left-color:#d83b35; }
		.compact-pill.medium { border-left-color:#f2a900; }
		.compact-pill.low { border-left-color:#1f8f4d; }
		.section { background:#fff; border:1px solid #d8e1f1; border-radius:8px; margin-bottom:14px; overflow:hidden; }
		.section-title { height:38px; display:flex; align-items:center; justify-content:space-between; gap:10px; padding:0 12px; color:#14325f; background:#f8fbff; border-bottom:1px solid #d8e1f1; cursor:pointer; font-size:13px; font-weight:700; letter-spacing:.06em; text-transform:uppercase; }
		.section-title .left { display:flex; align-items:center; gap:8px; }
		.section-title .right { display:flex; align-items:center; gap:10px; color:#667b9b; font-size:11px; font-weight:400; letter-spacing:.03em; }
		.section-title i { color:#0a65b6; transition:transform .15s ease; }
		.section.collapsed .section-title i { transform:rotate(-90deg); }
		.section-body { padding:14px; }
		.section.collapsed .section-body { display:none; }
		.summary { display: grid; grid-template-columns: repeat(5, minmax(120px, 1fr)); gap: 10px; margin-bottom: 14px; }
		.metric { background: #fff; border: 1px solid #d8e1f1; border-radius: 8px; padding: 12px; }
		.metric b { display: block; font-size: 24px; }
		.metric span { color: #667b9b; font-size: 12px; text-transform: uppercase; letter-spacing: .05em; }
		.notice { padding: 10px 12px; border: 1px solid #f2c36b; background: #fff7e2; color: #7a5600; border-radius: 8px; margin-bottom: 14px; font-size: 13px; }
		.notice.ok { border-color: #9dccad; background: #eef9f1; color: #205c35; }
		.rule-panel { background: #fff; border: 1px solid #d8e1f1; border-radius: 8px; padding: 14px; margin-bottom: 14px; }
		.rule-panel h3 { margin: 0 0 10px; font-size: 14px; letter-spacing: .04em; text-transform: uppercase; }
		.rule-grid { display: grid; grid-template-columns: repeat(4, minmax(180px, 1fr)); gap: 10px; }
		.rule-item { border: 1px solid #d8e1f1; border-radius: 6px; padding: 10px; background: #f8fbff; }
		.rule-item b { display: block; margin-bottom: 4px; color: #14325f; font-size: 12px; }
		.rule-item span { color: #526b88; font-size: 12px; line-height: 1.35; }
		.audit-detail { background:#fff; border:1px solid #b9c8de; border-left:5px solid #0a65b6; border-radius:8px; padding:14px; margin-bottom:12px; display:none; }
		.audit-detail h2 { margin:0 0 8px; font-size:16px; letter-spacing:.06em; }
		.audit-grid { display:grid; grid-template-columns: repeat(3, minmax(180px, 1fr)); gap:8px; }
		.audit-field { background:#f8fbff; border:1px solid #d8e1f1; border-radius:6px; padding:8px; font-size:12px; }
		.audit-field b { display:block; color:#506985; text-transform:uppercase; font-size:10px; letter-spacing:.06em; margin-bottom:3px; }
		.audit-json { margin-top:10px; white-space:pre-wrap; font-family:Consolas, monospace; font-size:11px; background:#0d1b2a; color:#d8f3ff; padding:10px; border-radius:6px; max-height:260px; overflow:auto; }
		body.detail-mode .compact-status,
		body.detail-mode #secMonthDashboard,
		body.detail-mode #secFilters,
		body.detail-mode #secSummary,
		body.detail-mode #secScheduler,
		body.detail-mode #secRules,
		body.detail-mode #secAlerts { display:none !important; }
		body.detail-mode main { padding:14px; }
		body.detail-mode header { padding:12px 16px; }
		body.detail-mode header .icon { width:34px; height:34px; font-size:18px; }
		body.detail-mode h1 { font-size:18px; }
		body.detail-mode header p { display:none; }
		body.detail-mode .audit-detail { display:block; margin-bottom:0; }
		body.detail-mode .audit-grid { grid-template-columns: repeat(4, minmax(160px, 1fr)); }
		body.detail-mode .ai-insight { display:block; }
		.ai-insight { margin-top:12px; border:1px solid #cfe0f5; border-left:5px solid #7c3aed; background:#fbfaff; border-radius:8px; padding:12px; }
		.ai-insight h3 { margin:0 0 8px; color:#3b216f; font-size:14px; letter-spacing:.06em; text-transform:uppercase; }
		.ai-pill { display:inline-block; padding:2px 8px; border-radius:999px; background:#efe8ff; color:#3b216f; font-size:11px; font-weight:700; margin-left:6px; }
		.ai-cols { display:grid; grid-template-columns: repeat(2, minmax(220px, 1fr)); gap:10px; margin-top:8px; }
		.ai-box { background:#fff; border:1px solid #d8e1f1; border-radius:6px; padding:9px; font-size:12px; line-height:1.45; }
		.ai-box b { display:block; margin-bottom:4px; color:#506985; text-transform:uppercase; font-size:10px; letter-spacing:.06em; }
		.baseline-grid { display:grid; grid-template-columns: repeat(2, minmax(240px, 1fr)); gap:10px; margin-top:12px; }
		.baseline-card { border:1px solid #cfe0f5; border-radius:7px; background:#fbfdff; padding:10px; font-size:12px; }
		.baseline-card h4 { margin:0 0 6px; color:#14325f; font-size:12px; text-transform:uppercase; letter-spacing:.05em; }
		.baseline-card .nums { color:#506985; line-height:1.5; }
		.baseline-card .apply-ai { margin-top:6px; color:#3b216f; background:#f3eeff; border-radius:5px; padding:6px; }
		.module-dashboard { display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap:10px; }
		.module-card { border:1px solid #d8e1f1; border-left:4px solid #0a65b6; background:#fff; border-radius:8px; padding:11px; }
		.module-card.alerty { border-left-color:#d83b35; background:#fffdfd; }
		.module-card h3 { margin:0 0 7px; font-size:13px; color:#0a2c61; letter-spacing:.08em; text-transform:uppercase; }
		.module-stats { display:grid; grid-template-columns: repeat(2, 1fr); gap:6px; font-size:11px; color:#506985; }
		.module-stats b { display:block; color:#14325f; font-size:16px; }
		.module-actions { margin-top:9px; display:flex; gap:7px; flex-wrap:wrap; }
		.module-actions button { height:27px; font-size:10px; padding:0 8px; }
		.ai-guide { margin-top:10px; padding:9px; border-radius:6px; background:#f3eeff; color:#3b216f; font-size:12px; line-height:1.45; }
		.list { display: grid; gap: 10px; }
		.pagination { display:flex; justify-content:flex-end; align-items:center; gap:10px; margin-top:12px; color:#506985; font-size:12px; letter-spacing:.04em; text-transform:uppercase; }
		.pagination button { height:30px; padding:0 10px; font-size:11px; }
		.pagination button:disabled { opacity:.45; cursor:not-allowed; }
		.card { background: #fff; border: 1px solid #d8e1f1; border-left: 5px solid #f2c36b; border-radius: 8px; padding: 13px; }
		.card.critical { border-left-color: #b42318; }
		.card.high { border-left-color: #d83b35; }
		.card.medium { border-left-color: #f2a900; }
		.card.low { border-left-color: #1f8f4d; }
		.card-head { display: flex; justify-content: space-between; gap: 12px; align-items: start; }
		.card h2 { margin: 0; font-size: 15px; }
		.card p { margin: 7px 0 0; color: #526b88; font-size: 13px; line-height: 1.45; }
		.compare-line { margin-top:8px; padding:8px; border-radius:6px; background:#f8fbff; border:1px solid #d8e1f1; color:#14325f; font-size:12px; line-height:1.45; }
		.compare-line b { color:#0a2c61; }
		.badge { padding: 3px 8px; border-radius: 999px; background: #eaf1fb; font-size: 11px; font-weight: 700; text-transform: uppercase; white-space: nowrap; }
		.badge.status-new { background: #eaf1fb; color: #0a65b6; }
		.badge.status-investigating { background: #fff7e2; color: #7a5600; }
		.badge.status-confirmed_issue { background: #fde8e8; color: #b42318; }
		.badge.status-false_positive { background: #e8f5e9; color: #1f8f4d; }
		.badge.status-resolved { background: #e8f5e9; color: #1f8f4d; }
		.review-controls { margin-top: 10px; display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
		.review-controls select { min-width: 120px; height: 30px; font-size: 12px; }
		.review-controls input { min-width: 160px; height: 30px; font-size: 12px; }
		.review-controls button { height: 30px; font-size: 12px; padding: 0 10px; }
		.empty, .error { background: #fff; border: 1px dashed #b9c8de; border-radius: 8px; padding: 28px; text-align: center; color: #667b9b; }
		.error { border-color: #d83b35; color: #9b1c16; display: none; }
		.loading { display: none; color: #506985; padding: 14px 0; }
		.scan-selector { display: flex; gap: 8px; align-items: center; }
		.scan-selector select { min-width: 200px; }
		/* F2: Extended disposition fields */
		.ext-review { margin-top: 8px; display: flex; gap: 6px; flex-wrap: wrap; }
		.ext-review select, .ext-review input { height: 28px; font-size: 11px; min-width: 100px; }
		.ext-review label { font-size: 10px; display: flex; flex-direction: column; gap: 2px; }
		/* F3: Demo-friendly */
		.demo-badge { display: inline-block; background: #1f8f4d; color: #fff; font-size: 10px; padding: 2px 7px; border-radius: 999px; margin-left: 6px; }
		.demo-ready { background: #e8f5e9; border: 1px solid #1f8f4d; }
		.demo-not-ready { background: #fde8e8; border: 1px solid #b42318; }
		.demo-panel { background: #fff; border: 1px solid #d8e1f1; border-radius: 8px; padding: 14px; margin-bottom: 14px; display: none; }
		.demo-panel h3 { margin: 0 0 8px; font-size: 14px; }
		.demo-panel .row { display: flex; gap: 10px; flex-wrap: wrap; }
		.demo-panel .stat { flex: 1; min-width: 100px; padding: 8px; background: #f8fbff; border-radius: 6px; }
		.demo-panel .stat b { display: block; font-size: 18px; }
		.demo-panel .stat span { font-size: 11px; color: #667b9b; }
		@media (max-width: 1180px) { .rule-grid { grid-template-columns: repeat(2, minmax(180px, 1fr)); } }
		@media (max-width: 820px) { .summary, .rule-grid { grid-template-columns: repeat(2, 1fr); } header, .toolbar, main { padding-left: 14px; padding-right: 14px; } }
	</style>
</head>
<body>
	<div class="shell">
		<header>
			<div class="icon"><i class="fa fa-exclamation-circle" aria-hidden="true"></i></div>
			<div>
				<h1>Fraud Detection</h1>
				<p>Alerts generated automatically by the daily fraud scheduler.</p>
			</div>
		</header>
		<main>
			<div class="loading" id="loading">Loading scheduled fraud alerts...</div>
			<div class="error" id="error"></div>
			<div id="results" style="display:none">
				<div class="audit-detail" id="auditDetail"></div>
				<div class="compact-status">
					<div class="compact-pill"><b id="monthTransactions">0</b><span>This month tx</span></div>
					<div class="compact-pill"><b id="compactTotal">0</b><span>Total alerts</span></div>
					<div class="compact-pill high"><b id="compactHigh">0</b><span>High</span></div>
					<div class="compact-pill medium"><b id="compactMedium">0</b><span>Medium</span></div>
					<div class="compact-pill"><b id="compactPage">1/1</b><span>Current page</span></div>
				</div>
				<div class="section" id="secMonthDashboard">
					<div class="section-title" onclick="toggleSection('secMonthDashboard')">
						<span class="left"><i class="fa fa-dashboard"></i> This month ERP dashboard by fromtrans</span>
						<span class="right"><span id="monthDashboardStatus">Loading</span><i class="fa fa-angle-down"></i></span>
					</div>
					<div class="section-body">
						<div class="module-dashboard" id="moduleDashboard"></div>
						<div class="ai-guide" id="dashboardAIGuide">Use this dashboard to pick the ERP module/fromtrans first, then drill down into alerts and AI evidence.</div>
					</div>
				</div>
				<div class="section collapsed" id="secFilters">
					<div class="section-title" onclick="toggleSection('secFilters')">
						<span class="left"><i class="fa fa-filter"></i> Filters</span>
						<span class="right"><span id="filterSummary">Active scope</span><i class="fa fa-angle-down"></i></span>
					</div>
					<div class="section-body">
						<section class="toolbar">
							<label>Severity
								<select id="severity">
									<option value="">All</option>
									<option value="CRITICAL">Critical</option>
									<option value="HIGH">High</option>
									<option value="MEDIUM">Medium</option>
									<option value="LOW">Low</option>
								</select>
							</label>
							<label>Status
								<select id="statusFilter">
									<option value="">Active</option>
									<option value="NEW">New</option>
									<option value="ACKNOWLEDGED">Acknowledged</option>
									<option value="RESOLVED">Resolved</option>
									<option value="HIDDEN">Hidden</option>
								</select>
							</label>
							<label>Date From
								<input id="dateFrom" type="date">
							</label>
							<label>Date To
								<input id="dateTo" type="date">
							</label>
							<label>Search<input id="search" type="search" placeholder="Rule, title or description"></label>
							<button type="button" onclick="resetAndLoadAlerts();return false;">Refresh Alerts</button>
						</section>
					</div>
				</div>
				<div class="section collapsed" id="secSummary">
					<div class="section-title" onclick="toggleSection('secSummary')">
						<span class="left"><i class="fa fa-bar-chart"></i> Summary details</span>
						<span class="right"><span id="summaryTitleCount">0 alerts</span><i class="fa fa-angle-down"></i></span>
					</div>
					<div class="section-body">
						<div class="summary">
							<div class="metric"><b id="total">0</b><span>Total</span></div>
							<div class="metric"><b id="critical">0</b><span>Critical</span></div>
							<div class="metric"><b id="high">0</b><span>High</span></div>
							<div class="metric"><b id="medium">0</b><span>Medium</span></div>
							<div class="metric"><b id="low">0</b><span>Low</span></div>
						</div>
					</div>
				</div>
				<div class="section collapsed" id="secScheduler">
					<div class="section-title" onclick="toggleSection('secScheduler')">
						<span class="left"><i class="fa fa-clock-o"></i> Scheduler run</span>
						<span class="right"><span id="schedulerTitleStatus">-</span><i class="fa fa-angle-down"></i></span>
					</div>
					<div class="section-body">
						<div class="notice" id="scanNotice"><b>Last scheduler run:</b> <span id="lastRun">-</span> &middot;
							<b>Status:</b> <span id="runStatus">-</span> &middot;
							<b>Transactions checked:</b> <span id="checkedTransactions">0</span> &middot;
							<b>Users baselined:</b> <span id="checkedUsers">0</span> &middot;
							<b>Indicators detected:</b> <span id="checkedDetected">0</span><br>
							<b>Scope:</b> <span id="scanScope">current login company</span>. Indicators require human review and are not fraud verdicts.
						</div>
					</div>
				</div>
				<div class="section collapsed" id="secRules">
					<div class="section-title" onclick="toggleSection('secRules')">
						<span class="left"><i class="fa fa-magic"></i> Alert rules & AI baseline</span>
						<span class="right"><span id="rulesTitleStatus">Click to view</span><i class="fa fa-angle-down"></i></span>
					</div>
					<div class="section-body">
						<div class="rule-grid">
							<div class="rule-item"><b>High transaction amount</b><span>Amount above the user's normal 30-day average.</span></div>
							<div class="rule-item"><b>Frequency spike</b><span>Unusually many transactions by the same user in one day.</span></div>
							<div class="rule-item"><b>High refund count</b><span>Refund activity above the user's baseline.</span></div>
							<div class="rule-item"><b>Abnormal discount</b><span>Discount value above expected user behavior.</span></div>
							<div class="rule-item"><b>Too many voids</b><span>Void count above normal baseline.</span></div>
							<div class="rule-item"><b>Outside working hours</b><span>Transaction time outside the user's normal activity window.</span></div>
							<div class="rule-item"><b>Repeated invoice modification</b><span>Invoice changed repeatedly beyond configured threshold.</span></div>
							<div class="rule-item"><b>Backdated transaction</b><span>Transaction date is far earlier than creation date.</span></div>
						</div>
						<div id="baselinePanel" class="baseline-grid"></div>
					</div>
				</div>
				<div class="section" id="secAlerts">
					<div class="section-title" onclick="toggleSection('secAlerts')">
						<span class="left"><i class="fa fa-list"></i> Detected alert records</span>
						<span class="right"><span id="recordsTitleStatus">Loading</span><i class="fa fa-angle-down"></i></span>
					</div>
					<div class="section-body">
						<div class="list" id="list"></div>
						<div class="pagination" id="pagination"></div>
					</div>
				</div>
			</div>
			<div class="empty" id="empty">Loading alerts generated by the scheduler...</div>
		</main>
	</div>
	<script>
		var fraudPage = 0;
		var fraudLimit = 10;
		var fraudTotal = 0;
		var detailMode = !!queryParam('alert_id');
		if (detailMode) document.body.classList.add('detail-mode');
		function toggleSection(id) {
			var el = document.getElementById(id);
			if (el) {
				el.classList.toggle('collapsed');
				if (id === 'secRules' && !el.classList.contains('collapsed') && !window.aiFraudBaselineLoaded) {
					window.aiFraudBaselineLoaded = true;
					loadBaselines();
				}
			}
		}
		function setText(id, value) {
			var el = document.getElementById(id);
			if (el) el.textContent = value;
		}
		function updateFilterSummary() {
			var parts = [];
			var sev = document.getElementById('severity').value;
			var status = document.getElementById('statusFilter').value || 'Active';
			var q = document.getElementById('search').value;
			if (sev) parts.push(sev);
			parts.push(status);
			if (q) parts.push('Search: ' + q);
			setText('filterSummary', parts.join(' | '));
		}
		function formBody(data) {
			var params = new URLSearchParams();
			Object.keys(data).forEach(function(k) {
				if (data[k] !== undefined && data[k] !== null && data[k] !== '') params.append(k, data[k]);
			});
			return params;
		}
		function esc(v) {
			return String(v == null ? '' : v).replace(/[&<>"']/g, function(c) {
				return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
			});
		}
		function queryParam(name) {
			var match = new RegExp('[?&]' + name + '=([^&]*)').exec(window.location.search);
			return match ? decodeURIComponent(match[1].replace(/\+/g, ' ')) : '';
		}
		function fmt(v) {
			if (!v) return '-';
			return String(v).replace('T', ' ').replace(/\.\d+$/, '');
		}
		function fmtNum(v, decimals) {
			var n = Number(v);
			if (!isFinite(n)) return '-';
			return n.toLocaleString(undefined, {minimumFractionDigits: decimals || 0, maximumFractionDigits: decimals || 2});
		}
		function auditMasterdataUrl(item) {
			var meta = item.metadata || {};
			var tx = String(meta.source_transaction_id || item.transaction_id || '');
			var parts = tx.split(':');
			var uniq = parts.length ? parts[parts.length - 1] : tx;
			var fromtrans = item.fromtrans || meta.fromtrans || meta.document_type || (parts.length >= 2 ? parts[parts.length - 2] : '');
			if (!uniq || !fromtrans) return '';
			return 'audit_masterdata.cfm?frommode=edit&fromsegm=' + encodeURIComponent(fromtrans) +
				'&fromsubsegm=&fromtype=full&fromtrans=' + encodeURIComponent(fromtrans) +
				'&fromlevel=cfn&audviewtype=rec&uniquenum_pri=' + encodeURIComponent(uniq);
		}
		function alertComparison(item) {
			var meta = item.metadata || {};
			var rule = String(item.rule_name || item.rule || '').toUpperCase();
			var sev = String(item.severity || '').toUpperCase();
			function baselineText() {
				var scope = meta.baseline_scope_label || meta.baseline_scope || 'selected ERP scope';
				var samples = meta.baseline_samples ? ('; samples <b>' + fmtNum(meta.baseline_samples, 0) + '</b>') : '';
				var period = (meta.baseline_period_start || meta.baseline_period_end)
					? ('; period <b>' + esc(fmt(meta.baseline_period_start).substring(0, 10)) + ' to ' + esc(fmt(meta.baseline_period_end).substring(0, 10)) + '</b>')
					: '';
				return '<b>' + esc(scope) + '</b>' + samples + period;
			}
			if (rule === 'HIGH_TRANSACTION_AMOUNT') {
				return 'This document amount is <b>SGD ' + fmtNum(meta.amount, 2) + '</b>. For this user and document type, most past transactions were at or below <b>SGD ' + fmtNum(meta.baseline_p95_amount || meta.baseline_amount || meta.baseline_average_amount, 2) + '</b>. This is about <b>' + fmtNum(meta.ratio, 1) + 'x higher</b>, so it should be reviewed.';
			}
			if (rule === 'TRANSACTION_FREQUENCY_SPIKE') {
				return 'This user created <b>' + fmtNum(meta.daily_count, 0) + '</b> transactions in one day. Their usual daily level for this scope is about <b>' + fmtNum(meta.baseline_daily_average, 2) + '</b>. This unusual burst should be checked.';
			}
			if (rule === 'HIGH_REFUND_COUNT') {
				return 'Refund count <b>' + fmtNum(meta.refund_count || meta.value, 0) + '</b> is compared with count thresholds LOW/MEDIUM/HIGH = <b>' + fmtNum(meta.threshold_low, 0) + ' / ' + fmtNum(meta.threshold_medium, 0) + ' / ' + fmtNum(meta.threshold_high, 0) + '</b>. Baseline average <b>' + fmtNum(meta.baseline, 2) + '</b> from ' + baselineText() + '. Result: <b>' + esc(sev) + '</b>.';
			}
			if (rule === 'TOO_MANY_VOID_TRANSACTIONS') {
				return 'Void count <b>' + fmtNum(meta.void_count || meta.value, 0) + '</b> is compared with count thresholds LOW/MEDIUM/HIGH = <b>' + fmtNum(meta.threshold_low, 0) + ' / ' + fmtNum(meta.threshold_medium, 0) + ' / ' + fmtNum(meta.threshold_high, 0) + '</b>. Baseline average <b>' + fmtNum(meta.baseline, 2) + '</b> from ' + baselineText() + '. Result: <b>' + esc(sev) + '</b>.';
			}
			if (rule === 'ABNORMAL_DISCOUNT') {
				return 'Discount <b>' + fmtNum(meta.discount || meta.value, 2) + '</b> is compared with discount baseline <b>' + fmtNum(meta.baseline, 2) + '</b> from ' + baselineText() + '. Ratio <b>' + fmtNum(meta.ratio, 2) + 'x</b>; thresholds LOW/MEDIUM/HIGH = <b>' + fmtNum(meta.threshold_low, 0) + 'x / ' + fmtNum(meta.threshold_medium, 0) + 'x / ' + fmtNum(meta.threshold_high, 0) + 'x</b>. Result: <b>' + esc(sev) + '</b>.';
			}
			if (rule === 'REPEATED_INVOICE_MODIFICATION') {
				return 'This document was modified <b>' + fmtNum(meta.invoice_modifications, 0) + '</b> time(s). Repeated changes can be valid, but the audit trail should confirm what changed and who approved it.';
			}
			if (rule === 'BACKDATED_TRANSACTION') {
				return 'The transaction date is <b>' + fmtNum(meta.lag_days, 0) + '</b> day(s) earlier than the creation date. Please confirm whether backdating is expected for this document.';
			}
			if (rule === 'LOGIN_OUTSIDE_NORMAL_HOURS') {
				return 'Transaction time <b>' + esc(meta.activity_time || '-') + '</b> is compared with this user normal activity window <b>' + esc(meta.normal_start || '-') + ' - ' + esc(meta.normal_end || '-') + '</b>. Result: <b>' + esc(sev) + '</b>.';
			}
			return item.description ? esc(item.description) : 'This transaction is unusual compared with historical ERP activity and should be reviewed.';
		}
		function renderAuditDetail(item) {
			var meta = item.metadata || {};
			var el = document.getElementById('auditDetail');
			var mods = Number(meta.invoice_modifications || 0) > 0 ? meta.invoice_modifications : '-';
			var fromtrans = item.fromtrans || meta.fromtrans || meta.document_type || '-';
			var fromtransLabel = item.fromtrans_label || meta.fromtrans_label || fromtrans;
			var moduleFromtrans = (meta.module ? meta.module + ' / ' : '') + (fromtransLabel === fromtrans ? fromtrans : fromtransLabel + ' (' + fromtrans + ')');
			var auditUrl = auditMasterdataUrl(item);
			var auditLink = auditUrl ? '<a href="' + auditUrl + '" target="_blank">Open document audit</a>' : (item.transaction_id ? '<a href="ai_realtime_query_check.cfm?search=' + encodeURIComponent(item.transaction_id) + '" target="_blank">Open transaction lookup</a>' : '-');
			var docText = meta.document_no || item.transaction_id || '-';
			var docHtml = auditUrl ? '<a href="' + auditUrl + '" target="_blank" style="color:#0a65b6;text-decoration:none;font-weight:bold;">' + esc(docText) + '</a>' : esc(docText);
			var ratioLine = '';
			if (meta.ratio) {
				ratioLine = '<div class="audit-field"><b>Deviation</b>' + esc(fmtNum(meta.ratio, 2)) + 'x normal baseline</div>';
			}
			var amountLine = '';
			if (meta.amount) {
				amountLine = '<div class="audit-field"><b>Amount</b>' + esc(fmtNum(meta.amount, 2)) + '</div>';
			}
			var baselineLine = '';
			if (meta.baseline_p95_amount || meta.baseline_amount || meta.baseline_average_amount) {
				baselineLine = '<div class="audit-field"><b>Baseline p95</b>' + esc(fmtNum(meta.baseline_p95_amount || meta.baseline_amount || meta.baseline_average_amount, 2)) + '</div>';
			}
			el.innerHTML =
				'<div class="section-title" style="margin:-14px -14px 12px -14px;border-radius:8px 8px 0 0;" onclick="var b=document.getElementById(\'auditBody\');if(b){b.style.display=(b.style.display===\'none\'?\'block\':\'none\');}">' +
					'<span>' + esc(item.title || item.rule_name || 'Fraud Alert') + '</span>' +
					'<span><i class="fa fa-angle-down"></i> &nbsp; <a href="javascript:void(0)" onclick="event.stopPropagation();document.getElementById(\'auditDetail\').style.display=\'none\';" style="color:#9b1c16;text-decoration:none;">Close</a></span>' +
				'</div>' +
				'<div id="auditBody">' +
				'<div class="audit-grid">' +
					'<div class="audit-field"><b>Document</b>' + docHtml + '</div>' +
					'<div class="audit-field"><b>User</b>' + esc(item.user_id || '-') + '</div>' +
					'<div class="audit-field"><b>Module / Fromtrans</b>' + esc(moduleFromtrans) + '</div>' +
					'<div class="audit-field"><b>Severity</b>' + esc(item.severity || '-') + '</div>' +
					'<div class="audit-field"><b>Transaction date</b>' + esc(fmt(item.event_at)) + '</div>' +
					'<div class="audit-field"><b>Created</b>' + esc(fmt(item.created_at)) + '</div>' +
					amountLine +
					baselineLine +
					ratioLine +
					(Number(meta.invoice_modifications || 0) > 0 ? '<div class="audit-field"><b>Modified count</b>' + esc(mods) + ' time(s)</div>' : '') +
					'<div class="audit-field"><b>Audit link</b>' + auditLink + '</div>' +
				'</div>' +
				'<div class="compare-line"><b>Compared with:</b> ' + alertComparison(item) + '</div>' +
				'<div class="review-controls">' +
					'<button type="button" class="small" onclick="loadAIInsight(' + esc(item.id || 0) + ');return false;">Apply AI / Explain Risk</button>' +
				'</div>' +
				'<div id="aiInsight" class="ai-insight" style="display:none;"></div>' +
				'</div>';
			el.style.display = 'block';
			el.scrollIntoView({behavior:'smooth', block:'start'});
			if (detailMode) loadAIInsight(item.id || 0);
		}
		async function loadAuditDetail(alertId) {
			if (!alertId) return;
			try {
				var data = await proxy('fraud_alert_get_local', {alert_id: alertId});
				if (data.error) throw new Error(data.error + (data.detail ? ': ' + data.detail : ''));
				renderAuditDetail(data);
			} catch (e) {
				showError('Could not load audit detail. ' + e.message);
			}
		}
		function renderAIInsight(data) {
			var el = document.getElementById('aiInsight');
			if (!el) return;
			var rationale = data.business_rationale || data.risk_rationale || [];
			var actions = data.reviewer_checklist || data.suggested_actions || [];
			var questions = data.questions_for_reviewer || [];
			function list(arr) {
				if (!arr || !arr.length) return '-';
				return '<ul style="margin:4px 0 0 18px;padding:0;">' + arr.map(function(v) {
					if (typeof v === 'object') return '';
					return '<li>' + esc(v) + '</li>';
				}).filter(Boolean).join('') + '</ul>';
			}
			el.innerHTML =
				'<h3>AI Explanation <span class="ai-pill">Confidence ' + esc(Math.round((Number(data.confidence || 0) * 100))) + '%</span></h3>' +
				'<div class="ai-box"><b>What this means</b>' + esc(data.user_summary || data.summary || '-') + '</div>' +
				(data.plain_comparison ? '<div class="ai-box" style="margin-top:8px;"><b>Compared with normal activity</b>' + esc(data.plain_comparison) + '</div>' : '') +
				'<div class="ai-cols">' +
					'<div class="ai-box"><b>Why it was flagged</b>' + list(rationale) + '</div>' +
					'<div class="ai-box"><b>What to check next</b>' + list(actions) + '</div>' +
					(questions.length ? '<div class="ai-box"><b>Reviewer questions</b>' + list(questions) + '</div>' : '') +
				'</div>';
			el.style.display = 'block';
		}
		async function loadAIInsight(alertId) {
			if (!alertId) return;
			var el = document.getElementById('aiInsight');
			if (el) {
				el.style.display = 'block';
				el.innerHTML = '<h3>AI Insight</h3><div class="ai-box">AI is analysing this alert...</div>';
			}
			try {
				var data = await proxy('fraud_alert_ai_insight', {alert_id: alertId});
				if (data.error) throw new Error(data.error + (data.detail ? ': ' + data.detail : ''));
				renderAIInsight(data);
			} catch (e) {
				if (el) el.innerHTML = '<h3>AI Insight</h3><div class="ai-box">Could not load AI insight. ' + esc(e.message) + '</div>';
			}
		}
		function renderBaselines(data) {
			var el = document.getElementById('baselinePanel');
			if (!el) return;
			if (!data || data.error) {
				el.innerHTML = '<div class="baseline-card"><h4>AI baseline</h4><div class="nums">Could not load baseline.</div></div>';
				return;
			}
			var cats = data.categories || [];
			el.innerHTML = cats.map(function(c) {
				var nums = [];
				['average','median','p95','max','low_candidates','medium_candidates','high_candidates'].forEach(function(k) {
					if (c[k] !== undefined && c[k] !== null && c[k] !== '') nums.push(k.replace('_',' ') + ': ' + c[k]);
				});
				return '<div class="baseline-card">' +
					'<h4>' + esc(c.label || c.rule) + '</h4>' +
					'<div class="nums">' + esc(nums.join(' | ') || '-') + '</div>' +
					'<div class="nums"><b>Current:</b> ' + esc(c.current_setting || '-') + '</div>' +
					'<div class="nums"><b>Suggested:</b> ' + esc(c.suggested_setting || '-') + '</div>' +
					'<div class="apply-ai"><b>Apply AI:</b> ' + esc(c.apply_ai || '-') + '</div>' +
				'</div>';
			}).join('');
		}
		async function loadBaselines() {
			try {
				var data = await proxy('fraud_baselines', {days: 60});
				renderBaselines(data);
				setText('rulesTitleStatus', ((data && data.categories) ? data.categories.length : 0) + ' AI baseline groups');
			} catch (e) {
				renderBaselines({error:e.message});
				setText('rulesTitleStatus', 'Baseline unavailable');
			}
		}
		function num(v) {
			var n = Number(v || 0);
			return n.toLocaleString ? n.toLocaleString() : String(n);
		}
		function money(v) {
			var n = Number(v || 0);
			return n.toLocaleString ? n.toLocaleString(undefined, {maximumFractionDigits: 2}) : String(n);
		}
		function focusFromtrans(fromtrans) {
			document.getElementById('search').value = fromtrans || '';
			updateFilterSummary();
			var rec = document.getElementById('secAlerts');
			if (rec) rec.classList.remove('collapsed');
			resetAndLoadAlerts();
		}
		function openDashboardAI(fromtrans) {
			focusFromtrans(fromtrans);
			var rules = document.getElementById('secRules');
			if (rules) rules.classList.remove('collapsed');
			var guide = document.getElementById('dashboardAIGuide');
			if (guide) guide.innerHTML = '<b>AI workflow for ' + esc(fromtrans || 'this module') + ':</b> filtered records below. Open one alert, then click <b>AI Insight</b> to explain evidence, suggested action, and threshold tuning for that ERP transaction type.';
		}
		function renderDashboard(data) {
			var el = document.getElementById('moduleDashboard');
			if (!el) return;
			if (!data || data.error) {
				el.innerHTML = '<div class="empty">Could not load monthly ERP dashboard.</div>';
				setText('monthDashboardStatus', 'Unavailable');
				return;
			}
			var rows = data.fromtrans || [];
			setText('monthTransactions', num(data.total_transactions || 0));
			setText('monthDashboardStatus', num(data.total_transactions || 0) + ' tx | ' + num(data.total_alerts || 0) + ' alerts');
			var guide = document.getElementById('dashboardAIGuide');
			if (guide && data.ai_entrypoints) guide.innerHTML = data.ai_entrypoints.map(function(x){ return '&bull; ' + esc(x); }).join('<br>');
			if (!rows.length) {
				el.innerHTML = '<div class="empty">No transactions found for this month.</div>';
				return;
			}
			el.innerHTML = rows.map(function(r) {
				var fromtrans = r.fromtrans || 'UNKNOWN';
				var fromtransLabel = r.fromtrans_label || fromtrans;
				var fromtransArg = JSON.stringify(fromtrans).replace(/'/g, '&#39;');
				var alerts = Number(r.alerts || 0);
				var alertRate = Number(r.transactions || 0) > 0 ? ((alerts / Number(r.transactions)) * 100).toFixed(2) + '%' : '-';
				return '<div class="module-card ' + (alerts > 0 ? 'alerty' : '') + '">' +
					'<h3>' + esc(fromtransLabel) + '</h3>' +
					'<div style="font-size:10px;color:#5b7294;text-transform:uppercase;letter-spacing:.6px;margin-top:-4px;margin-bottom:6px;">' + esc(fromtrans) + '</div>' +
					'<div class="module-stats">' +
						'<div><b>' + num(r.transactions) + '</b>Transactions</div>' +
						'<div><b>' + num(alerts) + '</b>Alerts</div>' +
						'<div><b>' + num(r.users) + '</b>Users</div>' +
						'<div><b>' + alertRate + '</b>Alert rate</div>' +
						'<div><b>' + money(r.total_amount) + '</b>Total amount</div>' +
						'<div><b>H ' + num(r.high_alerts) + ' / M ' + num(r.medium_alerts) + ' / L ' + num(r.low_alerts) + '</b>Severity</div>' +
					'</div>' +
					'<div class="module-actions">' +
						'<button type="button" class="secondary" onclick=\'focusFromtrans(' + fromtransArg + ');return false;\'>View records</button>' +
						'<button type="button" onclick=\'openDashboardAI(' + fromtransArg + ');return false;\'>Use AI here</button>' +
					'</div>' +
				'</div>';
			}).join('');
		}
		async function loadDashboard() {
			try {
				var data = await proxy('fraud_dashboard_local', {});
				renderDashboard(data);
			} catch (e) {
				renderDashboard({error:e.message});
			}
		}
		function setBusy(on) {
			document.getElementById('loading').style.display = on ? 'block' : 'none';
			document.getElementById('error').style.display = 'none';
		}
		function showError(msg) {
			var el = document.getElementById('error');
			el.textContent = msg;
			el.style.display = 'block';
		}
		function parseProxyJson(text) {
			var raw = String(text || '').trim();
			try { return JSON.parse(raw); } catch (ignore) {}

			for (var i = 0; i < raw.length; i++) {
				var open = raw.charAt(i);
				if (open !== '{' && open !== '[') continue;
				var close = open === '{' ? '}' : ']';
				var depth = 0;
				var inString = false;
				var quote = '';
				var escaped = false;
				for (var j = i; j < raw.length; j++) {
					var ch = raw.charAt(j);
					if (inString) {
						if (escaped) { escaped = false; continue; }
						if (ch === '\\') { escaped = true; continue; }
						if (ch === quote) { inString = false; quote = ''; }
						continue;
					}
					if (ch === '"' || ch === "'") { inString = true; quote = ch; continue; }
					if (ch === open) depth++;
					if (ch === close) depth--;
					if (depth === 0) {
						try { return JSON.parse(raw.slice(i, j + 1)); } catch (ignore2) { break; }
					}
				}
			}
			throw new Error(raw.substring(0, 220));
		}
		async function proxy(action, data) {
			var resp = await fetch('inc_ajax_ai_assistant.cfm?action=' + encodeURIComponent(action), {
				method: 'POST',
				headers: {'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'},
				body: formBody(data || {})
			});
			var text = await resp.text();
			return parseProxyJson(text);
		}
		async function runScan() {
			return loadStoredAlerts();
		}
		async function loadStoredAlerts(page) {
			if (page !== undefined && page !== null) fraudPage = Math.max(0, Number(page) || 0);
			var keepShell = document.getElementById('results').style.display === 'block';
			setBusy(true);
			document.getElementById('empty').style.display = 'none';
			if (keepShell) {
				document.getElementById('list').innerHTML = '<div class="empty">Loading page ' + (fraudPage + 1) + '...</div>';
			} else {
				document.getElementById('results').style.display = 'none';
			}
			try {
				var statusFilter = document.getElementById('statusFilter').value;
				var params = {
					limit: fraudLimit,
					offset: fraudPage * fraudLimit,
					severity: document.getElementById('severity').value,
					date_from: document.getElementById('dateFrom').value,
					date_to: document.getElementById('dateTo').value,
					search: document.getElementById('search').value
				};
				if (statusFilter) params.status = statusFilter;
				var responses = await Promise.all([proxy('fraud_alert_list_local', params), proxy('fraud_alert_summary_local', {})]);
				var data = responses[0], summaryResponse = responses[1] || {}, schedulerSummary = summaryResponse.scheduler || {}, runResult = schedulerSummary.last_result || {};
				if (summaryResponse.error) throw new Error(summaryResponse.error + (summaryResponse.detail ? ': ' + summaryResponse.detail : ''));
				document.getElementById('lastRun').textContent = schedulerSummary.last_run_at || 'Not run yet';
				document.getElementById('runStatus').textContent = schedulerSummary.last_run_status || '-';
				document.getElementById('checkedTransactions').textContent = runResult.transactions || 0;
				document.getElementById('checkedUsers').textContent = runResult.users || 0;
				document.getElementById('checkedDetected').textContent = runResult.detected || 0;
				document.getElementById('scanScope').textContent = runResult.masterfn && runResult.companyfn
					? runResult.masterfn + ' / ' + runResult.companyfn
					: 'current login company';
				document.getElementById('scanNotice').className = schedulerSummary.last_run_status === 'success' ? 'notice ok' : 'notice';
				setText('schedulerTitleStatus', (schedulerSummary.last_run_status || '-') + ' | checked ' + (runResult.transactions || 0));
				var items = data.items || data.alerts || [];
				fraudTotal = Number(data.total || items.length || 0);
				renderItems(items, {total_findings: fraudTotal, severity_counts: summaryResponse.severity_counts || {}});
			} catch (e) {
				showError('Could not load stored alerts. ' + e.message);
			} finally {
				setBusy(false);
			}
		}
		async function showReviewHistory(alertId) {
			try {
				var data = await proxy('alert_review_history', { alert_id: alertId, limit: 10 });
				var items = data.items || [];
				if (!items.length) {
					alert('No review history for this alert.');
					return;
				}
				var html = 'Review History:\n' + items.map(function(h) {
					return '  ' + h.created_at + ' | ' + h.previous_status + ' -> ' + h.new_status + ' | by ' + h.reviewer + (h.note ? ': ' + h.note : '');
				}).join('\n');
				alert(html);
			} catch (e) {
				showError('Could not load review history. ' + e.message);
			}
		}
		async function reviewAlert(alertId, action) {
			try {
				if (action === 'hide' && !confirm('Hide this alert permanently? The scheduler will not recreate the same event.')) return;
				await proxy('fraud_alert_action', {alert_id: alertId, alert_action: action});
				loadStoredAlerts();
			} catch (e) {
				showError('Review failed. ' + e.message);
			}
		}
		function renderScan(data) {
			var summary = data.summary || {};
			renderItems(data.findings || data.items || [], summary);
		}
		function renderItems(items, summary) {
			document.getElementById('results').style.display = 'block';
			document.getElementById('total').textContent = summary.total_findings || items.length || 0;
			var sevCounts = summary.severity_counts || {};
			var criticalCount = sevCounts.CRITICAL != null ? sevCounts.CRITICAL : items.filter(function(i){return String(i.severity).toUpperCase()==='CRITICAL';}).length;
			var highCount = sevCounts.HIGH != null ? sevCounts.HIGH : items.filter(function(i){return String(i.severity).toUpperCase()==='HIGH';}).length;
			var mediumCount = sevCounts.MEDIUM != null ? sevCounts.MEDIUM : items.filter(function(i){return String(i.severity).toUpperCase()==='MEDIUM';}).length;
			var lowCount = sevCounts.LOW != null ? sevCounts.LOW : items.filter(function(i){return String(i.severity).toUpperCase()==='LOW';}).length;
			document.getElementById('critical').textContent = criticalCount;
			document.getElementById('high').textContent = highCount;
			document.getElementById('medium').textContent = mediumCount;
			document.getElementById('low').textContent = lowCount;
			setText('compactTotal', summary.total_findings || items.length || 0);
			setText('compactHigh', highCount);
			setText('compactMedium', mediumCount);
			setText('compactLow', lowCount);
			setText('summaryTitleCount', (summary.total_findings || items.length || 0) + ' alerts | H ' + highCount + ' / M ' + mediumCount + ' / L ' + lowCount);
			var list = document.getElementById('list');
			if (!items.length) {
				list.innerHTML = '<div class="empty">No alert indicators found for this scope.</div>';
				renderPagination();
				return;
			}
			list.innerHTML = items.map(function(item, idx) {
				var meta = item.metadata || {};
				var severity = (item.severity || item.risk_level || 'medium').toLowerCase();
				var status = (item.status || 'new').toLowerCase();
				var alertId = item.id || item.alert_id || '';
				var statusBadge = status.replace('_', ' ');
				var recordNo = (fraudPage * fraudLimit) + idx + 1;
				var fromtrans = item.fromtrans || meta.fromtrans || meta.document_type || '';
				var fromtransLabel = item.fromtrans_label || meta.fromtrans_label || fromtrans;
				var moduleFromtrans = fromtrans ? (fromtransLabel === fromtrans ? fromtrans : fromtransLabel + ' (' + fromtrans + ')') : '';
				// F2: Show existing disposition if set
				return '<article class="card ' + esc(severity) + '">' +
					'<div class="card-head">' +
						'<h2>' + recordNo + '. ' + (alertId ? '<a href="javascript:void(0)" onclick="loadAuditDetail(' + alertId + ')" style="color:inherit;text-decoration:none;">' : '') + esc(item.title || item.alert_title || 'AI Alert') + (alertId ? '</a>' : '') + '</h2>' +
						'<div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap;">' +
							'<span class="badge">' + esc(severity) + '</span>' +
							(status ? '<span class="badge status-' + esc(status) + '">' + esc(statusBadge) + '</span>' : '') +
						'</div>' +
					'</div>' +
					'<p>' + esc(item.description || item.reason || item.message || '') + '</p>' +
					'<div class="compare-line"><b>Compared with:</b> ' + alertComparison(item) + '</div>' +
					'<p>Transaction: ' + esc(item.transaction_id || '-') +
					' &middot; User: ' + esc(item.user_id || '-') +
					(moduleFromtrans ? ' &middot; Fromtrans: ' + esc(moduleFromtrans) : '') +
					(item.rule_name ? ' &middot; Rule: ' + esc(item.rule_name) : '') +
					(item.risk_score ? ' &middot; Risk: ' + esc(item.risk_score) : '') +
					'</p>' +
					(alertId ? '<div class="review-controls">' +
						'<button type="button" class="small secondary" onclick="loadAuditDetail(' + alertId + ');return false;">View audit</button>' +
						'<button type="button" class="small" onclick="loadAuditDetail(' + alertId + ').then(function(){loadAIInsight(' + alertId + ');});return false;">AI Insight</button>' +
						(status === 'new' ? '<button type="button" class="small" onclick="reviewAlert(' + alertId + ', \'acknowledge\');return false;">Acknowledge</button>' : '') +
						(status !== 'resolved' && status !== 'hidden' ? '<button type="button" class="small" onclick="reviewAlert(' + alertId + ', \'resolve\');return false;">Resolve</button>' : '') +
						(status !== 'hidden' ? '<button type="button" class="small secondary" onclick="reviewAlert(' + alertId + ', \'hide\');return false;">Hide</button>' : '') +
					'</div>' : '') +
				'</article>';
			}).join('');
			renderPagination();
		}
		function renderPagination() {
			var el = document.getElementById('pagination');
			if (!el) return;
			var pages = Math.max(1, Math.ceil(fraudTotal / fraudLimit));
			var prevDisabled = fraudPage <= 0;
			var nextDisabled = fraudPage >= pages - 1;
			var from = fraudTotal ? (fraudPage * fraudLimit + 1) : 0;
			var to = Math.min(fraudTotal, (fraudPage + 1) * fraudLimit);
			setText('compactPage', (fraudPage + 1) + '/' + pages);
			setText('recordsTitleStatus', 'Showing ' + from + '-' + to + ' of ' + fraudTotal);
			el.innerHTML =
				'<span>Showing ' + from + '-' + to + ' of ' + fraudTotal + '</span>' +
				'<button type="button" class="secondary" ' + (prevDisabled ? 'disabled' : '') + ' onclick="event.preventDefault();event.stopPropagation();loadStoredAlerts(' + (fraudPage - 1) + ');return false;">Prev</button>' +
				'<span>Page ' + (fraudPage + 1) + ' / ' + pages + '</span>' +
				'<button type="button" class="secondary" ' + (nextDisabled ? 'disabled' : '') + ' onclick="event.preventDefault();event.stopPropagation();loadStoredAlerts(' + (fraudPage + 1) + ');return false;">Next</button>';
		}
		function resetAndLoadAlerts() {
			fraudPage = 0;
			updateFilterSummary();
			loadStoredAlerts(0);
		}
		document.getElementById('severity').addEventListener('change', resetAndLoadAlerts);
		document.getElementById('statusFilter').addEventListener('change', resetAndLoadAlerts);
		document.getElementById('dateFrom').addEventListener('change', resetAndLoadAlerts);
		document.getElementById('dateTo').addEventListener('change', resetAndLoadAlerts);
		document.getElementById('search').addEventListener('keydown', function(e) {
			if (e.key === 'Enter') resetAndLoadAlerts();
		});
		var directAlertId = queryParam('alert_id');
		if (directAlertId) {
			document.getElementById('results').style.display = 'block';
			document.getElementById('empty').style.display = 'none';
			loadAuditDetail(directAlertId);
		} else {
			loadDashboard();
			loadStoredAlerts();
		}
	</script>
</body>
</html>
