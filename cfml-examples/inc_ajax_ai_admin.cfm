<!--- ####################################################################################################################
Version 5.0.1
File  inc_ajax_ai_admin.cfm
SN   Date      By      Change
1.   20260715  Lopper  local-test admin proxy, no ERP bootstrap includes
##################################################################################################################### --->
<cfparam name="action" default="">
<cfparam name="path"   default="">
<cfparam name="method" default="GET">
<cfparam name="body"   default="">

<!--- Upload actions return multipart-ish content; everything else is JSON. --->
<cfset reset_action = "admin_upload,semantic_upload">
<cfif NOT listFind(reset_action, action)>
	<cfcontent reset="true">
	<cfcontent type="application/json">
</cfif>

<cfscript>
	host_api_url = "http://localhost:8000";
	ai_api_key   = "YJfgXD-P5WF9p3VCT1XN_ehsnB2KK_OfIYedBxz_J8M";
</cfscript>
<cftry>
	<cfinclude template="inc_ai_host_config.cfm">
	<cfcatch></cfcatch>
</cftry>
<cfscript>
	ai_api_url = host_api_url;
</cfscript>

<cfswitch expression="#Trim(action)#">
	<cfcase value="admin_call">
		<cfset reqPath = Trim(path)>
		<cfset pathOnly = ListFirst(reqPath, "?")>
		<cfset httpMethod = UCase(Trim(method))>

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
			<cfcontent type="#responseType#" reset="true">
			<cfoutput>#ToString(upstream.fileContent)#</cfoutput>
		<cfcatch>
			<cfheader statuscode="502" statustext="Bad Gateway">
			<cfoutput>{"error":"upstream request failed"}</cfoutput>
		</cfcatch>
		</cftry>
	</cfcase>

	<cfcase value="admin_upload">
		<cfparam name="domain"        type="string" default="">
		<cfparam name="company_code"  type="string" default="">
		<cfparam name="admin_user_id" type="string" default="">

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
			<cfcontent type="#responseType#" reset="true">
			<cfoutput>#ToString(upstream.fileContent)#</cfoutput>
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

	<cfcase value="semantic_upload">
		<cfparam name="scope_type"    type="string" default="global">
		<cfparam name="company_code"  type="string" default="">
		<cfparam name="masterfn"      type="string" default="">
		<cfparam name="companyfn"     type="string" default="">
		<cfparam name="module"        type="string" default="">
		<cfparam name="admin_user_id" type="string" default="">

		<cfset uploadTmpDir = GetTempDirectory()>
		<cftry>
			<cffile action="upload" filefield="file" destination="#uploadTmpDir#" nameconflict="makeunique" result="uploadResult">

			<cfhttp url="#ai_api_url#/admin/semantic/upload" method="POST" result="upstream" timeout="120" throwonerror="false">
				<cfhttpparam type="header" name="X-API-Key" value="#ai_api_key#">
				<cfhttpparam type="file" name="file" file="#uploadResult.serverDirectory#/#uploadResult.serverFile#" mimetype="#uploadResult.contentType#">
				<cfhttpparam type="formfield" name="scope_type" value="#scope_type#">
				<cfhttpparam type="formfield" name="company_code" value="#company_code#">
				<cfhttpparam type="formfield" name="masterfn" value="#masterfn#">
				<cfhttpparam type="formfield" name="companyfn" value="#companyfn#">
				<cfhttpparam type="formfield" name="module" value="#module#">
				<cfhttpparam type="formfield" name="admin_user_id" value="#admin_user_id#">
				<cfif structKeyExists(uploadResult, "clientFile")>
					<cfhttpparam type="formfield" name="original_filename" value="#uploadResult.clientFile#">
				</cfif>
			</cfhttp>

			<cfset responseType = "application/json; charset=utf-8">
			<cfif structKeyExists(upstream, "responseHeader") AND structKeyExists(upstream.responseHeader, "Content-Type")>
				<cfset responseType = upstream.responseHeader["Content-Type"]>
			</cfif>
			<cfcontent type="#responseType#" reset="true">
			<cfoutput>#ToString(upstream.fileContent)#</cfoutput>
		<cfcatch>
			<cfheader statuscode="502" statustext="Bad Gateway">
			<cfoutput>{"error":"semantic upload failed"}</cfoutput>
		</cfcatch>
		<cffinally>
			<cfif structKeyExists(uploadResult, "serverDirectory") AND FileExists("#uploadResult.serverDirectory#/#uploadResult.serverFile#")>
				<cffile action="delete" file="#uploadResult.serverDirectory#/#uploadResult.serverFile#">
			</cfif>
		</cffinally>
		</cftry>
	</cfcase>
</cfswitch>
