<!---@ ###########################################################################################################
Version 5.0.1
File Description:
No	Modified Date	Modified By		Change Log
1.	20260715	Lopper		Creation Of File 
################################################################################################################# @--->

<cfif NOT isDefined("host_api_url")>
	<cfset host_api_url = "http://124.155.214.47:8297">
</cfif>
<cftry>
	<cfinclude template="inc_ai_host_config.cfm">
	<cfcatch></cfcatch>
</cftry>
<cfif NOT isDefined("analytics_api_url")><cfset analytics_api_url = host_api_url></cfif>
<cfif NOT isDefined("ai_api_key")><cfset ai_api_key = "YJfgXD-P5WF9p3VCT1XN_ehsnB2KK_OfIYedBxz_J8M"></cfif>
<cfset aiFraudTitle = Tlt("<cfif set_language is 'english'>Fraud Detection</cfif>")>
<cfset aiDemandTitle = Tlt("<cfif set_language is 'english'>Demand Planning</cfif>")>
<cfif isDefined("bm_stylefolder") AND bm_stylefolder EQ "folder_style_h">
	<cfset aiIconWidth = "82">
	<cfset aiTextWidth = "77%">
	<cfset aiBorder = "1px solid ##b6ddf3">
<cfelse>
	<cfset aiIconWidth = "102">
	<cfset aiTextWidth = "72%">
	<cfset aiBorder = "3px solid ##e7ecf9">
</cfif>
<cfparam name="url.ai_fraud_page" default="0">
<cfset aiFraudLimit = 5>
<cfset aiFraudFetchLimit = 5>
<cfset aiFraudPage = max(0, val(url.ai_fraud_page))>
<cfset aiFraudOffset = aiFraudPage * aiFraudLimit>

<cffunction name="aiFraudDesktopFromtransLabel" access="public" returntype="string" output="false">
	<cfargument name="code" type="string" required="true">
	<cfset var fromtrans = Trim(arguments.code)>
	<cfset var fromlink = "">
	<cfset var fromsegm = "">
	<cfset var fromreport = "">
	<cfset var fromwhatsappproc = "n">
	<cfset var comain_tag_vindustry = "">
	<cfset var oldSetLanguage = "">
	<cfset var labelOut = "">
	<cfif fromtrans EQ ""><cfreturn ""></cfif>
	<cfif isDefined("set_language")><cfset oldSetLanguage = set_language></cfif>
	<cfset set_language = "english">
	<cfif NOT isDefined("cookie.cookindustry")><cfset cookie.cookindustry = ""></cfif>
	<cftry>
		<cfsavecontent variable="labelOut"><cfinclude template="inc_form_parse_fromtrans_description.cfm"></cfsavecontent>
		<cfcatch><cfset labelOut = ""></cfcatch>
	</cftry>
	<cfif oldSetLanguage NEQ ""><cfset set_language = oldSetLanguage></cfif>
	<cfset labelOut = ReReplace(Trim(labelOut), "\s+", " ", "all")>
	<cfif labelOut EQ ""><cfset labelOut = fromtrans></cfif>
	<cfreturn labelOut>
</cffunction>

<!--- Load fraud alert badge count via CFML proxy (non-blocking, silent on failure) --->
<cfset fraudBadgeCount = 0>
<cfset fraudPreviewItems = []>
<cfset fraudCheckedTransactions = 0>
<cfset fraudDetectedCount = 0>
<cftry>
	<cfhttp url="#analytics_api_url#/api/fraud-alerts?masterfn=#URLEncodedFormat(cookie.cookmfnunique)#&companyfn=#URLEncodedFormat(cookie.cookcfnunique)#&limit=#aiFraudFetchLimit#&offset=0" method="GET" result="badgeResp" timeout="5" throwonerror="false">
		<cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
		<cfhttpparam type="header" name="Cookie" value="cookuserloginid=#cookie.cookuserloginid#; cookmfnunique=#cookie.cookmfnunique#; cookcfnunique=#cookie.cookcfnunique#">
	</cfhttp>
	<cfif badgeResp.statusCode EQ "200 OK">
		<cfset badgeData = DeserializeJSON(badgeResp.fileContent)>
		<cfif structKeyExists(badgeData, "total")><cfset fraudBadgeCount = val(badgeData.total)></cfif>
		<cfif structKeyExists(badgeData, "items") AND isArray(badgeData.items)><cfset fraudPreviewItems = badgeData.items></cfif>
	</cfif>
<cfcatch></cfcatch>
</cftry>
<cftry>
	<cfhttp url="#analytics_api_url#/api/fraud-alerts-summary?masterfn=#URLEncodedFormat(cookie.cookmfnunique)#&companyfn=#URLEncodedFormat(cookie.cookcfnunique)#" method="GET" result="fraudSummaryResp" timeout="5" throwonerror="false">
		<cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
		<cfhttpparam type="header" name="Cookie" value="cookuserloginid=#cookie.cookuserloginid#; cookmfnunique=#cookie.cookmfnunique#; cookcfnunique=#cookie.cookcfnunique#">
	</cfhttp>
	<cfif fraudSummaryResp.statusCode EQ "200 OK">
		<cfset fraudSummaryData = DeserializeJSON(fraudSummaryResp.fileContent)>
		<cfif structKeyExists(fraudSummaryData, "scheduler") AND structKeyExists(fraudSummaryData.scheduler, "last_result")>
			<cfif structKeyExists(fraudSummaryData.scheduler.last_result, "transactions")><cfset fraudCheckedTransactions = val(fraudSummaryData.scheduler.last_result.transactions)></cfif>
			<cfif structKeyExists(fraudSummaryData.scheduler.last_result, "detected")><cfset fraudDetectedCount = val(fraudSummaryData.scheduler.last_result.detected)></cfif>
		</cfif>
	</cfif>
<cfcatch></cfcatch>
</cftry>

<!--- Kept for pages that execute inline scripts. The rightbot also has direct inline onclick fallback below. --->
<script type="text/javascript">
	var aiFraudPage = 0;
	var aiFraudLimit = 5;
	var aiFraudLoaded = false;
	function aiFraudEsc(v){
		return String(v == null ? '' : v).replace(/[&<>"']/g, function(c){
			return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
		});
	}
	function toggleAiFraudDetection(){
		if (typeof $ !== 'undefined') {
			$('##tbl_ai_fraud_detection').slideToggle(150);
		} else {
			var el = document.getElementById('tbl_ai_fraud_detection');
			if (el) el.style.display = (el.style.display === 'none' ? 'table' : 'none');
		}
	}
	function loadAiFraudInsight(alertId){
		var box = document.getElementById('ai_fraud_insight_' + alertId);
		if (!box || box.getAttribute('data-loaded') === 'y') return;
		box.style.display = 'block';
		box.innerHTML = '<span style="color:##506985;">AI analysing this record...</span>';
		fetch('inc_ajax_ai_assistant.cfm?action=fraud_alert_ai_insight&alert_id=' + encodeURIComponent(alertId), {credentials:'same-origin'})
			.then(function(r){ return r.json(); })
			.then(function(data){
				var evidence = data.risk_rationale || data.rationale || [];
				if (!Array.isArray(evidence)) evidence = [String(evidence || '')];
				box.setAttribute('data-loaded','y');
				box.innerHTML =
					'<div style="font-weight:bold;color:##3b216f;text-transform:uppercase;letter-spacing:.7px;margin-bottom:3px;">AI analysis</div>' +
					'<div style="color:##14325f;margin-bottom:4px;">' + aiFraudEsc(data.summary || 'AI reviewed this indicator using available ERP evidence.') + '</div>' +
					(evidence.length ? '<ul style="margin:4px 0 0 14px;padding:0;color:##506985;">' + evidence.slice(0,4).map(function(x){ return '<li style="margin-bottom:2px;">' + aiFraudEsc(x) + '</li>'; }).join('') + '</ul>' : '');
			})
			.catch(function(){
				box.innerHTML = '<span style="color:##9b1c16;">AI analysis unavailable. Open audit/evidence for details.</span>';
			});
	}
	function aiFraudFriendlyTitle(item){
		var meta = item.metadata || {};
		var rule = String(item.rule_name || item.rule || '').toUpperCase();
		if (rule === 'HIGH_TRANSACTION_AMOUNT') {
			var amount = Number(meta.amount || 0);
			var ratio = Number(meta.ratio || 0);
			return 'Amount unusually high' + (amount ? ' - SGD ' + amount.toLocaleString(undefined,{maximumFractionDigits:0}) : '') + (ratio ? ' (' + ratio.toFixed(1) + 'x normal)' : '');
		}
		if (rule === 'REPEATED_INVOICE_MODIFICATION') {
			return 'Document changed many times' + (meta.invoice_modifications ? ' (' + meta.invoice_modifications + 'x)' : '');
		}
		if (rule === 'TRANSACTION_FREQUENCY_SPIKE') return 'Unusual transaction burst';
		if (rule === 'BACKDATED_TRANSACTION') return 'Backdated transaction needs review';
		return item.title || item.rule_name || 'Suspicious record';
	}
	function aiFraudAuditUrl(item){
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
	window.ignoreAiFraudAlert = function(alertId, btn){
		if (!alertId) return false;
		if (btn) {
			btn.setAttribute('data-old-label', btn.innerHTML);
			btn.style.opacity = '.65';
			btn.style.pointerEvents = 'none';
			btn.innerHTML = 'Hiding...';
		}
		var params = new URLSearchParams();
		params.append('alert_id', alertId);
		params.append('alert_action', 'hide');
		fetch('inc_ajax_ai_assistant.cfm?action=fraud_alert_action', {
			method:'POST',
			headers:{'Content-Type':'application/x-www-form-urlencoded;charset=UTF-8'},
			body:params.toString(),
			credentials:'same-origin'
		}).then(function(resp){
			return resp.text().then(function(text){
				var data = {};
				try { data = text ? JSON.parse(text) : {}; } catch(e) {}
				if (!resp.ok || data.error) {
					throw new Error(data.error || text || 'Ignore failed');
				}
				var tr = btn;
				while (tr && tr.tagName !== 'TR') tr = tr.parentNode;
				if (tr) {
					var next = tr.nextElementSibling;
					tr.style.display = 'none';
					if (next && (next.id || '').indexOf('ai_fraud_detail_') === 0) next.style.display = 'none';
				}
				btn.innerHTML = 'Hidden';
			});
		}).catch(function(err){
			if (btn) {
				btn.style.opacity = '1';
				btn.style.pointerEvents = 'auto';
				btn.innerHTML = 'Failed';
				btn.title = err && err.message ? err.message : 'Ignore failed';
				setTimeout(function(){ btn.innerHTML = btn.getAttribute('data-old-label') || 'Ignore'; }, 1400);
			}
		});
		return false;
	};
	function loadAiFraudPage(page){
		aiFraudLoaded = true;
		aiFraudPage = Math.max(0, page || 0);
		var body = document.getElementById('ai_fraud_record_body');
		if (body) body.innerHTML = '<tr><td colspan="3" style="font-family:Century Gothic;font-size:10pt;color:##666;padding:4px 0 4px 38px;">Loading...</td></tr>';
		var url = 'inc_ajax_ai_assistant.cfm?action=fraud_alert_list_local&limit=' + aiFraudLimit + '&offset=0';
		fetch(url, {credentials:'same-origin'})
			.then(function(r){ return r.json(); })
			.then(renderAiFraudRecords)
			.catch(function(){
				renderAiFraudRecords({total:0, items:[], error:'Unable to load records'});
			});
	}
	function renderAiFraudRecords(data){
		var body = document.getElementById('ai_fraud_record_body');
		var foot = document.getElementById('ai_fraud_record_footer');
		if (!body) return;
		var items = data.items || data.alerts || [];
		var total = Number(data.total || items.length || 0);
		if (!items.length) {
			body.innerHTML = '<tr><td colspan="3" style="font-family:Century Gothic;font-size:9.5pt;color:##506985;padding:4px 0 4px 38px;text-transform:uppercase;letter-spacing:.7px;">No suspicious records found. Checking latest run...</td></tr>';
			fetch('inc_ajax_ai_assistant.cfm?action=fraud_alert_summary', {credentials:'same-origin'})
				.then(function(r){ return r.json(); })
				.then(function(summary){
					var last = summary && summary.scheduler && summary.scheduler.last_result ? summary.scheduler.last_result : {};
					var tx = Number(last.transactions || 0);
					var detected = Number(last.detected || 0);
					body.innerHTML = '<tr><td colspan="3" style="font-family:Century Gothic;font-size:9.5pt;color:##506985;padding:4px 0 4px 38px;text-transform:uppercase;letter-spacing:.7px;">No suspicious records found' + (tx ? ' after checking ' + tx.toLocaleString() + ' transaction(s)' : '') + '. Detected: ' + detected + '.</td></tr>';
				})
				.catch(function(){});
		} else {
			body.innerHTML = items.map(function(item, idx){
				var meta = item.metadata || {};
				var recordNo = idx + 1;
				var doc = meta.document_no || item.transaction_id || '';
				var fromtrans = item.fromtrans || meta.fromtrans || meta.document_type || '';
				var fromtransLabel = item.fromtrans_label || meta.fromtrans_label || fromtrans;
				var fromtransText = fromtrans ? (fromtransLabel === fromtrans ? fromtrans : fromtransLabel + ' (' + fromtrans + ')') : '';
				var modCount = Number(meta.invoice_modifications || 0);
				var mods = modCount > 0 && String(item.rule_name || '').toUpperCase() === 'REPEATED_INVOICE_MODIFICATION' ? (' | updated ' + modCount + 'x') : '';
				var sev = String(item.severity || '').toUpperCase();
				var sevColor = sev === 'CRITICAL' ? '##b42318' : (sev === 'HIGH' ? '##d83b35' : (sev === 'MEDIUM' ? '##f2a900' : '##1f8f4d'));
				var sevIcon = '<svg width="13" height="13" viewBox="0 0 16 16" style="vertical-align:-2px;margin-right:4px" aria-hidden="true"><circle cx="8" cy="8" r="7" fill="' + sevColor + '"/><rect x="7.25" y="3.2" width="1.5" height="6.6" rx=".7" fill="white"/><circle cx="8" cy="12.3" r="1" fill="white"/></svg>';
				var alertId = item.id || item.alert_id || '';
				var friendlyTitle = aiFraudFriendlyTitle(item);
				var auditUrl = aiFraudAuditUrl(item);
				var docHtml = auditUrl ? '<a href="' + auditUrl + '" target="_blank" style="color:##0a65b6;text-decoration:none;font-weight:bold;">' + aiFraudEsc(doc) + '</a>' : aiFraudEsc(doc);
				return '<tr>' +
					'<td width="10%" align="center" valign="top" style="font-family:Century Gothic;font-size:9pt;font-weight:normal;letter-spacing:1px;color:##0a2c61">&nbsp;&nbsp;' + recordNo + '.&nbsp;</td>' +
					'<td width="62%" align="left" valign="top" style="font-family:Century Gothic;font-size:9.5pt;font-weight:normal;letter-spacing:1px;text-transform:uppercase;word-break:break-word;">' +
						sevIcon + '<a style="cursor:pointer;font-weight:normal;color:##0a2c61;text-decoration:none;" onclick="window.open(\\'ai_fraud_alerts.cfm?alert_id=' + encodeURIComponent(alertId) + '&#nsQ#\\',\\'_blank\\')" href="javascript:void(0);" onmouseover="this.style.textDecoration=\\'underline\\'" onmouseout="this.style.textDecoration=\\'none\\'">' + aiFraudEsc(friendlyTitle) + '</a>' +
						'<div style="font-family:Century Gothic;font-size:8pt;color:##506985;letter-spacing:.4px;text-transform:uppercase;margin-left:18px;">' + docHtml + ' | ' + aiFraudEsc(item.user_id || '') + (fromtransText ? ' | ' + aiFraudEsc(fromtransText) : '') + aiFraudEsc(mods) + '</div>' +
					'</td>' +
					'<td width="28%" align="left" valign="top" style="font-family:Century Gothic;font-size:8.8pt;font-weight:normal;letter-spacing:1px;color:' + sevColor + ';text-transform:uppercase;">' + sevIcon + aiFraudEsc(sev) + '<br><a href="javascript:void(0)" onclick="event.cancelBubble=true;if(event.stopPropagation)event.stopPropagation();return window.ignoreAiFraudAlert(\\'' + aiFraudEsc(alertId) + '\\', this);" style="display:inline-block;margin-top:3px;padding:2px 7px;border:1px solid ##d7dfea;border-radius:10px;background:##f8fafc;color:##6b7280;text-decoration:none;font-size:7.5pt;font-weight:bold;letter-spacing:.8px;line-height:1.1;">IGNORE</a></td>' +
				'</tr><tr height="2"><td colspan="3"></td></tr>';
			}).join('');
		}
		if (foot) {
			foot.innerHTML = '<td colspan="3" align="right" style="font-family:Century Gothic;font-size:9pt;letter-spacing:1px;padding:3px 14px 3px 0;color:##506985;text-transform:uppercase;">Showing top ' + Math.min(items.length, aiFraudLimit) + ' suspicious record(s) &nbsp; | &nbsp; <a href="javascript:void(0)" onclick="var e=document.getElementById(\\'tbl_ai_fraud_detection\\');if(e)e.style.display=\\'none\\';return false;" style="color:##9b1c16;text-decoration:none;">Close</a></td>';
		}
	}
</script>

<!--- Fraud Detection: alert workspace --->
<cfoutput>
<table width="100%" border="0" cellspacing="0" cellpadding="0" class="butnlink3c bttRight" valign="middle" id="header_dkpan_ai_fraud_detection">
	<tr height="#bmm_panelhgt#" style="cursor:pointer" onclick="var e=document.getElementById('tbl_ai_fraud_detection');if(e){e.style.display=(e.style.display=='none'||e.style.display=='')?'table':'none';}">
		<td width="#aiIconWidth#" align="center" valign="middle" style="border-bottom:0px solid ##b6ddf3">
			<span style="color:##DD3D3D;font-size:28pt;cursor:pointer">
				<i class="fa fa-exclamation-circle<cfif fraudBadgeCount GT 0> fa-blink2</cfif>" aria-hidden="true"></i>
			</span>
		</td>
		<td width="#aiTextWidth#" align="left" style="text-transform:uppercase;border-bottom:#aiBorder#;cursor:pointer">
			<span style="font-size:12pt; font-family:Century Gothic; text-shadow:1px 1px ##efefef"><cfif set_language is 'english'>FRAUD DETECTION</cfif></span>
		</td>
		<td width="5%" align="right" valign="middle" style="border-bottom:#aiBorder#;padding-right:1px">
			<cfif fraudBadgeCount GT 0>
				<svg class="fa-blink2" width="30" height="18" viewBox="0 0 44 26" style="vertical-align:middle" aria-label="#fraudBadgeCount# fraud records">
					<rect x="2" y="3" width="40" height="20" rx="10" fill="##d83b35">
						<animate attributeName="opacity" values="1;.35;1" dur="1.2s" repeatCount="indefinite" />
					</rect>
					<text x="22" y="17" text-anchor="middle" font-family="Century Gothic, Arial" font-size="11" font-weight="700" fill="##ffffff"><cfif fraudBadgeCount GT 99>99+<cfelse>#fraudBadgeCount#</cfif></text>
				</svg>
			</cfif>
		</td>
		<td width="5%" align="center" valign="middle" style="border-bottom:#aiBorder#;padding-right:1px;cursor:pointer">
			<span class="downlink"><i class="fa fa-angle-down" aria-hidden="true"></i></span>
		</td>
		<td width="*">&nbsp;</td>
	</tr>
</table>
<table id="tbl_ai_fraud_detection" border="0" cellspacing="0" cellpadding="0" style="width:100%;display:none;">
	<tr>
		<td width="#aiIconWidth#">&nbsp;</td>
		<td width="#aiTextWidth#" valign="top">
</cfoutput>
			<table border="0" cellspacing="1" cellpadding="0" style="width:100%;table-layout:fixed;font-family:Century Gothic;letter-spacing:normal;text-transform:uppercase;font-weight:normal;">
				<tbody id="ai_fraud_record_body">
					<cfif arrayLen(fraudPreviewItems) EQ 0>
						<tr><td colspan="3" style="font-family:Century Gothic;font-size:9.5pt;color:##506985;padding:4px 0;text-transform:uppercase;letter-spacing:.7px;">No suspicious records found<cfif fraudCheckedTransactions GT 0> after checking #NumberFormat(fraudCheckedTransactions, "9,999,999")# transaction(s)</cfif>. Detected: #fraudDetectedCount#.</td></tr>
					<cfelse>
						<cfloop from="1" to="#arrayLen(fraudPreviewItems)#" index="aiFraudIdx">
							<cfset aiFraudItemPage = int((aiFraudIdx - 1) / aiFraudLimit)>
							<cfset aiFraudRowDisplay = "none">
							<cfif aiFraudItemPage EQ aiFraudPage><cfset aiFraudRowDisplay = "table-row"></cfif>
							<cfset aiFraudItem = fraudPreviewItems[aiFraudIdx]>
							<cfset aiFraudMeta = {}>
							<cfif structKeyExists(aiFraudItem, "metadata") AND isStruct(aiFraudItem.metadata)><cfset aiFraudMeta = aiFraudItem.metadata></cfif>
							<cfset aiFraudDoc = "">
							<cfif structKeyExists(aiFraudMeta, "document_no")><cfset aiFraudDoc = aiFraudMeta.document_no><cfelseif structKeyExists(aiFraudItem, "transaction_id")><cfset aiFraudDoc = aiFraudItem.transaction_id></cfif>
							<cfset aiFraudMods = "">
							<cfif structKeyExists(aiFraudMeta, "invoice_modifications") AND val(aiFraudMeta.invoice_modifications) GT 0 AND structKeyExists(aiFraudItem, "rule_name") AND ucase(aiFraudItem.rule_name) EQ "REPEATED_INVOICE_MODIFICATION"><cfset aiFraudMods = " | updated #val(aiFraudMeta.invoice_modifications)#x"></cfif>
							<cfset aiFraudModCount = "">
							<cfif structKeyExists(aiFraudMeta, "invoice_modifications") AND val(aiFraudMeta.invoice_modifications) GT 0 AND structKeyExists(aiFraudItem, "rule_name") AND ucase(aiFraudItem.rule_name) EQ "REPEATED_INVOICE_MODIFICATION"><cfset aiFraudModCount = val(aiFraudMeta.invoice_modifications)><cfelse><cfset aiFraudModCount = "-"></cfif>
							<cfset aiFraudModule = "">
							<cfif structKeyExists(aiFraudMeta, "module")><cfset aiFraudModule = aiFraudMeta.module></cfif>
							<cfset aiFraudUserLabel = "Source user">
							<cfif structKeyExists(aiFraudItem, "user_id") AND ListFindNoCase("onlinesys,system,sys,admin", aiFraudItem.user_id)><cfset aiFraudUserLabel = "System user"></cfif>
							<cfset aiFraudFromtrans = "">
							<cfif structKeyExists(aiFraudMeta, "fromtrans")><cfset aiFraudFromtrans = aiFraudMeta.fromtrans><cfelseif structKeyExists(aiFraudMeta, "document_type")><cfset aiFraudFromtrans = aiFraudMeta.document_type></cfif>
							<cfset aiFraudFromtransLabel = "">
							<cfif structKeyExists(aiFraudMeta, "fromtrans_label")>
								<cfset aiFraudFromtransLabel = aiFraudMeta.fromtrans_label>
							<cfelse>
								<cfset aiFraudFromtransLabel = aiFraudDesktopFromtransLabel(aiFraudFromtrans)>
							</cfif>
							<cfset aiFraudFromtransDisplay = aiFraudFromtrans>
							<cfif aiFraudFromtransLabel NEQ "" AND aiFraudFromtransLabel NEQ aiFraudFromtrans>
								<cfset aiFraudFromtransDisplay = aiFraudFromtransLabel & " (" & aiFraudFromtrans & ")">
							</cfif>
							<cfset aiFraudAmount = "">
							<cfif structKeyExists(aiFraudMeta, "amount")><cfset aiFraudAmount = NumberFormat(val(aiFraudMeta.amount), "9,999,999.99")></cfif>
							<cfset aiFraudRisk = "">
							<cfif structKeyExists(aiFraudItem, "risk_score")><cfset aiFraudRisk = NumberFormat(val(aiFraudItem.risk_score), "999.99")></cfif>
							<cfset aiFraudCompare = "">
							<cfset aiFraudBaselineText = "selected ERP scope">
							<cfif structKeyExists(aiFraudMeta, "baseline_scope_label") AND aiFraudMeta.baseline_scope_label NEQ "">
								<cfset aiFraudBaselineText = aiFraudMeta.baseline_scope_label>
							<cfelseif structKeyExists(aiFraudMeta, "baseline_scope") AND aiFraudMeta.baseline_scope NEQ "">
								<cfset aiFraudBaselineText = aiFraudMeta.baseline_scope>
							</cfif>
							<cfif structKeyExists(aiFraudMeta, "baseline_samples") AND val(aiFraudMeta.baseline_samples) GT 0>
								<cfset aiFraudBaselineText = aiFraudBaselineText & "; samples " & val(aiFraudMeta.baseline_samples)>
							</cfif>
							<cfif structKeyExists(aiFraudMeta, "baseline_period_start") AND structKeyExists(aiFraudMeta, "baseline_period_end")>
								<cfset aiFraudBaselineText = aiFraudBaselineText & "; period " & Left(aiFraudMeta.baseline_period_start, 10) & " to " & Left(aiFraudMeta.baseline_period_end, 10)>
							</cfif>
							<cfif structKeyExists(aiFraudItem, "rule_name") AND ucase(aiFraudItem.rule_name) EQ "HIGH_TRANSACTION_AMOUNT">
								<cfset aiFraudBaselineAmount = val(aiFraudMeta.baseline_average_amount)>
								<cfif structKeyExists(aiFraudMeta, "baseline_amount")><cfset aiFraudBaselineAmount = val(aiFraudMeta.baseline_amount)></cfif>
								<cfif structKeyExists(aiFraudMeta, "baseline_p95_amount")><cfset aiFraudBaselineAmount = val(aiFraudMeta.baseline_p95_amount)></cfif>
								<cfset aiFraudCompare = "Amount " & NumberFormat(val(aiFraudMeta.amount), "9,999,999.99") & " vs historical p95 " & NumberFormat(aiFraudBaselineAmount, "9,999,999.99") & " from " & aiFraudBaselineText & " (" & NumberFormat(val(aiFraudMeta.ratio), "9.99") & "x). Thresholds: Low " & val(aiFraudMeta.threshold_low) & "x, Medium " & val(aiFraudMeta.threshold_medium) & "x, High " & val(aiFraudMeta.threshold_high) & "x.">
							<cfelseif structKeyExists(aiFraudItem, "rule_name") AND ucase(aiFraudItem.rule_name) EQ "TRANSACTION_FREQUENCY_SPIKE">
								<cfset aiFraudCompare = "Daily count " & val(aiFraudMeta.daily_count) & " vs normal daily average " & NumberFormat(val(aiFraudMeta.baseline_daily_average), "9.99") & " from " & aiFraudBaselineText & " (" & NumberFormat(val(aiFraudMeta.ratio), "9.99") & "x). Minimum count: " & val(aiFraudMeta.minimum_count) & ".">
							<cfelseif structKeyExists(aiFraudItem, "rule_name") AND ucase(aiFraudItem.rule_name) EQ "HIGH_REFUND_COUNT">
								<cfset aiFraudCompare = "Refund count " & val(aiFraudMeta.refund_count) & " vs thresholds Low " & val(aiFraudMeta.threshold_low) & ", Medium " & val(aiFraudMeta.threshold_medium) & ", High " & val(aiFraudMeta.threshold_high) & ". Baseline: " & NumberFormat(val(aiFraudMeta.baseline), "9.99") & " from " & aiFraudBaselineText & ".">
							<cfelseif structKeyExists(aiFraudItem, "rule_name") AND ucase(aiFraudItem.rule_name) EQ "TOO_MANY_VOID_TRANSACTIONS">
								<cfset aiFraudCompare = "Void count " & val(aiFraudMeta.void_count) & " vs thresholds Low " & val(aiFraudMeta.threshold_low) & ", Medium " & val(aiFraudMeta.threshold_medium) & ", High " & val(aiFraudMeta.threshold_high) & ". Baseline: " & NumberFormat(val(aiFraudMeta.baseline), "9.99") & " from " & aiFraudBaselineText & ".">
							<cfelseif structKeyExists(aiFraudItem, "rule_name") AND ucase(aiFraudItem.rule_name) EQ "ABNORMAL_DISCOUNT">
								<cfset aiFraudCompare = "Discount " & NumberFormat(val(aiFraudMeta.discount), "9,999,999.99") & " vs baseline " & NumberFormat(val(aiFraudMeta.baseline), "9,999,999.99") & " from " & aiFraudBaselineText & " (" & NumberFormat(val(aiFraudMeta.ratio), "9.99") & "x).">
							<cfelseif structKeyExists(aiFraudItem, "rule_name") AND ucase(aiFraudItem.rule_name) EQ "REPEATED_INVOICE_MODIFICATION">
								<cfset aiFraudCompare = "Modified " & val(aiFraudMeta.invoice_modifications) & " time(s) vs thresholds Low >= " & val(aiFraudMeta.threshold_low) & ", Medium >= " & val(aiFraudMeta.threshold_medium) & ", High >= " & val(aiFraudMeta.threshold) & ".">
							<cfelseif structKeyExists(aiFraudItem, "rule_name") AND ucase(aiFraudItem.rule_name) EQ "BACKDATED_TRANSACTION">
								<cfset aiFraudCompare = "Backdated " & val(aiFraudMeta.lag_days) & " day(s), compared with created date vs transaction date. Thresholds Low >= " & val(aiFraudMeta.threshold_low_days) & ", Medium >= " & val(aiFraudMeta.threshold_medium_days) & ", High > " & val(aiFraudMeta.threshold_high_days) & " days.">
							<cfelseif structKeyExists(aiFraudItem, "rule_name") AND ucase(aiFraudItem.rule_name) EQ "LOGIN_OUTSIDE_NORMAL_HOURS">
								<cfset aiFraudCompare = "Transaction time " & aiFraudMeta.activity_time & " vs normal user window " & aiFraudMeta.normal_start & " - " & aiFraudMeta.normal_end & ".">
							</cfif>
							<cfset aiFraudCreatedAt = "">
							<cfif structKeyExists(aiFraudItem, "created_at") AND isDate(aiFraudItem.created_at)><cfset aiFraudCreatedAt = DateFormat(aiFraudItem.created_at, "yyyy-mm-dd") & " " & TimeFormat(aiFraudItem.created_at, "HH:nn")><cfelseif structKeyExists(aiFraudItem, "created_at")><cfset aiFraudCreatedAt = Replace(Left(aiFraudItem.created_at, 16), "T", " ")></cfif>
							<cfset aiFraudEventAt = "">
							<cfif structKeyExists(aiFraudItem, "event_at") AND isDate(aiFraudItem.event_at)><cfset aiFraudEventAt = DateFormat(aiFraudItem.event_at, "yyyy-mm-dd") & " " & TimeFormat(aiFraudItem.event_at, "HH:nn")><cfelseif structKeyExists(aiFraudItem, "event_at")><cfset aiFraudEventAt = Replace(Left(aiFraudItem.event_at, 16), "T", " ")></cfif>
							<cfif structKeyExists(aiFraudMeta, "occurred_at")><cfset aiFraudEventAt = Replace(Left(aiFraudMeta.occurred_at, 16), "T", " ")></cfif>
							<cfif structKeyExists(aiFraudMeta, "source_created_at")><cfset aiFraudCreatedAt = Replace(Left(aiFraudMeta.source_created_at, 16), "T", " ")></cfif>
							<cfset aiFraudUpdatedAt = "">
							<cfif structKeyExists(aiFraudItem, "updated_at") AND isDate(aiFraudItem.updated_at)><cfset aiFraudUpdatedAt = DateFormat(aiFraudItem.updated_at, "yyyy-mm-dd") & " " & TimeFormat(aiFraudItem.updated_at, "HH:nn")><cfelseif structKeyExists(aiFraudItem, "updated_at")><cfset aiFraudUpdatedAt = Replace(Left(aiFraudItem.updated_at, 16), "T", " ")></cfif>
							<cfset aiFraudAlertId = "">
							<cfif structKeyExists(aiFraudItem, "id")><cfset aiFraudAlertId = aiFraudItem.id></cfif>
							<cfset aiFraudTxUnique = "">
							<cfif structKeyExists(aiFraudMeta, "source_transaction_id") AND aiFraudMeta.source_transaction_id NEQ "">
								<cfset aiFraudTxUnique = ListLast(aiFraudMeta.source_transaction_id, ":")>
							<cfelseif structKeyExists(aiFraudItem, "transaction_id") AND aiFraudItem.transaction_id NEQ "">
								<cfset aiFraudTxUnique = ListLast(aiFraudItem.transaction_id, ":")>
							</cfif>
							<cfset aiFraudAuditUrl = "">
							<cfif aiFraudTxUnique NEQ "" AND aiFraudFromtrans NEQ "">
								<cfset aiFraudAuditUrl = "audit_masterdata.cfm?frommode=edit&fromsegm=#URLEncodedFormat(aiFraudFromtrans)#&fromsubsegm=&fromtype=full&fromtrans=#URLEncodedFormat(aiFraudFromtrans)#&fromlevel=cfn&audviewtype=rec&uniquenum_pri=#URLEncodedFormat(aiFraudTxUnique)#">
							</cfif>
							<cfset aiFraudSeverity = ucase(aiFraudItem.severity)>
							<cfset aiFraudColor = "##1f8f4d">
							<cfif aiFraudSeverity EQ "CRITICAL">
								<cfset aiFraudColor = "##b42318">
							<cfelseif aiFraudSeverity EQ "HIGH">
								<cfset aiFraudColor = "##d83b35">
							<cfelseif aiFraudSeverity EQ "MEDIUM">
								<cfset aiFraudColor = "##f2a900">
							</cfif>
							<cfset aiFraudFriendlyTitle = aiFraudItem.title>
							<cfif structKeyExists(aiFraudItem, "rule_name") AND ucase(aiFraudItem.rule_name) EQ "HIGH_TRANSACTION_AMOUNT">
								<cfset aiFraudFriendlyTitle = "Amount unusually high">
								<cfif structKeyExists(aiFraudMeta, "amount")><cfset aiFraudFriendlyTitle = aiFraudFriendlyTitle & " - SGD " & NumberFormat(val(aiFraudMeta.amount), "9,999,999")></cfif>
								<cfif structKeyExists(aiFraudMeta, "ratio")><cfset aiFraudFriendlyTitle = aiFraudFriendlyTitle & " (" & NumberFormat(val(aiFraudMeta.ratio), "9.9") & "x normal)"></cfif>
							<cfelseif structKeyExists(aiFraudItem, "rule_name") AND ucase(aiFraudItem.rule_name) EQ "REPEATED_INVOICE_MODIFICATION">
								<cfset aiFraudFriendlyTitle = "Document changed many times">
								<cfif structKeyExists(aiFraudMeta, "invoice_modifications")><cfset aiFraudFriendlyTitle = aiFraudFriendlyTitle & " (" & val(aiFraudMeta.invoice_modifications) & "x)"></cfif>
							<cfelseif structKeyExists(aiFraudItem, "rule_name") AND ucase(aiFraudItem.rule_name) EQ "TRANSACTION_FREQUENCY_SPIKE">
								<cfset aiFraudFriendlyTitle = "Unusual transaction burst">
							<cfelseif structKeyExists(aiFraudItem, "rule_name") AND ucase(aiFraudItem.rule_name) EQ "BACKDATED_TRANSACTION">
								<cfset aiFraudFriendlyTitle = "Backdated transaction needs review">
							</cfif>
							<cfoutput>
								<tr class="ai-fraud-row ai-fraud-page-#aiFraudItemPage#" style="display:#aiFraudRowDisplay#;">
									<td width="8%" align="left" valign="top" style="font-family:Century Gothic, Arial, sans-serif;font-size:10pt;font-weight:normal;letter-spacing:1px;color:##0a2c61">#(aiFraudOffset + aiFraudIdx)#.</td>
									<td width="72%" align="left" valign="top" style="font-family:Century Gothic, Arial, sans-serif;font-size:10.5pt;font-weight:normal;letter-spacing:1.2px;text-transform:uppercase;word-break:break-word;line-height:1.15;">
										<svg width="12" height="12" viewBox="0 0 16 16" style="vertical-align:-2px;margin-right:4px" aria-hidden="true"><circle cx="8" cy="8" r="7" fill="#aiFraudColor#"/><rect x="7.25" y="3.2" width="1.5" height="6.6" rx=".7" fill="white"/><circle cx="8" cy="12.3" r="1" fill="white"/></svg>
										<a style="cursor:pointer;font-weight:normal;color:##0a2c61;text-decoration:none;" onclick="var d=document.getElementById('ai_fraud_detail_#aiFraudAlertId#');if(d){var open=(d.style.display=='none'||d.style.display=='');d.style.display=open?'table-row':'none';if(open){loadAiFraudInsight('#aiFraudAlertId#');}}return false;" href="javascript:void(0);" onmouseover="this.style.textDecoration='underline'" onmouseout="this.style.textDecoration='none'">#htmlEditFormat(aiFraudFriendlyTitle)#</a>
										<div style="font-family:Century Gothic, Arial, sans-serif;font-size:8.5pt;color:##506985;letter-spacing:.45px;text-transform:uppercase;margin-left:17px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;line-height:1.2;"><cfif aiFraudAuditUrl NEQ ""><a href="#aiFraudAuditUrl#" target="_blank" style="color:##0a65b6;text-decoration:none;font-weight:bold;">#htmlEditFormat(aiFraudDoc)#</a><cfelse>#htmlEditFormat(aiFraudDoc)#</cfif> | #htmlEditFormat(aiFraudUserLabel)#: #htmlEditFormat(aiFraudItem.user_id)#<cfif aiFraudFromtransDisplay NEQ ""> | #htmlEditFormat(aiFraudFromtransDisplay)#</cfif>#htmlEditFormat(aiFraudMods)#</div>
									</td>
									<td width="20%" align="left" valign="top" style="font-family:Century Gothic, Arial, sans-serif;font-size:9.5pt;font-weight:normal;letter-spacing:1px;color:#aiFraudColor#;text-transform:uppercase;white-space:nowrap;line-height:1.15;">
										<svg width="11" height="11" viewBox="0 0 16 16" style="vertical-align:-1px;margin-right:3px" aria-hidden="true"><circle cx="8" cy="8" r="7" fill="#aiFraudColor#"/><rect x="7.25" y="3.2" width="1.5" height="6.6" rx=".7" fill="white"/><circle cx="8" cy="12.3" r="1" fill="white"/></svg>#htmlEditFormat(aiFraudSeverity)#
										<br><a href="javascript:void(0)" onclick="event.cancelBubble=true;if(event.stopPropagation)event.stopPropagation();var b=this;b.innerHTML='Hiding...';b.style.opacity='.65';b.style.pointerEvents='none';fetch('inc_ajax_ai_assistant.cfm?action=fraud_alert_action',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded;charset=UTF-8'},body:'alert_id=#URLEncodedFormat(aiFraudAlertId)#&alert_action=hide',credentials:'same-origin'}).then(function(r){return r.text().then(function(t){var d={};try{d=t?JSON.parse(t):{};}catch(e){}if(!r.ok||d.error){throw new Error(d.error||t||'Ignore failed');}var tr=b;while(tr&&tr.tagName!='TR'){tr=tr.parentNode;}if(tr){var nx=tr.nextElementSibling;tr.style.display='none';if(nx&&nx.id&&nx.id.indexOf('ai_fraud_detail_')==0){nx.style.display='none';}}});}).catch(function(e){b.style.opacity='1';b.style.pointerEvents='auto';b.innerHTML='FAILED';b.title=e&&e.message?e.message:'Ignore failed';setTimeout(function(){b.innerHTML='IGNORE';},1400);});return false;" style="display:inline-block;margin-top:3px;padding:2px 7px;border:1px solid ##d7dfea;border-radius:10px;background:##f8fafc;color:##6b7280;text-decoration:none;font-size:7.5pt;font-weight:bold;letter-spacing:.8px;line-height:1.1;">IGNORE</a>
									</td>
								</tr>
								<tr id="ai_fraud_detail_#aiFraudAlertId#" style="display:none;">
									<td>&nbsp;</td>
									<td colspan="2" style="font-family:Century Gothic, Arial, sans-serif;font-size:8.7pt;color:##14325f;letter-spacing:.25px;line-height:1.35;text-transform:none;padding:5px 0 8px 17px;border-bottom:1px dotted ##b6ddf3;">
										<div style="text-align:right;margin-bottom:3px;text-transform:uppercase;letter-spacing:.7px;">
											<a style="color:##9b1c16;text-decoration:none;font-weight:bold;font-size:8pt;" href="javascript:void(0)" onclick="var d=document.getElementById('ai_fraud_detail_#aiFraudAlertId#');if(d)d.style.display='none';return false;">Close</a>
										</div>
										<table width="100%" border="0" cellspacing="0" cellpadding="0" style="font-family:Century Gothic, Arial, sans-serif;font-size:8.7pt;color:##14325f;text-transform:none;">
											<tr>
												<td width="50%" style="padding:1px 4px 1px 0;"><span style="color:##506985;text-transform:uppercase;font-size:7.6pt;">Document</span><br><span style="font-weight:bold;"><cfif aiFraudAuditUrl NEQ ""><a href="#aiFraudAuditUrl#" target="_blank" style="color:##0a65b6;text-decoration:none;">#htmlEditFormat(aiFraudDoc)#</a><cfelse>#htmlEditFormat(aiFraudDoc)#</cfif></span></td>
												<td width="50%" style="padding:1px 0 1px 4px;"><span style="color:##506985;text-transform:uppercase;font-size:7.6pt;">#htmlEditFormat(aiFraudUserLabel)#</span><br><span style="font-weight:bold;">#htmlEditFormat(aiFraudItem.user_id)#</span></td>
											</tr>
											<tr>
												<td style="padding:3px 4px 1px 0;"><span style="color:##506985;text-transform:uppercase;font-size:7.6pt;">Module / Fromtrans</span><br>#htmlEditFormat(aiFraudModule)#<cfif aiFraudModule NEQ "" AND aiFraudFromtransDisplay NEQ ""> / </cfif>#htmlEditFormat(aiFraudFromtransDisplay)#</td>
												<td style="padding:3px 0 1px 4px;"><span style="color:##506985;text-transform:uppercase;font-size:7.6pt;">Severity / Risk</span><br><span style="color:#aiFraudColor#;font-weight:bold;">#htmlEditFormat(aiFraudSeverity)#</span><cfif aiFraudRisk NEQ ""> / #htmlEditFormat(aiFraudRisk)#</cfif></td>
											</tr>
											<tr>
												<td style="padding:3px 4px 1px 0;"><span style="color:##506985;text-transform:uppercase;font-size:7.6pt;">Transaction date</span><br>#htmlEditFormat(aiFraudEventAt)#</td>
												<td style="padding:3px 0 1px 4px;"><span style="color:##506985;text-transform:uppercase;font-size:7.6pt;">Amount</span><br><cfif aiFraudAmount NEQ "">#htmlEditFormat(aiFraudAmount)#<cfelse>-</cfif></td>
											</tr>
											<tr>
												<td style="padding:3px 4px 1px 0;"><span style="color:##506985;text-transform:uppercase;font-size:7.6pt;">Created</span><br>#htmlEditFormat(aiFraudCreatedAt)#</td>
												<td style="padding:3px 0 1px 4px;"><span style="color:##506985;text-transform:uppercase;font-size:7.6pt;">Last update</span><br>#htmlEditFormat(aiFraudUpdatedAt)#</td>
											</tr>
											<cfif aiFraudModCount NEQ "-">
												<tr>
													<td colspan="2" style="padding:3px 0 1px 0;"><span style="color:##506985;text-transform:uppercase;font-size:7.6pt;">Modified</span><br>#htmlEditFormat(aiFraudModCount)# time(s)</td>
												</tr>
											</cfif>
											<cfif aiFraudCompare NEQ "">
												<tr>
													<td colspan="2" style="padding:5px 0 2px 0;border-top:1px dotted ##d8e1f1;"><span style="color:##506985;text-transform:uppercase;font-size:7.6pt;">Compared with</span><br><span style="color:##0a2c61;">#htmlEditFormat(aiFraudCompare)#</span></td>
												</tr>
											</cfif>
										</table>
										<div id="ai_fraud_insight_#aiFraudAlertId#" data-loaded="n" style="display:none;margin-top:6px;padding:7px 8px;border:1px solid ##d8c9fb;border-left:4px solid ##7c3aed;border-radius:6px;background:##fbfaff;color:##14325f;"></div>
										<div style="margin-top:6px;text-align:center;text-transform:uppercase;letter-spacing:.5px;">
											<cfif aiFraudAuditUrl NEQ ""><a style="color:##0a65b6;text-decoration:none;font-weight:bold;" href="#aiFraudAuditUrl#" target="_blank">Open document audit</a> &nbsp; | &nbsp;</cfif>
											<a style="color:##0a65b6;text-decoration:none;font-weight:bold;" href="ai_fraud_alerts.cfm?alert_id=#URLEncodedFormat(aiFraudAlertId)#&#nsQ#" target="_blank">AI evidence</a> &nbsp; | &nbsp;
											<a style="color:##9b1c16;text-decoration:none;font-weight:bold;" href="javascript:void(0)" onclick="var d=document.getElementById('ai_fraud_detail_#aiFraudAlertId#');if(d)d.style.display='none';return false;">Close</a>
										</div>
									</td>
								</tr>
								<tr class="ai-fraud-row ai-fraud-page-#aiFraudItemPage#" style="display:#aiFraudRowDisplay#;" height="2"><td colspan="3"></td></tr>
							</cfoutput>
						</cfloop>
					</cfif>
				</tbody>
				<tfoot>
					<cfoutput>
						<tr id="ai_fraud_record_footer" class="ai-fraud-footer">
							<td colspan="3" align="right" style="font-family:Century Gothic, Arial, sans-serif;font-size:9.5pt;letter-spacing:1px;padding:5px 0 3px 0;text-transform:uppercase;color:##506985;">
								Showing top #arrayLen(fraudPreviewItems)# suspicious record(s) &nbsp; | &nbsp; <a href="javascript:void(0)" onclick="var e=document.getElementById('tbl_ai_fraud_detection');if(e)e.style.display='none';return false;" style="color:##9b1c16;text-decoration:none;">Close</a>
							</td>
						</tr>
					</cfoutput>
				</tfoot>
			</table>
<cfoutput>
		</td>
		<td width="5%">&nbsp;</td>
		<td width="5%">&nbsp;</td>
		<td width="*">&nbsp;</td>
	</tr>
</table>
</cfoutput>

<!--- Demand Planning: dedicated chatbox-style workspace --->
<cfoutput>
<table width="100%" border="0" cellspacing="0" cellpadding="0" class="butnlink3c bttRight" valign="middle" id="header_dkpan_ai_demand_planning">
	<tr height="#bmm_panelhgt#">
		<td width="#aiIconWidth#" align="center" valign="middle" style="border-bottom:0px solid ##b6ddf3">
			<a style='cursor:pointer' onclick="window.open('ai_demand_planning.cfm?&#nsQ#','_blank')" href="javascript:void(0);">
				<span style="color:##0a2c61;font-size:27pt;cursor:pointer"><i class="fa fa-line-chart" aria-hidden="true"></i></span>
			</a>
		</td>
		<td width="#aiTextWidth#" align="left" style="text-transform:uppercase;border-bottom:#aiBorder#;cursor:pointer">
			<a style='cursor:pointer' onclick="window.open('ai_demand_planning.cfm?&#nsQ#','_blank')" href="javascript:void(0);">
				<span style="font-size:12pt; font-family:Century Gothic; text-shadow:1px 1px ##efefef"><cfif set_language is 'english'>DEMAND PLANNING</cfif></span>
			</a>
		</td>
		<td width="5%" align="right" valign="middle" style="border-bottom:#aiBorder#;padding-right:1px"></td>
		<td width="5%" align="center" valign="middle" style="border-bottom:#aiBorder#;padding-right:1px">&nbsp;</td>
		<td width="*">&nbsp;</td>
	</tr>
</table>
</cfoutput>
