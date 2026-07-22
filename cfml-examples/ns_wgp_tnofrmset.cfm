<!--- ##############################################################################################################
Version 5.0.1
File	ns_wgp_tnofrmset.cfm
SNO	DATE 		BY 		LOG
001	20150812	harley		File Created based on existing file - Cross Browser Version
002	20160216	sonny		add min-width for mobile
003	20160523	csl		newui
004	20160530	harley		new menu colours for newui
005	20160531	harley		TNO Menu colour reversal
006	20160610	Saravanan	changes for enable_ineterco_datasource_yn
007	20160628	harley		Set Max Menu height to be 50% if menu length > 20.
008	20160921	csl		minor style chg
009	20161014	csl		minor style chg
010	20161110	Aaron		Display simplified menu on non-compat
011	20161114	Aaron		Fixed app menu height
012	20161125	Saravanan	changes to freeze pane
013	20170428	Ngoc Quan	New layout v6(style h)
014	20170504	Ngoc Quan	Fix menu style
015	20170607	Saravanan	changes for entity switching cookie issue
016	20170801	csl		force to use latest style h if cookie.cooksqlfilename NEQ cookie.cooksql_mainsync (YM)
017	20170821	csl		adjust UI
018	20180309	Saravanan	changes for simplified menu
019	20181214	Nick		50 >> 90
020	20190103	Saravanan			use inc_chk_portal_user to set poralstr
021	20210325	Saravanan			donot force sytle to 'H' redwoon
022	20210611	Aaron		Support Ticket for Style UI G
023	20240820	NamLee		add pop-up Privacy Notice for TNO Systems (TSK-28593)
024	20240822	NamLee		revert to version 20210611
025	20240829	Jasen		Add "folder_style_i"
026.	20240903	Jasen		Add "style_frmset.css"
027.	20240911	Jasen		Add "tno_sub_menu"
028.	20240912	Jasen		Amend "tno_sub_menu"
029.	20240913	Jasen		Amend "tno_sub_menu"
030.	20240913	Jasen		Amend "tno_sub_menu"
031.	20240916	Jasen		Amend "tno_sub_menu"
032.	20240918	Jasen		Add "icn_sub_menu_header_url" and amend "tno_sub_menu" style for mdual
033.	20241022	DingYong	add setPageTitle
034.	20241125	Lopper		add samesite=strict to cookies for TNO
035.	20250313	Jasen		Add StyleShtUIVersion(j)
036.	20250314	Jasen		Amend StyleShtUIVersion(j)
037.	20250317 	Yan		add fontawesome-pro-6.7.2-web for StyleShtUIVersion(j)
038.	20250318 	Yan		remove fontawesome-pro-6.7.2-web for StyleShtUIVersion(j)
039.	20250321	Jasen		Amend StyleShtUIVersion(j)
040.	20250520	Jasen		Include "inc_chk_user_server_connection.cfm"
041. 	20250909 	Yan 		add instantchat_drill_in_yn
042.	20240722	Lopper		added ai assistant button to the bottom right of the screen
################################################################################################################ --->
<!--- 	Notes:
	File created based on methods defined in existing ns_wgp_tnofrmset.cfm.
	Existing filename appended with _ie8 and is redirected to for backwards compatibility.
--->
<cfoutput><!--- LLCFStart --->
	<!--- Initialisation of Values --->
	<cfparam name="fldrgraphic" default="graphics_main_all">
	<cfparam name="bmm_ck_applic" default="wapplic_tnocentral">
	<cfparam name="bmm_ck_modules" default="wmodules_mainlogin">
	<cfparam name="fromsrc" default="">
	<cfparam name="mobile_app" default="n">
	<cfparam name="vle_alert_yn" default="n">
	<cfparam name="vle_alert_entity_yn" default="n">
	<cfparam name="instantchat_drill_in_yn" default="n">
	<cfif fromsrc EQ "welcome">
		<cfquery datasource="#cookie.cooksql_mainsync#_active" name="qs_user_sys">
			select 	cpa_idunique, clientfilename, welcomeuser, language, var_50_001 as fyear,var_50_002, TAG_OTHERS01
			from 	sys_mas_pass
			where 	userloginid='#cookie.cookuserloginid#'
					and masterfn= <cfqueryparam  value="#cookie.cookmfnunique#"  cfsqltype="cf_sql_varchar">
		</cfquery>
		<cfset bmm_userpagelogin = qs_user_sys.welcomeuser>
	<cfelse>
		<cfset bmm_userpagelogin = "">
	</cfif>

	<cfif not isdefined('L1')><cfset L1="0"></cfif>
	<cfif not isdefined('L2')><cfset L2="0"></cfif>
	<cfif not isdefined('ns_')><cfset ns_='ns_'></cfif>
	<cfif cookuserloginid is 'm8'>
		<cfquery datasource="#cookie.cooksql_mainsync#_active" name="qy_ns">
			select 	masterset_yn04 from sys_sec_mfn
			where 	masterfn = '#cookie.cookmfnunique#' and tag_table_usage = 'mfn'
		</cfquery>
		<cfcookie encodevalue="true" httponly="yes" samesite="strict" name="cookentproj" value="ns_#Mid(qy_ns.masterset_yn04,6,3)#">
	</cfif>
	<cfset singleScreenHeader = "">
	<cfif mid(cookie.cookentproj,4,1) is "y"><cfset singleScreenHeader = "1"></cfif>
	<cfif mid(cookie.cookmultipurpose,3,2) is "E2">
		<cfset edtn_tnomenuheight = "8">
		<cfset edtn_tnomenufile = "ns_wgp_tnotnomenuNull">
	<cfelse>
		<cfset edtn_tnomenuheight = "33">
		<cfset edtn_tnomenufile = "ns_wgp_tnotnomenu">
	</cfif>
	<cfinclude template="inc_chk_portal_user.cfm">
	
	
	<cfinclude template="inc_chk_simplified_menu.cfm">
	<cfif simplified_menu is 'y'>
		<cfset frameset_col_1_width = '75'>
		<cfset frameset_col_2_width = '25'>
		<cfset frameset_src = 'ns_wgp_tnotnomenu2'>
	<cfelse>
		<cfset frameset_col_1_width = edtn_tnomenuheight>
		<cfset frameset_col_2_width = '67'>
		<cfset frameset_src = edtn_tnomenufile>
	</cfif>
	<cfif instantchat_drill_in_yn EQ 'y'>
		<cfset tnoapp_src = "ns_wgp_tnoframeset.cfm?L1=#L1#&L2=#L2#&ns_=#ns_##portalstr#&bmm_ck_applic=#bmm_ck_applic#&bmm_ck_modules=#bmm_ck_modules#&fromsrc=#fromsrc#&mobile_app=#mobile_app#&instantchat_drill_in_yn=y&uniquenum_pri=#uniquenum_pri#&docnum=#docnum#">
	<cfelse>
		<cfset tnoapp_src = "ns_wgp_tnoframeset.cfm?L1=#L1#&L2=#L2#&ns_=#ns_##portalstr#&bmm_ck_applic=#bmm_ck_applic#&bmm_ck_modules=#bmm_ck_modules#&fromsrc=#fromsrc#&mobile_app=#mobile_app#">
	</cfif>
	<cfif cookie.cookuserloginid neq 'm8'>
		<cfif bmm_userpagelogin is "sts">
			<cfquery name="lnksPm" datasource="#cookie.cooksql_mainsync#_active">
				select 	TAG_NNNN_YN02, TAG_NNNN_YN03,TAG_NNNN_YN04
				from 	sys_user_access
				where 	TAG_OTHERS01 like 'EsTsPrSt' and uniquenum_pri =
						(select UNIQUENUM_PRI from sys_mas_pass where userloginid = '#cookie.cookuserloginid#' and TAG_OTHERS01= 'ns_'
						and masterfn=<cfqueryparam  value="#cookie.cookmfnunique#"  cfsqltype="cf_sql_varchar">)
			</cfquery>
			<cfif lnksPm.RecordCount eq 1>
				<cfset tnoapp_src = "ns_wgp_tnoframeset.cfm?L1=6&L2=2&L3=2&L4=1&L5=0&Fk=EsTsPrSt&tpMn=#lnksPm.TAG_NNNN_YN02##lnksPm.TAG_NNNN_YN03##lnksPm.TAG_NNNN_YN04#&ns_=#ns_##portalstr#&bmm_ck_applic=#bmm_ck_applic#&bmm_ck_modules=#bmm_ck_modules#&fromsrc=#fromsrc#&mobile_app=#mobile_app#">
			</cfif>
		</cfif>
	</cfif>
	<cfset tno_topmenu_link = "#frameset_src#.cfm?vle_alert_yn=#vle_alert_yn#&vle_alert_entity_yn=#vle_alert_entity_yn#&L1=#L1#&L2=#L2#&ns_=#ns_##portalstr#&bmm_ck_applic=#bmm_ck_applic#&bmm_ck_modules=#bmm_ck_modules#&fromsrc=#fromsrc#&mobile_app=#mobile_app#">
	<!--- Get Version Layout --->
	<cfinclude template="sym_meta_lang_a.cfm">
	<cfparam name="StyleShtUIVersion" default="">
	<cfif StyleShtUIVersion EQ "b" or StyleShtUIVersion EQ "B">
		<cfset bm_stylefolder = "folder_style_b">
		<cfset bm_foldergp = "#fldrgraphic#">
	<cfelseif StyleShtUIVersion EQ "c" or StyleShtUIVersion EQ "C">
		<cfset bm_stylefolder = "folder_style_c">
		<cfset bm_foldergp = "#fldrgraphic#">
	<cfelseif StyleShtUIVersion EQ "d" or StyleShtUIVersion EQ "D">
			<cfset bm_stylefolder = "folder_style_d">
			<cfset bm_foldergp = "#fldrgraphic#">
	<cfelseif StyleShtUIVersion EQ "e" or StyleShtUIVersion EQ "E">
			<cfset bm_stylefolder = "folder_style_e">
			<cfset bm_foldergp = "#fldrgraphic#">
	<cfelseif StyleShtUIVersion EQ "f" or StyleShtUIVersion EQ "F">
			<cfset bm_stylefolder = "folder_style_f">
			<cfset bm_foldergp = "#fldrgraphic#">
	<cfelseif StyleShtUIVersion EQ "g" or StyleShtUIVersion EQ "G">
			<cfset bm_stylefolder = "folder_style_g">
			<cfset bm_foldergp = "#fldrgraphic#">
	<cfelseif StyleShtUIVersion EQ "h" or StyleShtUIVersion EQ "H">
			<cfset bm_stylefolder = "folder_style_h">
			<cfset bm_foldergp = "#fldrgraphic#">
	<cfelseif StyleShtUIVersion EQ "i" or StyleShtUIVersion EQ "I">
			<cfset bm_stylefolder = "folder_style_i">
			<cfset bm_foldergp = "#fldrgraphic#">
	<cfelseif StyleShtUIVersion EQ "j" or StyleShtUIVersion EQ "J">
		<cfset bm_stylefolder = "folder_style_j">
		<cfset bm_foldergp = "#fldrgraphic#">
	<cfelse>
		<cfset bm_stylefolder = "folder_style">
		<cfset bm_foldergp = "#fldrgraphic#">
	</cfif>



	<cfparam name="user_uiversion" default="">
	<cfset user_uiversion = mid(cookie.cookmultipurpose,6,1)>

	<!--- CSL 20170801 Force to use new UI h if below 
	<cfif cookie.cooksqlfilename NEQ cookie.cooksql_mainsync>
		<cfset bm_stylefolder = "folder_style_h">
		<cfset user_uiversion = "h">
	</cfif>--->
	<cfinclude template="inc_chk_simplified_menu.cfm">
	
	<cfif listContains(cgi.server_name, "globe3cloud", ".") GT 0 AND FileExists("inc_chk_user_server_connection.cfm")>
		<cfinclude template="inc_chk_user_server_connection.cfm">
	</cfif>
	<!--- CSL 20170501 REMOVE USER SETTING FOR VERSION
	<cfif user_uiversion EQ "g" or user_uiversion EQ "G">
		<cfset bm_stylefolder = "folder_style_g">
		<cfset bm_foldergp = "#fldrgraphic#">
	<cfelseif user_uiversion EQ "h" or user_uiversion EQ "H">
		<cfset bm_stylefolder = "folder_style_h">
		<cfset bm_foldergp = "#fldrgraphic#">
	</cfif>	--->
	<!--- End Get Version Layout --->
	<!doctype html>
	<!--[if lt IE 7 ]><html class="ie6"><![endif]-->
	<!--[if IE 7 ]><html class="ie7"><![endif]-->
	<!--[if IE 8 ]><html class="ie8"><![endif]-->
	<!--[if IE 9 ]><html class="ie9"><![endif]-->
	<!--[if (gt IE 9)|!(IE)]><!--> <html class=""> <!--<![endif]-->
		<head>
			<meta name="generator">
			<script language="JavaScript" src="../../folder_jquery/jquery.min.js"></script>
			<script type="text/Javascript">
				$(window).focus(function() {
					checkinterco();
				});
				if ($('html').is('.ie6, .ie7, .ie8, .ie9')) {
					window.location = window.location.href.replace('ns_wgp_tnofrmset.cfm', 'ns_wgp_tnofrmset_ie8.cfm');
				}
				else
				{
					<cfif simplified_menu is 'y'>
						window.location = window.location.href.replace('ns_wgp_tnofrmset.cfm', 'ns_wgp_tnofrmset_ie8.cfm');
					</cfif>
				}
				function checkinterco()
				{
					document.all.frmProcessInterco.src= "inn_chk_interco_prog.cfm"
				}
			</script>
			<title><cfinclude template="inc_html_title.cfm"></title>
			<link href="../../folder_graphics/#fldrgraphic#/favicon.ico" rel="shortcut icon"  type="image/x-icon"/>
			<cfif bm_stylefolder EQ "folder_style_h">
				<cfset vle_file_topmenu = listfirst(tno_topmenu_link,'?')>
				<cfset tno_topmenu_link = replace(tno_topmenu_link,"#vle_file_topmenu#","ns_wgp_tnotnomenu_v6.cfm","ALL")>
				<style>
					html {margin:0;padding:0;background-color:##FBFDFF;height:100%;width:100%;min-width: 1140px;}
					html > body {padding:0 0 0 0;position:relative;margin:0;height: calc(100% - 47px);width:100%;overflow-y:hidden;}
					iframe.frame_tnotopmenu {width:100%;overflow:hidden;padding:0;margin:0;border:0px;<cfif simplified_menu is 'y'>height:74px;<cfelse>height:48px;</cfif>}
					iframe##frame_tnoapp {min-width:100%;overflow-x:auto;padding:0;margin:0;height:100%;border:0;}
					.tno_topmenu_mask {position:absolute;width:100%;height:100%;top:0;left:0;right:0;bottom:0;z-index:-1;}
					.tno_topmenu {position:absolute;top:0;right:0;left:0;background-color:##082b46; border-top: 0px solid ##333333; border-bottom: 0px solid ##333333; color:white; z-index:2;font-family: Century Gothic,Candara,Segoe,Segoe UI,Optima,Arial,sans-serif; padding:2;margin:0;height:38px; padding: 5px 0px;}
					.tno_topmenu table {width:100%;border-collapse:collapse;}
					.tno_topmenu table tr {height:36px;}
					.tno_topmenu table td {vertical-align:middle;font-size:11pt; letter-spacing:1px; font-family: Century Gothic;text-transform: uppercase;}
					.tno_topmenu table td.col-left {padding-left:8px;}
					.tno_topmenu table td.col-right {padding-right:4px;text-align:left;}
					.tno_topmenu table td.col-hidden {width:20%;text-align:center;}
					.tno_topmenu table td.col-hidden ul.menu {display:none}
					.tno_topmenu table td.col-hidden:hover ul.menu {display:block}
					.tno_topmenu table td ul.menu {margin:0;padding:0;}
					.tno_topmenu table td ul.menu .caret-right {float:right;height:0;width:0;border-top: 3px solid transparent;border-bottom: 3px solid transparent;border-left: 4px solid white;margin:8px 0 0 4px;display:inline-block;}
					.tno_topmenu table td ul.menu .caret-down {height:0;width:0;border-left: 3px solid transparent;border-right: 3px solid transparent;border-top: 4px solid white;display:inline-block;margin:0px 2px 2px 4px;}
					.tno_topmenu table td ul.menu > li {display:inline-block;list-style:none;margin:2px 11px 0 0;}
					.tno_topmenu table td ul.menu > li > a > i{font-size:1.4em !important}
					.tno_topmenu table td ul.menu > li.separator {margin:0px;}
					.tno_topmenu table td ul.menu > li.separator span {display:none;height:8px;width:1px;background-color:##B0C4DE;}
					.tno_topmenu table td ul.menu > li > a {text-decoration:none;display:inline-block; color:##ffffff; line-height:24px;padding:5px 10px 3px 10px;font-size: 11pt;}
					.tno_topmenu table td ul.menu > li > a:after {content: "";display: table;clear: both;}
					.tno_topmenu table td ul.menu > li.active > a {background-color:##163C79;color:##FFF;text-shadow: 1px 1px ##595959;-webkit-border-radius: 3px 3px 0px 0px;-moz-border-radius: 3px 3px 0px 0px;border-radius: 3px 3px 0px 0px;}
					.tno_topmenu table td ul.menu > li > a:hover {background-color:##F7A815;color:##FFF;text-shadow: 1px 1px ##595959;-webkit-border-radius: 3px;-moz-border-radius: 3px;border-radius: 3px;}
					.tno_topmenu table td ul.menu > li.active > a .caret-down, .tno_topmenu table td ul.menu > li > a:hover .caret-down {border-top: 4px solid white;}
					.tno_topmenu table td ul.menu > li ul {position:absolute;padding:0;margin:0;min-width:320px;display:block;display:none;background-color:##163C79;-webkit-box-shadow:  8px 8px 15px 4px rgba(99,99,99,1);-moz-box-shadow:  8px 8px 15px 4px rgba(99,99,99,1);box-shadow: 8px 8px 15px 4px rgba(99,99,99,1);}
					.tno_topmenu table td ul.menu > li ul.scroll-list {max-height:90vh;overflow-y:auto;}
					.tno_topmenu table td ul.menu > li ul li {list-style:none;letter-spacing:1px !important}
					.tno_topmenu table td ul.menu > li ul li a {display:block;text-decoration:none;padding:2px 8px 2px 12px;line-height:24px;vertical-align:middle;color:##FFF;text-shadow: 1px 1px ##393939;}
					.tno_topmenu table td ul.menu > li ul li a:after {content: "";display: table;clear: both;}
					.tno_topmenu table td ul.menu > li ul li a:hover, .tno_topmenu table td ul.menu > li ul li.active a {background-color:##F7A815; color: black; text-shadow: none; font-weight: bold;}
					.tno_topmenu table td ul.menu > li ul li.active ul li a {background-color:##154997; color:##fff; font-weight: normal;}
					.tno_topmenu table td ul.menu > li ul li.active ul li a:hover {color:black !important; background-color:##F7A815 !important; font-weight: bold;}
					.tno_topmenu table td ul.menu > li ul li ul {min-width:360px;top:0;background-color:##154997;}
					.tno_topmenu table td ul.menu > li ul li ul li a {}
					.tno_topmenu table td ul.menu > li ul li ul li a:hover, .tno_topmenu table td ul.menu > li ul li ul li.active a {background-color:##163C79;color:##FFF;}
					.tno_topmenu table td ul.menu > li ul li.toggleup a {text-align:center;display:block;vertical-align:middle;height:20px;background-color:##163C79;}
					.tno_topmenu table td ul.menu > li ul li.toggledown a {text-align:center;display:block;vertical-align:middle;height:20px;background-color:##163C79;}
					.tno_topmenu table td ul.menu > li ul li.toggleup span {position:relative;top:6px;height:0;width:0;border-left: 5px solid transparent;border-right: 5px solid transparent;border-bottom: 6px solid white;display:inline-block;}
					.tno_topmenu table td ul.menu > li ul li.toggledown span {position:relative;top:6px;height:0;width:0;border-left: 5px solid transparent;border-right: 5px solid transparent;border-top: 6px solid white;display:inline-block;}
					.tno_topmenu table td.col-right {text-align:right;}
					.tno_topmenu table td ul.menu > li ul.sublist li {text-align:left;}
					.tno_topmenu table td.col-right .ename {margin:2px 0 0 6px;line-height:26px;vertical-align:middle; display:inline-block; padding:0px 10px;font-size:15px;color:##252525;border:1px solid ##333333; font-weight: bold;}
					.tno_topmenu table td.col-right .ename-default {background-color:##f3f3f3;}
					.tno_topmenu table td.col-right .ename-custom {background-color:##6192A9;}
					.tno_topmenu table td.col-right .fyear {background-color:##DC7303;margin:2px 0 0 6px;line-height:26px;vertical-align:middle;display:inline-block;padding:0px 6px;font-size:15px;color:##FFF;border:1px solid ##945512; font-weight: bold;}
					.tno_topmenu table td.col-right .outlet {display:none;}
					.menu_btn_lbl {font-size:22px;color:white;font-family:Century Gothic;padding: 0px 10px 0px 10px;cursor:pointer;text-decoration:none;-webkit-border-radius: 4px;-moz-border-radius: 4px;border-radius: 4px;font-weight:bold;}
					ul.tno_notif {position:absolute;top:82px;right:0;margin:0;padding:0;z-index:3;}
					.tno_notif li {-webkit-border-radius: 4px;-moz-border-radius: 4px;border-radius: 4px;padding:8px 6px;min-width:240px;margin:2px 4px 0 0;background-color:##E69241;color:##FFF;font-weight:bold;font-family: Century Gothic,Candara,Segoe,Segoe UI,Optima,Arial,sans-serif;list-style:none;text-align:center;font-size:14px;vertical-align:middle;border:1px solid ##DAA520;}
					.hyperlink1e {background-color: ##de1616; color: ##f2f2f2; border: 1px solid ##555555; border-radius: 2px; padding:1px 5px 0px 7px !important; text-align: center; text-decoration: none; display: inline-block; font-size: 14pt; font-weight: bold; font-family: Calibri; CURSOR: pointer;width:40px;line-height: 19px !important;}
					.hyperlink1e:hover {letter-spacing: 1px; background-color: ##E67708; color: ##ffffff; border: 1px solid ##ffffff; border-radius: 1px; padding:1px 5px 0px 7px !important; text-align: center; text-decoration: none; display: inline-block; font-size: 14pt; font-weight: bold; font-family: Calibri; CURSOR: pointer;width:40px;line-height: 19px !important;}
					.tno_topmenu table td ul.menu > li > a.fontFor41{letter-spacing: 1px;}
					.tno_topmenu table td ul.menu > li > a.fontFor61{letter-spacing: 1px; font-size: 10pt;}
					.fontMap{font-size: 10pt !important;}

					.tno_topmenu_appl{background-color: ##163C79 !important;}
					.tno_topmenu_appl span {vertical-align:middle;display:inline-block; color:##ffffff; line-height:24px;padding:5px 10px 3px 10px;font-size: 13pt; font-weight: bold;}
					.tno_topmenu_appl li a {font-size: 10pt;line-height:16px !important;}
					.tno_topmenu_appl li a:hover {color:black !important; background-color:##F7A815 !important;}

					@media (min-width: 1600px) {
					  .tno_topmenu table td ul.menu > li > a > i{font-size:1.3em !important}
					  .tno_topmenu table td ul.menu > li > a {font-size: 12pt; font-weight:bold;letter-spacing:2px;}
					  .tno_topmenu table td ul.menu > li > a.fontFor41{letter-spacing: 1px;}
					  .tno_topmenu table td ul.menu > li > a.fontFor61{letter-spacing: 1px; font-size: 10pt;}
					  .tno_topmenu table td ul.menu > li {margin:2px 15px 0 0;}
					}
				</style>
				
				<link href="../../#bm_stylefolder#/style_scm_tno.css" rel="stylesheet">
				<link href="../../#bm_stylefolder#/font-awesome.min.css" rel="stylesheet">
				<link href="../../#bm_stylefolder#/style_e_tno.css" rel="stylesheet">
			<cfelseif bm_stylefolder EQ "folder_style_i" OR bm_stylefolder EQ "folder_style_j">
				<cfset vle_file_topmenu = listfirst(tno_topmenu_link,'?')>
				<cfset tno_topmenu_link = replace(tno_topmenu_link,"#vle_file_topmenu#","ns_wgp_tnotnomenu_v6.cfm","ALL")>
				<link href="../../#bm_stylefolder#/style_frmset.css" rel="stylesheet">
				<link href="../../#bm_stylefolder#/style_scm_tno.css" rel="stylesheet">
				<link href="../../#bm_stylefolder#/font-awesome.min.css" rel="stylesheet">
				<link href="../../#bm_stylefolder#/style_e_tno.css" rel="stylesheet">
			<cfelse>
				<style>
					html {margin:0;padding:0;background-color:##FBFDFF;height:100%;width:100%;min-width: 1140px;}
					html > body {padding:0 0 0 0;position:relative;margin:0;height: calc(100% - 32px);width:100%;overflow-y:hidden;}
					iframe.frame_tnotopmenu {width:100%;overflow:hidden;padding:0;margin:0;border:0px;margin-bottom:-4px;<cfif simplified_menu is 'y'>height:74px;<cfelse>height:32px;</cfif>}
					iframe##frame_tnoapp {min-width:100%;overflow-x:auto;padding:0;margin:0;height:100%;border:0;}
					.tno_topmenu_mask {position:absolute;width:100%;height:100%;top:0;left:0;right:0;bottom:0;z-index:-1;}
					.tno_topmenu {position:absolute;top:0;right:0;left:0;background-color:##ececec; border-top: 0px solid ##333333; border-bottom: 0px solid ##333333; color:white; z-index:2;font-family: Calibri,Candara,Segoe,Segoe UI,Optima,Arial,sans-serif; padding:2;margin:0;height:33px;}
					.tno_topmenu table {width:100%;border-collapse:collapse;}
					.tno_topmenu table tr {height:28px;}
					.tno_topmenu table td {vertical-align:middle;font-size:14px; letter-spacing:1px; font-family: Calibri;}
					.tno_topmenu table td.col-left {width:70%;padding-left:8px;}
					.tno_topmenu table td.col-right {width:30%;text-align:right;padding-right:4px;}
					.tno_topmenu table td.col-left ul.menu {margin:0;padding:0;}
					.tno_topmenu table td.col-left ul.menu .caret-right {float:right;height:0;width:0;border-top: 3px solid transparent;border-bottom: 3px solid transparent;border-left: 4px solid white;margin:8px 0 0 4px;display:inline-block;}
					.tno_topmenu table td.col-left ul.menu .caret-down {height:0;width:0;border-left: 3px solid transparent;border-right: 3px solid transparent;border-top: 4px solid black;display:inline-block;margin:0px 2px 2px 4px;}
					.tno_topmenu table td.col-left ul.menu > li {display:inline-block;list-style:none;margin:0 5px 0 0;}
					.tno_topmenu table td.col-left ul.menu > li.separator {margin:0 3px;}
					.tno_topmenu table td.col-left ul.menu > li.separator span {display:inline-block;height:8px;width:1px;background-color:##B0C4DE;}
					.tno_topmenu table td.col-left ul.menu > li > a {text-decoration:none;display:inline-block; color:##111111; line-height:24px;padding:0 6px;}
					.tno_topmenu table td.col-left ul.menu > li > a:after {content: "";display: table;clear: both;}
					.tno_topmenu table td.col-left ul.menu > li.active > a, .tno_topmenu table td.col-left ul.menu > li > a:hover {background-color:##163C79;color:##FFF;text-shadow: 1px 1px ##595959;}
					.tno_topmenu table td.col-left ul.menu > li.active > a .caret-down, .tno_topmenu table td.col-left ul.menu > li > a:hover .caret-down {border-top: 4px solid white;}
					.tno_topmenu table td.col-left ul.menu > li ul {position:absolute;padding:0;margin:0;min-width:268px;display:block;display:none;background-color:##163C79;-webkit-box-shadow: 4px 4px 4px 1px rgba(99,99,99,1);-moz-box-shadow: 4px 4px 4px 1px rgba(99,99,99,1);box-shadow: 8px 8px 15px 4px rgba(99,99,99,1);}
					.tno_topmenu table td.col-left ul.menu > li ul.scroll-list {max-height:50vh;overflow-y:auto;}
					.tno_topmenu table td.col-left ul.menu > li ul li {list-style:none;}
					.tno_topmenu table td.col-left ul.menu > li ul li a {display:block;text-decoration:none;padding:0 8px 0 12px;line-height:24px;vertical-align:middle;color:##FFF;text-shadow: 1px 1px ##393939;}
					.tno_topmenu table td.col-left ul.menu > li ul li a:after {content: ""; display: table; clear: both;}
					.tno_topmenu table td.col-left ul.menu > li ul li a:hover, .tno_topmenu table td.col-left ul.menu > li ul li.active a {background-color:##154997; text-shadow:none;}
					.tno_topmenu table td.col-left ul.menu > li ul li ul {min-width:228px;top:0;background-color:##154997;}
					.tno_topmenu table td.col-left ul.menu > li ul li ul li a {}
					.tno_topmenu table td.col-left ul.menu > li ul li ul li a:hover, .tno_topmenu table td.col-left ul.menu > li ul li ul li.active a {background-color:##163C79;color:##FFF;}
					.tno_topmenu table td.col-left ul.menu > li ul li.toggleup a {text-align:center;display:block;vertical-align:middle;height:20px;background-color:##163C79;}
					.tno_topmenu table td.col-left ul.menu > li ul li.toggledown a {text-align:center;display:block;vertical-align:middle;height:20px;background-color:##163C79;}
					.tno_topmenu table td.col-left ul.menu > li ul li.toggleup span {position:relative;top:6px;height:0;width:0;border-left: 5px solid transparent;border-right: 5px solid transparent;border-bottom: 6px solid white;display:inline-block;}
					.tno_topmenu table td.col-left ul.menu > li ul li.toggledown span {position:relative;top:6px;height:0;width:0;border-left: 5px solid transparent;border-right: 5px solid transparent;border-top: 6px solid white;display:inline-block;}
					.tno_topmenu table td.col-right {text-align:right;}
					.tno_topmenu table td.col-right .ename {margin:2px 0 0 6px;line-height:26px;vertical-align:middle; display:inline-block; padding:0px 10px;font-size:15px;color:##252525;border:1px solid ##333333; font-weight: bold;}
					.tno_topmenu table td.col-right .ename-default {background-color:##f3f3f3;}
					.tno_topmenu table td.col-right .ename-custom {background-color:##6192A9;}
					.tno_topmenu table td.col-right .fyear {background-color:##DC7303;margin:2px 0 0 6px;line-height:26px;vertical-align:middle;display:inline-block;padding:0px 6px;font-size:15px;color:##FFF;border:1px solid ##945512; font-weight: bold;}
					.tno_topmenu table td.col-right .outlet {display:none;}
					.menu_btn_lbl {font-size:22px;color:white;font-family:calibri;padding: 0px 10px 0px 10px;cursor:pointer;text-decoration:none;-webkit-border-radius: 4px;-moz-border-radius: 4px;border-radius: 4px;font-weight:bold;}
					ul.tno_notif {position:absolute;top:82px;right:0;margin:0;padding:0;z-index:3;}
					.tno_notif li {-webkit-border-radius: 4px;-moz-border-radius: 4px;border-radius: 4px;padding:8px 6px;min-width:240px;margin:2px 4px 0 0;background-color:##E69241;color:##FFF;font-weight:bold;font-family: Calibri,Candara,Segoe,Segoe UI,Optima,Arial,sans-serif;list-style:none;text-align:center;font-size:14px;vertical-align:middle;border:1px solid ##DAA520;}
				</style>
				<link href="../../#bm_stylefolder#/font-awesome.min.css" rel="stylesheet">
			</cfif>
		</head>
		<body>
			<iframe src="#tno_topmenu_link#" name="tnomenu" class="frame_tnotopmenu" id="frame_tnotopmenu"></iframe>
			<iframe src="#tnoapp_src#" name="tnoapp" id="frame_tnoapp"></iframe>
			<div  id="ifrmProcesswrapperGlobe3" style="display:none;position:absolute;left:0px;top:5px;width:2100px;height:1760px;z-index:999;" tabindex="-1" align="center">
				<div  class="menu_btn_lbl" style="height:200px">&nbsp;</div>
				<div id="ifrmProcesswrapperGlobe3msg" align="center" class="menu_btn_lbl" style="background:darkgreen;display:none;width:400px;position:absolute;z-index:1000;" >
				</div>
			</div>
			<input type="hidden" id="frmIntercoCookie" value="">
			<input type="hidden" id='cmpqupi' value="#cookie.cookcfnunique#">
			<cfif isdefined('dsp_ent')>
				<input type="hidden" id='oldcmpuq' value="#dsp_ent#">
			<cfelse>
				<input type="hidden" id='oldcmpuq' value="#cookie.cookcfnunique#">
			</cfif>
			<CFQUERY datasource="#cookie.cooksql_mainsync#_active" name="qs_set_co_main">select  co_name
				from set_co_main
				where companyfn=<cfqueryparam  value="#cookie.cookcfnunique#"  cfsqltype="cf_sql_varchar">
				and tag_table_usage=<cfqueryparam  value="co_main"  cfsqltype="cf_sql_varchar">
			</CFQUERY>
			<input type="hidden" id='hid_pgcompname' value="#qs_set_co_main.co_name#">

			<iframe src="" id="frmProcessGlobe3" style="display:none;position:absolute;left:50px;height:460px;top:30px;z-index:1000;" scrolling="no" frameborder="0"></iframe>
			<input type="hidden" id="frmIntercotab" value="n">
			<iframe src="" id="frmProcessInterco" style="display:none;position:absolute;left:0px;height:0px;top:0px" scrolling="no" frameborder="0"></iframe>
			
			<cfinclude template="widget_ai_assistant.cfm">

			<cfif bm_stylefolder EQ "folder_style_i" OR bm_stylefolder EQ "folder_style_j">
				<cfif cookie.cooklang NEQ cookie.cooklang2>
					<cfset vle_tno_sub_menu_min_width = 420>
					<cfset vle_tno_sub_menu_max_width = 580>
				<cfelse>
					<cfset vle_tno_sub_menu_min_width = 350>
					<cfset vle_tno_sub_menu_max_width = 480>
				</cfif>
				
				<cfif bm_stylefolder EQ "folder_style_j">
					<cfset vle_side_menu_background_color = "##e0e7f7">
					<cfset vle_side_menu_border_color = "##ddd">
				<cfelse>
					<cfset vle_side_menu_background_color = "##e0e7f7">
					<cfset vle_side_menu_border_color = "##eef2fc">
				</cfif>
				
				<div id="tno_sub_menu" class="cell_input_lay2" style="background-color: #vle_side_menu_background_color#; min-width: #vle_tno_sub_menu_min_width#px; max-width: #vle_tno_sub_menu_max_width#px; position: fixed; height: 100%; top: 144px; z-index: 999999999; left: 280px; display: none; border-radius: 10px 10px 0px 0px;" onmouseenter="subMenuActionYn('in')" onmouseleave="subMenuActionYn('out')">
					<table border="0" cellspacing="0" cellpadding="0" valign="top" width="100%">
						<tr height="42px">
							<td style="border-bottom: 1px solid #vle_side_menu_border_color#">
								<table style="background: #vle_side_menu_background_color#; height: 100%; border-radius: 10px 10px 0px 0px; padding: 0px 15px;" border="0" cellspacing="0" cellpadding="0" valign="top" width="100%">
									<tr height="42px">
										<td id="td_tno_sub_menu_sel_url" align="center">
											<i class="fa fa-list" id="icn_sub_menu_header_url" style="display: none;"></i>&nbsp;
											<span id="tno_sub_menu_sel_text" style="font-weight: bold; text-transform: uppercase; font-family: Century Gothic; letter-spacing: 2px;"></span>
										</td>
										<td width="25px" align="right" style="cursor: pointer;" onclick="document.getElementById('tno_sub_menu').style.display = 'none';">
											<i class="fa fa-close" style="color: ##166ebd;"></i>
										</td>
									</tr>
								</table>
							</td>
						</tr>
					</table>
					<div id="div_tno_sub_menu_sel_content" style="height: 80%; background: white; overflow-y: auto; overflow-x: hidden;" class="div_side_menu_scroll">
						<table border="0" cellspacing="0" cellpadding="0" valign="top" style="height: 100%; width: 100%;">
							<tr>
								<td valign="top">
									<table style="width: 100%; background: #vle_side_menu_background_color#; height: 100%; padding: 0px 15px;" border="0" cellspacing="0" cellpadding="0" valign="top">
										<tr>
											<td valign="top" id="td_tno_sub_menu_sel_content"></td>
										</tr>
									</table>
								</td>
							</tr>
						</table>
					</div>
				</div>
				
				<cfif bm_stylefolder EQ "folder_style_j">
					<cfset icn_side_menu_toggle_btn_right_color = "##166ebd">
					<cfset icn_side_menu_toggle_btn_right_hove_color = "##f3f3f3">
				<cfelse>
					<cfset icn_side_menu_toggle_btn_right_color = "##166ebd">
					<cfset icn_side_menu_toggle_btn_right_hove_color = "##e0e7f7">
				</cfif>
				
				<div style="display: none;" id="div_side_menu_toggle_btn_right" class="cls_side_menu_toggle_btn cls_side_menu_toggle_btn_right" onclick="openMainMenu(this);" onmouseenter="document.getElementById('icn_side_menu_toggle_btn_right').style.color = '#icn_side_menu_toggle_btn_right_hove_color#';" onmouseleave="document.getElementById('icn_side_menu_toggle_btn_right').style.color = '#icn_side_menu_toggle_btn_right_color#';">
					<i class="fa fa-caret-right" id="icn_side_menu_toggle_btn_right" style="color: #icn_side_menu_toggle_btn_right_color#"></i>
				</div>
				
				<input type="hidden" name="fmi_show_tno_main_menu_yn" id="fmi_show_tno_main_menu_yn" value="">
				<input type="hidden" name="fmi_show_tno_sub_menu_yn" id="fmi_show_tno_sub_menu_yn" value="">
					
				<script type="text/Javascript">
					function subMenuActionYn(action) {
						document.getElementById("fmi_show_tno_sub_menu_yn").value = action;
						
						if(action == 'out') {
							setTimeout(()=> {
								if(document.getElementById("fmi_show_tno_main_menu_yn").value != "in") {
									document.getElementById("tno_sub_menu").style.display = "none";
								}
							} ,200);
						}
					}
					
					function openMainMenu(ele) {
						ele.style.display = "none";
						tnoapp.document.all.leftbar.cols = '300,*';
					}
					
					function selectSubMenu(subMenuId) {
						if(document.getElementsByClassName("sub_menu_style_active").length > 0) {
							document.getElementsByClassName("sub_menu_style_active")[0].className = "sub_menu_style";
						}
						
						document.getElementById(subMenuId).className = "sub_menu_style_active";
					}
					function setPageTitle(vtitle){
						<cfif (access_multico_yn eq 'n' and cookie.cookuserloginid neq 'm8') or not isdefined("comain_co_code")>
							top.parent.document.title = vtitle;
						<cfelse>
							top.parent.document.title = '#comain_co_code# - '+vtitle;
						</cfif>
					}
				</script>
			</cfif>
		</body>
	</html>
</cfoutput><!--- LLCFEnd --->