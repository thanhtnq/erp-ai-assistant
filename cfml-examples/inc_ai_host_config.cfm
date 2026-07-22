<!---@ ###########################################################################################################
Version 5.0.1
File Description:
No	Modified Date	Modified By		Change Log
1.	20240722	Lopper		Creation Of File 
################################################################################################################# @--->
<cfparam name="request.ai_force_local_api" default="no">

<cfset aiHostConfigHttpHost = "">
<cfset aiHostConfigServerName = "">
<cfif structKeyExists(CGI, "HTTP_HOST")>
	<cfset aiHostConfigHttpHost = LCase(Trim(CGI.HTTP_HOST))>
</cfif>
<cfif structKeyExists(CGI, "SERVER_NAME")>
	<cfset aiHostConfigServerName = LCase(Trim(CGI.SERVER_NAME))>
</cfif>

<cfset aiHostConfigIsLocal = false>
<cfif request.ai_force_local_api EQ "yes"
	OR FindNoCase("localhost", aiHostConfigHttpHost)
	OR FindNoCase("127.0.0.1", aiHostConfigHttpHost)
	OR REFindNoCase("(^|[/:])192\.168\.", aiHostConfigHttpHost)
	OR REFindNoCase("(^|[/:])10\.", aiHostConfigHttpHost)
	OR REFindNoCase("(^|[/:])172\.(1[6-9]|2[0-9]|3[0-1])\.", aiHostConfigHttpHost)
	OR FindNoCase("localhost", aiHostConfigServerName)
	OR FindNoCase("127.0.0.1", aiHostConfigServerName)
	OR REFindNoCase("^192\.168\.", aiHostConfigServerName)
	OR REFindNoCase("^10\.", aiHostConfigServerName)
	OR REFindNoCase("^172\.(1[6-9]|2[0-9]|3[0-1])\.", aiHostConfigServerName)>
	<cfset aiHostConfigIsLocal = true>
</cfif>

<cfif aiHostConfigIsLocal>
	<cfset host_api_url = "http://localhost:8000">
	<cfset analytics_api_url = host_api_url>
	<cfset ai_api_url = host_api_url>
	<cfset skills_server_url = "http://localhost:3001">
<cfelse>
	<cfset host_api_url = "http://124.155.214.47:8297">
	<cfset analytics_api_url = host_api_url>
	<cfset ai_api_url = host_api_url>
</cfif>

<cfif aiHostConfigIsLocal>
	<cfset ai_host_config_env = "local">
<cfelse>
	<cfset ai_host_config_env = "server">
</cfif>
