<!--- ####################################################################################################################
Version	5.0.1
File 	inc_ajax_ai_assistant.cfm
SN  	Date	    	By			Change
1.	20260701	Lopper			creation of new file - proxy cho ERP AI Assistant, giáº¥u API key server-side
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
	local_api_url = "http://localhost:8000";
	host_api_url = "http://124.155.214.47:8297";
	ai_api_url = "http://124.155.214.47:8297";
	ai_api_key = "YJfgXD-P5WF9p3VCT1XN_ehsnB2KK_OfIYedBxz_J8M";
	skills_server_url = "http://localhost:3001";
</cfscript>
<cfset upstream_cookie_header = "cookuserloginid=#cookie.cookuserloginid#; cookmfnunique=#cookie.cookmfnunique#; cookcfnunique=#cookie.cookcfnunique#; cooklang=#cookie.cooklang#">
<cfset upstream_erp_user_id = cookie.cookuserloginid>
<cfset upstream_erp_company_id = cookie.cookmfnunique>
<cfset upstream_erp_company_fn = cookie.cookcfnunique>
<cfset upstream_erp_lang = cookie.cooklang>

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
			<cfheader name="Content-Type" value="text/event-stream; charset=utf-8">
			<cfheader name="Cache-Control" value="no-cache">
			<cfoutput>#httpResponse.fileContent#</cfoutput>
		<cfcatch>
			<cfheader name="Content-Type" value="text/event-stream; charset=utf-8">
			<cfoutput>event: done
data: {}

</cfoutput>
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

</cfswitch>





