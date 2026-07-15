<!--- ####################################################################################################################
Version	5.0.1
File 	inc_ajax_ai_assistant.cfm
SN  	Date	    	By			Change
1.	20260715	Lopper			creation of new file - proxy cho ERP AI Assistant, giáº¥u API key server-side
##################################################################################################################### --->
<cfparam name="action" default="">

<cfinclude template="inc_syspathname.cfm">
<cfinclude template="sym_meta_lang_a.cfm">
<cfinclude template="inc_qs_set_co_main.cfm">

<!--- action nÃ o tá»± set content-type riÃªng (SSE / binary áº£nh) thÃ¬ bá» qua reset json máº·c Ä‘á»‹nh --->
<cfset reset_action = "chat_stream,get_image">
<cfif NOT listFind(reset_action, action)>
	<cfcontent reset="true">
	<cfcontent type="application/json">
</cfif>

<!--- Config AI API - ưu tiên .env trên server, không bao giờ render ra client --->
<cfscript>
	host_api_url = "http://localhost:8000";
	ai_api_key = "YJfgXD-P5WF9p3VCT1XN_ehsnB2KK_OfIYedBxz_J8M";
	skills_server_url = "http://localhost:3001";
</cfscript>
<cftry>
	<cfinclude template="inc_ai_host_config.cfm">
	<cfcatch></cfcatch>
</cftry>
<cfscript>
	analytics_api_url = host_api_url;
	ai_api_url = host_api_url;
</cfscript>
<cfset upstream_cookie_header = "cookuserloginid=#cookie.cookuserloginid#; cookmfnunique=#cookie.cookmfnunique#; cookcfnunique=#cookie.cookcfnunique#; cooklang=#cookie.cooklang#">
<cfset upstream_erp_user_id = cookie.cookuserloginid>
<cfset upstream_erp_company_id = cookie.cookmfnunique>
<cfset upstream_erp_company_fn = cookie.cookcfnunique>
<cfset upstream_erp_lang = cookie.cooklang>

<cffunction name="aiFraudFromtransLabel" access="public" returntype="string" output="false">
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

<cfswitch expression="#Trim(action)#">

	<!--- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• CHAT / STREAM â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• --->
	<cfcase value="chat_stream">
		<cfparam name="user_id"    type="string" default="">
		<cfparam name="company_id" type="string" default="">
		<cfparam name="masterfn"   type="string" default="">
		<cfparam name="companyfn"  type="string" default="">
		<cfparam name="lang"       type="string" default="">
		<cfparam name="query"      type="string" default="">
		<cfparam name="session_id" type="string" default="">

		<cfset requestBody = {
			"user_id"     : user_id,
			"company_id"  : company_id,
			"company_code": company_id,
			"masterfn"    : masterfn,
			"companyfn"   : companyfn,
			"lang"        : lang,
			"query"       : query,
			"text"        : query,
			"session_id"  : session_id
		}>

		<cftry>
			<cfhttp url="#ai_api_url#/chat/stream" method="POST" result="httpResponse" timeout="120">
				<cfhttpparam type="header" name="Content-Type" value="application/json">
				<cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
				<cfhttpparam type="header" name="Cookie" value="#upstream_cookie_header#">
				<cfhttpparam type="header" name="X-ERP-User-ID" value="#upstream_erp_user_id#">
				<cfhttpparam type="header" name="X-ERP-Company-ID" value="#upstream_erp_company_id#">
				<cfhttpparam type="header" name="X-ERP-Company-FN" value="#upstream_erp_company_fn#">
				<cfhttpparam type="header" name="X-ERP-Lang" value="#upstream_erp_lang#">
				<cfhttpparam type="body" value="#SerializeJSON(requestBody)#">
			</cfhttp>
			<cfset streamContent = REReplace(ToString(httpResponse.fileContent), "^\s+", "", "one")>
			<cfcontent reset="true" type="text/event-stream; charset=utf-8">
			<cfheader name="Cache-Control" value="no-cache">
			<cfheader name="X-Accel-Buffering" value="no">
			<cfoutput>#streamContent#</cfoutput><cfabort>
		<cfcatch>
			<cfcontent reset="true" type="text/event-stream; charset=utf-8">
			<cfheader name="Cache-Control" value="no-cache">
			<cfoutput>event: done
data: {}

</cfoutput><cfabort>
		</cfcatch>
		</cftry>
	</cfcase>

	<!--- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• GREETING â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• --->
	<cfcase value="chat_greeting">
		<cfparam name="user_id"    type="string" default="">
		<cfparam name="company_id" type="string" default="">
		<cfparam name="modules"    type="string" default="[]">

		<cfset requestBody = {
			"query"     : "hello",
			"text"      : "hello",
			"user_id"   : user_id,
			"company_id": company_id,
			"modules"   : DeserializeJSON(modules)
		}>

		<cfhttp url="#ai_api_url#/chat/greeting" method="POST" result="httpResponse" timeout="30">
			<cfhttpparam type="header" name="Content-Type" value="application/json">
			<cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
			<cfhttpparam type="header" name="Cookie" value="#upstream_cookie_header#">
			<cfhttpparam type="header" name="X-ERP-User-ID" value="#upstream_erp_user_id#">
			<cfhttpparam type="header" name="X-ERP-Company-ID" value="#upstream_erp_company_id#">
			<cfhttpparam type="header" name="X-ERP-Company-FN" value="#upstream_erp_company_fn#">
			<cfhttpparam type="header" name="X-ERP-Lang" value="#upstream_erp_lang#">
			<cfhttpparam type="body" value="#SerializeJSON(requestBody)#">
		</cfhttp>
		<cftry>
			<cfoutput>#httpResponse.fileContent#</cfoutput>
		<cfcatch>
			<cfoutput>{"error": "AI service unavailable"}</cfoutput>
		</cfcatch>
		</cftry>
	</cfcase>

	<!--- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• SESSIONS: list â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• --->
	<cfcase value="get_sessions">
		<cfparam name="user_id"    type="string" default="">
		<cfparam name="company_id" type="string" default="">

		<cfset requestBody = {"user_id": user_id, "company_id": company_id}>

		<cfhttp url="#ai_api_url#/chat/sessions" method="POST" result="httpResponse" timeout="30">
			<cfhttpparam type="header" name="Content-Type" value="application/json">
			<cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
			<cfhttpparam type="header" name="Cookie" value="#upstream_cookie_header#">
			<cfhttpparam type="header" name="X-ERP-User-ID" value="#upstream_erp_user_id#">
			<cfhttpparam type="header" name="X-ERP-Company-ID" value="#upstream_erp_company_id#">
			<cfhttpparam type="header" name="X-ERP-Company-FN" value="#upstream_erp_company_fn#">
			<cfhttpparam type="header" name="X-ERP-Lang" value="#upstream_erp_lang#">
			<cfhttpparam type="body" value="#SerializeJSON(requestBody)#">
		</cfhttp>
		<cftry>
			<cfoutput>#httpResponse.fileContent#</cfoutput>
		<cfcatch>
			<cfoutput>{"error": "AI service unavailable"}</cfoutput>
		</cfcatch>
		</cftry>
	</cfcase>

	<!--- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• SESSIONS: rename â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• --->
	<cfcase value="sessions_rename">
		<cfparam name="session_id" type="string" default="">
		<cfparam name="title"      type="string" default="">
		<cfparam name="user_id"    type="string" default="">
		<cfparam name="company_id" type="string" default="">

		<cfset requestBody = {"session_id": session_id, "title": title, "user_id": user_id, "company_id": company_id}>

		<cfhttp url="#ai_api_url#/chat/sessions/rename" method="POST" result="httpResponse" timeout="15">
			<cfhttpparam type="header" name="Content-Type" value="application/json">
			<cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
			<cfhttpparam type="header" name="Cookie" value="#upstream_cookie_header#">
			<cfhttpparam type="header" name="X-ERP-User-ID" value="#upstream_erp_user_id#">
			<cfhttpparam type="header" name="X-ERP-Company-ID" value="#upstream_erp_company_id#">
			<cfhttpparam type="header" name="X-ERP-Company-FN" value="#upstream_erp_company_fn#">
			<cfhttpparam type="header" name="X-ERP-Lang" value="#upstream_erp_lang#">
			<cfhttpparam type="body" value="#SerializeJSON(requestBody)#">
		</cfhttp>
		<cftry>
			<cfoutput>#httpResponse.fileContent#</cfoutput>
		<cfcatch>
			<cfoutput>{"error": "AI service unavailable"}</cfoutput>
		</cfcatch>
		</cftry>
	</cfcase>

	<!--- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• SESSIONS: delete â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• --->
	<cfcase value="sessions_delete">
		<cfparam name="session_id" type="string" default="">
		<cfparam name="user_id"    type="string" default="">
		<cfparam name="company_id" type="string" default="">

		<cfset requestBody = {"session_id": session_id, "user_id": user_id, "company_id": company_id}>

		<cfhttp url="#ai_api_url#/chat/sessions/delete" method="POST" result="httpResponse" timeout="15">
			<cfhttpparam type="header" name="Content-Type" value="application/json">
			<cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
			<cfhttpparam type="header" name="Cookie" value="#upstream_cookie_header#">
			<cfhttpparam type="header" name="X-ERP-User-ID" value="#upstream_erp_user_id#">
			<cfhttpparam type="header" name="X-ERP-Company-ID" value="#upstream_erp_company_id#">
			<cfhttpparam type="header" name="X-ERP-Company-FN" value="#upstream_erp_company_fn#">
			<cfhttpparam type="header" name="X-ERP-Lang" value="#upstream_erp_lang#">
			<cfhttpparam type="body" value="#SerializeJSON(requestBody)#">
		</cfhttp>
		<cftry>
			<cfoutput>#httpResponse.fileContent#</cfoutput>
		<cfcatch>
			<cfoutput>{"error": "AI service unavailable"}</cfoutput>
		</cfcatch>
		</cftry>
	</cfcase>

	<!--- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• SESSIONS: create â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• --->
	<cfcase value="sessions_create">
		<cfparam name="session_id" type="string" default="">
		<cfparam name="user_id"    type="string" default="">
		<cfparam name="company_id" type="string" default="">
		<cfparam name="title"      type="string" default="Untitled chat">

		<cfset requestBody = {"session_id": session_id, "user_id": user_id, "company_id": company_id, "title": title}>

		<cfhttp url="#ai_api_url#/chat/sessions/create" method="POST" result="httpResponse" timeout="15">
			<cfhttpparam type="header" name="Content-Type" value="application/json">
			<cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
			<cfhttpparam type="header" name="Cookie" value="#upstream_cookie_header#">
			<cfhttpparam type="header" name="X-ERP-User-ID" value="#upstream_erp_user_id#">
			<cfhttpparam type="header" name="X-ERP-Company-ID" value="#upstream_erp_company_id#">
			<cfhttpparam type="header" name="X-ERP-Company-FN" value="#upstream_erp_company_fn#">
			<cfhttpparam type="header" name="X-ERP-Lang" value="#upstream_erp_lang#">
			<cfhttpparam type="body" value="#SerializeJSON(requestBody)#">
		</cfhttp>
		<cftry>
			<cfoutput>#httpResponse.fileContent#</cfoutput>
		<cfcatch>
			<cfoutput>{"error": "AI service unavailable"}</cfoutput>
		</cfcatch>
		</cftry>
	</cfcase>

	<!--- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• HISTORY: messages theo session â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• --->
	<cfcase value="chat_history">
		<cfparam name="user_id"    type="string" default="">
		<cfparam name="company_id" type="string" default="">
		<cfparam name="session_id" type="string" default="">
		<cfparam name="limit"      type="numeric" default="5">
		<cfparam name="before_id"  type="string" default="">

		<cfset requestBody = {"user_id": user_id, "company_id": company_id, "session_id": session_id, "limit": limit}>
		<cfif before_id NEQ "">
			<cfset requestBody["before_id"] = before_id>
		</cfif>

		<cfhttp url="#ai_api_url#/chat/history" method="POST" result="httpResponse" timeout="15">
			<cfhttpparam type="header" name="Content-Type" value="application/json">
			<cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
			<cfhttpparam type="header" name="Cookie" value="#upstream_cookie_header#">
			<cfhttpparam type="header" name="X-ERP-User-ID" value="#upstream_erp_user_id#">
			<cfhttpparam type="header" name="X-ERP-Company-ID" value="#upstream_erp_company_id#">
			<cfhttpparam type="header" name="X-ERP-Company-FN" value="#upstream_erp_company_fn#">
			<cfhttpparam type="header" name="X-ERP-Lang" value="#upstream_erp_lang#">
			<cfhttpparam type="body" value="#SerializeJSON(requestBody)#">
		</cfhttp>
		<cftry>
			<cfoutput>#httpResponse.fileContent#</cfoutput>
		<cfcatch>
			<cfoutput>{"error": "AI service unavailable"}</cfoutput>
		</cfcatch>
		</cftry>
	</cfcase>

	<!--- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• HISTORY: xoÃ¡ toÃ n bá»™ â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• --->
	<cfcase value="clear_history">
		<cfparam name="user_id"    type="string" default="">
		<cfparam name="company_id" type="string" default="">

		<cfhttp url="#ai_api_url#/history/#company_id#/#user_id#" method="DELETE" result="httpResponse" timeout="15">
			<cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
			<cfhttpparam type="header" name="Cookie" value="#upstream_cookie_header#">
			<cfhttpparam type="header" name="X-ERP-User-ID" value="#upstream_erp_user_id#">
			<cfhttpparam type="header" name="X-ERP-Company-ID" value="#upstream_erp_company_id#">
			<cfhttpparam type="header" name="X-ERP-Company-FN" value="#upstream_erp_company_fn#">
			<cfhttpparam type="header" name="X-ERP-Lang" value="#upstream_erp_lang#">
		</cfhttp>
		<cftry>
			<cfoutput>#httpResponse.fileContent#</cfoutput>
		<cfcatch>
			<cfoutput>{"error": "AI service unavailable"}</cfoutput>
		</cfcatch>
		</cftry>
	</cfcase>

	<!--- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• FEEDBACK â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• --->
	<cfcase value="feedback">
		<cfparam name="user_id"         type="string" default="">
		<cfparam name="company_id"      type="string" default="">
		<cfparam name="rating"          type="string" default="up">
		<cfparam name="reason"          type="string" default="">
		<cfparam name="comment"         type="string" default="">
		<cfparam name="query_text"      type="string" default="">
		<cfparam name="entry_version_id" type="string" default="">

		<cfset requestBody = {"user_id": user_id, "company_id": company_id, "rating": rating}>
		<cfif reason NEQ "">           <cfset requestBody["reason"] = reason> </cfif>
		<cfif comment NEQ "">          <cfset requestBody["comment"] = comment> </cfif>
		<cfif query_text NEQ "">       <cfset requestBody["query_text"] = query_text> </cfif>
		<cfif entry_version_id NEQ ""> <cfset requestBody["entry_version_id"] = entry_version_id> </cfif>

		<cfhttp url="#ai_api_url#/feedback" method="POST" result="httpResponse" timeout="15">
			<cfhttpparam type="header" name="Content-Type" value="application/json">
			<cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
			<cfhttpparam type="header" name="Cookie" value="#upstream_cookie_header#">
			<cfhttpparam type="header" name="X-ERP-User-ID" value="#upstream_erp_user_id#">
			<cfhttpparam type="header" name="X-ERP-Company-ID" value="#upstream_erp_company_id#">
			<cfhttpparam type="header" name="X-ERP-Company-FN" value="#upstream_erp_company_fn#">
			<cfhttpparam type="header" name="X-ERP-Lang" value="#upstream_erp_lang#">
			<cfhttpparam type="body" value="#SerializeJSON(requestBody)#">
		</cfhttp>
		<cftry>
			<cfoutput>#httpResponse.fileContent#</cfoutput>
		<cfcatch>
			<cfoutput>{"error": "AI service unavailable"}</cfoutput>
		</cfcatch>
		</cftry>
	</cfcase>

	<!--- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• áº¢NH minh hoáº¡ trong step (proxy binary, GET tá»« <img src>) â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• --->
	<cfcase value="skills_healthcheck_local">
		<cfset targetUrl = "http://localhost:3001/health">
		<cfset result = {
			"ok": false,
			"scope": "local",
			"url": targetUrl,
			"status_code": 0,
			"body": "",
			"error": ""
		}>
		<cftry>
			<cfhttp url="#targetUrl#" method="GET" result="httpResponse" timeout="8" throwonerror="false">
				<cfhttpparam type="header" name="Accept" value="application/json">
			</cfhttp>
			<cfset result.ok = true>
			<cfif structKeyExists(httpResponse, "statusCode")>
				<cfset result.status_code = val(listFirst(httpResponse.statusCode, " "))>
			<cfelse>
				<cfset result.status_code = 200>
			</cfif>
			<cfset result.body = left(toString(httpResponse.fileContent), 2000)>
		<cfcatch>
			<cfset result.error = cfcatch.message & (len(cfcatch.detail) ? ": " & cfcatch.detail : "")>
		</cfcatch>
		</cftry>
		<cfcontent reset="true">
		<cfcontent type="application/json; charset=utf-8">
		<cfoutput>#SerializeJSON(result)#</cfoutput>
	</cfcase>

	<cfcase value="skills_healthcheck_host">
		<cfset targetUrl = skills_server_url & "/health">
		<cfset result = {
			"ok": false,
			"scope": "host",
			"url": targetUrl,
			"status_code": 0,
			"body": "",
			"error": ""
		}>
		<cftry>
			<cfhttp url="#targetUrl#" method="GET" result="httpResponse" timeout="8" throwonerror="false">
				<cfhttpparam type="header" name="Accept" value="application/json">
			</cfhttp>
			<cfset result.ok = true>
			<cfif structKeyExists(httpResponse, "statusCode")>
				<cfset result.status_code = val(listFirst(httpResponse.statusCode, " "))>
			<cfelse>
				<cfset result.status_code = 200>
			</cfif>
			<cfset result.body = left(toString(httpResponse.fileContent), 2000)>
		<cfcatch>
			<cfset result.error = cfcatch.message & (len(cfcatch.detail) ? ": " & cfcatch.detail : "")>
		</cfcatch>
		</cftry>
		<cfcontent reset="true">
		<cfcontent type="application/json; charset=utf-8">
		<cfoutput>#SerializeJSON(result)#</cfoutput>
	</cfcase>

	<cfcase value="get_image">
		<cfparam name="image_path" type="string" default="">

		<cfhttp url="#ai_api_url#/images/#image_path#" method="GET" result="httpResponse" timeout="15" getasbinary="auto">
			<cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
			<cfhttpparam type="header" name="Cookie" value="#upstream_cookie_header#">
			<cfhttpparam type="header" name="X-ERP-User-ID" value="#upstream_erp_user_id#">
			<cfhttpparam type="header" name="X-ERP-Company-ID" value="#upstream_erp_company_id#">
			<cfhttpparam type="header" name="X-ERP-Company-FN" value="#upstream_erp_company_fn#">
			<cfhttpparam type="header" name="X-ERP-Lang" value="#upstream_erp_lang#">
		</cfhttp>
		<cfset imgContentType = "image/png">
		<cfif structKeyExists(httpResponse, "responseHeader") AND structKeyExists(httpResponse.responseHeader, "Content-Type")>
			<cfset imgContentType = httpResponse.responseHeader["Content-Type"]>
		</cfif>
		<cfcontent type="#imgContentType#" variable="#httpResponse.fileContent#" reset="true">
	</cfcase>

	<!--- ═══════════════════════════════════════════════════════════════════════
	     FRAUD DETECTION: scan
	     ═══════════════════════════════════════════════════════════════════════ --->
	<cfcase value="fraud_scan">
		<cfparam name="scan_type"    type="string" default="all">
		<cfparam name="severity"     type="string" default="all">
		<cfparam name="max_findings" type="numeric" default="8">
		<cfparam name="date_from"    type="string" default="">
		<cfparam name="date_to"      type="string" default="">

		<cfset requestBody = {
			"masterfn"    : upstream_erp_company_id,
			"companyfn"   : upstream_erp_company_fn,
			"scan_type"   : scan_type,
			"severity"    : severity,
			"max_findings": max_findings
		}>
		<cfif date_from NEQ ""> <cfset requestBody["date_from"] = date_from> </cfif>
		<cfif date_to   NEQ ""> <cfset requestBody["date_to"]   = date_to>   </cfif>

		<cftry>
			<cfhttp url="#analytics_api_url#/api/analytics/fraud-scan" method="POST" result="httpResponse" timeout="60">
				<cfhttpparam type="header" name="Content-Type" value="application/json">
				<cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
				<cfhttpparam type="header" name="Cookie" value="#upstream_cookie_header#">
				<cfhttpparam type="header" name="X-ERP-User-ID" value="#upstream_erp_user_id#">
				<cfhttpparam type="header" name="X-ERP-Company-ID" value="#upstream_erp_company_id#">
				<cfhttpparam type="header" name="X-ERP-Company-FN" value="#upstream_erp_company_fn#">
				<cfhttpparam type="header" name="X-ERP-Lang" value="#upstream_erp_lang#">
				<cfhttpparam type="body" value="#SerializeJSON(requestBody)#">
			</cfhttp>
			<cfoutput>#httpResponse.fileContent#</cfoutput>
		<cfcatch>
			<cfoutput>{"error":"Fraud scan failed","detail":"#JSStringFormat(cfcatch.message)#"}</cfoutput>
		</cfcatch>
		</cftry>
	</cfcase>

	<!--- ═══════════════════════════════════════════════════════════════════════
	     DEMAND PLANNING: forecast
	     ═══════════════════════════════════════════════════════════════════════ --->
	<cfcase value="demand_plan">
		<cfparam name="horizon_days"    type="numeric" default="90">
		<cfparam name="sku_filter"      type="string" default="all">
		<cfparam name="location_filter" type="string" default="all">

		<cfset requestBody = {
			"masterfn"       : upstream_erp_company_id,
			"companyfn"      : upstream_erp_company_fn,
			"horizon_days"   : horizon_days,
			"sku_filter"     : sku_filter,
			"location_filter": location_filter
		}>

		<cftry>
			<cfhttp url="#analytics_api_url#/api/analytics/demand-plan" method="POST" result="httpResponse" timeout="60">
				<cfhttpparam type="header" name="Content-Type" value="application/json">
				<cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
				<cfhttpparam type="header" name="Cookie" value="#upstream_cookie_header#">
				<cfhttpparam type="header" name="X-ERP-User-ID" value="#upstream_erp_user_id#">
				<cfhttpparam type="header" name="X-ERP-Company-ID" value="#upstream_erp_company_id#">
				<cfhttpparam type="header" name="X-ERP-Company-FN" value="#upstream_erp_company_fn#">
				<cfhttpparam type="header" name="X-ERP-Lang" value="#upstream_erp_lang#">
				<cfhttpparam type="body" value="#SerializeJSON(requestBody)#">
			</cfhttp>
			<cfoutput>#httpResponse.fileContent#</cfoutput>
		<cfcatch>
			<cfoutput>{"error":"Demand forecast failed","detail":"#JSStringFormat(cfcatch.message)#"}</cfoutput>
		</cfcatch>
		</cftry>
	</cfcase>

	<!--- ═══════════════════════════════════════════════════════════════════════
	     AI ALERTS: list
	     ═══════════════════════════════════════════════════════════════════════ --->
	<cfcase value="alert_list">
		<cfparam name="status"      type="string" default="">
		<cfparam name="alert_type"  type="string" default="">
		<cfparam name="disposition" type="string" default="">
		<cfparam name="limit"       type="numeric" default="50">
		<cfparam name="offset"      type="numeric" default="0">

		<cfset queryParams = "masterfn=#URLEncodedFormat(upstream_erp_company_id)#&companyfn=#URLEncodedFormat(upstream_erp_company_fn)#&limit=#limit#&offset=#offset#">
		<cfif status      NEQ ""> <cfset queryParams = queryParams & "&status=#URLEncodedFormat(status)#">       </cfif>
		<cfif alert_type  NEQ ""> <cfset queryParams = queryParams & "&alert_type=#URLEncodedFormat(alert_type)#">   </cfif>
		<cfif disposition NEQ ""> <cfset queryParams = queryParams & "&disposition=#URLEncodedFormat(disposition)#"> </cfif>

		<cftry>
			<cfhttp url="#analytics_api_url#/admin/ai-alerts?#queryParams#" method="GET" result="httpResponse" timeout="30">
				<cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
				<cfhttpparam type="header" name="Cookie" value="#upstream_cookie_header#">
				<cfhttpparam type="header" name="X-ERP-User-ID" value="#upstream_erp_user_id#">
				<cfhttpparam type="header" name="X-ERP-Company-ID" value="#upstream_erp_company_id#">
				<cfhttpparam type="header" name="X-ERP-Company-FN" value="#upstream_erp_company_fn#">
				<cfhttpparam type="header" name="X-ERP-Lang" value="#upstream_erp_lang#">
			</cfhttp>
			<cfoutput>#httpResponse.fileContent#</cfoutput>
		<cfcatch>
			<cfoutput>{"error":"Failed to list alerts","detail":"#JSStringFormat(cfcatch.message)#"}</cfoutput>
		</cfcatch>
		</cftry>
	</cfcase>

	<!--- Scheduled fraud alerts: list generated alerts; frontend never starts a scan. --->
	<cfcase value="fraud_alert_list_local">
		<cfparam name="status" type="string" default="">
		<cfparam name="severity" type="string" default="">
		<cfparam name="date_from" type="string" default="">
		<cfparam name="date_to" type="string" default="">
		<cfparam name="search" type="string" default="">
		<cfparam name="limit" type="numeric" default="50">
		<cfparam name="offset" type="numeric" default="0">
		<cftry>
			<cfset cfDsn = "">
			<cfif isDefined("cookie.cooksql_mainsync")>
				<cfset cfDsn = cookie.cooksql_mainsync & "_active">
			<cfelseif isDefined("cookie.cooksqlfilename")>
				<cfset cfDsn = cookie.cooksqlfilename & "_active">
			</cfif>
			<cfif cfDsn EQ ""><cfthrow message="No CF datasource available"></cfif>
			<cfquery datasource="#cfDsn#" name="qFraudCount">
				SELECT COUNT(*) AS total
				FROM memo_long_table
				WHERE tag_table_usage = <cfqueryparam value="ai_fraud_detection" cfsqltype="cf_sql_varchar">
				  AND masterfn = <cfqueryparam value="#upstream_erp_company_id#" cfsqltype="cf_sql_varchar">
				  AND companyfn = <cfqueryparam value="#upstream_erp_company_fn#" cfsqltype="cf_sql_varchar">
				  AND COALESCE(tag_deleted_yn, 'n') = 'n'
				  AND COALESCE(tag_void_yn, 'n') = 'n'
				  <cfif status NEQ "">AND UPPER(COALESCE(tag_others02, 'NEW')) = <cfqueryparam value="#UCase(status)#" cfsqltype="cf_sql_varchar"><cfelse>AND UPPER(COALESCE(tag_others02, 'NEW')) IN ('NEW','ACKNOWLEDGED','ACK')</cfif>
				  <cfif severity NEQ "">AND UPPER(COALESCE(tag_others01, 'LOW')) = <cfqueryparam value="#UCase(severity)#" cfsqltype="cf_sql_varchar"></cfif>
				  <cfif date_from NEQ "">AND COALESCE(date_trans, date_post) >= <cfqueryparam value="#date_from#" cfsqltype="cf_sql_date"></cfif>
				  <cfif date_to NEQ "">AND COALESCE(date_trans, date_post) < (<cfqueryparam value="#date_to#" cfsqltype="cf_sql_date">::date + INTERVAL '1 day')</cfif>
				  <cfif search NEQ "">AND (notes_memo ILIKE <cfqueryparam value="%#search#%" cfsqltype="cf_sql_varchar"> OR var_50_001 ILIKE <cfqueryparam value="%#search#%" cfsqltype="cf_sql_varchar"> OR var_50_002 ILIKE <cfqueryparam value="%#search#%" cfsqltype="cf_sql_varchar"> OR var_25_001 ILIKE <cfqueryparam value="%#search#%" cfsqltype="cf_sql_varchar"> OR var_25_002 ILIKE <cfqueryparam value="%#search#%" cfsqltype="cf_sql_varchar">)</cfif>
			</cfquery>
			<cfquery datasource="#cfDsn#" name="qFraudRows">
				SELECT idcode, uniquenum_pri, tag_others01, tag_others02, tag_others03, tag_others04,
				       var_25_001, var_25_002, var_50_001, var_50_002,
				       num_20_2_d_001, date_post, date_lastupdate, date_trans, notes_memo
				FROM memo_long_table
				WHERE tag_table_usage = <cfqueryparam value="ai_fraud_detection" cfsqltype="cf_sql_varchar">
				  AND masterfn = <cfqueryparam value="#upstream_erp_company_id#" cfsqltype="cf_sql_varchar">
				  AND companyfn = <cfqueryparam value="#upstream_erp_company_fn#" cfsqltype="cf_sql_varchar">
				  AND COALESCE(tag_deleted_yn, 'n') = 'n'
				  AND COALESCE(tag_void_yn, 'n') = 'n'
				  <cfif status NEQ "">AND UPPER(COALESCE(tag_others02, 'NEW')) = <cfqueryparam value="#UCase(status)#" cfsqltype="cf_sql_varchar"><cfelse>AND UPPER(COALESCE(tag_others02, 'NEW')) IN ('NEW','ACKNOWLEDGED','ACK')</cfif>
				  <cfif severity NEQ "">AND UPPER(COALESCE(tag_others01, 'LOW')) = <cfqueryparam value="#UCase(severity)#" cfsqltype="cf_sql_varchar"></cfif>
				  <cfif date_from NEQ "">AND COALESCE(date_trans, date_post) >= <cfqueryparam value="#date_from#" cfsqltype="cf_sql_date"></cfif>
				  <cfif date_to NEQ "">AND COALESCE(date_trans, date_post) < (<cfqueryparam value="#date_to#" cfsqltype="cf_sql_date">::date + INTERVAL '1 day')</cfif>
				  <cfif search NEQ "">AND (notes_memo ILIKE <cfqueryparam value="%#search#%" cfsqltype="cf_sql_varchar"> OR var_50_001 ILIKE <cfqueryparam value="%#search#%" cfsqltype="cf_sql_varchar"> OR var_50_002 ILIKE <cfqueryparam value="%#search#%" cfsqltype="cf_sql_varchar"> OR var_25_001 ILIKE <cfqueryparam value="%#search#%" cfsqltype="cf_sql_varchar"> OR var_25_002 ILIKE <cfqueryparam value="%#search#%" cfsqltype="cf_sql_varchar">)</cfif>
				ORDER BY COALESCE(num_20_2_d_001, 0) DESC, COALESCE(date_trans, date_post) DESC, idcode DESC
				LIMIT <cfqueryparam value="#limit#" cfsqltype="cf_sql_integer"> OFFSET <cfqueryparam value="#offset#" cfsqltype="cf_sql_integer">
			</cfquery>
			<cfset localItems = []>
			<cfloop query="qFraudRows">
				<cfset payload = {}>
				<cftry><cfset payload = DeserializeJSON(qFraudRows.notes_memo)><cfcatch><cfset payload = {}></cfcatch></cftry>
				<cfset meta = {}>
				<cfif isStruct(payload) AND structKeyExists(payload, "metadata") AND isStruct(payload.metadata)><cfset meta = payload.metadata></cfif>
				<cfset localFromtrans = "">
				<cfif structKeyExists(meta, "fromtrans")><cfset localFromtrans = meta.fromtrans><cfelseif structKeyExists(meta, "document_type")><cfset localFromtrans = meta.document_type></cfif>
				<cfset localFromtransLabel = aiFraudFromtransLabel(localFromtrans)>
				<cfif localFromtrans NEQ ""><cfset meta.fromtrans_label = localFromtransLabel></cfif>
				<cfset localDesc = "">
				<cfif isStruct(payload) AND structKeyExists(payload, "description")><cfset localDesc = payload.description></cfif>
				<cfset arrayAppend(localItems, {"id":qFraudRows.idcode,"alert_key":qFraudRows.uniquenum_pri,"rule_name":qFraudRows.var_50_001,"rule":qFraudRows.var_50_001,"title":qFraudRows.var_50_002,"description":localDesc,"severity":qFraudRows.tag_others01,"status":qFraudRows.tag_others02,"risk_score":qFraudRows.num_20_2_d_001,"user_id":qFraudRows.var_25_001,"transaction_id":qFraudRows.var_25_002,"fromtrans":localFromtrans,"fromtrans_label":localFromtransLabel,"source":"CFML_LOCAL_MEMO","created_at":qFraudRows.date_post,"updated_at":qFraudRows.date_lastupdate,"event_at":qFraudRows.date_trans,"metadata":meta})>
			</cfloop>
			<cfoutput>#SerializeJSON({"total":qFraudCount.total,"limit":limit,"offset":offset,"items":localItems,"source":"cfml_local_memo_long_table"})#</cfoutput>
		<cfcatch><cfoutput>{"error":"Failed to list local fraud alerts","detail":"#JSStringFormat(cfcatch.message)#"}</cfoutput></cfcatch>
		</cftry>
	</cfcase>

	<cfcase value="fraud_alert_list">
		<cfparam name="status" type="string" default="">
		<cfparam name="severity" type="string" default="">
		<cfparam name="date_from" type="string" default="">
		<cfparam name="date_to" type="string" default="">
		<cfparam name="search" type="string" default="">
		<cfparam name="limit" type="numeric" default="50">
		<cfparam name="offset" type="numeric" default="0">
		<cfset queryParams = "masterfn=#URLEncodedFormat(upstream_erp_company_id)#&companyfn=#URLEncodedFormat(upstream_erp_company_fn)#&limit=#limit#&offset=#offset#">
		<cfif status NEQ ""><cfset queryParams = queryParams & "&status=#URLEncodedFormat(status)#"></cfif>
		<cfif severity NEQ ""><cfset queryParams = queryParams & "&severity=#URLEncodedFormat(severity)#"></cfif>
		<cfif date_from NEQ ""><cfset queryParams = queryParams & "&date_from=#URLEncodedFormat(date_from)#"></cfif>
		<cfif date_to NEQ ""><cfset queryParams = queryParams & "&date_to=#URLEncodedFormat(date_to)#"></cfif>
		<cfif search NEQ ""><cfset queryParams = queryParams & "&search=#URLEncodedFormat(search)#"></cfif>
		<cftry>
			<cfhttp url="#analytics_api_url#/api/fraud-alerts?#queryParams#" method="GET" result="httpResponse" timeout="30">
				<cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
				<cfhttpparam type="header" name="Cookie" value="#upstream_cookie_header#">
			</cfhttp>
			<cfoutput>#httpResponse.fileContent#</cfoutput>
		<cfcatch>
			<!--- API/server fallback: read persisted ERP memo records directly. --->
			<cftry>
				<cfset cfDsn = "">
				<cfif isDefined("cookie.cooksql_mainsync")>
					<cfset cfDsn = cookie.cooksql_mainsync & "_active">
				<cfelseif isDefined("cookie.cooksqlfilename")>
					<cfset cfDsn = cookie.cooksqlfilename & "_active">
				</cfif>
				<cfif cfDsn EQ ""><cfthrow message="No CF datasource available"></cfif>
				<cfquery datasource="#cfDsn#" name="qFraudCount">
					SELECT COUNT(*) AS total
					FROM memo_long_table
					WHERE tag_table_usage = <cfqueryparam value="ai_fraud_detection" cfsqltype="cf_sql_varchar">
					  AND masterfn = <cfqueryparam value="#upstream_erp_company_id#" cfsqltype="cf_sql_varchar">
					  AND companyfn = <cfqueryparam value="#upstream_erp_company_fn#" cfsqltype="cf_sql_varchar">
					  AND COALESCE(tag_deleted_yn, 'n') = 'n'
					  AND COALESCE(tag_void_yn, 'n') = 'n'
					  <cfif status NEQ "">AND UPPER(COALESCE(tag_others02, 'NEW')) = <cfqueryparam value="#UCase(status)#" cfsqltype="cf_sql_varchar"><cfelse>AND UPPER(COALESCE(tag_others02, 'NEW')) IN ('NEW','ACKNOWLEDGED','ACK')</cfif>
					  <cfif severity NEQ "">AND UPPER(COALESCE(tag_others01, 'LOW')) = <cfqueryparam value="#UCase(severity)#" cfsqltype="cf_sql_varchar"></cfif>
					  <cfif date_from NEQ "">AND COALESCE(date_trans, date_post) >= <cfqueryparam value="#date_from#" cfsqltype="cf_sql_date"></cfif>
					  <cfif date_to NEQ "">AND COALESCE(date_trans, date_post) < (<cfqueryparam value="#date_to#" cfsqltype="cf_sql_date">::date + INTERVAL '1 day')</cfif>
					  <cfif search NEQ "">AND (notes_memo ILIKE <cfqueryparam value="%#search#%" cfsqltype="cf_sql_varchar"> OR var_50_001 ILIKE <cfqueryparam value="%#search#%" cfsqltype="cf_sql_varchar"> OR var_50_002 ILIKE <cfqueryparam value="%#search#%" cfsqltype="cf_sql_varchar"> OR var_25_001 ILIKE <cfqueryparam value="%#search#%" cfsqltype="cf_sql_varchar"> OR var_25_002 ILIKE <cfqueryparam value="%#search#%" cfsqltype="cf_sql_varchar">)</cfif>
				</cfquery>
				<cfquery datasource="#cfDsn#" name="qFraudRows">
					SELECT idcode, uniquenum_pri, tag_others01, tag_others02, tag_others03, tag_others04,
					       var_25_001, var_25_002, var_50_001, var_50_002,
					       num_20_2_d_001, date_post, date_lastupdate, date_trans, notes_memo
					FROM memo_long_table
					WHERE tag_table_usage = <cfqueryparam value="ai_fraud_detection" cfsqltype="cf_sql_varchar">
					  AND masterfn = <cfqueryparam value="#upstream_erp_company_id#" cfsqltype="cf_sql_varchar">
					  AND companyfn = <cfqueryparam value="#upstream_erp_company_fn#" cfsqltype="cf_sql_varchar">
					  AND COALESCE(tag_deleted_yn, 'n') = 'n'
					  AND COALESCE(tag_void_yn, 'n') = 'n'
					  <cfif status NEQ "">AND UPPER(COALESCE(tag_others02, 'NEW')) = <cfqueryparam value="#UCase(status)#" cfsqltype="cf_sql_varchar"><cfelse>AND UPPER(COALESCE(tag_others02, 'NEW')) IN ('NEW','ACKNOWLEDGED','ACK')</cfif>
					  <cfif severity NEQ "">AND UPPER(COALESCE(tag_others01, 'LOW')) = <cfqueryparam value="#UCase(severity)#" cfsqltype="cf_sql_varchar"></cfif>
					  <cfif date_from NEQ "">AND COALESCE(date_trans, date_post) >= <cfqueryparam value="#date_from#" cfsqltype="cf_sql_date"></cfif>
					  <cfif date_to NEQ "">AND COALESCE(date_trans, date_post) < (<cfqueryparam value="#date_to#" cfsqltype="cf_sql_date">::date + INTERVAL '1 day')</cfif>
					  <cfif search NEQ "">AND (notes_memo ILIKE <cfqueryparam value="%#search#%" cfsqltype="cf_sql_varchar"> OR var_50_001 ILIKE <cfqueryparam value="%#search#%" cfsqltype="cf_sql_varchar"> OR var_50_002 ILIKE <cfqueryparam value="%#search#%" cfsqltype="cf_sql_varchar"> OR var_25_001 ILIKE <cfqueryparam value="%#search#%" cfsqltype="cf_sql_varchar"> OR var_25_002 ILIKE <cfqueryparam value="%#search#%" cfsqltype="cf_sql_varchar">)</cfif>
					ORDER BY COALESCE(num_20_2_d_001, 0) DESC, COALESCE(date_trans, date_post) DESC, idcode DESC
					LIMIT <cfqueryparam value="#limit#" cfsqltype="cf_sql_integer"> OFFSET <cfqueryparam value="#offset#" cfsqltype="cf_sql_integer">
				</cfquery>
				<cfset fallbackItems = []>
				<cfloop query="qFraudRows">
					<cfset payload = {}>
					<cftry><cfset payload = DeserializeJSON(qFraudRows.notes_memo)><cfcatch><cfset payload = {}></cfcatch></cftry>
					<cfset meta = {}>
					<cfif isStruct(payload) AND structKeyExists(payload, "metadata") AND isStruct(payload.metadata)><cfset meta = payload.metadata></cfif>
					<cfset fallbackDesc = "">
					<cfif isStruct(payload) AND structKeyExists(payload, "description")><cfset fallbackDesc = payload.description></cfif>
					<cfset arrayAppend(fallbackItems, {
						"id": qFraudRows.idcode,
						"alert_key": qFraudRows.uniquenum_pri,
						"rule_name": qFraudRows.var_50_001,
						"rule": qFraudRows.var_50_001,
						"title": qFraudRows.var_50_002,
						"description": fallbackDesc,
						"severity": qFraudRows.tag_others01,
						"status": qFraudRows.tag_others02,
						"risk_score": qFraudRows.num_20_2_d_001,
						"user_id": qFraudRows.var_25_001,
						"transaction_id": qFraudRows.var_25_002,
						"source": "CFML_FALLBACK",
						"created_at": qFraudRows.date_post,
						"updated_at": qFraudRows.date_lastupdate,
						"event_at": qFraudRows.date_trans,
						"metadata": meta
					})>
				</cfloop>
				<cfoutput>#SerializeJSON({"total":qFraudCount.total,"limit":limit,"offset":offset,"items":fallbackItems,"source":"cfml_memo_long_table_fallback"})#</cfoutput>
			<cfcatch><cfoutput>{"error":"Failed to list scheduled fraud alerts","detail":"#JSStringFormat(cfcatch.message)#"}</cfoutput></cfcatch>
			</cftry>
		</cfcatch>
		</cftry>
	</cfcase>

	<cfcase value="fraud_dashboard">
		<cfset queryParams = "masterfn=#URLEncodedFormat(upstream_erp_company_id)#&companyfn=#URLEncodedFormat(upstream_erp_company_fn)#">
		<cftry>
			<cfhttp url="#analytics_api_url#/api/fraud-dashboard?#queryParams#" method="GET" result="httpResponse" timeout="20">
				<cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
			</cfhttp>
			<cfoutput>#httpResponse.fileContent#</cfoutput>
		<cfcatch>
			<cftry>
				<cfset cfDsn = "">
				<cfif isDefined("cookie.cooksql_mainsync")><cfset cfDsn = cookie.cooksql_mainsync & "_active"><cfelseif isDefined("cookie.cooksqlfilename")><cfset cfDsn = cookie.cooksqlfilename & "_active"></cfif>
				<cfif cfDsn EQ ""><cfthrow message="No CF datasource available"></cfif>
				<cfquery datasource="#cfDsn#" name="qDash">
					SELECT
						COALESCE(NULLIF(notes_memo::jsonb->'metadata'->>'fromtrans',''), NULLIF(notes_memo::jsonb->'metadata'->>'document_type',''), split_part(COALESCE(var_25_002, uniquenum_sec, ''), ':', 2), 'UNKNOWN') AS fromtrans,
						COUNT(*) AS alerts,
						SUM(CASE WHEN UPPER(COALESCE(tag_others01, 'LOW')) = 'HIGH' THEN 1 ELSE 0 END) AS high_alerts,
						SUM(CASE WHEN UPPER(COALESCE(tag_others01, 'LOW')) = 'MEDIUM' THEN 1 ELSE 0 END) AS medium_alerts,
						SUM(CASE WHEN UPPER(COALESCE(tag_others01, 'LOW')) = 'LOW' THEN 1 ELSE 0 END) AS low_alerts
					FROM memo_long_table
					WHERE tag_table_usage = <cfqueryparam value="ai_fraud_detection" cfsqltype="cf_sql_varchar">
					  AND masterfn = <cfqueryparam value="#upstream_erp_company_id#" cfsqltype="cf_sql_varchar">
					  AND companyfn = <cfqueryparam value="#upstream_erp_company_fn#" cfsqltype="cf_sql_varchar">
					  AND COALESCE(tag_deleted_yn, 'n') = 'n'
					  AND COALESCE(date_trans, date_post) >= date_trunc('month', NOW())
					GROUP BY 1
					ORDER BY COUNT(*) DESC
				</cfquery>
				<cfset dashRows = []>
				<cfset dashAlertTotal = 0>
				<cfloop query="qDash">
					<cfset dashAlertTotal = dashAlertTotal + val(qDash.alerts)>
					<cfset arrayAppend(dashRows, {"fromtrans":qDash.fromtrans,"fromtrans_label":aiFraudFromtransLabel(qDash.fromtrans),"transactions":0,"users":0,"total_amount":0,"avg_amount":0,"alerts":qDash.alerts,"high_alerts":qDash.high_alerts,"medium_alerts":qDash.medium_alerts,"low_alerts":qDash.low_alerts})>
				</cfloop>
				<cfoutput>#SerializeJSON({"month":DateFormat(Now(),"yyyy-mm"),"total_transactions":0,"total_alerts":dashAlertTotal,"fromtrans":dashRows,"source":"cfml_memo_long_table_fallback","ai_entrypoints":["API is offline; showing persisted memo_long_table fraud records.","Open a module row to filter persisted alerts and use AI Insight when API returns."]})#</cfoutput>
			<cfcatch><cfoutput>{"error":"Failed to load fraud dashboard","detail":"#JSStringFormat(cfcatch.message)#"}</cfoutput></cfcatch>
			</cftry>
		</cfcatch>
		</cftry>
	</cfcase>

	<cfcase value="fraud_dashboard_local">
		<cftry>
			<cfset cfDsn = "">
			<cfif isDefined("cookie.cooksql_mainsync")><cfset cfDsn = cookie.cooksql_mainsync & "_active"><cfelseif isDefined("cookie.cooksqlfilename")><cfset cfDsn = cookie.cooksqlfilename & "_active"></cfif>
			<cfif cfDsn EQ ""><cfthrow message="No CF datasource available"></cfif>
			<cfquery datasource="#cfDsn#" name="qLatestMonth">
				SELECT COALESCE(date_trunc('month', MAX(COALESCE(occurred_at, created_at))), date_trunc('month', NOW())) AS period_start
				FROM fraud_transaction_source
				WHERE masterfn = <cfqueryparam value="#upstream_erp_company_id#" cfsqltype="cf_sql_varchar">
				  AND companyfn = <cfqueryparam value="#upstream_erp_company_fn#" cfsqltype="cf_sql_varchar">
			</cfquery>
			<cfset dashPeriod = qLatestMonth.period_start>
			<cfquery datasource="#cfDsn#" name="qDash">
				WITH month_tx AS (
					SELECT COALESCE(NULLIF(metadata->>'fromtrans',''), NULLIF(metadata->>'document_type',''), split_part(transaction_id, ':', 2), 'UNKNOWN') AS fromtrans,
					       COUNT(*) AS transactions, COUNT(DISTINCT user_id) AS users,
					       SUM(ABS(COALESCE(amount,0))) AS total_amount, AVG(ABS(COALESCE(amount,0))) AS avg_amount
					FROM fraud_transaction_source
					WHERE masterfn = <cfqueryparam value="#upstream_erp_company_id#" cfsqltype="cf_sql_varchar">
					  AND companyfn = <cfqueryparam value="#upstream_erp_company_fn#" cfsqltype="cf_sql_varchar">
					  AND COALESCE(occurred_at, created_at) >= <cfqueryparam value="#dashPeriod#" cfsqltype="cf_sql_timestamp">
					  AND COALESCE(occurred_at, created_at) < (<cfqueryparam value="#dashPeriod#" cfsqltype="cf_sql_timestamp">::timestamp + INTERVAL '1 month')
					GROUP BY 1
				),
				alert_tx AS (
					SELECT COALESCE(NULLIF(notes_memo::jsonb->'metadata'->>'fromtrans',''), NULLIF(notes_memo::jsonb->'metadata'->>'document_type',''), split_part(COALESCE(var_25_002, uniquenum_sec, ''), ':', 2), 'UNKNOWN') AS fromtrans,
					       COUNT(*) AS alerts,
					       SUM(CASE WHEN UPPER(COALESCE(tag_others01, 'LOW')) = 'HIGH' THEN 1 ELSE 0 END) AS high_alerts,
					       SUM(CASE WHEN UPPER(COALESCE(tag_others01, 'LOW')) = 'MEDIUM' THEN 1 ELSE 0 END) AS medium_alerts,
					       SUM(CASE WHEN UPPER(COALESCE(tag_others01, 'LOW')) = 'LOW' THEN 1 ELSE 0 END) AS low_alerts
					FROM memo_long_table
					WHERE tag_table_usage = <cfqueryparam value="ai_fraud_detection" cfsqltype="cf_sql_varchar">
					  AND masterfn = <cfqueryparam value="#upstream_erp_company_id#" cfsqltype="cf_sql_varchar">
					  AND companyfn = <cfqueryparam value="#upstream_erp_company_fn#" cfsqltype="cf_sql_varchar">
					  AND COALESCE(tag_deleted_yn, 'n') = 'n'
					  AND UPPER(COALESCE(tag_others02, 'NEW')) IN ('NEW','ACKNOWLEDGED','ACK')
					GROUP BY 1
				)
				SELECT COALESCE(m.fromtrans, a.fromtrans) AS fromtrans,
				       COALESCE(m.transactions,0) AS transactions, COALESCE(m.users,0) AS users,
				       COALESCE(m.total_amount,0) AS total_amount, COALESCE(m.avg_amount,0) AS avg_amount,
				       COALESCE(a.alerts,0) AS alerts, COALESCE(a.high_alerts,0) AS high_alerts,
				       COALESCE(a.medium_alerts,0) AS medium_alerts, COALESCE(a.low_alerts,0) AS low_alerts
				FROM month_tx m FULL OUTER JOIN alert_tx a ON a.fromtrans = m.fromtrans
				ORDER BY COALESCE(a.alerts,0) DESC, COALESCE(m.transactions,0) DESC
			</cfquery>
			<cfset dashRows = []><cfset dashTxTotal = 0><cfset dashAlertTotal = 0>
			<cfloop query="qDash">
				<cfset dashTxTotal = dashTxTotal + val(qDash.transactions)><cfset dashAlertTotal = dashAlertTotal + val(qDash.alerts)>
				<cfset arrayAppend(dashRows, {"fromtrans":qDash.fromtrans,"fromtrans_label":aiFraudFromtransLabel(qDash.fromtrans),"transactions":qDash.transactions,"users":qDash.users,"total_amount":qDash.total_amount,"avg_amount":qDash.avg_amount,"alerts":qDash.alerts,"high_alerts":qDash.high_alerts,"medium_alerts":qDash.medium_alerts,"low_alerts":qDash.low_alerts})>
			</cfloop>
			<cfoutput>#SerializeJSON({"month":DateFormat(dashPeriod,"yyyy-mm"),"total_transactions":dashTxTotal,"total_alerts":dashAlertTotal,"fromtrans":dashRows,"source":"cfml_local_erp_db","ai_entrypoints":["Local ERP data is loaded first.","Choose a fromtrans, then use AI Insight only when analysis is needed."]})#</cfoutput>
		<cfcatch><cfoutput>{"error":"Failed to load local fraud dashboard","detail":"#JSStringFormat(cfcatch.message)#"}</cfoutput></cfcatch>
		</cftry>
	</cfcase>

	<cfcase value="fraud_alert_summary_local">
		<cftry>
			<cfset cfDsn = "">
			<cfif isDefined("cookie.cooksql_mainsync")><cfset cfDsn = cookie.cooksql_mainsync & "_active"><cfelseif isDefined("cookie.cooksqlfilename")><cfset cfDsn = cookie.cooksqlfilename & "_active"></cfif>
			<cfif cfDsn EQ ""><cfthrow message="No CF datasource available"></cfif>
			<cfquery datasource="#cfDsn#" name="qSeverity">
				SELECT UPPER(COALESCE(tag_others01, 'LOW')) AS severity, COUNT(*) AS count
				FROM memo_long_table
				WHERE tag_table_usage = <cfqueryparam value="ai_fraud_detection" cfsqltype="cf_sql_varchar">
				  AND masterfn = <cfqueryparam value="#upstream_erp_company_id#" cfsqltype="cf_sql_varchar">
				  AND companyfn = <cfqueryparam value="#upstream_erp_company_fn#" cfsqltype="cf_sql_varchar">
				  AND COALESCE(tag_deleted_yn, 'n') = 'n'
				  AND UPPER(COALESCE(tag_others02, 'NEW')) IN ('NEW','ACKNOWLEDGED','ACK')
				GROUP BY 1
			</cfquery>
			<cfset sev = {}><cfloop query="qSeverity"><cfset sev[qSeverity.severity] = qSeverity.count></cfloop>
			<cfoutput>#SerializeJSON({"scheduler":{"last_run_status":"local","last_result":{"transactions":0,"users":0,"detected":0}},"alert_counts":{},"severity_counts":sev,"source":"cfml_local_memo_long_table"})#</cfoutput>
		<cfcatch><cfoutput>{"error":"Failed to load local fraud summary","detail":"#JSStringFormat(cfcatch.message)#"}</cfoutput></cfcatch>
		</cftry>
	</cfcase>

	<cfcase value="fraud_alert_summary">
		<cfset queryParams = "masterfn=#URLEncodedFormat(upstream_erp_company_id)#&companyfn=#URLEncodedFormat(upstream_erp_company_fn)#">
		<cftry>
			<cfhttp url="#analytics_api_url#/api/fraud-alerts-summary?#queryParams#" method="GET" result="httpResponse" timeout="15">
				<cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
			</cfhttp>
			<cfoutput>#httpResponse.fileContent#</cfoutput>
		<cfcatch><cfoutput>{"error":"Failed to load fraud scheduler summary","detail":"#JSStringFormat(cfcatch.message)#"}</cfoutput></cfcatch>
		</cftry>
	</cfcase>

	<cfcase value="fraud_alert_get">
		<cfparam name="alert_id" type="numeric" default="0">
		<cfif alert_id LTE 0>
			<cfoutput>{"error":"alert_id is required"}</cfoutput><cfabort>
		</cfif>
		<cfset queryParams = "masterfn=#URLEncodedFormat(upstream_erp_company_id)#&companyfn=#URLEncodedFormat(upstream_erp_company_fn)#">
		<cftry>
			<cfhttp url="#analytics_api_url#/api/fraud-alerts/#alert_id#?#queryParams#" method="GET" result="httpResponse" timeout="15">
				<cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
			</cfhttp>
			<cfoutput>#httpResponse.fileContent#</cfoutput>
		<cfcatch><cfoutput>{"error":"Failed to load fraud alert","detail":"#JSStringFormat(cfcatch.message)#"}</cfoutput></cfcatch>
		</cftry>
	</cfcase>

	<cfcase value="fraud_alert_get_local">
		<cfparam name="alert_id" type="numeric" default="0">
		<cfif alert_id LTE 0>
			<cfoutput>{"error":"alert_id is required"}</cfoutput><cfabort>
		</cfif>
		<cftry>
			<cfset cfDsn = "">
			<cfif isDefined("cookie.cooksql_mainsync")><cfset cfDsn = cookie.cooksql_mainsync & "_active"><cfelseif isDefined("cookie.cooksqlfilename")><cfset cfDsn = cookie.cooksqlfilename & "_active"></cfif>
			<cfif cfDsn EQ ""><cfthrow message="No CF datasource available"></cfif>
			<cfquery datasource="#cfDsn#" name="qFraudOne">
				SELECT *
				FROM memo_long_table
				WHERE idcode = <cfqueryparam value="#alert_id#" cfsqltype="cf_sql_integer">
				  AND tag_table_usage = <cfqueryparam value="ai_fraud_detection" cfsqltype="cf_sql_varchar">
				  AND masterfn = <cfqueryparam value="#upstream_erp_company_id#" cfsqltype="cf_sql_varchar">
				  AND companyfn = <cfqueryparam value="#upstream_erp_company_fn#" cfsqltype="cf_sql_varchar">
				  AND COALESCE(tag_deleted_yn, 'n') = 'n'
			</cfquery>
			<cfif qFraudOne.recordCount EQ 0><cfoutput>{"error":"Fraud alert not found"}</cfoutput><cfabort></cfif>
			<cfset payload = {}><cftry><cfset payload = DeserializeJSON(qFraudOne.notes_memo)><cfcatch><cfset payload = {}></cfcatch></cftry>
			<cfset meta = {}><cfif isStruct(payload) AND structKeyExists(payload, "metadata") AND isStruct(payload.metadata)><cfset meta = payload.metadata></cfif>
			<cfset localFromtrans = "">
			<cfif structKeyExists(meta, "fromtrans")><cfset localFromtrans = meta.fromtrans><cfelseif structKeyExists(meta, "document_type")><cfset localFromtrans = meta.document_type></cfif>
			<cfset localFromtransLabel = aiFraudFromtransLabel(localFromtrans)>
			<cfif localFromtrans NEQ ""><cfset meta.fromtrans_label = localFromtransLabel></cfif>
			<cfset localDesc = ""><cfif isStruct(payload) AND structKeyExists(payload, "description")><cfset localDesc = payload.description></cfif>
			<cfoutput>#SerializeJSON({"id":qFraudOne.idcode,"alert_key":qFraudOne.uniquenum_pri,"rule_name":qFraudOne.var_50_001,"rule":qFraudOne.var_50_001,"title":qFraudOne.var_50_002,"description":localDesc,"severity":qFraudOne.tag_others01,"status":qFraudOne.tag_others02,"risk_score":qFraudOne.num_20_2_d_001,"masterfn":qFraudOne.masterfn,"companyfn":qFraudOne.companyfn,"user_id":qFraudOne.var_25_001,"transaction_id":qFraudOne.var_25_002,"fromtrans":localFromtrans,"fromtrans_label":localFromtransLabel,"source":"CFML_LOCAL_MEMO","created_at":qFraudOne.date_post,"updated_at":qFraudOne.date_lastupdate,"event_at":qFraudOne.date_trans,"metadata":meta})#</cfoutput>
		<cfcatch><cfoutput>{"error":"Failed to load local fraud alert","detail":"#JSStringFormat(cfcatch.message)#"}</cfoutput></cfcatch>
		</cftry>
	</cfcase>

	<cfcase value="fraud_alert_ai_insight">
		<cfparam name="alert_id" type="numeric" default="0">
		<cfif alert_id LTE 0>
			<cfoutput>{"error":"alert_id is required"}</cfoutput><cfabort>
		</cfif>
		<cfset queryParams = "masterfn=#URLEncodedFormat(upstream_erp_company_id)#&companyfn=#URLEncodedFormat(upstream_erp_company_fn)#">
		<cftry>
			<cfhttp url="#analytics_api_url#/api/fraud-alerts/#alert_id#/ai-insight?#queryParams#" method="GET" result="httpResponse" timeout="45">
				<cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
			</cfhttp>
			<cfoutput>#httpResponse.fileContent#</cfoutput>
		<cfcatch><cfoutput>{"error":"Failed to load AI fraud insight","detail":"#JSStringFormat(cfcatch.message)#"}</cfoutput></cfcatch>
		</cftry>
	</cfcase>

	<cfcase value="fraud_baselines">
		<cfparam name="days" type="numeric" default="60">
		<cfset queryParams = "masterfn=#URLEncodedFormat(upstream_erp_company_id)#&companyfn=#URLEncodedFormat(upstream_erp_company_fn)#&days=#days#">
		<cftry>
			<cfhttp url="#analytics_api_url#/api/fraud-baselines?#queryParams#" method="GET" result="httpResponse" timeout="30">
				<cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
			</cfhttp>
			<cfoutput>#httpResponse.fileContent#</cfoutput>
		<cfcatch><cfoutput>{"error":"Failed to load fraud baselines","detail":"#JSStringFormat(cfcatch.message)#"}</cfoutput></cfcatch>
		</cftry>
	</cfcase>

	<!--- Scheduled fraud alert lifecycle: acknowledge, resolve, or permanently hide. --->
	<cfcase value="fraud_alert_action">
		<cfparam name="alert_id" type="numeric" default="0">
		<cfparam name="alert_action" type="string" default="">
		<cfif NOT ListFindNoCase("acknowledge,resolve,hide", alert_action)>
			<cfoutput>{"error":"Invalid fraud alert action"}</cfoutput><cfabort>
		</cfif>
		<cfif alert_id LTE 0>
			<cfoutput>{"error":"alert_id is required"}</cfoutput><cfabort>
		</cfif>
		<cfif LCase(alert_action) EQ "hide">
			<cftry>
				<cfset cfDsn = "">
				<cfif isDefined("cookie.cooksql_mainsync")>
					<cfset cfDsn = cookie.cooksql_mainsync & "_active">
				<cfelseif isDefined("cookie.cooksqlfilename")>
					<cfset cfDsn = cookie.cooksqlfilename & "_active">
				</cfif>
				<cfif cfDsn EQ ""><cfthrow message="No CF datasource available"></cfif>
				<cfquery datasource="#cfDsn#" name="qHideFraudAlert">
					UPDATE memo_long_table
					SET tag_others02 = <cfqueryparam value="HIDDEN" cfsqltype="cf_sql_varchar">,
					    tag_closed03_yn = <cfqueryparam value="y" cfsqltype="cf_sql_varchar">,
					    userid_cookie = <cfqueryparam value="#Left(upstream_erp_user_id,10)#" cfsqltype="cf_sql_varchar">,
					    date_lastupdate = NOW()
					WHERE idcode = <cfqueryparam value="#alert_id#" cfsqltype="cf_sql_integer">
					  AND tag_table_usage = <cfqueryparam value="ai_fraud_detection" cfsqltype="cf_sql_varchar">
					  AND masterfn = <cfqueryparam value="#upstream_erp_company_id#" cfsqltype="cf_sql_varchar">
					  AND companyfn = <cfqueryparam value="#upstream_erp_company_fn#" cfsqltype="cf_sql_varchar">
					  AND COALESCE(tag_deleted_yn, 'n') = 'n'
				</cfquery>
				<cfoutput>#SerializeJSON({"id":alert_id,"status":"HIDDEN","source":"cfml_local_update"})#</cfoutput>
				<cfabort>
				<cfcatch><cfoutput>{"error":"Fraud alert update failed","detail":"#JSStringFormat(cfcatch.message)#"}</cfoutput><cfabort></cfcatch>
			</cftry>
		</cfif>
		<cfset queryParams = "masterfn=#URLEncodedFormat(upstream_erp_company_id)#&companyfn=#URLEncodedFormat(upstream_erp_company_fn)#">
		<cfset requestBody = {"actor": upstream_erp_user_id}>
		<cftry>
			<cfhttp url="#analytics_api_url#/api/fraud-alerts/#alert_id#/#alert_action#?#queryParams#" method="POST" result="httpResponse" timeout="15">
				<cfhttpparam type="header" name="Content-Type" value="application/json">
				<cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
				<cfhttpparam type="body" value="#SerializeJSON(requestBody)#">
			</cfhttp>
			<cfoutput>#httpResponse.fileContent#</cfoutput>
		<cfcatch><cfoutput>{"error":"Fraud alert update failed","detail":"#JSStringFormat(cfcatch.message)#"}</cfoutput></cfcatch>
		</cftry>
	</cfcase>

	<!--- ═══════════════════════════════════════════════════════════════════════
	     AI ALERTS: review (update status)
	     ═══════════════════════════════════════════════════════════════════════ --->
	<cfcase value="alert_review">
		<cfparam name="alert_id" type="numeric" default="0">
		<cfparam name="status"   type="string" default="">
		<cfparam name="reviewer" type="string" default="">
		<cfparam name="note"     type="string" default="">
		<cfparam name="disposition_reason" type="string" default="">
		<cfparam name="next_action"        type="string" default="">
		<cfparam name="rule_feedback"      type="string" default="">

		<cfif alert_id LTE 0 OR status EQ "">
			<cfoutput>{"error":"alert_id and status are required"}</cfoutput>
			<cfabort>
		</cfif>

		<cfset requestBody = {
			"masterfn" : upstream_erp_company_id,
			"companyfn": upstream_erp_company_fn,
			"status"   : status,
			"reviewer" : reviewer,
			"note"     : note
		}>
		<cfif disposition_reason NEQ ""> <cfset requestBody["disposition_reason"] = disposition_reason> </cfif>
		<cfif next_action NEQ "">        <cfset requestBody["next_action"] = next_action> </cfif>
		<cfif rule_feedback NEQ "">      <cfset requestBody["rule_feedback"] = rule_feedback> </cfif>

		<cftry>
			<cfhttp url="#analytics_api_url#/admin/ai-alerts/#alert_id#" method="PATCH" result="httpResponse" timeout="15">
				<cfhttpparam type="header" name="Content-Type" value="application/json">
				<cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
				<cfhttpparam type="header" name="Cookie" value="#upstream_cookie_header#">
				<cfhttpparam type="header" name="X-ERP-User-ID" value="#upstream_erp_user_id#">
				<cfhttpparam type="header" name="X-ERP-Company-ID" value="#upstream_erp_company_id#">
				<cfhttpparam type="header" name="X-ERP-Company-FN" value="#upstream_erp_company_fn#">
				<cfhttpparam type="header" name="X-ERP-Lang" value="#upstream_erp_lang#">
				<cfhttpparam type="body" value="#SerializeJSON(requestBody)#">
			</cfhttp>
			<cfoutput>#httpResponse.fileContent#</cfoutput>
		<cfcatch>
			<cfoutput>{"error":"Failed to review alert","detail":"#JSStringFormat(cfcatch.message)#"}</cfoutput>
		</cfcatch>
		</cftry>
	</cfcase>

	<!--- ═══════════════════════════════════════════════════════════════════════
	     AI RECOMMENDATIONS: action (accept/adjust/reject)
	     ═══════════════════════════════════════════════════════════════════════ --->
	<cfcase value="recommendation_action">
		<cfparam name="recommendation_id" type="string" default="">
		<cfparam name="action"            type="string" default="">
		<cfparam name="actor"             type="string" default="">
		<cfparam name="note"              type="string" default="">
		<cfparam name="adjusted_qty"      type="numeric" default="0">
		<cfparam name="reject_reason"     type="string" default="">

		<cfif recommendation_id EQ "" OR action EQ "">
			<cfoutput>{"error":"recommendation_id and action are required"}</cfoutput>
			<cfabort>
		</cfif>

		<cfset requestBody = {
			"masterfn"         : upstream_erp_company_id,
			"companyfn"        : upstream_erp_company_fn,
			"recommendation_id": recommendation_id,
			"action"           : action,
			"actor"            : actor,
			"note"             : note,
			"adjusted_qty"     : adjusted_qty
		}>
		<cfif reject_reason NEQ "">
			<cfset requestBody["reject_reason"] = reject_reason>
		</cfif>

		<cftry>
			<cfhttp url="#analytics_api_url#/admin/ai-recommendations/actions" method="POST" result="httpResponse" timeout="15">
				<cfhttpparam type="header" name="Content-Type" value="application/json">
				<cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
				<cfhttpparam type="header" name="Cookie" value="#upstream_cookie_header#">
				<cfhttpparam type="header" name="X-ERP-User-ID" value="#upstream_erp_user_id#">
				<cfhttpparam type="header" name="X-ERP-Company-ID" value="#upstream_erp_company_id#">
				<cfhttpparam type="header" name="X-ERP-Company-FN" value="#upstream_erp_company_fn#">
				<cfhttpparam type="header" name="X-ERP-Lang" value="#upstream_erp_lang#">
				<cfhttpparam type="body" value="#SerializeJSON(requestBody)#">
			</cfhttp>
			<cfoutput>#httpResponse.fileContent#</cfoutput>
		<cfcatch>
			<cfoutput>{"error":"Failed to record recommendation action","detail":"#JSStringFormat(cfcatch.message)#"}</cfoutput>
		</cfcatch>
		</cftry>
	</cfcase>

	<!--- ═══════════════════════════════════════════════════════════════════════
	     AI SETTINGS: get demand defaults
	     ═══════════════════════════════════════════════════════════════════════ --->
	<cfcase value="demand_settings_get">
		<cfset queryParams = "masterfn=#URLEncodedFormat(upstream_erp_company_id)#&companyfn=#URLEncodedFormat(upstream_erp_company_fn)#&user_id=#URLEncodedFormat(upstream_erp_user_id)#">

		<cftry>
			<cfhttp url="#analytics_api_url#/admin/settings/demand?#queryParams#" method="GET" result="httpResponse" timeout="15">
				<cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
				<cfhttpparam type="header" name="Cookie" value="#upstream_cookie_header#">
				<cfhttpparam type="header" name="X-ERP-User-ID" value="#upstream_erp_user_id#">
				<cfhttpparam type="header" name="X-ERP-Company-ID" value="#upstream_erp_company_id#">
				<cfhttpparam type="header" name="X-ERP-Company-FN" value="#upstream_erp_company_fn#">
				<cfhttpparam type="header" name="X-ERP-Lang" value="#upstream_erp_lang#">
			</cfhttp>
			<cfoutput>#httpResponse.fileContent#</cfoutput>
		<cfcatch>
			<cfoutput>{"error":"Failed to load demand settings","detail":"#JSStringFormat(cfcatch.message)#"}</cfoutput>
		</cfcatch>
		</cftry>
	</cfcase>

	<!--- ═══════════════════════════════════════════════════════════════════════
	     AI SETTINGS: save demand defaults
	     ═══════════════════════════════════════════════════════════════════════ --->
	<cfcase value="demand_settings_save">
		<cfif upstream_erp_user_id NEQ "m8">
			<cfoutput>{"error":"Only m8 can update demand planning settings"}</cfoutput>
			<cfabort>
		</cfif>

		<cfparam name="horizon_days"    type="string" default="90">
		<cfparam name="sku_filter"      type="string" default="all">
		<cfparam name="location_filter" type="string" default="all">
		<cfparam name="result_limit"    type="string" default="100">
		<cfparam name="auto_run"        type="string" default="n">

		<cfset settingsToSave = {
			"horizon_days"    : horizon_days,
			"sku_filter"      : sku_filter,
			"location_filter" : location_filter,
			"result_limit"    : result_limit,
			"auto_run"        : auto_run
		}>
		<cfset savedSettings = {}>

		<cftry>
			<cfloop collection="#settingsToSave#" item="settingName">
				<cfset queryParams = "masterfn=#URLEncodedFormat(upstream_erp_company_id)#&companyfn=#URLEncodedFormat(upstream_erp_company_fn)#&user_id=#URLEncodedFormat(upstream_erp_user_id)#&setting_key=#URLEncodedFormat(settingName)#&setting_val=#URLEncodedFormat(settingsToSave[settingName])#">
				<cfhttp url="#analytics_api_url#/admin/settings/demand?#queryParams#" method="PUT" result="httpResponse" timeout="15">
					<cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
					<cfhttpparam type="header" name="Cookie" value="#upstream_cookie_header#">
					<cfhttpparam type="header" name="X-ERP-User-ID" value="#upstream_erp_user_id#">
					<cfhttpparam type="header" name="X-ERP-Company-ID" value="#upstream_erp_company_id#">
					<cfhttpparam type="header" name="X-ERP-Company-FN" value="#upstream_erp_company_fn#">
					<cfhttpparam type="header" name="X-ERP-Lang" value="#upstream_erp_lang#">
				</cfhttp>
				<cfset savedSettings[settingName] = settingsToSave[settingName]>
			</cfloop>
			<cfoutput>#SerializeJSON({"status":"updated","settings":savedSettings})#</cfoutput>
		<cfcatch>
			<cfoutput>{"error":"Failed to save demand settings","detail":"#JSStringFormat(cfcatch.message)#"}</cfoutput>
		</cfcatch>
		</cftry>
	</cfcase>

	<!--- Demand Planning chat history: list --->
	<cfcase value="demand_chat_history">
		<cfparam name="limit" type="numeric" default="50">
		<cfset queryParams = "masterfn=#URLEncodedFormat(upstream_erp_company_id)#&companyfn=#URLEncodedFormat(upstream_erp_company_fn)#&user_id=#URLEncodedFormat(upstream_erp_user_id)#&limit=#limit#">
		<cftry>
			<cfhttp url="#analytics_api_url#/api/analytics/demand/chat-history?#queryParams#" method="GET" result="httpResponse" timeout="15">
				<cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
				<cfhttpparam type="header" name="Cookie" value="#upstream_cookie_header#">
				<cfhttpparam type="header" name="X-ERP-User-ID" value="#upstream_erp_user_id#">
				<cfhttpparam type="header" name="X-ERP-Company-ID" value="#upstream_erp_company_id#">
				<cfhttpparam type="header" name="X-ERP-Company-FN" value="#upstream_erp_company_fn#">
				<cfhttpparam type="header" name="X-ERP-Lang" value="#upstream_erp_lang#">
			</cfhttp>
			<cfoutput>#httpResponse.fileContent#</cfoutput>
		<cfcatch>
			<cfoutput>{"items":[],"error":"Failed to load demand chat history","detail":"#JSStringFormat(cfcatch.message)#"}</cfoutput>
		</cfcatch>
		</cftry>
	</cfcase>

	<!--- Demand Planning chat history: save one message --->
	<cfcase value="demand_chat_save">
		<cfparam name="role" type="string" default="">
		<cfparam name="content" type="string" default="">
		<cfparam name="meta_json" type="string" default="{}">

		<cfset requestBody = {
			"masterfn" : upstream_erp_company_id,
			"companyfn": upstream_erp_company_fn,
			"user_id"  : upstream_erp_user_id,
			"role"     : role,
			"content"  : content,
			"meta"     : {}
		}>
		<cfif isJSON(meta_json)>
			<cfset requestBody["meta"] = DeserializeJSON(meta_json)>
		</cfif>

		<cftry>
			<cfhttp url="#analytics_api_url#/api/analytics/demand/chat-history" method="POST" result="httpResponse" timeout="15">
				<cfhttpparam type="header" name="Content-Type" value="application/json">
				<cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
				<cfhttpparam type="header" name="Cookie" value="#upstream_cookie_header#">
				<cfhttpparam type="header" name="X-ERP-User-ID" value="#upstream_erp_user_id#">
				<cfhttpparam type="header" name="X-ERP-Company-ID" value="#upstream_erp_company_id#">
				<cfhttpparam type="header" name="X-ERP-Company-FN" value="#upstream_erp_company_fn#">
				<cfhttpparam type="header" name="X-ERP-Lang" value="#upstream_erp_lang#">
				<cfhttpparam type="body" value="#SerializeJSON(requestBody)#">
			</cfhttp>
			<cfoutput>#httpResponse.fileContent#</cfoutput>
		<cfcatch>
			<cfoutput>{"error":"Failed to save demand chat message","detail":"#JSStringFormat(cfcatch.message)#"}</cfoutput>
		</cfcatch>
		</cftry>
	</cfcase>

	<!--- Demand Planning smart chat answer --->
	<cfcase value="demand_chat_answer">
		<cfparam name="message" type="string" default="">

		<cfset requestBody = {
			"masterfn" : upstream_erp_company_id,
			"companyfn": upstream_erp_company_fn,
			"user_id"  : upstream_erp_user_id,
			"message"  : message
		}>

		<cftry>
			<cfhttp url="#analytics_api_url#/api/analytics/demand/chat-answer" method="POST" result="httpResponse" timeout="35">
				<cfhttpparam type="header" name="Content-Type" value="application/json">
				<cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
				<cfhttpparam type="header" name="Cookie" value="#upstream_cookie_header#">
				<cfhttpparam type="header" name="X-ERP-User-ID" value="#upstream_erp_user_id#">
				<cfhttpparam type="header" name="X-ERP-Company-ID" value="#upstream_erp_company_id#">
				<cfhttpparam type="header" name="X-ERP-Company-FN" value="#upstream_erp_company_fn#">
				<cfhttpparam type="header" name="X-ERP-Lang" value="#upstream_erp_lang#">
				<cfhttpparam type="body" value="#SerializeJSON(requestBody)#">
			</cfhttp>
			<cfoutput>#httpResponse.fileContent#</cfoutput>
		<cfcatch>
			<cfoutput>{"answer":"Demand chat answer failed: #JSStringFormat(cfcatch.message)#","source":"error"}</cfoutput>
		</cfcatch>
		</cftry>
	</cfcase>

	<!--- Demand Planning chat history: clear --->
	<cfcase value="demand_chat_clear">
		<cfset queryParams = "masterfn=#URLEncodedFormat(upstream_erp_company_id)#&companyfn=#URLEncodedFormat(upstream_erp_company_fn)#&user_id=#URLEncodedFormat(upstream_erp_user_id)#">
		<cftry>
			<cfhttp url="#analytics_api_url#/api/analytics/demand/chat-history?#queryParams#" method="DELETE" result="httpResponse" timeout="15">
				<cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
				<cfhttpparam type="header" name="Cookie" value="#upstream_cookie_header#">
				<cfhttpparam type="header" name="X-ERP-User-ID" value="#upstream_erp_user_id#">
				<cfhttpparam type="header" name="X-ERP-Company-ID" value="#upstream_erp_company_id#">
				<cfhttpparam type="header" name="X-ERP-Company-FN" value="#upstream_erp_company_fn#">
				<cfhttpparam type="header" name="X-ERP-Lang" value="#upstream_erp_lang#">
			</cfhttp>
			<cfoutput>#httpResponse.fileContent#</cfoutput>
		<cfcatch>
			<cfoutput>{"error":"Failed to clear demand chat history","detail":"#JSStringFormat(cfcatch.message)#"}</cfoutput>
		</cfcatch>
		</cftry>
	</cfcase>

	<!--- ═══════════════════════════════════════════════════════════════════════
	     AI ALERTS: review history
	     ═══════════════════════════════════════════════════════════════════════ --->
	<cfcase value="alert_review_history">
		<cfparam name="alert_id" type="numeric" default="0">
		<cfparam name="limit" type="numeric" default="20">
		<cfset queryParams = "masterfn=#URLEncodedFormat(upstream_erp_company_id)#&companyfn=#URLEncodedFormat(upstream_erp_company_fn)#&limit=#limit#">
		<cftry>
			<cfhttp url="#analytics_api_url#/admin/ai-alerts/#alert_id#/history?#queryParams#" method="GET" result="httpResponse" timeout="15">
				<cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
				<cfhttpparam type="header" name="Cookie" value="#upstream_cookie_header#">
				<cfhttpparam type="header" name="X-ERP-User-ID" value="#upstream_erp_user_id#">
				<cfhttpparam type="header" name="X-ERP-Company-ID" value="#upstream_erp_company_id#">
				<cfhttpparam type="header" name="X-ERP-Company-FN" value="#upstream_erp_company_fn#">
				<cfhttpparam type="header" name="X-ERP-Lang" value="#upstream_erp_lang#">
			</cfhttp>
			<cfoutput>#httpResponse.fileContent#</cfoutput>
		<cfcatch>
			<cfoutput>{"items":[],"error":"#JSStringFormat(cfcatch.message)#"}</cfoutput>
		</cfcatch>
		</cftry>
	</cfcase>

	<!--- ═══════════════════════════════════════════════════════════════════════
	     AI ALERTS: count open alerts by severity (for badge)
	     ═══════════════════════════════════════════════════════════════════════ --->
	<cfcase value="alert_count">
		<cfparam name="severity" type="string" default="critical,high">
		<cfset queryParams = "masterfn=#URLEncodedFormat(upstream_erp_company_id)#&companyfn=#URLEncodedFormat(upstream_erp_company_fn)#&severity=#URLEncodedFormat(severity)#">
		<cftry>
			<cfhttp url="#analytics_api_url#/admin/ai-alerts/count?#queryParams#" method="GET" result="httpResponse" timeout="15">
				<cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
				<cfhttpparam type="header" name="Cookie" value="#upstream_cookie_header#">
				<cfhttpparam type="header" name="X-ERP-User-ID" value="#upstream_erp_user_id#">
				<cfhttpparam type="header" name="X-ERP-Company-ID" value="#upstream_erp_company_id#">
				<cfhttpparam type="header" name="X-ERP-Company-FN" value="#upstream_erp_company_fn#">
				<cfhttpparam type="header" name="X-ERP-Lang" value="#upstream_erp_lang#">
			</cfhttp>
			<cfoutput>#httpResponse.fileContent#</cfoutput>
		<cfcatch>
			<cfoutput>{"count":0,"error":"#JSStringFormat(cfcatch.message)#"}</cfoutput>
		</cfcatch>
		</cftry>
	</cfcase>

	<!--- ═══════════════════════════════════════════════════════════════════════
	     AI RECOMMENDATIONS: list actions for a recommendation
	     ═══════════════════════════════════════════════════════════════════════ --->
	<cfcase value="recommendation_actions_list">
		<cfparam name="recommendation_id" type="string" default="">
		<cfset queryParams = "masterfn=#URLEncodedFormat(upstream_erp_company_id)#&companyfn=#URLEncodedFormat(upstream_erp_company_fn)#">
		<cfif recommendation_id NEQ "">
			<cfset queryParams = queryParams & "&recommendation_id=#URLEncodedFormat(recommendation_id)#">
		</cfif>
		<cftry>
			<cfhttp url="#analytics_api_url#/admin/ai-recommendations/actions?#queryParams#" method="GET" result="httpResponse" timeout="15">
				<cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
				<cfhttpparam type="header" name="Cookie" value="#upstream_cookie_header#">
				<cfhttpparam type="header" name="X-ERP-User-ID" value="#upstream_erp_user_id#">
				<cfhttpparam type="header" name="X-ERP-Company-ID" value="#upstream_erp_company_id#">
				<cfhttpparam type="header" name="X-ERP-Company-FN" value="#upstream_erp_company_fn#">
				<cfhttpparam type="header" name="X-ERP-Lang" value="#upstream_erp_lang#">
			</cfhttp>
			<cfoutput>#httpResponse.fileContent#</cfoutput>
		<cfcatch>
			<cfoutput>{"items":[],"error":"#JSStringFormat(cfcatch.message)#"}</cfoutput>
		</cfcatch>
		</cftry>
	</cfcase>

	<!--- ═══════════════════════════════════════════════════════════════════════
	     DEMAND: list recent forecasts
	     ═══════════════════════════════════════════════════════════════════════ --->
	<cfcase value="demand_forecasts_list">
		<cfparam name="limit" type="numeric" default="10">
		<cfset queryParams = "masterfn=#URLEncodedFormat(upstream_erp_company_id)#&companyfn=#URLEncodedFormat(upstream_erp_company_fn)#&limit=#limit#">
		<cftry>
			<cfhttp url="#analytics_api_url#/api/analytics/demand/forecasts?#queryParams#" method="GET" result="httpResponse" timeout="15">
				<cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
				<cfhttpparam type="header" name="Cookie" value="#upstream_cookie_header#">
				<cfhttpparam type="header" name="X-ERP-User-ID" value="#upstream_erp_user_id#">
				<cfhttpparam type="header" name="X-ERP-Company-ID" value="#upstream_erp_company_id#">
				<cfhttpparam type="header" name="X-ERP-Company-FN" value="#upstream_erp_company_fn#">
				<cfhttpparam type="header" name="X-ERP-Lang" value="#upstream_erp_lang#">
			</cfhttp>
			<cfoutput>#httpResponse.fileContent#</cfoutput>
		<cfcatch>
			<cfoutput>{"forecasts":[],"error":"#JSStringFormat(cfcatch.message)#"}</cfoutput>
		</cfcatch>
		</cftry>
	</cfcase>

	<!--- ═══════════════════════════════════════════════════════════════════════
	     DEMAND: get results for a specific forecast
	     ═══════════════════════════════════════════════════════════════════════ --->
	<cfcase value="demand_results">
		<cfparam name="forecast_id" type="numeric" default="0">
		<cfparam name="action_filter" type="string" default="all">
		<cfparam name="limit" type="numeric" default="50">
		<cfparam name="offset" type="numeric" default="0">
		<cfset queryParams = "masterfn=#URLEncodedFormat(upstream_erp_company_id)#&companyfn=#URLEncodedFormat(upstream_erp_company_fn)#&limit=#limit#&offset=#offset#">
		<cfif forecast_id GT 0>
			<cfset queryParams = queryParams & "&forecast_id=#forecast_id#">
		</cfif>
		<cfif action_filter NEQ "all">
			<cfset queryParams = queryParams & "&action=#URLEncodedFormat(action_filter)#">
		</cfif>
		<cftry>
			<cfhttp url="#analytics_api_url#/api/analytics/demand/results?#queryParams#" method="GET" result="httpResponse" timeout="15">
				<cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
				<cfhttpparam type="header" name="Cookie" value="#upstream_cookie_header#">
				<cfhttpparam type="header" name="X-ERP-User-ID" value="#upstream_erp_user_id#">
				<cfhttpparam type="header" name="X-ERP-Company-ID" value="#upstream_erp_company_id#">
				<cfhttpparam type="header" name="X-ERP-Company-FN" value="#upstream_erp_company_fn#">
				<cfhttpparam type="header" name="X-ERP-Lang" value="#upstream_erp_lang#">
			</cfhttp>
			<cfoutput>#httpResponse.fileContent#</cfoutput>
		<cfcatch>
			<cfoutput>{"items":[],"error":"#JSStringFormat(cfcatch.message)#"}</cfoutput>
		</cfcatch>
		</cftry>
	</cfcase>

	<!--- ═══════════════════════════════════════════════════════════════════════
	     DEMAND: copy summary text for buyer
	     ═══════════════════════════════════════════════════════════════════════ --->
	<cfcase value="demand_summary_text">
		<cfparam name="forecast_id" type="numeric" default="0">
		<cfset queryParams = "masterfn=#URLEncodedFormat(upstream_erp_company_id)#&companyfn=#URLEncodedFormat(upstream_erp_company_fn)#">
		<cfif forecast_id GT 0>
			<cfset queryParams = queryParams & "&forecast_id=#forecast_id#">
		</cfif>
		<cftry>
			<cfhttp url="#analytics_api_url#/api/analytics/demand/summary-text?#queryParams#" method="GET" result="httpResponse" timeout="15">
				<cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
				<cfhttpparam type="header" name="Cookie" value="#upstream_cookie_header#">
				<cfhttpparam type="header" name="X-ERP-User-ID" value="#upstream_erp_user_id#">
				<cfhttpparam type="header" name="X-ERP-Company-ID" value="#upstream_erp_company_id#">
				<cfhttpparam type="header" name="X-ERP-Company-FN" value="#upstream_erp_company_fn#">
				<cfhttpparam type="header" name="X-ERP-Lang" value="#upstream_erp_lang#">
			</cfhttp>
			<cfoutput>#httpResponse.fileContent#</cfoutput>
		<cfcatch>
			<cfoutput>{"text":"Failed to generate summary","error":"#JSStringFormat(cfcatch.message)#"}</cfoutput>
		</cfcatch>
		</cftry>
	</cfcase>

	<!--- ═══════════════════════════════════════════════════════════════════════
	     DEMO READINESS: pre-demo health check
	     ═══════════════════════════════════════════════════════════════════════ --->
	<cfcase value="demo_readiness">
		<cfset queryParams = "masterfn=#URLEncodedFormat(upstream_erp_company_id)#&companyfn=#URLEncodedFormat(upstream_erp_company_fn)#">
		<cftry>
			<cfhttp url="#analytics_api_url#/admin/demo-readiness?#queryParams#" method="GET" result="httpResponse" timeout="60">
				<cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
				<cfhttpparam type="header" name="Cookie" value="#upstream_cookie_header#">
				<cfhttpparam type="header" name="X-ERP-User-ID" value="#upstream_erp_user_id#">
				<cfhttpparam type="header" name="X-ERP-Company-ID" value="#upstream_erp_company_id#">
				<cfhttpparam type="header" name="X-ERP-Company-FN" value="#upstream_erp_company_fn#">
				<cfhttpparam type="header" name="X-ERP-Lang" value="#upstream_erp_lang#">
			</cfhttp>
			<cfoutput>#httpResponse.fileContent#</cfoutput>
		<cfcatch>
			<cfoutput>{"error":"Demo readiness check failed","detail":"#JSStringFormat(cfcatch.message)#"}</cfoutput>
		</cfcatch>
		</cftry>
	</cfcase>

	<cfdefaultcase>
		<cfoutput>{"error":"Unknown action","action":"#JSStringFormat(Trim(action))#"}</cfoutput>
	</cfdefaultcase>
</cfswitch>
