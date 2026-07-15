<!---@ ###########################################################################################################
Version 5.0.1
File Description:
No	Modified Date	Modified By		Change Log
1.	20260715	Lopper		Creation Of File 
################################################################################################################# @--->
<cfparam name="cookie.cookuserloginid" default="user_001">
<cfset isDemandAdmin = (cookie.cookuserloginid EQ "m8")>
<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="utf-8">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<title>Demand Planning - Globe3 ERP AI</title>
	<link href="../../folder_style_j/font-awesome.min.css" rel="stylesheet">
	<style>
		* { box-sizing: border-box; }
		body { margin: 0; height: 100vh; background: #eaeff7; color: #14325f; font-family: "Century Gothic", Arial, sans-serif; overflow: hidden; }
		.app { height: 100vh; display: grid; grid-template-columns: 320px minmax(0, 1fr); }
		.sidebar { background: #fff; border-right: 1px solid #d8e1f1; display: flex; flex-direction: column; min-width: 0; overflow: auto; }
		.brand { padding: 18px; border-bottom: 1px solid #d8e1f1; display: flex; gap: 12px; align-items: center; }
		.brand .icon { width: 40px; height: 40px; border-radius: 8px; display: grid; place-items: center; background: #0f905d; color: #fff; font-size: 21px; }
		h1 { margin: 0; font-size: 19px; letter-spacing: .07em; }
		.brand p { margin: 4px 0 0; color: #667b9b; font-size: 12px; }
		.settings { padding: 14px; display: grid; gap: 12px; border-bottom: 1px solid #d8e1f1; }
		label { display: grid; gap: 5px; color: #506985; font-size: 11px; font-weight: 700; letter-spacing: .04em; text-transform: uppercase; }
		select, input { width: 100%; height: 34px; border: 1px solid #b9c8de; border-radius: 6px; background: #fff; color: #14325f; padding: 0 9px; font: inherit; font-size: 13px; }
		button { height: 36px; border: 0; border-radius: 6px; background: #0a65b6; color: #fff; padding: 0 14px; font-weight: 700; letter-spacing: .04em; cursor: pointer; }
		button.secondary { background: #fff; color: #0a65b6; border: 1px solid #b9c8de; }
		button.small { height: 28px; font-size: 11px; padding: 0 9px; }
		.notes { padding: 14px; color: #667b9b; font-size: 12px; line-height: 1.5; }
		.admin-settings { margin: 0 14px 14px; padding: 12px; display: none; gap: 10px; border: 1px solid #d8e1f1; border-radius: 8px; background: #f8fbff; }
		.admin-settings.open { display: grid; }
		.admin-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; color: #14325f; font-weight: 700; font-size: 12px; letter-spacing: .05em; text-transform: uppercase; }
		.checkline { display: flex; align-items: center; gap: 8px; color: #506985; font-size: 12px; text-transform: none; letter-spacing: 0; }
		.checkline input { width: 15px; height: 15px; }
		.chat { min-width: 0; min-height: 0; display: grid; grid-template-rows: auto minmax(0, 1fr) auto; background: #f8fbff; }
		.chat-head { padding: 14px 18px; background: #fff; border-bottom: 1px solid #d8e1f1; display: flex; justify-content: space-between; gap: 12px; align-items: center; }
		.chat-head b { letter-spacing: .06em; }
		.head-actions { display: flex; align-items: center; gap: 8px; }
		.command-center { padding: 14px 18px; background: #fff; border-bottom: 1px solid #d8e1f1; display: grid; gap: 10px; }
		.command-title { display: flex; justify-content: space-between; gap: 12px; align-items: end; flex-wrap: wrap; }
		.command-title b { font-size: 14px; letter-spacing: .04em; }
		.command-title span { color: #667b9b; font-size: 12px; }
		.command-grid { display: grid; grid-template-columns: repeat(4, minmax(150px, 1fr)); gap: 10px; }
		.command-card { border: 1px solid #d8e1f1; border-radius: 8px; background: #f8fbff; padding: 11px; min-width: 0; display: grid; gap: 8px; }
		.command-card h2 { margin: 0; font-size: 13px; color: #14325f; letter-spacing: .03em; }
		.command-card p { margin: 0; color: #667b9b; font-size: 11px; line-height: 1.35; }
		.chip-row { display: flex; flex-wrap: wrap; gap: 6px; }
		.prompt-chip { height: 26px; border: 1px solid #b9c8de; border-radius: 999px; background: #fff; color: #0a65b6; padding: 0 9px; font-size: 11px; font-weight: 700; letter-spacing: 0; }
		.prompt-chip.primary { background: #0a65b6; color: #fff; border-color: #0a65b6; }
		.sidebar .command-center { padding: 14px; border-bottom: 1px solid #d8e1f1; }
		.sidebar .command-title { display: grid; gap: 4px; align-items: start; }
		.sidebar .command-title span { font-size: 11px; line-height: 1.35; }
		.sidebar .command-grid { grid-template-columns: 1fr; gap: 8px; }
		.sidebar .command-card { padding: 10px; }
		.sidebar .command-card p { display: none; }
		.messages { min-width: 0; min-height: 0; padding: 14px 18px; overflow: auto; display: flex; flex-direction: column; gap: 10px; border-bottom: 1px solid #d8e1f1; background: #f8fbff; }
		.msg { max-width: 820px; border: 1px solid #d8e1f1; border-radius: 8px; background: #fff; padding: 13px; line-height: 1.45; font-size: 14px; }
		.msg.user { margin-left: auto; background: #eaf1fb; }
		.msg.ai { margin-right: auto; }
		.chat-tools { display: flex; justify-content: space-between; align-items: center; gap: 10px; color: #667b9b; font-size: 12px; padding: 0 2px; }
		.result-workspace { min-width: 0; min-height: 0; overflow: auto; padding: 16px 18px; }
		.result-workspace.empty { display: none; }
		.result-card { width: 100%; max-width: 1480px; border: 1px solid #d8e1f1; border-radius: 8px; background: #fff; padding: 13px; line-height: 1.45; font-size: 14px; }
		.summary { display: grid; grid-template-columns: repeat(4, minmax(110px, 1fr)); gap: 10px; margin: 10px 0; }
		.metric { border: 1px solid #d8e1f1; border-radius: 8px; padding: 10px; background: #fff; }
		.metric b { display: block; font-size: 22px; }
		.metric span { color: #667b9b; font-size: 11px; text-transform: uppercase; }
		.table-shell { width: 100%; max-height: calc(100vh - 390px); min-height: 280px; overflow: auto; border: 1px solid #d8e1f1; border-radius: 8px; background: #fff; }
		table { width: 100%; min-width: 960px; border-collapse: collapse; font-size: 12px; }
		th, td { border-bottom: 1px solid #e4ebf6; padding: 8px 9px; text-align: left; white-space: nowrap; }
		th { position: sticky; top: 0; z-index: 1; background: #f8fbff; color: #506985; text-transform: uppercase; font-size: 10px; letter-spacing: .04em; }
		tr:hover td { background: #f8fbff; }
		tr.expandable { cursor: pointer; }
		tr.expandable:hover td { background: #eaf1fb; }
		tr.detail-row td { background: #f8fbff; padding: 0; }
		tr.detail-row .detail-inner { padding: 10px 14px; border-bottom: 1px solid #e4ebf6; font-size: 12px; color: #506985; display: grid; gap: 4px; }
		.result-meta { display: flex; justify-content: space-between; gap: 10px; align-items: center; color: #667b9b; font-size: 12px; margin: 8px 0 10px; flex-wrap: wrap; }
		.pagination { display: flex; gap: 6px; align-items: center; }
		.pagination button { height: 28px; font-size: 11px; padding: 0 10px; }
		.pagination span { font-size: 12px; color: #506985; }
		.action-btns { display: flex; gap: 4px; flex-wrap: nowrap; }
		.action-btns button { height: 24px; font-size: 10px; padding: 0 7px; }
		.action-btns button.accept { background: #1f8f4d; }
		.action-btns button.adjust { background: #f2a900; }
		.action-btns button.reject { background: #b9c8de; color: #14325f; }
		.action-btns button.done { background: #e4ebf6; color: #667b9b; cursor: default; }
		.adjust-input { width: 60px; height: 24px; font-size: 10px; padding: 0 4px; border: 1px solid #b9c8de; border-radius: 4px; }
		.action-feedback { font-size: 10px; color: #1f8f4d; display: none; margin-left: 4px; }
		.action-feedback.fail { color: #d83b35; }
		/* D1: Forecast selector + recommended rows filter */
		.forecast-selector { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; }
		.forecast-selector select { min-width: 200px; height: 30px; font-size: 12px; }
		.forecast-selector button { height: 30px; font-size: 11px; padding: 0 10px; }
		.filter-badge { display: inline-block; background: #eaf1fb; color: #0a65b6; font-size: 10px; padding: 2px 7px; border-radius: 999px; cursor: pointer; }
		.filter-badge.active { background: #0a65b6; color: #fff; }
		/* D2: Reject reason dropdown */
		.reject-reason { margin-top: 4px; display: flex; gap: 4px; align-items: center; }
		.reject-reason select { height: 24px; font-size: 10px; min-width: 120px; }
		.reject-reason button { height: 24px; font-size: 10px; padding: 0 7px; }
		.saved-action-state { font-size: 10px; color: #667b9b; margin-left: 4px; }
		.composer { padding: 12px 18px; border-top: 1px solid #d8e1f1; background: #fff; display: flex; gap: 10px; }
		.composer input { height: 38px; }
		.error { color: #9b1c16; }
		.empty-state { padding: 28px; text-align: center; color: #667b9b; border: 1px dashed #b9c8de; border-radius: 8px; background: #fff; }
		.empty-state b { display: block; font-size: 16px; margin-bottom: 6px; color: #506985; }
		.empty-actions { margin-top: 14px; display: flex; justify-content: center; flex-wrap: wrap; gap: 8px; }
		.no-data-guide { margin-top: 12px; display: grid; grid-template-columns: repeat(3, minmax(150px, 1fr)); gap: 10px; text-align: left; }
		.no-data-guide div { border: 1px solid #e4ebf6; border-radius: 8px; padding: 10px; background: #f8fbff; }
		.no-data-guide b { margin: 0 0 4px; font-size: 12px; color: #14325f; }
		.no-data-guide span { display: block; color: #667b9b; font-size: 11px; line-height: 1.35; }
		.ai-diagnosis { max-width: 1180px; margin: 10px auto 0; display: grid; gap: 14px; color: #14325f; }
		.ai-diagnosis .diag-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
		.ai-diagnosis h2 { margin: 0; font-size: 18px; letter-spacing: .03em; }
		.ai-diagnosis p { margin: 4px 0 0; color: #667b9b; font-size: 13px; line-height: 1.45; }
		.diag-grid { display: grid; grid-template-columns: repeat(3, minmax(160px, 1fr)); gap: 10px; }
		.diag-item { border-left: 3px solid #0a65b6; background: #fff; padding: 11px; box-shadow: inset 0 0 0 1px #e4ebf6; }
		.diag-item.warn { border-left-color: #f2a900; }
		.diag-item b { display: block; margin-bottom: 4px; font-size: 12px; }
		.diag-item span { display: block; color: #667b9b; font-size: 11px; line-height: 1.35; }
		.readiness-strip { display: grid; grid-template-columns: repeat(5, minmax(100px, 1fr)); gap: 8px; }
		.readiness-pill { background: #fff; border: 1px solid #d8e1f1; border-radius: 8px; padding: 9px; }
		.readiness-pill b { display: block; font-size: 16px; }
		.readiness-pill span { color: #667b9b; font-size: 10px; text-transform: uppercase; }
		.readiness-pill.err { border-color: #f4b4b4; color: #9b1c16; }
		.ai-activity { max-width: 1180px; margin: 10px auto 0; display: grid; gap: 12px; color: #14325f; }
		.ai-activity h2 { margin: 0; font-size: 18px; letter-spacing: .03em; }
		.ai-activity p { margin: 3px 0 0; color: #667b9b; font-size: 13px; }
		.activity-steps { display: grid; grid-template-columns: repeat(5, minmax(120px, 1fr)); gap: 8px; }
		.activity-step { background: #fff; border: 1px solid #d8e1f1; border-radius: 8px; padding: 10px; min-height: 68px; }
		.activity-step b { display: block; font-size: 12px; margin-bottom: 4px; }
		.activity-step span { display: block; color: #667b9b; font-size: 11px; line-height: 1.35; }
		.activity-step.active { border-color: #0a65b6; box-shadow: inset 3px 0 0 #0a65b6; }
		.activity-step.done { border-color: #b8dec9; box-shadow: inset 3px 0 0 #1f8f4d; }
		.activity-step.warn { border-color: #f5d58a; box-shadow: inset 3px 0 0 #f2a900; }
		.activity-step.fail { border-color: #f4b4b4; box-shadow: inset 3px 0 0 #d83b35; }
		.save-feedback { font-size: 11px; color: #0f905d; display: none; }
		.save-feedback.fail { color: #d83b35; }
		@media (max-width: 1180px) { .command-grid { grid-template-columns: repeat(2, minmax(150px, 1fr)); } }
		@media (max-width: 860px) { .app { grid-template-columns: 1fr; } .sidebar { display: none; } .chat { grid-template-rows: auto minmax(0, 1fr) auto; } .summary, .command-grid, .no-data-guide, .diag-grid, .readiness-strip, .activity-steps { grid-template-columns: 1fr; } }
	</style>
</head>
<body>
	<div class="app">
		<aside class="sidebar">
			<div class="brand">
				<div class="icon"><i class="fa fa-line-chart" aria-hidden="true"></i></div>
				<div>
					<h1>Demand Planning</h1>
					<p>Forecast and replenishment chatbox.</p>
				</div>
			</div>
			<div class="settings">
				<label>SKU
					<input id="sku" value="all">
				</label>
				<label>Location
					<input id="location" value="all">
				</label>
				<label>Horizon
					<select id="horizon">
						<option value="30">30 days</option>
						<option value="60">60 days</option>
						<option value="90" selected>90 days</option>
						<option value="180">180 days</option>
					</select>
				</label>
				<button onclick="runForecast()">Generate Forecast</button>
				<button class="secondary" onclick="clearChat()">Clear</button>
				<cfif isDemandAdmin>
					<button class="secondary" onclick="toggleSettings()" title="Demand settings">Settings</button>
				</cfif>
			</div>
			<div class="command-center">
				<div class="command-title">
					<div>
						<b>Question Lanes</b>
						<span>Click a sample question or type in the chatbox.</span>
					</div>
				</div>
				<div class="command-grid">
					<div class="command-card">
						<h2>Forecast Demand</h2>
						<p>Estimate future demand by SKU, location, and planning horizon.</p>
						<div class="chip-row">
							<button class="prompt-chip primary" onclick="usePrompt('forecast all SKU for 90 days')">90 day forecast</button>
							<button class="prompt-chip" onclick="usePrompt('forecast all SKU for 180 days')">180 days</button>
						</div>
					</div>
					<div class="command-card">
						<h2>Find Reorder Risk</h2>
						<p>Show items where forecast, safety stock, and on-hand suggest replenishment.</p>
						<div class="chip-row">
							<button class="prompt-chip primary" onclick="usePrompt('show reorder rows')">Reorder rows</button>
							<button class="prompt-chip" onclick="usePrompt('status')">Current status</button>
						</div>
					</div>
					<div class="command-card">
						<h2>Review Data Quality</h2>
						<p>Find low-confidence rows, missing history, missing stock, or incomplete inputs.</p>
						<div class="chip-row">
							<button class="prompt-chip primary" onclick="usePrompt('show review rows')">Review rows</button>
							<button class="prompt-chip" onclick="usePrompt('help')">What can I ask?</button>
						</div>
					</div>
					<div class="command-card">
						<h2>Buyer Actions</h2>
						<p>Accept, adjust, reject recommendations, then copy a summary for purchasing.</p>
						<div class="chip-row">
							<button class="prompt-chip primary" onclick="usePrompt('copy summary')">Copy summary</button>
							<button class="prompt-chip" onclick="usePrompt('show ok rows')">OK rows</button>
						</div>
					</div>
				</div>
			</div>
			<cfif isDemandAdmin>
				<div class="admin-settings" id="adminSettings">
					<div class="admin-head">
						<span>m8 Settings</span>
						<button class="secondary small" onclick="loadDemandSettings()">Reload</button>
					</div>
					<label>Default Result Limit
						<input id="settingResultLimit" type="number" min="10" max="500" value="100">
					</label>
					<label class="checkline">
						<input id="settingAutoRun" type="checkbox">
						Auto run on open
					</label>
					<button onclick="saveDemandSettings()">Save Settings</button>
					<span class="save-feedback" id="saveFeedback"></span>
				</div>
			</cfif>
			<div class="notes">Settings are scoped by the active ERP login and company cookies through the server-side AI proxy.</div>
		</aside>
		<section class="chat">
			<div class="chat-head">
				<b>Demand Planning Chatbox</b>
				<div class="head-actions">
					<cfif isDemandAdmin>
						<button class="secondary" onclick="toggleSettings()">Settings</button>
					</cfif>
					<button class="secondary" onclick="runForecast()">Run</button>
				</div>
			</div>
			<div class="messages" id="messages">
				<div class="msg ai">Demand Planning chat history appears here. Use the question lanes on the left or type forecast, reorder, review, OK rows, or buyer summary.</div>
			</div>
			<div class="result-workspace empty" id="resultWorkspace"></div>
			<div class="composer">
				<input id="prompt" placeholder="Example: forecast all SKU for 90 days">
				<button onclick="sendPrompt()">Send</button>
			</div>
		</section>
	</div>
	<script>
		var IS_M8 = <cfoutput>#SerializeJSON(isDemandAdmin)#</cfoutput>;
		var demandUiSettings = { result_limit: 100, auto_run: 'n' };
		var _allItems = [];
		var _pageSize = 100;
		var _currentPage = 0;
		var _historyLoaded = false;
		// D1: Forecast selector state
		var _forecasts = [];
		var _currentForecastId = 0;
		// D1: Row filter state
		var _filterMode = 'all'; // 'all', 'reorder', 'review', 'ok'

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
		function addMsg(kind, html, persist, meta) {
			var el = document.createElement('div');
			el.className = 'msg ' + kind;
			el.innerHTML = html;
			document.getElementById('messages').appendChild(el);
			el.scrollIntoView({block: 'end'});
			if (persist !== false) {
				saveChatMessage(kind === 'user' ? 'user' : 'ai', stripHtml(html), meta || {});
			}
			return el;
		}
		function stripHtml(html) {
			var el = document.createElement('div');
			el.innerHTML = html;
			return (el.textContent || el.innerText || '').trim();
		}
		function setResult(html) {
			var el = document.getElementById('resultWorkspace');
			el.innerHTML = html || '';
			if (html) el.classList.remove('empty'); else el.classList.add('empty');
		}
		function hideResult() {
			setResult('');
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
		async function saveChatMessage(role, content, meta) {
			try {
				await proxy('demand_chat_save', {
					role: role,
					content: content,
					meta_json: JSON.stringify(meta || {})
				});
			} catch (e) {
				if (window.console) console.warn('Demand chat save failed', e);
			}
		}
		async function loadChatHistory() {
			try {
				var data = await proxy('demand_chat_history', { limit: 80 });
				var items = data.items || [];
				if (!items.length) return;
				var messages = document.getElementById('messages');
				messages.innerHTML = '';
				items.forEach(function(item) {
					addMsg(item.role === 'user' ? 'user' : 'ai', esc(item.content), false, item.meta || {});
				});
				_historyLoaded = true;
			} catch (e) {
				if (window.console) console.warn('Demand chat history load failed', e);
			}
		}
		function readSettings() {
			return {
				sku_filter: document.getElementById('sku').value || 'all',
				location_filter: document.getElementById('location').value || 'all',
				horizon_days: document.getElementById('horizon').value || 90
			};
		}
		function applySettings(settings) {
			if (!settings) return;
			if (settings.sku_filter) document.getElementById('sku').value = settings.sku_filter;
			if (settings.location_filter) document.getElementById('location').value = settings.location_filter;
			if (settings.horizon_days) document.getElementById('horizon').value = settings.horizon_days;
			demandUiSettings.result_limit = Math.max(10, parseInt(settings.result_limit || demandUiSettings.result_limit, 10) || 100);
			demandUiSettings.auto_run = settings.auto_run || 'n';
			if (IS_M8) {
				document.getElementById('settingResultLimit').value = demandUiSettings.result_limit;
				document.getElementById('settingAutoRun').checked = demandUiSettings.auto_run === 'y';
			}
		}
		function toggleSettings() {
			var panel = document.getElementById('adminSettings');
			if (panel) panel.classList.toggle('open');
		}
		async function loadDemandSettings() {
			if (!IS_M8) return;
			try {
				var data = await proxy('demand_settings_get', {});
				applySettings(data.settings || {});
			} catch (e) {
				addMsg('ai', '<span class="error">Could not load settings. ' + esc(e.message) + '</span>');
			}
		}
		async function saveDemandSettings() {
			if (!IS_M8) return;
			var settings = readSettings();
			settings.result_limit = document.getElementById('settingResultLimit').value || 100;
			settings.auto_run = document.getElementById('settingAutoRun').checked ? 'y' : 'n';
			var fb = document.getElementById('saveFeedback');
			fb.className = 'save-feedback';
			fb.style.display = 'none';
			try {
				var data = await proxy('demand_settings_save', settings);
				applySettings((data && data.settings) || settings);
				fb.textContent = 'Settings saved.';
				fb.style.display = 'inline';
				setTimeout(function(){ fb.style.display = 'none'; }, 3000);
			} catch (e) {
				fb.textContent = 'Save failed: ' + e.message;
				fb.className = 'save-feedback fail';
				fb.style.display = 'inline';
			}
		}
		function normalizePrompt(text) {
			return String(text || '').toLowerCase()
				.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
		}
		function applyPromptScope(prompt) {
			var days = prompt.match(/\b(30|60|90|180)\b/);
			if (days) document.getElementById('horizon').value = days[1];

			var sku = prompt.match(/\bsku\s*[:=]?\s*([a-zA-Z0-9._-]+)/i);
			if (sku && /^(for|day|days|ngay)$/i.test(sku[1] || '')) sku = null;
			if (sku && sku[1] && sku[1].toLowerCase() !== 'all') {
				document.getElementById('sku').value = sku[1];
			}

			var location = prompt.match(/\b(?:location|warehouse|kho|wh)\s*[:=]?\s*([a-zA-Z0-9._-]+)/i);
			if (location && /^(for|day|days|ngay)$/i.test(location[1] || '')) location = null;
			if (location && location[1] && location[1].toLowerCase() !== 'all') {
				document.getElementById('location').value = location[1];
			}

			var n = normalizePrompt(prompt);
			if (/\b(all|tat ca|toan bo)\b/.test(n)) {
				if (!sku) document.getElementById('sku').value = 'all';
				if (!location) document.getElementById('location').value = 'all';
			}
		}
		function isDemandForecastIntent(prompt) {
			var n = normalizePrompt(prompt);
			if (/\b(la gi|what is|explain|giai thich)\b/.test(n) && !/\b(forecast|du bao|reorder|bo sung|replenish)\b/.test(n)) {
				return false;
			}
			return /\b(forecast|du bao|run forecast|generate forecast|lap du bao|chay du bao)\b/.test(n);
		}
		function replyDemandHelp() {
			addMsg('ai',
				'Demand Planning only handles forecasting and replenishment questions. You can type: ' +
				'<b>forecast all SKU for 90 days</b>, <b>forecast SKU 1810-T0032 for 60 days</b>, ' +
				'<b>show reorder rows</b>, <b>show review rows</b>, or <b>copy summary</b>.',
				true,
				{ intent: 'help' }
			);
		}
		function replyDemandIntro() {
			addMsg('ai',
				'Demand Planning helps you ask about SKU demand and replenishment. I can forecast by SKU/location/horizon, find reorder rows, identify review rows caused by missing data, and create a buyer summary. Try: <b>forecast all SKU for 90 days</b>.',
				true,
				{ intent: 'intro' }
			);
		}
		function replyWhatICheck() {
			addMsg('ai',
				'When Demand Planning runs, I check real ERP data through the server proxy: <b>SKU master</b>, <b>current stock</b>, <b>sales history</b>, <b>on-order purchase quantity</b>, and <b>committed demand</b>. Then I calculate moving average demand, service factor, safety stock, reorder point, and recommended quantity. If ERP returns no rows, I explain the missing data instead of inventing results.',
				true,
				{ intent: 'what_checked' }
			);
		}
		function replyNoDataExplanation() {
			addMsg('ai',
				'If the forecast has no rows, check this order: 1) whether SKU and Location filters are too narrow, 2) whether SKU master has rows, 3) whether current stock has rows, 4) whether sales history exists within the horizon, and 5) whether the analytics API is using the correct company scope. You can try <b>forecast all SKU for 180 days</b> or run the live data readiness check.',
				true,
				{ intent: 'no_data_explanation' }
			);
		}
		function replyDemandConcept(topic) {
			var text = 'Reorder rows are items where forecast, safety stock, and on-hand quantity indicate possible replenishment need. Safety stock is a buffer quantity based on demand and service factor. Review rows require user checking because confidence is low or inputs such as sales history or stock are missing.';
			if (topic === 'safety') text = 'Safety stock is a buffer quantity used to reduce stock-out risk. The module calculates it from demand, service factor/Z-score, and lead time. If inputs are missing, the row is marked for review instead of being automatically decided.';
			if (topic === 'reorder') text = 'A reorder row is a SKU/location where recommended quantity is greater than 0 or action=reorder. The user should review evidence before accepting, adjusting, or rejecting because the module does not automatically create PR/PO.';
			addMsg('ai', text, true, { intent: 'concept', topic: topic || 'general' });
		}
		function replyDemandStatus() {
			if (!_allItems.length) {
				addMsg('ai', 'No forecast is currently displayed. Type <b>forecast all SKU for 90 days</b> or click Run.', true, { intent: 'status' });
				return;
			}
			var reorder = getFilteredCount('reorder');
			var review = getFilteredCount('review');
			var ok = getFilteredCount('ok');
			addMsg('ai', 'The current forecast has ' + esc(_allItems.length) + ' SKU rows: ' + esc(reorder) + ' reorder, ' + esc(review) + ' review, and ' + esc(ok) + ' OK.', true, { intent: 'status' });
		}
		function getFilteredCount(mode) {
			var prev = _filterMode;
			_filterMode = mode;
			var count = getFilteredItems().length;
			_filterMode = prev;
			return count;
		}
		function usePrompt(text) {
			var input = document.getElementById('prompt');
			input.value = text;
			sendPrompt();
		}
		async function askDemandAI(prompt) {
			var loading = addMsg('ai', 'I am reading your question, loading the latest forecast, and checking ERP context within Demand Planning...', false, { status: 'thinking' });
			try {
				var data = await proxy('demand_chat_answer', { message: prompt });
				if (loading && loading.parentNode) loading.parentNode.removeChild(loading);
				var answer = esc(data.answer || 'I could not generate a Demand Planning answer.').replace(/\n/g, '<br>');
				addMsg('ai', answer, true, { intent: 'smart_chat', source: data.source || 'unknown' });
			} catch (e) {
				if (loading && loading.parentNode) loading.parentNode.removeChild(loading);
				addMsg('ai', 'I could not answer from Demand Planning context. ' + esc(e.message), true, { intent: 'smart_chat_error' });
			}
		}
		async function sendPrompt() {
			var prompt = document.getElementById('prompt').value.trim();
			if (!prompt) return;
			addMsg('user', esc(prompt), true, { source: 'prompt' });
			document.getElementById('prompt').value = '';
			var n = normalizePrompt(prompt);

			if (/\b(help|huong dan|cach dung|lam gi|what can|how to)\b/.test(n)) {
				replyDemandHelp();
				return;
			}
			if (/^demand\s*\??$/.test(n) || /^demand planning\s*\??$/.test(n) || /\b(demand la gi|demand planning la gi)\b/.test(n)) {
				askDemandAI(prompt);
				return;
			}
			if (/\b(ban kiem tra gi|dang xu ly gi|phia sau|what.*check|what.*doing|behind)\b/.test(n)) {
				askDemandAI(prompt);
				return;
			}
			if (/\b(vi sao.*khong|why.*no|khong co forecast|khong ra data|no data|0 rows)\b/.test(n)) {
				askDemandAI(prompt);
				return;
			}
			if (/\b(safety stock|ton an toan)\b/.test(n)) {
				askDemandAI(prompt);
				return;
			}
			if (/\b(reorder la gi|what is reorder|can mua la gi)\b/.test(n)) {
				askDemandAI(prompt);
				return;
			}
			if (/\b(copy|clipboard|tom tat cho buyer|copy summary)\b/.test(n)) {
				copySummary();
				return;
			}
			if (/\b(status|summary|tong ket|ket qua hien tai|current)\b/.test(n)) {
				replyDemandStatus();
				return;
			}
			if (/\b(reorder|can mua|bo sung)\b/.test(n)) {
				if (!_allItems.length) { replyDemandStatus(); return; }
				setFilter('reorder');
				addMsg('ai', 'Filtering reorder rows.', true, { intent: 'filter', filter: 'reorder' });
				return;
			}
			if (/\b(review|kiem tra|can xem lai)\b/.test(n)) {
				if (!_allItems.length) { replyDemandStatus(); return; }
				setFilter('review');
				addMsg('ai', 'Filtering review rows.', true, { intent: 'filter', filter: 'review' });
				return;
			}
			if (/\b(ok|du hang|sufficient)\b/.test(n)) {
				if (!_allItems.length) { replyDemandStatus(); return; }
				setFilter('ok');
				addMsg('ai', 'Filtering OK rows.', true, { intent: 'filter', filter: 'ok' });
				return;
			}
			if (isDemandForecastIntent(prompt)) {
				applyPromptScope(prompt);
				runForecast({ suppressUserMessage: true, sourcePrompt: prompt });
				return;
			}
			askDemandAI(prompt);
		}
		async function runForecast(options) {
			options = options || {};
			var settings = readSettings();
			var requestText = 'Forecast ' + esc(settings.sku_filter) + ' / ' + esc(settings.location_filter) + ' for ' + esc(settings.horizon_days) + ' days';
			if (!options.suppressUserMessage) {
				addMsg('user', requestText, true, { source: 'run_forecast', settings: settings });
			}
			addMsg('ai', 'I am reading the ERP scope, checking SKU/stock/sales/PO/committed data, calculating demand, and saving the forecast trail...', false, { status: 'loading' });
			hideResult();
			try {
				var data = await proxy('demand_plan', settings);
				var items = data.items || [];
				if (!items.length) {
					hideResult();
					var readiness = await fetchDemandReadiness();
					addMsg('ai', renderNoDataChat(settings, data, readiness), true, {
						status: 'no_rows',
						forecast_id: data.forecast_id || '',
						settings: settings,
						readiness: readiness && readiness.demand ? readiness.demand : {}
					});
					return;
				}
				setResult(renderForecast(data));
				var summary = data.summary || {};
				addMsg('ai', 'Forecast complete. I found ' + esc(summary.total_skus || items.length || 0) + ' SKU rows, including ' + esc(summary.need_reorder || 0) + ' reorder, ' + esc(summary.need_review || 0) + ' review, and ' + esc(summary.sufficient || 0) + ' OK. The result was saved as forecast #' + esc(data.forecast_id || '' ) + '.', true, {
					forecast_id: data.forecast_id,
					summary: summary
				});
			} catch (e) {
				hideResult();
				addMsg('ai', 'Demand forecast failed. ' + esc(e.message), true, { status: 'error' });
			}
		}
		function renderForecastWaiting(settings) {
			return '<div class="empty-state"><b>Forecast is running</b>' +
				'The result table will appear here when ERP rows are returned. Chat will explain what was checked.</div>';
		}
		function renderForecastError(message) {
			return '<div class="empty-state"><b>Forecast failed</b><span class="error">' + esc(message) + '</span></div>';
		}
		function renderForecastActivity(settings, activeStep, errorText) {
			var steps = [
				['intent', 'Understand request', 'Prompt mapped to Demand Planning forecast scope.'],
				['scope', 'ERP scope', 'SKU=' + (settings.sku_filter || 'all') + ', Location=' + (settings.location_filter || 'all') + ', Horizon=' + (settings.horizon_days || 90) + ' days.'],
				['erp', 'Read ERP data', 'Query SKU master, stock, sales history, on-order, committed stock via server proxy.'],
				['calc', 'Calculate demand', 'Moving average demand, service factor, safety stock, reorder quantity.'],
				['save', 'Persist trail', 'Save forecast rows, chat history, and recommendation actions for review.']
			];
			var activeSeen = false;
			var html = '<div class="ai-activity" id="aiActivity">' +
				'<div><h2>' + (errorText ? 'AI activity stopped' : 'AI is working on demand planning') + '</h2>' +
				'<p>' + (errorText ? esc(errorText) : 'Visible processing trail. This shows what the module is checking without exposing private model reasoning.') + '</p></div>' +
				'<div class="activity-steps">';
			steps.forEach(function(step) {
				var cls = 'done';
				if (errorText) {
					cls = step[0] === activeStep ? 'fail' : (activeSeen ? '' : 'done');
					if (step[0] === activeStep) activeSeen = true;
				} else if (step[0] === activeStep) {
					cls = 'active';
					activeSeen = true;
				} else if (activeSeen) {
					cls = '';
				}
				html += '<div class="activity-step ' + cls + '" id="activity-' + step[0] + '">' +
					'<b>' + esc(step[1]) + '</b><span>' + esc(step[2]) + '</span></div>';
			});
			html += '</div></div>';
			return html;
		}
		function updateForecastActivity(activeStep, note) {
			var box = document.getElementById('aiActivity');
			if (!box) return;
			['intent','scope','erp','calc','save'].forEach(function(step) {
				var el = document.getElementById('activity-' + step);
				if (!el) return;
				el.className = 'activity-step';
				if (step === activeStep) el.className = 'activity-step active';
				if ((activeStep === 'erp' && (step === 'intent' || step === 'scope')) ||
					(activeStep === 'calc' && (step === 'intent' || step === 'scope' || step === 'erp')) ||
					(activeStep === 'save' && step !== 'save')) {
					el.className = 'activity-step done';
				}
			});
			var p = box.querySelector('p');
			if (p && note) p.textContent = note;
		}
		function toggleDetail(rowIdx) {
			var detailId = 'detail-' + rowIdx;
			var existing = document.getElementById(detailId);
			if (existing) {
				existing.remove();
				return;
			}
			var item = _allItems[rowIdx];
			if (!item) return;
			var details = {};
			try { details = JSON.parse(item.details_json || '{}'); } catch(e) {}
			var tr = document.createElement('tr');
			tr.id = detailId;
			tr.className = 'detail-row';
			tr.innerHTML = '<td colspan="7"><div class="detail-inner">' +
				'<div><b>SKU:</b> ' + esc(item.sku) + '</div>' +
				'<div><b>Location:</b> ' + esc(item.location) + '</div>' +
				'<div><b>Forecast Qty:</b> ' + esc(item.forecast_qty) + '</div>' +
				'<div><b>On Hand:</b> ' + esc(item.on_hand_qty) + '</div>' +
				'<div><b>Safety Stock:</b> ' + esc(item.safety_stock) + '</div>' +
				'<div><b>Reorder Point:</b> ' + esc(item.reorder_point) + '</div>' +
				'<div><b>Recommended Qty:</b> ' + esc(item.recommended_qty) + '</div>' +
				'<div><b>Confidence:</b> ' + esc(item.confidence) + '</div>' +
				(details.history_window ? '<div><b>History Window:</b> ' + esc(details.history_window) + '</div>' : '') +
				(details.historical_order_count ? '<div><b>Historical Orders:</b> ' + esc(details.historical_order_count) + '</div>' : '') +
				(details.last_order_date ? '<div><b>Last Order:</b> ' + esc(details.last_order_date) + '</div>' : '') +
				(details.stock_value ? '<div><b>Stock Value:</b> ' + esc(details.stock_value) + '</div>' : '') +
				(details.missing_inputs && details.missing_inputs.length ? '<div><b>Missing Inputs:</b> ' + esc(details.missing_inputs.join(', ')) + '</div>' : '') +
				(details.model ? '<div><b>Model:</b> ' + esc(details.model) + '</div>' : '') +
				'</div></td>';
			var refRow = document.querySelector('#forecast-table tbody tr:nth-child(' + (rowIdx + 1 - _currentPage * _pageSize + 1) + ')');
			if (refRow && refRow.parentNode) {
				refRow.parentNode.insertBefore(tr, refRow.nextSibling);
			}
		}
		function renderActionButtons(item, globalIdx) {
			var recId = item.forecast_id + '-' + esc(item.sku) + '-' + esc(item.location);
			var actionState = item._actionState || '';
			if (actionState === 'accepted') {
				return '<div class="action-btns"><button class="done small">Accepted</button></div>';
			}
			if (actionState === 'rejected') {
				return '<div class="action-btns"><button class="done small">Rejected</button></div>';
			}
			if (actionState === 'adjusted') {
				return '<div class="action-btns"><button class="done small">Adjusted</button></div>';
			}
			return '<div class="action-btns" id="ab-' + globalIdx + '">' +
				'<button class="accept small" onclick="event.stopPropagation();doRecAction(' + globalIdx + ',\'accepted\')">Accept</button>' +
				'<button class="adjust small" onclick="event.stopPropagation();showAdjust(' + globalIdx + ')">Adjust</button>' +
				'<button class="reject small" onclick="event.stopPropagation();doRecAction(' + globalIdx + ',\'rejected\')">Reject</button>' +
				'<span class="action-feedback" id="fb-' + globalIdx + '"></span>' +
				'</div>';
		}
		async function doRecAction(globalIdx, action) {
			var item = _allItems[globalIdx];
			if (!item) return;
			var recId = (item.forecast_id || '') + '-' + esc(item.sku) + '-' + esc(item.location);
			var fb = document.getElementById('fb-' + globalIdx);
			if (fb) { fb.style.display = 'none'; }
			try {
				var data = await proxy('recommendation_action', {
					recommendation_id: recId,
					action: action,
					actor: 'user',
					note: '',
					adjusted_qty: 0
				});
				item._actionState = action;
				// Re-render the action cell
				var container = document.getElementById('ab-' + globalIdx);
				if (container) {
					container.innerHTML = '<button class="done small">' + action.charAt(0).toUpperCase() + action.slice(1) + '</button>';
				}
				if (fb) { fb.textContent = action + ' ✓'; fb.className = 'action-feedback'; fb.style.display = 'inline'; setTimeout(function(){ fb.style.display = 'none'; }, 3000); }
			} catch (e) {
				if (fb) { fb.textContent = 'Failed: ' + e.message; fb.className = 'action-feedback fail'; fb.style.display = 'inline'; }
			}
		}
		function showAdjust(globalIdx) {
			var container = document.getElementById('ab-' + globalIdx);
			if (!container) return;
			var item = _allItems[globalIdx];
			if (!item) return;
			container.innerHTML = '<input class="adjust-input" id="adj-' + globalIdx + '" type="number" min="1" value="' + esc(item.recommended_qty || 0) + '" onclick="event.stopPropagation()">' +
				'<button class="accept small" onclick="event.stopPropagation();submitAdjust(' + globalIdx + ')">Save</button>' +
				'<button class="reject small" onclick="event.stopPropagation();cancelAdjust(' + globalIdx + ')">Cancel</button>' +
				'<span class="action-feedback" id="fb-' + globalIdx + '"></span>';
		}
		function cancelAdjust(globalIdx) {
			var item = _allItems[globalIdx];
			if (!item) return;
			var container = document.getElementById('ab-' + globalIdx);
			if (container) container.outerHTML = renderActionButtons(item, globalIdx);
		}
		async function submitAdjust(globalIdx) {
			var item = _allItems[globalIdx];
			if (!item) return;
			var adjInput = document.getElementById('adj-' + globalIdx);
			var adjustedQty = parseInt(adjInput ? adjInput.value : 0, 10);
			if (isNaN(adjustedQty) || adjustedQty < 1) {
				var fb = document.getElementById('fb-' + globalIdx);
				if (fb) { fb.textContent = 'Qty must be >= 1'; fb.className = 'action-feedback fail'; fb.style.display = 'inline'; }
				return;
			}
			var recId = (item.forecast_id || '') + '-' + esc(item.sku) + '-' + esc(item.location);
			try {
				var data = await proxy('recommendation_action', {
					recommendation_id: recId,
					action: 'adjusted',
					actor: 'user',
					note: 'Adjusted to ' + adjustedQty,
					adjusted_qty: adjustedQty
				});
				item._actionState = 'adjusted';
				var container = document.getElementById('ab-' + globalIdx);
				if (container) {
					container.innerHTML = '<button class="done small">Adjusted (' + adjustedQty + ')</button>';
				}
			} catch (e) {
				var fb = document.getElementById('fb-' + globalIdx);
				if (fb) { fb.textContent = 'Failed: ' + e.message; fb.className = 'action-feedback fail'; fb.style.display = 'inline'; }
			}
		}
		// ─── D1: Forecast Selector ──────────────────────────────────────────────
		async function loadForecasts() {
			try {
				var data = await proxy('demand_forecasts_list', { limit: 20 });
				_forecasts = data.forecasts || [];
				var sel = document.getElementById('forecastSelector');
				if (!sel) return;
				sel.innerHTML = '<option value="0">-- Latest forecast --</option>' +
					_forecasts.map(function(f) {
						return '<option value="' + esc(f.id) + '">#' + esc(f.id) + ' ' + esc(f.created_at || '') + ' (' + esc(f.total_skus || 0) + ' SKU)</option>';
					}).join('');
			} catch (e) {
				if (window.console) console.warn('Load forecasts failed', e);
			}
		}
		async function selectForecast() {
			var sel = document.getElementById('forecastSelector');
			if (!sel) return;
			var fid = parseInt(sel.value, 10) || 0;
			if (!fid) { runForecast(); return; }
			_currentForecastId = fid;
			setBusy(true);
			try {
				var data = await proxy('demand_results', { forecast_id: fid, limit: 500 });
				var items = data.items || [];
				_allItems = items;
				_currentPage = 0;
				_pageSize = demandUiSettings.result_limit || 100;
				setResult(renderForecastTable(items, data.summary || {}));
				addMsg('ai', 'Loaded forecast #' + fid + ' (' + items.length + ' SKU rows).', true, { forecast_id: fid });
			} catch (e) {
				showError('Failed to load forecast: ' + e.message);
			} finally {
				setBusy(false);
			}
		}
		function setBusy(on) {
			var el = document.getElementById('loadingIndicator');
			if (el) el.style.display = on ? 'block' : 'none';
		}
		function showError(msg) {
			setResult('<div class="result-card"><span class="error">' + esc(msg) + '</span></div>');
		}

		// ─── D1: Row Filter ─────────────────────────────────────────────────────
		function setFilter(mode) {
			_filterMode = mode;
			// Update badge styles
			['all','reorder','review','ok'].forEach(function(m) {
				var el = document.getElementById('filter-' + m);
				if (el) el.className = 'filter-badge' + (m === mode ? ' active' : '');
			});
			_currentPage = 0;
			renderCurrentPage();
		}
		function getFilteredItems() {
			if (_filterMode === 'all') return _allItems;
			return _allItems.filter(function(item) {
				var status = (item.status || item.recommendation || '').toLowerCase();
				if (_filterMode === 'reorder') return status === 'reorder' || (item.recommended_qty || 0) > 0;
				if (_filterMode === 'review') return status === 'review' || status === 'low_confidence';
				if (_filterMode === 'ok') return status === 'sufficient' || status === 'ok' || (item.recommended_qty || 0) <= 0;
				return true;
			});
		}
		function renderCurrentPage() {
			var filtered = getFilteredItems();
			var start = _currentPage * _pageSize;
			var end = Math.min(start + _pageSize, filtered.length);
			var pageItems = filtered.slice(start, end);
			var tbody = document.getElementById('forecast-body');
			if (!tbody) return;
			tbody.innerHTML = pageItems.map(function(item, idx) {
				var globalIdx = _allItems.indexOf(item);
				return '<tr class="expandable" onclick="toggleDetail(' + globalIdx + ')">' +
					'<td>' + esc(item.sku) + '</td>' +
					'<td>' + esc(item.location) + '</td>' +
					'<td>' + esc(item.forecast_qty) + '</td>' +
					'<td>' + esc(item.on_hand_qty) + '</td>' +
					'<td>' + esc(item.safety_stock) + '</td>' +
					'<td>' + esc(item.recommended_qty) + '</td>' +
					'<td onclick="event.stopPropagation()">' + renderActionButtons(item, globalIdx) + '</td>' +
					'</tr>';
			}).join('');
			renderPagination(Math.ceil(filtered.length / _pageSize));
			// Update meta
			var meta = document.getElementById('resultMeta');
			if (meta) meta.innerHTML = 'Showing ' + esc(pageItems.length) + ' of ' + esc(filtered.length) + ' SKU rows' +
				(_filterMode !== 'all' ? ' (' + esc(_filterMode) + ' filter)' : '');
		}

		// ─── D2: Reject Reason ──────────────────────────────────────────────────
		function renderActionButtons(item, globalIdx) {
			var recId = item.forecast_id + '-' + esc(item.sku) + '-' + esc(item.location);
			var actionState = item._actionState || '';
			if (actionState === 'accepted') {
				return '<div class="action-btns"><button class="done small">Accepted</button></div>';
			}
			if (actionState === 'rejected') {
				return '<div class="action-btns"><button class="done small">Rejected</button>' +
					(item._rejectReason ? '<span class="saved-action-state">' + esc(item._rejectReason) + '</span>' : '') +
					'</div>';
			}
			if (actionState === 'adjusted') {
				return '<div class="action-btns"><button class="done small">Adjusted</button></div>';
			}
			return '<div class="action-btns" id="ab-' + globalIdx + '">' +
				'<button class="accept small" onclick="event.stopPropagation();doRecAction(' + globalIdx + ',\'accepted\')">Accept</button>' +
				'<button class="adjust small" onclick="event.stopPropagation();showAdjust(' + globalIdx + ')">Adjust</button>' +
				'<button class="reject small" onclick="event.stopPropagation();showRejectReason(' + globalIdx + ')">Reject</button>' +
				'<span class="action-feedback" id="fb-' + globalIdx + '"></span>' +
				'</div>';
		}
		function showRejectReason(globalIdx) {
			var container = document.getElementById('ab-' + globalIdx);
			if (!container) return;
			container.innerHTML = '<div class="reject-reason">' +
				'<select id="rr-' + globalIdx + '">' +
					'<option value="">Select reason...</option>' +
					'<option value="existing_po">Existing PO</option>' +
					'<option value="order_canceled">Known order canceled</option>' +
					'<option value="supplier_delay">Supplier delay</option>' +
					'<option value="seasonal">Seasonal / demand shift</option>' +
					'<option value="data_wrong">Data wrong / inaccurate</option>' +
					'<option value="other">Other</option>' +
				'</select>' +
				'<button class="small" onclick="event.stopPropagation();submitReject(' + globalIdx + ')">Confirm</button>' +
				'<button class="small secondary" onclick="event.stopPropagation();cancelReject(' + globalIdx + ')">Cancel</button>' +
				'<span class="action-feedback" id="fb-' + globalIdx + '"></span>' +
				'</div>';
		}
		function cancelReject(globalIdx) {
			var item = _allItems[globalIdx];
			if (!item) return;
			var container = document.getElementById('ab-' + globalIdx);
			if (container) container.outerHTML = renderActionButtons(item, globalIdx);
		}
		async function submitReject(globalIdx) {
			var item = _allItems[globalIdx];
			if (!item) return;
			var sel = document.getElementById('rr-' + globalIdx);
			var reason = sel ? sel.value : '';
			if (!reason) {
				var fb = document.getElementById('fb-' + globalIdx);
				if (fb) { fb.textContent = 'Please select a reason'; fb.className = 'action-feedback fail'; fb.style.display = 'inline'; }
				return;
			}
			var recId = (item.forecast_id || '') + '-' + esc(item.sku) + '-' + esc(item.location);
			try {
				var data = await proxy('recommendation_action', {
					recommendation_id: recId,
					action: 'rejected',
					actor: 'user',
					note: 'Rejected: ' + reason,
					adjusted_qty: 0,
					reject_reason: reason
				});
				item._actionState = 'rejected';
				item._rejectReason = reason;
				var container = document.getElementById('ab-' + globalIdx);
				if (container) {
					container.innerHTML = '<button class="done small">Rejected</button><span class="saved-action-state">' + esc(reason) + '</span>';
				}
			} catch (e) {
				var fb = document.getElementById('fb-' + globalIdx);
				if (fb) { fb.textContent = 'Failed: ' + e.message; fb.className = 'action-feedback fail'; fb.style.display = 'inline'; }
			}
		}

		// ─── D1: Copy Summary for Buyer ────────────────────────────────────────
		async function copySummary() {
			try {
				var data = await proxy('demand_summary_text', {});
				var text = data.text || 'No summary available.';
				// Try clipboard API
				if (navigator.clipboard && navigator.clipboard.writeText) {
					await navigator.clipboard.writeText(text);
					addMsg('ai', 'Summary copied to clipboard.', true, { status: 'copied' });
				} else {
					// Fallback: show in a textarea for manual copy
					var ta = document.createElement('textarea');
					ta.value = text;
					ta.style.position = 'fixed';
					ta.style.left = '-9999px';
					document.body.appendChild(ta);
					ta.select();
					try { document.execCommand('copy'); } catch (ignore) {}
					document.body.removeChild(ta);
					addMsg('ai', 'Summary copied to clipboard.', true, { status: 'copied' });
				}
			} catch (e) {
				addMsg('ai', '<span class="error">Failed to copy summary: ' + esc(e.message) + '</span>', true, { status: 'error' });
			}
		}

		// ─── D2: Saved Action State (load from server) ─────────────────────────
		async function loadSavedActions() {
			try {
				var data = await proxy('recommendation_actions_list', {});
				var actions = data.items || [];
				if (!actions.length || !_allItems.length) return;
				// Map actions to items
				actions.forEach(function(a) {
					var parts = (a.recommendation_id || '').split('-');
					if (parts.length < 3) return;
					var fid = parts[0];
					var sku = parts.slice(1, -1).join('-') || parts[1];
					var loc = parts[parts.length - 1];
					_allItems.forEach(function(item) {
						if (String(item.forecast_id) === fid && item.sku === sku && item.location === loc) {
							item._actionState = a.action;
							if (a.action === 'rejected' && a.reject_reason) {
								item._rejectReason = a.reject_reason;
							}
						}
					});
				});
				renderCurrentPage();
			} catch (e) {
				if (window.console) console.warn('Load saved actions failed', e);
			}
		}

		function renderForecast(data) {
			var summary = data.summary || {};
			var items = data.items || [];
			_allItems = items;
			_currentPage = 0;
			_pageSize = demandUiSettings.result_limit || 100;

			// Empty states
			if (!items.length) {
				return renderNoRowsPlaceholder();
			}

			var html = '<div class="result-card"><b>Forecast complete</b>' +
				'<div class="summary">' +
					'<div class="metric"><b>' + esc(summary.total_skus || items.length || 0) + '</b><span>Total SKU</span></div>' +
					'<div class="metric"><b>' + esc(summary.need_reorder || 0) + '</b><span>Reorder</span></div>' +
					'<div class="metric"><b>' + esc(summary.need_review || 0) + '</b><span>Review</span></div>' +
					'<div class="metric"><b>' + esc(summary.sufficient || 0) + '</b><span>OK</span></div>' +
				'</div>';
			return html + renderForecastTable(items, summary) + '</div>';
		}
		function renderNoRowsPlaceholder() {
			return '<div class="empty-state"><b>No result table yet</b>The chat response explains what was checked and what to try next.</div>';
		}
		function readinessCount(readiness, key) {
			var item = readiness && readiness.demand ? readiness.demand[key] : null;
			if (!item) return 'unknown';
			if (item.status === 'error') return 'error';
			return item.count == null ? 0 : item.count;
		}
		function renderNoDataChat(settings, data, readiness) {
			return '<b>I ran the Demand forecast, but no SKU rows came back.</b><br>' +
				'Scope checked: SKU=<b>' + esc(settings.sku_filter || 'all') + '</b>, Location=<b>' + esc(settings.location_filter || 'all') + '</b>, Horizon=<b>' + esc(settings.horizon_days || 90) + ' days</b>.<br><br>' +
				'What I checked behind the scenes: ERP scope, SKU master, current stock, sales history, on-order PO, and committed orders through the server-side AI proxy.<br>' +
				'Live data signals now: SKU master=<b>' + esc(readinessCount(readiness, 'sku_master')) + '</b>, Stock=<b>' + esc(readinessCount(readiness, 'current_stock')) + '</b>, Sales history=<b>' + esc(readinessCount(readiness, 'sales_history')) + '</b>, On order=<b>' + esc(readinessCount(readiness, 'on_order')) + '</b>, Committed=<b>' + esc(readinessCount(readiness, 'committed')) + '</b>.<br><br>' +
				'My recommendation: keep SKU and Location as <b>all</b>, try <b>180 days</b>, then run demo readiness if the counts are still zero. I will not fabricate demand rows when ERP data is missing.';
		}
		async function fetchDemandReadiness() {
			try {
				return await proxy('demo_readiness', {});
			} catch (e) {
				return { demand: {}, error: e.message };
			}
		}
		async function loadDemandReadiness() {
			var el = document.getElementById('demandReadiness');
			if (!el) return;
			try {
				var data = await fetchDemandReadiness();
				var demand = data.demand || {};
				var keys = [
					['sku_master', 'SKU master'],
					['current_stock', 'Stock'],
					['sales_history', 'Sales history'],
					['on_order', 'On order'],
					['committed', 'Committed']
				];
				el.innerHTML = keys.map(function(pair) {
					var item = demand[pair[0]] || {};
					var cls = item.status === 'error' ? ' err' : '';
					var val = item.status === 'error' ? '!' : (item.count == null ? 0 : item.count);
					return '<div class="readiness-pill' + cls + '"><b>' + esc(val) + '</b><span>' + esc(pair[1]) + '</span></div>';
				}).join('');
			} catch (e) {
				el.innerHTML = '<div class="readiness-pill err"><b>!</b><span>Readiness failed</span></div>';
			}
		}
		function renderForecastTable(items, summary) {
			var totalPages = Math.ceil(items.length / _pageSize);
			var pageItems = items.slice(0, _pageSize);

			var html = '';

			// D1: Forecast selector
			html += '<div class="forecast-selector">' +
				'<select id="forecastSelector" onchange="selectForecast()"><option value="0">Loading forecasts...</option></select>' +
				'<button class="secondary small" onclick="loadForecasts()">Refresh</button>' +
				'</div>';

			// D1: Filter badges
			html += '<div style="display:flex;gap:6px;margin-bottom:8px;">' +
				'<span class="filter-badge active" id="filter-all" onclick="setFilter(\'all\')">All (' + esc(items.length) + ')</span>' +
				'<span class="filter-badge" id="filter-reorder" onclick="setFilter(\'reorder\')">Reorder (' + esc(summary.need_reorder || 0) + ')</span>' +
				'<span class="filter-badge" id="filter-review" onclick="setFilter(\'review\')">Review (' + esc(summary.need_review || 0) + ')</span>' +
				'<span class="filter-badge" id="filter-ok" onclick="setFilter(\'ok\')">OK (' + esc(summary.sufficient || 0) + ')</span>' +
				'</div>';

			html += '<div class="result-meta">' +
				'<span id="resultMeta">Showing ' + esc(pageItems.length) + ' of ' + esc(items.length) + ' SKU rows</span>' +
				(totalPages > 1 ? '<div class="pagination" id="pagination"></div>' : '') +
				'<span>Click a row for details</span>' +
				'</div>';

			html += '<div class="table-shell"><table id="forecast-table"><thead><tr>' +
				'<th>SKU</th><th>Location</th><th>Forecast</th><th>On Hand</th><th>Safety Stock</th><th>Recommend</th><th>Action</th>' +
				'</tr></thead><tbody id="forecast-body">';

			html += pageItems.map(function(item, idx) {
				return '<tr class="expandable" onclick="toggleDetail(' + idx + ')">' +
					'<td>' + esc(item.sku) + '</td>' +
					'<td>' + esc(item.location) + '</td>' +
					'<td>' + esc(item.forecast_qty) + '</td>' +
					'<td>' + esc(item.on_hand_qty) + '</td>' +
					'<td>' + esc(item.safety_stock) + '</td>' +
					'<td>' + esc(item.recommended_qty) + '</td>' +
					'<td onclick="event.stopPropagation()">' + renderActionButtons(item, idx) + '</td>' +
					'</tr>';
			}).join('');

			html += '</tbody></table></div>';

			// Partial errors
			if (summary.partial_errors && summary.partial_errors.length) {
				html += '<div class="empty-state" style="margin-top:10px;border-color:#d83b35;color:#9b1c16;">' +
					'<b>Partial Errors</b>' +
					summary.partial_errors.map(function(e) { return esc(e.message || e.error || ''); }).join('<br>') +
					'</div>';
			}

			html += '<div style="margin-top:8px;display:flex;gap:8px;">' +
				'<button class="secondary small" onclick="copySummary()">Copy Summary for Buyer</button>' +
				'</div>' +
				'<p>Review recommendations before creating any ERP purchasing document.</p>';

			// Defer pagination + forecast list + saved actions
			setTimeout(function() {
				renderPagination(totalPages);
				loadForecasts();
				loadSavedActions();
			}, 50);

			return html;
		}
		function renderPagination(totalPages) {
			var container = document.getElementById('pagination');
			if (!container) return;
			var html = '';
			if (_currentPage > 0) html += '<button class="secondary small" onclick="goToPage(' + (_currentPage - 1) + ')">Prev</button>';
			html += '<span>Page ' + (_currentPage + 1) + ' of ' + totalPages + '</span>';
			if (_currentPage < totalPages - 1) html += '<button class="secondary small" onclick="goToPage(' + (_currentPage + 1) + ')">Next</button>';
			container.innerHTML = html;
		}
		function goToPage(page) {
			_currentPage = page;
			var start = page * _pageSize;
			var end = Math.min(start + _pageSize, _allItems.length);
			var pageItems = _allItems.slice(start, end);
			var tbody = document.getElementById('forecast-body');
			if (!tbody) return;
			tbody.innerHTML = pageItems.map(function(item, idx) {
				var globalIdx = start + idx;
				return '<tr class="expandable" onclick="toggleDetail(' + globalIdx + ')">' +
					'<td>' + esc(item.sku) + '</td>' +
					'<td>' + esc(item.location) + '</td>' +
					'<td>' + esc(item.forecast_qty) + '</td>' +
					'<td>' + esc(item.on_hand_qty) + '</td>' +
					'<td>' + esc(item.safety_stock) + '</td>' +
					'<td>' + esc(item.recommended_qty) + '</td>' +
					'<td onclick="event.stopPropagation()">' + renderActionButtons(item, globalIdx) + '</td>' +
					'</tr>';
			}).join('');
			renderPagination(Math.ceil(_allItems.length / _pageSize));
		}
		function clearChat() {
			document.getElementById('messages').innerHTML = '<div class="msg ai">Demand Planning chat cleared.</div>';
			proxy('demand_chat_clear', {}).catch(function(e){ if (window.console) console.warn('Demand chat clear failed', e); });
			_allItems = [];
			hideResult();
		}
		document.getElementById('prompt').addEventListener('keydown', function(e) {
			if (e.key === 'Enter') sendPrompt();
		});
		(function initDemandPage(){
			loadChatHistory().then(function(){
				if (!IS_M8) return;
				loadDemandSettings().then(function(){
					if (demandUiSettings.auto_run === 'y') runForecast();
				});
			});
		})();
	</script>
</body>
</html>
