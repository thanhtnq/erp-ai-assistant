<!--- ####################################################################################################################
Version	5.0.1
File 	inc_ajax_ai_admin.cfm
SN  	Date	    	By			Change
1.	20260701	Lopper			creation of new file - proxy tổng quát cho Globe3 AI Admin dashboard,
						giấu API key server-side. Khác với inc_ajax_ai_assistant.cfm (liệt kê từng
						action), file này forward chung theo "path" vì admin có 25-30+ endpoint
						và hay có thêm endpoint mới (feedback, knowledge, documents, scheduler,
						analytics...). Chỉ 2 action: admin_call (JSON) và admin_upload (multipart).
##################################################################################################################### --->
<cfparam name="action" default="">
<cfparam name="path"   default="">
<cfparam name="method" default="GET">
<cfparam name="body"   default="">

<cfinclude template="inc_syspathname.cfm">
<cfinclude template="sym_meta_lang_a.cfm">
<cfinclude template="inc_qs_set_co_main.cfm">

<!--- admin_upload trả JSON từ upstream nhưng nhận multipart nên tự set content-type riêng --->
<cfset reset_action = "admin_upload">
<cfif NOT listFind(reset_action, action)>
	<cfcontent reset="true">
	<cfcontent type="application/json">
</cfif>

<!--- Config AI API - CHỈ tồn tại ở server, không bao giờ render ra client.
     Giữ nguyên logic đọc .env như bản gốc trong admin_dashboard.cfm (đã dời vào đây). --->
<cfscript>
	ai_api_url = "http://124.155.214.47:8297";
	ai_api_key = "YJfgXD-P5WF9p3VCT1XN_ehsnB2KK_OfIYedBxz_J8M";
</cfscript>

<!--- TODO: nếu hệ thống có kiểm tra quyền admin riêng (vd query sys_sec_cip như inc_ajax_whatsapp.cfm),
     chèn check ở đây trước khi cho forward - file này hiện chưa tự giới hạn ai được gọi. --->

<cfswitch expression="#Trim(action)#">

	<!--- ══════════════════ FORWARD CHUNG CHO MỌI /admin/... (JSON) ══════════════════ --->
	<cfcase value="admin_call">
		<cfset reqPath   = Trim(path)>
		<cfset pathOnly  = ListFirst(reqPath, "?")> <!--- phần trước dấu ? để check whitelist, không tính query string --->
		<cfset httpMethod = UCase(Trim(method))>

		<!--- Whitelist: chỉ cho forward path bắt đầu bằng "admin/", chặn path traversal / absolute URL --->
		<cfset isAllowed = (Left(LCase(pathOnly), 6) EQ "admin/")
			AND (NOT Find("..", reqPath))
			AND (NOT REFindNoCase("^https?://", reqPath))>

		<cfset allowedMethods = "GET,POST,PUT,DELETE,PATCH">
		<cfif NOT listFindNoCase(allowedMethods, httpMethod)>
			<cfset httpMethod = "GET">
		</cfif>

		<cfif NOT Len(reqPath) OR NOT isAllowed>
			<cfheader statuscode="403" statustext="Forbidden">
			<cfoutput>{"error":"path not allowed"}</cfoutput>
			<cfabort>
		</cfif>

		<cftry>
			<cfhttp url="#ai_api_url#/#reqPath#" method="#httpMethod#" result="upstream" timeout="60" throwonerror="false">
				<cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
				<cfif Len(Trim(body))>
					<cfhttpparam type="header" name="Content-Type" value="application/json">
					<cfhttpparam type="body" value="#body#">
				</cfif>
			</cfhttp>

			<cfset responseType = "application/json; charset=utf-8">
			<cfif structKeyExists(upstream, "responseHeader") AND structKeyExists(upstream.responseHeader, "Content-Type")>
				<cfset responseType = upstream.responseHeader["Content-Type"]>
			</cfif>
			<cfset statusCode = 200>
			<cfif structKeyExists(upstream, "statuscode")>
				<cfset statusCode = Val(ListFirst(upstream.statuscode, " "))>
				<cfif NOT statusCode><cfset statusCode = 200></cfif>
			</cfif>

			<cfheader statuscode="#statusCode#">
			<cfcontent type="#responseType#" variable="#upstream.fileContent#" reset="true">
		<cfcatch>
			<cfheader statuscode="502" statustext="Bad Gateway">
			<cfoutput>{"error":"upstream request failed"}</cfoutput>
		</cfcatch>
		</cftry>
	</cfcase>

	<!--- ══════════════════ UPLOAD FILE (multipart) -> /admin/documents/upload ══════════════════ --->
	<cfcase value="admin_upload">
		<cfparam name="domain"         type="string" default="">
		<cfparam name="company_code"   type="string" default="">
		<cfparam name="admin_user_id"  type="string" default="">

		<cfset uploadTmpDir = GetTempDirectory()>
		<cftry>
			<cffile action="upload" filefield="file" destination="#uploadTmpDir#" nameconflict="makeunique" result="uploadResult">

			<cfhttp url="#ai_api_url#/admin/documents/upload" method="POST" result="upstream" timeout="120" throwonerror="false">
				<cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
				<cfhttpparam type="file" name="file" file="#uploadResult.serverDirectory#/#uploadResult.serverFile#" mimetype="#uploadResult.contentType#">
				<cfhttpparam type="formfield" name="domain" value="#domain#">
				<cfhttpparam type="formfield" name="company_code" value="#company_code#">
				<cfhttpparam type="formfield" name="admin_user_id" value="#admin_user_id#">
			</cfhttp>

			<cfset responseType = "application/json; charset=utf-8">
			<cfif structKeyExists(upstream, "responseHeader") AND structKeyExists(upstream.responseHeader, "Content-Type")>
				<cfset responseType = upstream.responseHeader["Content-Type"]>
			</cfif>
			<cfcontent type="#responseType#" variable="#upstream.fileContent#" reset="true">
		<cfcatch>
			<cfheader statuscode="502" statustext="Bad Gateway">
			<cfoutput>{"error":"upload failed"}</cfoutput>
		</cfcatch>
		<cffinally>
			<cfif structKeyExists(uploadResult, "serverDirectory") AND FileExists("#uploadResult.serverDirectory#/#uploadResult.serverFile#")>
				<cffile action="delete" file="#uploadResult.serverDirectory#/#uploadResult.serverFile#">
			</cfif>
		</cffinally>
		</cftry>
	</cfcase>

</cfswitch>
