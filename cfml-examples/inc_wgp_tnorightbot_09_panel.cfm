<!--- ###########################################################################################################
Version	5.0.1
File 	inc_wgp_tnorightbot_09_panel.cfm
SNO	DATE		BY		LOG
1.	20180911	csl		Creation of file for mdual - different layout with <BR>
2.	20180915	csl		amend style
3.	20181005	csl		amend for minilogo for demo2011mfn p11011004464072155
4.	20181017	csl		minor
5.	20181130	csl		minor
6.	20190130	Aaron		Work Flow Approval panel in desktop
7.	20190214	csl		add support email link
8.	20190511	csl		change query to cookie.cooksql_mainsync
9.	20190630	csl		staff pix upgrade
10.	20190719	csl		minor UI
11.	20191124	csl		mainsync and reportdb auto-check db size and revert if have diff
12.	20191210 	Edwin 		add cmpt_sbook, cmpt_insp, cmpt_jo for YonMing - TSK-19515 (NgacTran)
13.	20200107	csl		globe3_stop_cookie_mainsync.txt - detect if this file present, if yes stop setting mainsync cookie to slave. same for reportdb cookie. Only work for Lucee/Linux on AWS cloud.  So that Lucee admin datasource no need to manual change.
14.	20200204	csl		change location to folder triggercloud
15.	20201229	NgacTran 	fix process notification open 2 windows - JR Auto - TSK-21539
016 	20210113 	Nick 		name="frame_wflow", added
17.	20210322	Aaron		Added changes for Support Portal
18.	20210322	Aaron		Added m8 restriction for Support Portal
19.	20210527	Saravanan	reporting db for cloud db
20.	20210708	vantran		set desc_title for Approval Dashboard, Forum
21.	20210723	Aaron		Added for Support Ticket testing: hupfarrimfn, devielec1711176mfn, thyehongmfn
22.	20210812	Aaron		Support Ticket: Removed Restrictions
23.	20210901	sonny		show ip address of mainsync and reportdb
24.	20211105	oliver		empty vle_staff_code, no need to show photo
25.	20220729	Lam		add vle_mainstorefld_bs and vle_mainstorefld - TNO - TSK-24625
26.	20230419	Saravanan		changes for app_review
27.	20230911	Saravanan		changes for brand limit approval
28.	20230911	DingYong	Fix Loading issue
29.	20230913	Saravanan	 changes for brand limit approval
30.	20231017	DingYong	undo 20230911 changes(Fix Loading issue)
31.	20240411        ThanhHung       added cacheBuster for hrm_self_update for TNO (TSK-27685) 
32.	20250408	Saravanan	fix companyfn for wfappgrp
33.	20250410		Saravanan	use global condition for wfappgrp
34.	20260220		WeiJun   	Addon hide_desktop_quick_info_buttons_yn for TNO(TSK-NA)
35.	20240722	Lopper		added ai assistant button to the bottom right of the screen
################################################################################################################## --->
<cfparam name="my_privitype" default="">
<cfparam name="my_staff_unique" default="">
<cfparam name="my_admin_wflow" default="n">

<!--- 20260220 [start] hide_desktop_quick_info_buttons_yn --->
<cfset hide_desktop_quick_info_buttons_yn = "n">
<cfquery datasource="#cookie.cooksql_mainsync#_active" name="qs_hide_desktop_quick_info_buttons">
	SELECT      uniquenum_pri
	FROM        sys_sec_cip
	WHERE       tag_table_usage = 'ns_adduser_ex'
	AND         userid_cookie = <cfqueryparam value="#cookie.cookuserloginid#" cfsqltype="cf_sql_varchar">
	AND         masterfn = <cfqueryparam value="#cookie.cookmfnunique#" cfsqltype="cf_sql_varchar">
	AND         tag_deleted_yn = 'n'
	AND         privi_oth01 ILIKE '___________________y%' <!--- cbxpvoth_01_20 --->
</cfquery>
<cfif qs_hide_desktop_quick_info_buttons.recordCount GT 0>
	<cfset hide_desktop_quick_info_buttons_yn = "y">
</cfif>
<!--- 20260220 [end  ] hide_desktop_quick_info_buttons_yn --->

<cfoutput>

<style>
	.downlink   {font-size: 16pt; COLOR: ##6dabcd; padding: 2px 5px 2px 8px; background: transparent; border-radius:3px }
	.downlink:hover   {font-size: 16pt; COLOR: ##ffffff; padding: 2px 5px 2px 8px; background: ##fe910f; border-radius:3px }
	.creditctrllink   {font-size: 10pt; COLOR: ##222222; font-family:Century Gothic; letter-spacing:1px }
	.creditctrllink:hover   {font-size: 10pt; COLOR: ##222222; font-family:Century Gothic; letter-spacing:1px; text-decoration:underline }
</style>
		<cfquery datasource="#cookie.cooksql_mainsync#_active" name="qs_set_co_masterco">
			select 		idcode,uniquenum_pri,co_name,co_code, co_unique
			from 		set_co_main
			where 		masterfn = <cfqueryparam  value="#cookie.cookmfnunique#"  cfsqltype="cf_sql_varchar">
						and tag_table_usage=<cfqueryparam  value="co_main"  cfsqltype="cf_sql_varchar">
						and tag_mhgc_fn=<cfqueryparam  value="mfn"  cfsqltype="cf_sql_varchar">
		</cfquery>
		<cfset masterco_cfn = qs_set_co_masterco.co_unique>

		<table width="93%" border="0" cellspacing="0" cellpadding="0" valign="middle">
			<tr height="95">
				<td width="100%" align="top">
					<table width="100%" border="0" cellspacing="0" cellpadding="0" class="" valign="middle"  style="background:##ffffff; border-top:1px solid ##b6ddf3; border-bottom:1px solid ##b6ddf3; border-radius:0px">
						<!---<tr height="4"><td width="100%" colspan="99" class="deskwelbar"></td></tr> --->
						<tr height="3"><td></td></tr>
						<tr height="99">
							<td width="1%" align="center" valign="middle">&nbsp;&nbsp;</td>
							<cfif cookie.cookmfnunique is "demo2011mfn">
								<cfif FileExists("#syspathname_mapdrive##mainstorefld_bs#\contentstore\userlogo\#cookie.cookcfnunique#\minilogo.png")>
									<td width="76%" nowrap align="right" valign="middle" style="background-image:url(../../../#mainstorefld#/contentstore/userlogo/#set_cfn#/minilogo.png);background-repeat:no-repeat ; background-position:left;">
								<cfelse>
									<cfif FileExists("#syspathname_mapdrive##mainstorefld_bs#\contentstore\userlogo\#masterco_cfn#\minilogo.png")>
										<td width="76%" nowrap align="right" valign="middle" style="background-image:url(../../../#mainstorefld#/contentstore/userlogo/#masterco_cfn#/minilogo.png);background-repeat:no-repeat ; background-position:left;">
									<cfelse>
										<td width="76%" nowrap align="right" valign="middle" style="background-image:url(../../folder_graphics/#fldrgraphic#/sm_globe3_hori.png);background-repeat:no-repeat; background-size:40%; background-position:left;">
									</cfif>
								</cfif>
							<cfelse>
								<cfif FileExists("#syspathname_mapdrive##mainstorefld_bs#\contentstore\userlogo\#cookie.cookcfnunique#\minilogo.png")>
									<td width="76%" nowrap align="right" valign="middle" style="background-image:url(../../../#mainstorefld#/contentstore/userlogo/#set_cfn#/minilogo.png);background-repeat:no-repeat ; background-position:left;">
								<cfelse>
									<cfif FileExists("#syspathname_mapdrive##mainstorefld_bs#\contentstore\userlogo\#masterco_cfn#\minilogo.png")>
										<td width="76%" nowrap align="right" valign="middle" style="background-image:url(../../../#mainstorefld#/contentstore/userlogo/#masterco_cfn#/minilogo.png);background-repeat:no-repeat ; background-position:left;">
									<cfelse>
										<td width="76%" nowrap align="right" valign="middle" style="background-image:url(../../folder_graphics/#fldrgraphic#/sm_globe3_hori.png);background-repeat:no-repeat ; background-position:left;">
									</cfif>
								</cfif>
							</cfif>
								<cfif cookie.cooklang NEQ cookie.cooklang2>
									<cfset bmm_goodday_fontsize = "14pt">
								<cfelse>
									<cfset bmm_goodday_fontsize = "17pt">
								</cfif>
								<span style="font-family:Calibri;font-size:#bmm_goodday_fontsize#;font-weight:bold; color:##1e5085; text-shadow:1px 1px 1px ##dedede; letter-spacing:1px "><cfif set_language is 'english'>GOOD DAY</cfif> <i class="fa fa-exclamation" aria-hidden="true"></i></span> <!--- GOOD DAY --->   <br>
								<cfif len(staff_name) GT 18>
									<cfset bmm_staff_name_fontsize = "11pt">
								<cfelse>
									<cfset bmm_staff_name_fontsize = "13pt">
								</cfif>
								<span style="font-family:Calibri;font-size:#bmm_staff_name_fontsize#;font-weight:bold;text-transform:uppercase; color:##1e5085; text-shadow:1px 0px 1px ##dedede; letter-spacing:1px ">#staff_name# </span>	&nbsp;
							</td>
							<td width="1%" align="center" valign="middle">&nbsp;&nbsp;</td>
							<cfif linkimg is "">
								<cfset bmm_widthcolpix = "11%">
							<cfelse>
								<cfset bmm_widthcolpix = "17%">
							</cfif>
							<cfif cookie.cookmfnunique is "demo2011mfn" and cookie.cookuserloginid is "m8">
								<cfset vle_staff_code = "A101">
								<cfset linkimg = "  ../../../v50mainstore/demo2011mfn/p11011004464072155/contentstore/staffphoto/p11011004464072155/main_A101.jpg">
                                                                <cfset cacheBuster = CreateUUID()>
								<td width="#bmm_widthcolpix#" nowrap align="right" valign="middle">
									<img src ='#linkimg#?cb=#cacheBuster#' style="border:1px solid ##acacac;border-radius:50%" height="75" width="75">&nbsp;
								</td>
							<cfelse>							
								<cfif vle_staff_code neq "" and fileexists("#syspathname##vle_mainstorefld_bs#\contentstore\staffphoto\#vle_bmm_counique#\main_#vle_staff_code#.jpg")>
									<td width="#bmm_widthcolpix#" nowrap align="right" valign="middle">
                                                                                <cfset cacheBuster = CreateUUID()>
										<cfif fileexists("#syspathname##vle_mainstorefld_bs#\contentstore\staffphoto\#vle_bmm_counique#\main_#vle_staff_code#.jpg")>
											<img src ='#linkimg#?cb=#cacheBuster#' style="border:1px solid ##acacac;border-radius:50%" height="75" width="75">&nbsp;
										<cfelse>
										</cfif>
									</td>
								<cfelse>
									<td width="7%" nowrap align="center" valign="middle" style="font-size:25pt; color:##5692bb">
										<i class="fa fa-smile-o" aria-hidden="true"></i>
									</td>
								</cfif>
							</cfif>
							<td width="3%" align="center" valign="middle">&nbsp;&nbsp;</td>
						</tr>

					</table>
					<br><br>
					<cfflush>
					<table width="100%" border="0" cellspacing="0" cellpadding="0" class="" valign="middle" style="background:##ffffff">
						<tr height="1"><td></td></tr>
					</table>
					<cfparam name="display_dual_lang_yn" default= "n">
					<cfif display_dual_lang_yn EQ 'y'>
						<cfset bmm_panelhgt = "55">
					<cfelse>
						<cfset bmm_panelhgt = "55">
					</cfif>

					<table width="100%" border="0" cellspacing="0" cellpadding="0">
						<tr height="25">
							<td width="1%" align="center" valign="middle"></td>
							<td width="39%" align="left" colspan="">
									<span style="padding:3px 8px 3px 0px; font-family:Century Gothic; font-size:20pt; font-weight:bold; background:##ffffff; color:##0c427f; letter-spacing:5px; border:0px solid ##1791d6; border-radius:4px"> &nbsp;<span style="font-size:20pt; font-family:Calibri">FY</span>#cookie.cookfyearnow#&nbsp; </span>

							</td>
							<td width="*" align="right" colspan="">
									<a href="mailto:support@globe3.com" style="font-size:11pt; color:##537ca0; font-weight:normal; text-decoration:none; letter-spacing:1px">
										<i class="fa fa-envelope-o" aria-hidden="true"></i> support@globe3.com
									</a>
									<br/><br/>
									<a href="javascript:void(0)" onclick="window.open('inc_support_ticket.cfm')" style="font-size:11pt; color:##537ca0; font-weight:normal; text-decoration:none; letter-spacing:1px">
										<i class="fa fa-ticket" aria-hidden="true"></i> <cfif set_language is 'english'>Support Ticket</cfif>
									</a>
							</td>
							<td width="2%" align="center" valign="middle">&nbsp;

							</td>
						</tr>
						<tr height="22"><td></td></tr>
					</table>



					<table width="100%" border="0" cellspacing="0" cellpadding="0" class="butnlink3b" valign="middle" style="<cfif hide_desktop_quick_info_buttons_yn EQ 'y'>display:none;</cfif>">
						<tr>
							<td width="100%">
								<!--- Approval --->
								<cfset desc_title = Tlt("<cfif set_language is 'english'>Approval Dashboard</cfif>")>
								<table width="100%" border="0" cellspacing="0" cellpadding="0" class="butnlink3c bttRight" valign="middle" id="header_dkpan_appr">
									<tr height="#bmm_panelhgt#">
										<td width="82" align="center" valign="middle" style="border-bottom:0px solid ##b6ddf3">
										<a style='cursor:pointer' onclick="setLinkUrl('fr_mgmtconsole_topmain.cfm?fromdemo=y&fromlink=wflowconsole&fromtype=#fromtype#&#nsQ#','topmain','#desc_title#')" href="javascript:void(0);">
												<span style="color:##0a65b6;font-size:27pt;cursor:pointer; text-shadow:1px 1px ##efefef"><i class="fa fa-briefcase" aria-hidden="true"></i></span>
										</a>
										</td>
										<td width="77%" align="left" style="text-transform:uppercase;border-bottom:1px solid ##b6ddf3;cursor:pointer"
											onclick="setLinkUrl('fr_mgmtconsole_topmain.cfm?fromdemo=y&fromlink=wflowconsole&fromtype=#fromtype#&#nsQ#','topmain','#desc_title#')">
											<a style='cursor:pointer' onclick="setLinkUrl('fr_mgmtconsole_topmain.cfm?fromdemo=y&fromlink=wflowconsole&fromtype=#fromtype#&#nsQ#','topmain','#desc_title#')"
												href="javascript:void(0);">
												<span style="font-size:12pt; font-family:Century Gothic; text-shadow:1px 1px ##efefef"><cfif set_language is 'english'>APPROVAL DASHBOARD</cfif></span>

											</a>
											<cfif show_blinkicon_yn EQ "y">
												<img src ='../../folder_graphics/#fldrgraphic#/alert_blink.gif' />
											<cfelse>
												&nbsp;
											</cfif>
										</td>
										<td width="5%" align="right" valign="middle" style="border-bottom:1px solid ##b6ddf3;padding-right:1px" onclick="toggleWFlowApp()">
											<span class="downlink"><i class="fa fa-angle-down" aria-hidden="true"></i></span>
										</td>
										<td width="5%" align="center" valign="middle" style="border-bottom:1px solid ##b6ddf3;padding-right:1px">&nbsp;

										</td>
										<td width="*">&nbsp;</td>
									</tr>
								</table>

								<div id="div_wflow_app" style="display: none;">
									<div id="div_wflow_app_rows">
										<cfinclude template="inc_ajax_wflow_app_panel.cfm">
									</div>

									<cfquery datasource="#cookie.cooksql_mainsync#_active" name="qs_entity">
										SELECT  	uniquenum_pri, co_name
										FROM 		set_co_main
										WHERE 		masterfn = '#cookie.cookmfnunique#'
													AND tag_table_usage='co_main'
													AND tag_active_yn='y'
													AND uniquenum_pri != '#cookie.cookcfnunique#'
										ORDER BY	date_lastupdate, idcode
									</cfquery>
									<cfloop query="qs_entity">
										<CFQUERY datasource="#cookie.cooksql_mainsync#_active" name="qs_result">
											select 			uniquenum_pri
											from 			sys_vactivity_data
											where 	 		(
																companyfn=<cfqueryparam  value="#qs_entity.uniquenum_pri#"  cfsqltype="cf_sql_varchar">
																OR
																(
																	wflow_function = 'asset' and masterfn = <cfqueryparam  value="#cookie.cookmfnunique#"  cfsqltype="cf_sql_varchar">
																)
															)
															and tag_table_usage='wflow'
															and wflow_data_activenow = 'y' and wflow_data_done = 'n' and tag_void_yn = <cfqueryparam  value="n"  cfsqltype="cf_sql_varchar">
															and (
																staff_unique = '#my_staff_unique#' <cfif my_privitype neq ''> or (wflow_sysrole = '#my_privitype#' and <cfif left(cookie.cooksql_mainsync,3) eq 'ora'> <cfif my_privitype neq ''> nvl(wflow_sysrole,' ') <> ' ' </cfif><cfelse>wflow_sysrole <> ''</cfif> ) </cfif> <cfif my_admin_wflow eq "y"> or staff_unique = 'sysadmin'</cfif>
																or staff_unique in
																(
																	Select m.acctnumcfnunique
																	from 		set_codes_main m inner join set_codes_data d
																	on		m.uniquenum_pri = d.uniquenum_pri
																	and		m.tag_table_usage = m.tag_table_usage
																	and		d.tag_global01_yn = 'y'
																	where	<cfinclude template="inc_get_wfappgrp_qry.cfm">
																	and 		m.tag_table_usage='wfappgrp'
																	and d.var_25_001 = '#my_staff_unique#'
																	and m.tag_active_yn = 'y'
																)
															)
															and (wflow_status = 'cir')
											order by		wflow_function,date_trans,dnum_auto
										</CFQUERY>
										<cfset qs_result_list = QuotedValueList(qs_result.uniquenum_pri)>
										<CFQUERY datasource="#cookie.cooksql_mainsync#_active" name="qs_result2">
											select 			uniquenum_pri
											from 			sys_vactivity_data
											where 	 		(
																companyfn=<cfqueryparam  value="#qs_entity.uniquenum_pri#"  cfsqltype="cf_sql_varchar">
																OR
																(
																	wflow_function = 'asset' and masterfn = <cfqueryparam  value="#cookie.cookmfnunique#"  cfsqltype="cf_sql_varchar">
																)
															)
															and tag_table_usage='wflow'
															and wflow_data_activenow = 'y' and wflow_data_done = 'n' and tag_void_yn = <cfqueryparam  value="n"  cfsqltype="cf_sql_varchar">
															and staff_altn_unique = '#my_staff_unique#' and staff_altn_unique <> ''
															and (
																(WFLOW_FUNCTION not in ('EsLmPrLa','exp_clm'))
																or
																(staff_altn_unique <> '' and WFLOW_FUNCTION in ('EsLmPrLa','exp_clm'))
															)
															and (wflow_status = 'cir')
															<cfif qs_result_list neq ''>
																AND CASE WHEN WFLOW_FUNCTION = 'EsLmPrLa' THEN uniquenum_pri not in (#PreserveSingleQuotes(qs_result_list)#) ELSE 1 = 1 END
															</cfif>
											order by		wflow_function,date_trans,dnum_auto
										</CFQUERY>

										<cfset records_count = qs_result.recordcount + qs_result2.recordcount>
										<cfif records_count GT 0>
											<div style="font-family: Century Gothic; font-size:10.5pt; letter-spacing:1px; text-align: left; text-transform: uppercase; padding:2px; margin-bottom: 3px; border-radius:0px; border-top: solid 0px ##dedede; background-color: ##ffffff; color: ##0a2c61; cursor: pointer;" onclick="changeEntity('#qs_entity.uniquenum_pri#')">
												&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
												<span style="color:##147be8; font-size:13pt"><i class="fa fa-chevron-circle-right" aria-hidden="true"></i></span>&nbsp; #qs_entity.co_name# <span style="font-size:8pt; font-weight:normal">(#records_count# NOS)</span>
											</div>
										</cfif>
									</cfloop>
								</div>
								<cfinclude template="inc_approval_review_link.cfm">
								<!--- CREDIT CONTROL --->
								<cfif show_credit_control_alert_frame_yn EQ "y">
									<cfset show_blinkicon_credit_control_yn = "n">
									<cfset bmm_bgcolor_ccm = "##0F905D">
									<cfif cnt_chk_check GT 0>
										<cfset show_blinkicon_credit_control_yn = "y">
										<cfset bmm_bgcolor_ccm = "##d21a1a">
									</cfif>
									<table width="100%" border="0" cellspacing="0" cellpadding="0" class="butnlink3c bttRight" valign="middle" id="header_dkpan_creditcontrol">
										<tr height="#bmm_panelhgt#">
											<td width="82" align="center" valign="middle" style="border-bottom:0px solid ##b6ddf3">
												<span style="color:#bmm_bgcolor_ccm#;font-size:23pt;cursor:pointer"><i class="fa fa-credit-card-alt trigger02" aria-hidden="true"></i></span>
											</td>
											<td width="77%" align="left" style="text-transform:uppercase;border-bottom:1px solid ##b6ddf3;cursor:pointer"
												class="trigger02">
												<a class="trigger02" style='cursor:pointer' name="alert_trigger02"
													href="javascript:void(0);">
													<span style="font-size:12pt; font-family:Century Gothic; text-shadow:1px 1px ##efefef"><cfif set_language is 'english'>CREDIT CONTROL</cfif></span>

												</a>

												<cfif show_blinkicon_credit_control_yn EQ "y">
													<img src ='../../folder_graphics/#fldrgraphic#/alert_blink.gif' />
												<cfelse>
													&nbsp;
												</cfif>
												<cfif show_star_yn EQ "y">
													<i id="star_flicker" style="color: ##cc190d;" class="fa fa-star"></i>
													<script type="text/javascript">
														$(function ()
														{
																flicker();
																function flicker (){
																	$('##star_flicker').fadeIn(650, function ()
																	{
																			$('##star_flicker').fadeOut(650, function (){
																				setTimeout(flicker, 650);
																			});
																	});
																}
														});

													</script>
												</cfif>
											</td>
											<td width="5%" align="right" valign="middle" style="border-bottom:1px solid ##b6ddf3;padding-right:1px" onclick="toggleCreditControl()">
												<span class="downlink"><i class="fa fa-angle-down" aria-hidden="true"></i></span>
											</td>
											<td width="5%" align="center" valign="middle" style="border-bottom:1px solid ##b6ddf3;padding-right:1px">&nbsp;

											</td>
											<td width="*">&nbsp;</td>
										</tr>
									</table>
								</cfif>
								<div>
									<cfset crc_trans_list_full = "sal_quo,sal_soe,stk_do,sal_inv,pur_pr,pur_po,lea_order,veh_sbook,veh_inspct,veh_vjo,cmpt_sbook,cmpt_insp,cmpt_jo">
									<cfset crc_trans_list_with_access = "">
									<cfloop index="fromtrans" list="#crc_trans_list_full#">
										<cfset alert_yn = "n">
										<cfset fromsegm = "crc_admin">
										<cfinclude template='inc_chk_access_right.cfm'>
										<cfif gotAccess is "y" and accessMode is "F">
											<cfset crc_trans_list_with_access = listappend(crc_trans_list_with_access, "#fromtrans#")>
										</cfif>
									</cfloop>

									<cfparam name="vle_crc_companyfn" default="#cookie.cookcfnunique#">
									<cfquery datasource="#cookie.cooksql_mainsync#_active" name="qs_set_co_main_crc">
										select 	tag_crc_trans_yn
										from 	set_co_main
										where 	companyfn=<cfqueryparam  value="#vle_crc_companyfn#"  cfsqltype="cf_sql_varchar">
											and tag_table_usage = <cfqueryparam  value="co_main"  cfsqltype="cf_sql_varchar">
									</cfquery>
									<cfloop query="qs_set_co_main_crc">
										<cfset tag_crc_sal_quo_yn = "#mid(tag_crc_trans_yn,1,1)#">
										<cfset tag_crc_sal_soe_yn = "#mid(tag_crc_trans_yn,2,1)#">
										<!---<cfset tag_crc_sal_soc_yn = "#mid(tag_crc_trans_yn,3,1)#">---><!---@ CSL Do not use because of multitrans insertion complexity @--->
										<cfset tag_crc_stk_do_yn = "#mid(tag_crc_trans_yn,4,1)#">
										<cfset tag_crc_sal_inv_yn = "#mid(tag_crc_trans_yn,7,1)#">
										<cfset tag_crc_pur_pr_yn = "#mid(tag_crc_trans_yn,5,1)#">
										<cfset tag_crc_pur_po_yn = "#mid(tag_crc_trans_yn,6,1)#">
										<cfset tag_crc_lea_order_yn = "#mid(tag_crc_trans_yn,8,1)#">
									</cfloop>
									<cfset go_crc = "n">
									<cfloop index="fromtrans" list="#crc_trans_list_with_access#">
										<cfif fromtrans is "sal_quo">
											<cfif tag_crc_sal_quo_yn is "y"><cfset go_crc = "y"><cfelse><cfset crc_trans_list_with_access = listdeleteat(crc_trans_list_with_access, listfind(crc_trans_list_with_access,fromtrans))></cfif>
										</cfif>
										<cfif (fromtrans is "sal_soe" or fromtrans is "sal_soc")>
											<cfif tag_crc_sal_soe_yn is "y"><cfset go_crc = "y"><cfelse><cfset crc_trans_list_with_access = listdeleteat(crc_trans_list_with_access, listfind(crc_trans_list_with_access,fromtrans))></cfif>
										</cfif>
										<!---<cfif fromtrans is "sal_soc" and tag_crc_sal_soc_yn is "y">---><!---@ CSL Do not use because of multitrans insertion complexity @--->
											<!---<cfset go_crc = "y">--->
										<!---</cfif>--->
										<cfif fromtrans is "stk_do">
											<cfif tag_crc_stk_do_yn is "y"><cfset go_crc = "y"><cfelse><cfset crc_trans_list_with_access = listdeleteat(crc_trans_list_with_access, listfind(crc_trans_list_with_access,fromtrans))></cfif>
										</cfif>
										<cfif fromtrans is "sal_inv">
											<cfif tag_crc_sal_inv_yn is "y"><cfset go_crc = "y"><cfelse><cfset crc_trans_list_with_access = listdeleteat(crc_trans_list_with_access, listfind(crc_trans_list_with_access,fromtrans))></cfif>
										</cfif>
										<cfif fromtrans is "pur_pr">
											<cfif tag_crc_pur_pr_yn is "y"><cfset go_crc = "y"><cfelse><cfset crc_trans_list_with_access = listdeleteat(crc_trans_list_with_access, listfind(crc_trans_list_with_access,fromtrans))></cfif>
										</cfif>
										<cfif (fromtrans is "pur_po" or fromtrans is "pur_poc")>
											<cfif tag_crc_pur_po_yn is "y"><cfset go_crc = "y"><cfelse><cfset crc_trans_list_with_access = listdeleteat(crc_trans_list_with_access, listfind(crc_trans_list_with_access,fromtrans))></cfif>
										</cfif>
										<cfif fromtrans is "lea_order">
											<cfif tag_crc_lea_order_yn is "y"><cfset go_crc = "y"><cfelse><cfset crc_trans_list_with_access = listdeleteat(crc_trans_list_with_access, listfind(crc_trans_list_with_access,fromtrans))></cfif>
										</cfif>
									</cfloop>

									<table id="tbl_credit_control" border="0" cellspacing="1" cellpadding="0" style="width: 100%; padding:2px 6px 2px 11px; font-family: calibri; letter-spacing: normal; text-transform: uppercase; display: none; font-weight: normal;">
										<tr style="background-color: ##ffffff; font-weight: bold;">
											<td width="10%" align="center" valign="top">

											</td>
											<td width="*" align="left" valign="top" style="font-family: Century Gothic; font-size:10pt; font-weight:bold; letter-spacing:1px">

											</td>
											<td width="20%" align="left" valign="top" style="font-family: Century Gothic; font-size:10pt; font-weight:bold; letter-spacing:1px">

											</td>
										</tr>
										<tr height="2"><td colspan="3"></td></tr>
										<cfset set_counter = 0>
										<cfloop index="fromtrans" list="#crc_trans_list_with_access#">
											<cfinclude template="inc_form_parse_fromtrans_values.cfm">
											<cfquery datasource="#cookie.cooksql_mainsync#_active" name="qs_result">
												SELECT 		count(idcode) as crc_cnt
												FROM 		#database_table#
												WHERE 		companyfn=<cfqueryparam  value="#cookie.cookcfnunique#"  cfsqltype="cf_sql_varchar">
														AND crc_rele_yn='n'
													<cfif fromtrans is "sal_soe">
														AND (tag_table_usage = 'sal_soc' or (tag_table_usage = 'sal_soe' and tag_closed02_yn = 'n'))
													<cfelseif fromtrans is "pur_po">
														AND (tag_table_usage = 'pur_poc' or (tag_table_usage = 'pur_po' and tag_closed02_yn = 'n'))
													<cfelse>
														AND tag_table_usage=<cfqueryparam  value="#fromtrans#"  cfsqltype="cf_sql_varchar">
													</cfif>

													<cfif fromtrans neq "veh_sbook" and fromtrans neq "veh_inspct" and fromtrans neq "veh_vjo" and fromtrans neq "cmpt_sbook" and fromtrans neq "cmpt_insp" and fromtrans neq "cmpt_jo">
														AND tag_closed03_yn = 'n'
													</cfif>
														AND tag_autogen_record_yn = 'n'
														AND tag_void_yn='n'
														<!---AND amount_forex <> '0'--->
													<cfif crc_release_final_only_yn is "y">
														AND (tag_wflow_app_yn = 'y' or tag_closed01_yn = 'y')
													</cfif>
											</cfquery>

											<cfif qs_result.crc_cnt NEQ 0>
											<cfset set_counter = set_counter + 1>
												<tr>
													<td align="center" valign="top" style="font-family: Century Gothic; font-size:10pt; font-weight:normal; letter-spacing:1px">
														&nbsp;&nbsp;#set_counter#.&nbsp;
													</td>
													<td align="left" valign="top" style="font-family: Century Gothic; font-size:10pt; font-weight:normal; letter-spacing:1px">
														<a style="cursor: pointer; font-weight: normal;" onclick="window.open('crc_admin_topmain.cfm?fromlink=scm_crc_admin&frommode=new&fromsegm=crc_admin&fromtrans=#fromtrans#&fromtype=full&tpMn=YYY&fromlevel=cfn','topmain')" target="_parent" title="" class="creditctrllink" onmouseover="this.style.textDecoration='underline'" onmouseout="this.style.textDecoration='none'"><cfinclude template="inc_form_parse_fromtrans_description.cfm"></a>
													</td>
													<td align="left" valign="top" style="font-family: Century Gothic; font-size:10pt; font-weight:normal; letter-spacing:1px">
														<a style="cursor: pointer; font-weight: normal;" onclick="window.open('crc_admin_topmain.cfm?fromlink=scm_crc_admin&frommode=new&fromsegm=crc_admin&fromtrans=#fromtrans#&fromtype=full&tpMn=YYY&fromlevel=cfn','topmain')" target="_parent" title="" class="creditctrllink" onmouseover="this.style.textDecoration='underline'" onmouseout="this.style.textDecoration='none'">(#qs_result.crc_cnt# <cfif set_language is 'english'>Records</cfif>)</a>
													</td>
												</tr>
												<tr height="2"><td colspan="3"></td></tr>
											</cfif>
										</cfloop>
									</table>
								</div>
								<cfinclude template="inc_brandlimit_approval_link.cfm">
								<!--- CREDIT CONTROL --->


								<!--- Alerts --->
								<table width="100%" border="0" cellspacing="0" cellpadding="0" class="butnlink3c bttRight" valign="middle" id="header_dkpan_alerts">
									<tr height="#bmm_panelhgt#">
										<td width="82" align="center" valign="middle" style="border-bottom:0px solid ##b6ddf3">
											<span style="color:##DD3D3D;font-size:28pt;cursor:pointer"><i class="fa fa-exclamation-triangle trigger fa-blink2" aria-hidden="true"></i></span>
										</td>
										<td width="77%" align="left" style="text-transform:uppercase;border-bottom:1px solid ##b6ddf3;cursor:pointer"
											class="trigger">
											<a class="trigger" style='cursor:pointer' name="alert_trigger"
												href="javascript:void(0);">
												<span style="font-size:12pt; font-family:Century Gothic; text-shadow:1px 1px ##efefef"><cfif set_language is 'english'>ALERTS</cfif></span>

											</a>
										</td>
										<td width="5%" align="right" valign="middle" style="border-bottom:1px solid ##b6ddf3;padding-right:1px">

										</td>
										<td width="5%" align="center" valign="middle" style="border-bottom:1px solid ##b6ddf3;padding-right:1px">&nbsp;

										</td>
										<td width="*">&nbsp;</td>
									</tr>
								</table>


								<!--- LATEST RECORDS --->
								<table width="100%" border="0" cellspacing="0" cellpadding="0" class="butnlink3c bttRight" valign="middle" id="header_dkpan_latest">
									<tr height="#bmm_panelhgt#">
										<td width="82" align="center" valign="middle" style="border-bottom:0px solid ##b6ddf3">
											<span style="color:##0a65b6;font-size:25pt;cursor:pointer"><i class="fa fa-database trigger01" aria-hidden="true"></i></span>
										</td>
										<td width="77%" align="left" style="text-transform:uppercase;border-bottom:1px solid ##b6ddf3;cursor:pointer"
											class="trigger01">
											<a class="trigger01" style='cursor:pointer' name="alert_trigger01"
												href="javascript:void(0);">
												<span style="font-size:12pt; font-family:Century Gothic; text-shadow:1px 1px ##efefef"><cfif set_language is 'english'>LATEST RECORDS</cfif></span>

											</a>
										</td>
										<td width="5%" align="right" valign="middle" style="border-bottom:1px solid ##b6ddf3;padding-right:1px">

										</td>
										<td width="5%" align="center" valign="middle" style="border-bottom:1px solid ##b6ddf3;padding-right:1px">&nbsp;

										</td>
										<td width="*">&nbsp;</td>
									</tr>
								</table>
								<!--- PROCESS NOTIFICATION --->
								<table width="100%" border="0" cellspacing="0" cellpadding="0" class="butnlink3c bttRight" valign="middle" id="header_dkpan_pnotif">
									<tr height="#bmm_panelhgt#">
										<td width="82" align="center" valign="middle" style="border-bottom:0px solid ##b6ddf3">
											<a style='cursor:pointer' onclick="setLinkUrlParams('fr_mgmtconsole_topmain.cfm?fromlink=dsk_notification&fromdesktop=y&fromtrans=dsk_notification','_blank')" href="javascript:void(0);">
												<span style="color:##DD3D3D;font-size:27pt;cursor:pointer"><i class="fa fa-podcast" aria-hidden="true"></i></span>
											</a>
										</td>
										<td width="77%" align="left" style="text-transform:uppercase;border-bottom:1px solid ##b6ddf3;cursor:pointer"
											<!--- onclick="setLinkUrlParams('fr_mgmtconsole_topmain.cfm?fromlink=dsk_notification&fromdesktop=y&fromtrans=dsk_notification','_blank')" --->>
											<a style='cursor:pointer' onclick="setLinkUrlParams('fr_mgmtconsole_topmain.cfm?fromlink=dsk_notification&fromdesktop=y&fromtrans=dsk_notification','_blank')"
												href="javascript:void(0);">
												<span style="font-size:12pt; font-family:Century Gothic; text-shadow:1px 1px ##efefef"><cfif set_language is 'english'>PROCESS NOTIFICATION</cfif></span>

											</a>
										</td>
										<td width="5%" align="right" valign="middle" style="border-bottom:1px solid ##b6ddf3;padding-right:1px">

										</td>
										<td width="5%" align="center" valign="middle" style="border-bottom:1px solid ##b6ddf3;padding-right:1px">&nbsp;

										</td>
										<td width="*">&nbsp;</td>
									</tr>
								</table>
								<!--- FORUM --->
								<cfif mfn_forum_func_on_yn EQ "y">
								<cfset desc_title = Tlt("<cfif set_language is 'english'>Forum</cfif>")>
								<table width="100%" border="0" cellspacing="0" cellpadding="0" class="butnlink3c bttRight" valign="middle" id="header_dkpan_forum">
									<tr height="#bmm_panelhgt#">
										<td width="82" align="center" valign="middle" style="border-bottom:0px solid ##b6ddf3">
											<a style='cursor:pointer' onclick="setLinkUrl('forum.cfm?fromlink=myfav&fromtrans=setup&fromsegm=tnomenu&#nsQ#','botmain','#desc_title#')" href="javascript:void(0);">
												<span style="color:##0a65b6;font-size:29pt;cursor:pointer"><i class="fa fa-comments" aria-hidden="true"></i></span>
											</a>
										</td>
										<td width="77%" align="left" style="text-transform:uppercase;border-bottom:1px solid ##b6ddf3;cursor:pointer">
											<a style='cursor:pointer' onclick="setLinkUrl('forum.cfm?fromlink=myfav&fromtrans=setup&fromsegm=tnomenu&#nsQ#','botmain','#desc_title#')"
												href="javascript:void(0);">
												<span style="font-size:12pt; font-family:Century Gothic; text-shadow:1px 1px ##efefef"><cfif set_language is 'english'>FORUM</cfif></span>

											</a>
										</td>
										<td width="5%" align="right" valign="middle" style="border-bottom:1px solid ##b6ddf3;padding-right:1px">

										</td>
										<td width="5%" align="center" valign="middle" style="border-bottom:1px solid ##b6ddf3;padding-right:1px">&nbsp;

										</td>
										<td width="*">&nbsp;</td>
									</tr>
								</table>
								</cfif>

								<!--- AI desktop links for style H rightbot panel. --->
								<cfinclude template="inc_ai_desktop_links.cfm">



							</td>
						</tr>
					</table>
				</td>
			</tr>

			<tr height="38"><td align="center">

				<cfif cookie.cookuserloginid EQ "m8"><br>
					
					<cfinclude template="inc_chk_sync_rpt_datasource.cfm">
					<span style="font-size:11pt;color:##fefefe">
						<cfif fileexists('../../../triggercloud/globe3_stop_cookie_mainsync.txt')>
							MSYNC SERVER NOT AVAILABLE (../../../triggercloud/globe3_stop_cookie_mainsync.txt)<br>
						</cfif>
						<cfif fileexists('../../../triggercloud/globe3_stop_cookie_reportdb.txt')>
							REPORTDB SERVER NOT AVAILABLE (../../../triggercloud/globe3_stop_cookie_reportdb.txt)<br>
						</cfif>
						<cfparam name="vle_mainsyncIP" default="">
						<cfparam name="vle_reportdbIP" default="">
						<cfset dbsize_master_mb = qs_master.dbsize/1024>
						1. LIVE DB #cookie.cooksqlfilename# (#numberformat(dbsize_master_mb)#MB)<br>
							
						<cfif mainsync_db EQ "" or mainsync_db_avl_yn is "n">
							<cfif flag_diff_db_ms_yn is "y">
								2. MAINSYNC DB detected; slave DB size diff over-tolerance setting: #diffsize_tolerance_kb#KB (#vle_mainsyncIP#)<br>
							<cfelse>
								2. MAINSYNC DB #cookie.cooksql_mainsync# (#vle_mainsyncIP#)<br>
							</cfif>
						<cfelse>
							<cfset dbsize_ms_mb = qs_mainsync_db.dbsize/1024>
							2. MAINSYNC DB #cookie.cooksql_mainsync# <cfif cookie.cooksql_mainsync NEQ cookie.cooksqlfilename>(#numberformat(dbsize_ms_mb)#MB | #datadiff_ms#KB) (#vle_mainsyncIP#)</cfif><br>
						</cfif>
						<cfif qs_network_dbsrc.rpt_slave EQ "" or reportdb_db_avl_yn is "n">
							<cfif flag_diff_db_rr_yn is "y">
								3. REPORTDB DB detected; slave DB size diff over-tolerance setting: #diffsize_tolerance_kb#KB (#vle_reportdbIP#)<br>
							<cfelse>
								3. REPT DB #cookie.cooksql_reportdb# (#vle_reportdbIP#)<br>
							</cfif>
						<cfelse>
							<cfset dbsize_rr_mb = qs_reportdb_db.dbsize/1024>
							3. REPT DB #cookie.cooksql_reportdb# <cfif cookie.cooksql_reportdb NEQ cookie.cooksqlfilename>(#numberformat(dbsize_rr_mb)#MB | #datadiff_rr#KB) (#vle_reportdbIP#)</cfif><br>
						</cfif>
						#cookie.cookmfnunique# <br>
						#cookie.cookcfnunique#<br>
						#cookie.cooklang#<br>
						#cookie.cooklang2#<br>
					</span>
				</cfif>
			</td></tr>

		</table>

		<CFINCLUDE template="inc_asset_mouseover_preview.cfm">
		<SCRIPT id="app_modal" type="text/html">
			<div style="background-color: rgba(0,0,0,0.5);position:absolute;width:100%;height:100%;z-index:9;display:none;padding-top:32px;" id="div_app_modal">
				<div id="div_app_modal_container" style="background-color: white; border: 1px solid ##B0C4DE; width: 90%;margin: auto; height: 90%;">
					<iframe id="frame_wflow"  name="frame_wflow" src="about:blank" style="width: 100%; height: 100%; display: none;" onload="frameWFlowLoaded(this)"></iframe>
				</div>
			</div>
		</SCRIPT>
		<SCRIPT tyoe="text/javascript">
			var close_app_modal_from_child;
			var wflow_app_row_selected = "";
			var wflow_app_visible = false;
			var credit_control_visible = false;
			mouseoverPreview_bindAll();

			function toggleWFlowApp() {
				document.getElementById('div_wflow_app').style.display = (wflow_app_visible?'none':'block');
				wflow_app_visible = !wflow_app_visible;
			}

			function toggleCreditControl() {
				document.getElementById('tbl_credit_control').style.display = (credit_control_visible?'none':'table');
				credit_control_visible = !credit_control_visible;
			}
			
			function toggleApprovalReview() {
				document.getElementById('tbl_approval_review').style.display = (approval_review_visible?'none':'table');
				approval_review_visible = !approval_review_visible;
			}

			function changeEntity(cfn) {
				window.parent.location = 'wgp_tnocompany.cfm?companyfn=' + cfn + '&groupfn=&holdfn=&masterfn=#cookie.cookmfnunique#&ns_=ns_&from_appr_panel=y'
			}

			function showApprovalModal(wflow_link, uniquenum_pri) {
				$('##frame_wflow').hide();
				wflow_app_row_selected = uniquenum_pri;
				$('##frame_wflow').attr('src', wflow_link + "&from_desktop_approval_yn=y");
				$('##div_app_modal').show();
			}

			function wflowAppPanelReload() {
				$('##div_wflow_app_rows_loader').show();
				$.ajax({
					url: 'inc_ajax_wflow_app_panel.cfm',
					data: 'my_privitype=#my_privitype#&my_staff_unique=#my_staff_unique#&my_admin_wflow=#my_admin_wflow#&from_ajax=y&selected_page_number=1',
					dataType: 'html',
					async: true,
					cache: false,
					success: function(oAjaxResult) {
						setTimeout(function () {
							$('##div_wflow_app_rows').html(oAjaxResult);
							$('##div_wflow_app_rows_loader').hide();
							mouseoverPreview_bindAll();
						}, 500);
					}
				});
			}

			function wflowAppPanelSetPage(page_num) {
				$('##div_wflow_app_rows_loader').show();
				$.ajax({
					url: 'inc_ajax_wflow_app_panel.cfm',
					data: 'my_privitype=#my_privitype#&my_staff_unique=#my_staff_unique#&my_admin_wflow=#my_admin_wflow#&from_ajax=y&selected_page_number=' + page_num,
					dataType: 'html',
					async: true,
					cache: false,
					success: function(oAjaxResult) {
						setTimeout(function () {
							$('##div_wflow_app_rows').html(oAjaxResult);
							$('##div_wflow_app_rows_loader').hide();
							mouseoverPreview_bindAll();
						}, 500);
					}
				});
			}

			function frameWFlowLoaded(oIFrame) {
				if(oIFrame.src != "about:blank") {
					$('##frame_wflow').show();
				}
			}

			if(window.parent.parent.location.href.indexOf('from_appr_panel=y') != -1) {
				toggleWFlowApp();
			}

			$( document ).ready(function() {
				if($('##div_app_modal').length == 0) {
					if(!close_app_modal_from_child) {
						close_app_modal_from_child = function () {
							$('##div_app_modal').hide();
						}
					}

					$('body').prepend($('##app_modal').html());

					$('##div_app_modal').click(function() {
						$('##div_app_modal').hide();
					});

					$('##div_app_modal_container').click(function(event){
						event.stopPropagation();
					});

					$(window).scroll(function() {
						var margin_top = (window.pageYOffset || document.documentElement.scrollTop)  - (document.documentElement.clientTop || 0);
						document.getElementById('div_app_modal').style.paddingTop = ((margin_top + 32) + "px");
					});
				}
			});
		</SCRIPT>
</cfoutput>
