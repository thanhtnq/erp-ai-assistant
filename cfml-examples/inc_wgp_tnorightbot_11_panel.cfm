<!--- ###########################################################################################################
Version	5.0.1
File 	inc_wgp_tnorightbot_11_panel.cfm
SNO	DATE		BY		LOG
1.	20240903	Jasen		Clone from "inc_wgp_tnorightbot_09_panel.cfm" 
2.	20240905	Jasen		Amend layout
3.	20240909	Jasen		Amend layout
4.	20240913	Jasen		Amend layout
5.	20240920	Jasen		Amend layout
6.	20250319	Jasen		Add "vle_folder_style_color"
7. 	20250328 	Yan 		Enhance StyleShtUIVersion J
8.	20250408		Saravanan	fix companyfn for wfappgrp
9.	20250410		Saravanan	use global condition for wfappgrp
10.	20250423	Jasen			Add "vle_bmimg_main_top_border" and "vle_bmimg_main_left_border"
11.	20250424	Jasen			Amend "vle_bmimg_main_top_border" and "vle_bmimg_main_left_border"
12. 	20250729 	Yan 		add whatsapp order (ScSmWa) , whatsapp_order_notification_yn , instant_chat (activate_instant_chat_yn),instant_chat_notification_yn
13. 	20250729 	Yan 		remove loginuser is neq 'm8' and add loginUserUniq
14. 	20250730 	Yan 		remove instant_chat_notification_yn , whatsapp_order_notification_yn
15. 	20250806 	Yan 		enhance instant chat link (botmain)(cen_instant_chat)
16. 	20250909 	Yan 		remove tag_table_usage for unread count (cen_instant_chat)
17. 	20260121 	Yan 		change flt_main to flt_data (ScSmWa)
18. 	20260220 	WeiJun 		Addon hide_desktop_quick_info_buttons_yn for TNO(TSK-NA)
19. 	20260409 	WeiJun 		Addon REPORT ORM and AI CHATBOX for TNO(TSK-NA)
20. 	20260603 	WeiJun 		Addon gate desktop AI CHATBOX by MAC right AiCbDt for TNO(TSK-NA)
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
	/* for whatsapp unread count */
	@keyframes blink {
		0%   { opacity: 1; }
		50%  { opacity: 0; }
		100% { opacity: 1; }
	}

	.blink {
		animation: blink 1.5s step-start 0s infinite;
	}

</style>
		<cfquery datasource="#cookie.cooksql_mainsync#_active" name="qs_set_co_masterco">
			select 		idcode,uniquenum_pri,co_name,co_code, co_unique
			from 		set_co_main
			where 		masterfn = <cfqueryparam  value="#cookie.cookmfnunique#"  cfsqltype="cf_sql_varchar">
						and tag_table_usage=<cfqueryparam  value="co_main"  cfsqltype="cf_sql_varchar">
						and tag_mhgc_fn=<cfqueryparam  value="mfn"  cfsqltype="cf_sql_varchar">
		</cfquery>
		<cfset masterco_cfn = qs_set_co_masterco.co_unique>

		<cfif bmimg_bg_image is "">
			<cfset bmimg_panel_bgcolor = "##e7ecf9">
			<cfset bmimg_inner_panel_boxshadow = "box-shadow: 1px 1px 4px ##d4dde7;">
			<cfset vle_bmimg_main_top_border = "">
			<cfset vle_bmimg_main_left_border = "">
		<cfelse>
			<cfset bmimg_panel_bgcolor = "##ffffff">
			<cfset bmimg_inner_panel_boxshadow = "">
			<cfset vle_bmimg_main_top_border = "">
			<cfset vle_bmimg_main_left_border = "">
		</cfif>		
		<cfif StyleShtUIVersion EQ "j">
			<cfset bmimg_panel_bgcolor = "##fff">
			<cfset bmimg_inner_panel_boxshadow = "">
			<cfset vle_bmimg_main_top_border = "border-top: 1px solid ##dce6ef;">
			<cfset vle_bmimg_main_left_border = "border-left: 1px solid ##dce6ef;">
		</cfif>
		
		<table width="97%" border="0" cellspacing="0" cellpadding="0" valign="middle">
			<tr height="95">
				<td width="100%" align="top" class="rightbot_table" style="background-color: #bmimg_panel_bgcolor# ;box-shadow: 2px 2px 5px ##c5d0db; #vle_bmimg_main_top_border# #vle_bmimg_main_left_border#">
					<table width="100%" border="0" cellspacing="0" cellpadding="0" valign="middle">
						<tr>
							<td class="rightbot_left"></td>
							<td>
								<table width="100%" border="0" cellspacing="0" cellpadding="0" class="" valign="middle">
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
								<br>
								
								<br>
								<cfflush>
								
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
												<span style="padding:3px 8px 3px 0px; font-family:Century Gothic; font-size:20pt; font-weight:bold; background:transparent; color:##0c427f; letter-spacing:5px; border:0px solid ##1791d6; border-radius:4px"> &nbsp;<span style="font-size:20pt; font-family:Calibri">FY</span>#cookie.cookfyearnow#&nbsp; </span>
			
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
								<table width="100%" border="0" cellspacing="0" cellpadding="0" class="butnlink3b" valign="middle" style="#bmimg_inner_panel_boxshadow# border-radius: 6px; <cfif hide_desktop_quick_info_buttons_yn EQ 'y'>display:none;</cfif>">
									<tr height="11"><td></td></tr>
									<tr>
										<td width="100%" style="border-radius: 6px">
											<!--- Approval --->
											<cfset desc_title = Tlt("<cfif set_language is 'english'>Approval Dashboard</cfif>")>
											<table width="100%" border="0" cellspacing="0" cellpadding="0" class="butnlink3c bttRight" valign="middle" id="header_dkpan_appr">
												<tr height="#bmm_panelhgt#">
													<td width="102" align="center" valign="middle" style="border-bottom:0px solid ##e7ecf9">
													<a style='cursor:pointer' onclick="setLinkUrl('fr_mgmtconsole_topmain.cfm?fromdemo=y&fromlink=wflowconsole&fromtype=#fromtype#&#nsQ#','topmain','#desc_title#')" href="javascript:void(0);">
															<span style="color:##0a65b6;font-size:27pt;cursor:pointer; text-shadow:1px 1px ##efefef"><i class="fa fa-briefcase" aria-hidden="true"></i></span>
													</a>
													</td>
													<td width="72%" align="left" style="text-transform:uppercase;border-bottom:3px solid ##e7ecf9;cursor:pointer"
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
													<td width="5%" align="right" valign="middle" style="border-bottom:3px solid ##e7ecf9;padding-right:1px" onclick="toggleWFlowApp()">
														<span class="downlink"><i class="fa fa-angle-down" aria-hidden="true"></i></span>
													</td>
													<td width="5%" align="center" valign="middle" style="border-bottom:3px solid ##e7ecf9;padding-right:1px">&nbsp;
			
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
																				where 		<cfinclude template="inc_get_wfappgrp_qry.cfm">
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
												
												<cfif cnt_chk_check GT 0>
													<cfset show_blinkicon_credit_control_yn = "y">
												</cfif>
												<table width="100%" border="0" cellspacing="0" cellpadding="0" class="butnlink3c bttRight" valign="middle" id="header_dkpan_creditcontrol">
													<tr height="#bmm_panelhgt#">
														<td width="102" align="center" valign="middle" style="border-bottom:0px solid ##e7ecf9">
															<span style="color:##0F905D;font-size:23pt;cursor:pointer"><i class="fa fa-credit-card-alt trigger02" aria-hidden="true"></i></span>
														</td>
														<td width="72%" align="left" style="text-transform:uppercase;border-bottom:3px solid ##e7ecf9;cursor:pointer"
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
														<td width="5%" align="right" valign="middle" style="border-bottom:3px solid ##e7ecf9;padding-right:1px" onclick="toggleCreditControl()">
															<span class="downlink"><i class="fa fa-angle-down" aria-hidden="true"></i></span>
														</td>
														<td width="5%" align="center" valign="middle" style="border-bottom:3px solid ##e7ecf9;padding-right:1px">&nbsp;
			
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
													<td width="102" align="center" valign="middle" style="border-bottom:0px solid ##e7ecf9">
														<span style="color:##DD3D3D;font-size:28pt;cursor:pointer"><i class="fa fa-exclamation-triangle trigger fa-blink2" aria-hidden="true"></i></span>
													</td>
													<td width="72%" align="left" style="text-transform:uppercase;border-bottom:3px solid ##e7ecf9;cursor:pointer"
														class="trigger">
														<a class="trigger" style='cursor:pointer' name="alert_trigger"
															href="javascript:void(0);">
															<span style="font-size:12pt; font-family:Century Gothic; text-shadow:1px 1px ##efefef"><cfif set_language is 'english'>ALERTS</cfif></span>
			
														</a>
													</td>
													<td width="5%" align="right" valign="middle" style="border-bottom:3px solid ##e7ecf9;padding-right:1px">
			
													</td>
													<td width="5%" align="center" valign="middle" style="border-bottom:3px solid ##e7ecf9;padding-right:1px">&nbsp;
			
													</td>
													<td width="*">&nbsp;</td>
												</tr>
											</table>
			
			
											<!--- LATEST RECORDS --->
											<table width="100%" border="0" cellspacing="0" cellpadding="0" class="butnlink3c bttRight" valign="middle" id="header_dkpan_latest">
												<tr height="#bmm_panelhgt#">
													<td width="102" align="center" valign="middle" style="border-bottom:0px solid ##e7ecf9">
														<span style="color:##0a65b6;font-size:25pt;cursor:pointer"><i class="fa fa-database trigger01" aria-hidden="true"></i></span>
													</td>
													<td width="72%" align="left" style="text-transform:uppercase;border-bottom:3px solid ##e7ecf9;cursor:pointer"
														class="trigger01">
														<a class="trigger01" style='cursor:pointer' name="alert_trigger01"
															href="javascript:void(0);">
															<span style="font-size:12pt; font-family:Century Gothic; text-shadow:1px 1px ##efefef"><cfif set_language is 'english'>LATEST RECORDS</cfif></span>
			
														</a>
													</td>
													<td width="5%" align="right" valign="middle" style="border-bottom:3px solid ##e7ecf9;padding-right:1px">
			
													</td>
													<td width="5%" align="center" valign="middle" style="border-bottom:3px solid ##e7ecf9;padding-right:1px">&nbsp;
			
													</td>
													<td width="*">&nbsp;</td>
												</tr>
											</table>
											<!--- PROCESS NOTIFICATION --->
											<table width="100%" border="0" cellspacing="0" cellpadding="0" class="butnlink3c bttRight" valign="middle" id="header_dkpan_pnotif">
												<tr height="#bmm_panelhgt#">
													<td width="102" align="center" valign="middle" style="border-bottom:0px solid ##e7ecf9">
														<a style='cursor:pointer' onclick="setLinkUrlParams('fr_mgmtconsole_topmain.cfm?fromlink=dsk_notification&fromdesktop=y&fromtrans=dsk_notification','_blank')" href="javascript:void(0);">
															<span style="color:##DD3D3D;font-size:27pt;cursor:pointer"><i class="fa fa-podcast" aria-hidden="true"></i></span>
														</a>
													</td>
													<td width="72%" align="left" style="text-transform:uppercase;border-bottom:3px solid ##e7ecf9;cursor:pointer"
														<!--- onclick="setLinkUrlParams('fr_mgmtconsole_topmain.cfm?fromlink=dsk_notification&fromdesktop=y&fromtrans=dsk_notification','_blank')" --->>
														<a style='cursor:pointer' onclick="setLinkUrlParams('fr_mgmtconsole_topmain.cfm?fromlink=dsk_notification&fromdesktop=y&fromtrans=dsk_notification','_blank')"
															href="javascript:void(0);">
															<span style="font-size:12pt; font-family:Century Gothic; text-shadow:1px 1px ##efefef"><cfif set_language is 'english'>PROCESS NOTIFICATION</cfif></span>
			
														</a>
													</td>
													<td width="5%" align="right" valign="middle" style="border-bottom:3px solid ##e7ecf9;padding-right:1px">
			
													</td>
													<td width="5%" align="center" valign="middle" style="border-bottom:3px solid ##e7ecf9;padding-right:1px">&nbsp;
			
													</td>
													<td width="*">&nbsp;</td>
												</tr>
											</table>
											<!--- REPORT ORM --->
											<cfif isDefined("cookie.cookuserloginid") and cookie.cookuserloginid eq 'm8'>
												<table width="100%" border="0" cellspacing="0" cellpadding="0" class="butnlink3c bttRight" valign="middle" id="header_dkpan_report">
													<tr height="#bmm_panelhgt#" style="cursor:pointer" onclick="window.open('./orm_report_runner.cfm?fromlink=rpt_main&fromtrans=rpt_main&fromsegm=tnomenu&#nsQ#','_blank')">
														<td width="102" align="center" valign="middle" style="border-bottom:0px solid ##e7ecf9">
															<span style="color:##0a65b6;font-size:27pt;cursor:pointer"><i class="fa fa-bar-chart" aria-hidden="true"></i></span>
														</td>
														<td width="72%" align="left" style="text-transform:uppercase;border-bottom:3px solid ##e7ecf9;cursor:pointer">
															<span style="font-size:12pt; font-family:Century Gothic; text-shadow:1px 1px ##efefef"><cfif set_language is 'english'>REPORT</cfif></span>
														</td>
														<td width="5%" align="right" valign="middle" style="border-bottom:3px solid ##e7ecf9;padding-right:1px">

														</td>
														<td width="5%" align="center" valign="middle" style="border-bottom:3px solid ##e7ecf9;padding-right:1px">&nbsp;

														</td>
														<td width="*">&nbsp;</td>
													</tr>
												</table>
											</cfif>
											<!--- AI CHATBOX --->
											<!--- 20260603 [start] gate desktop AI CHATBOX by MAC right AiCbDt, was m8-only (TSK-NA) --->
											<cfset funId = 'AiCbDt'>
											<cfinclude template="inc_get_access_info.cfm">
											<cfif gotAccess is 'y'>
												<table width="100%" border="0" cellspacing="0" cellpadding="0" class="butnlink3c bttRight" valign="middle" id="header_dkpan_ai_chatbox">
													<tr height="#bmm_panelhgt#" style="cursor:pointer" onclick="window.open('ai_chatbox.cfm?&#nsQ#','_blank')">
														<td width="102" align="center" valign="middle" style="border-bottom:0px solid ##e7ecf9">
															<span style="color:##0a65b6;font-size:27pt;cursor:pointer"><i class="fa fa-commenting" aria-hidden="true"></i></span>
														</td>
														<td width="72%" align="left" style="text-transform:uppercase;border-bottom:3px solid ##e7ecf9;cursor:pointer">
															<span style="font-size:12pt; font-family:Century Gothic; text-shadow:1px 1px ##efefef"><cfif set_language is 'english'>AI CHATBOX</cfif></span>
														</td>
														<td width="5%" align="right" valign="middle" style="border-bottom:3px solid ##e7ecf9;padding-right:1px">

														</td>
														<td width="5%" align="center" valign="middle" style="border-bottom:3px solid ##e7ecf9;padding-right:1px">&nbsp;

														</td>
														<td width="*">&nbsp;</td>
													</tr>
												</table>
											<!--- AI desktop links share the AiCbDt access gate. --->
											
											</cfif>
											<cfinclude template="inc_ai_desktop_links.cfm">
											<!--- 20260603 [end  ] gate desktop AI CHATBOX by MAC right AiCbDt, was m8-only (TSK-NA) --->
											<!--- FORUM --->
											<cfif mfn_forum_func_on_yn EQ "y">
											<cfset desc_title = Tlt("<cfif set_language is 'english'>Forum</cfif>")>
											<table width="100%" border="0" cellspacing="0" cellpadding="0" class="butnlink3c bttRight" valign="middle" id="header_dkpan_forum">
												<tr height="#bmm_panelhgt#">
													<td width="102" align="center" valign="middle" style="border-bottom:0px solid ##e7ecf9">
														<a style='cursor:pointer' onclick="setLinkUrl('forum.cfm?fromlink=myfav&fromtrans=setup&fromsegm=tnomenu&#nsQ#','botmain','#desc_title#')" href="javascript:void(0);">
															<span style="color:##0a65b6;font-size:29pt;cursor:pointer"><i class="fa fa-comments" aria-hidden="true"></i></span>
														</a>
													</td>
													<td width="72%" align="left" style="text-transform:uppercase;border-bottom:3px solid ##e7ecf9;cursor:pointer">
														<a style='cursor:pointer' onclick="setLinkUrl('forum.cfm?fromlink=myfav&fromtrans=setup&fromsegm=tnomenu&#nsQ#','botmain','#desc_title#')"
															href="javascript:void(0);">
															<span style="font-size:12pt; font-family:Century Gothic; text-shadow:1px 1px ##efefef"><cfif set_language is 'english'>FORUM</cfif></span>
			
														</a>
													</td>
													<td width="5%" align="right" valign="middle" style="border-bottom:3px solid ##e7ecf9;padding-right:1px">
			
													</td>
													<td width="5%" align="center" valign="middle" style="border-bottom:3px solid ##e7ecf9;padding-right:1px">&nbsp;
			
													</td>
													<td width="*">&nbsp;</td>
												</tr>
											</table>
											</cfif>
											
											<!--- WHATSAPP ORDER --->
											<cfset funId = 'ScSmWa'>
											<cfinclude template='inc_get_access_info.cfm'>
											<cfif gotAccess is 'y'>
												<cfset loginUserUniq = ''>
												<cfquery datasource="#cookie.cooksqlfilename#_active" name="qs_sys_sec_cip">
													select 	ck_userloginid,uniquenum_pri,staff_code,staff_unique,staff_desc
													from 	sys_sec_cip
													where 	tag_table_usage ='ns_adduser'
													and 	masterfn = <cfqueryparam value="#cookie.cookmfnunique#" cfsqltype="cf_sql_varchar">
													and  	ck_userloginid = <cfqueryparam value="#cookie.COOKUSERLOGINID#" cfsqltype="cf_sql_varchar">
													and uniquenum_pri not in
														(
															Select uniquenum_pri
															from	sys_sec_cip
															WHERE 	masterfn 	= '#cookie.cookmfnunique#'
															and 	tag_table_usage = 'ns_adduser_ex'
															and		tag_others02 = 'y'
															and		ck_cpaunique <> ''
															and tag_global01_yn='n'
														)

													and uniquenum_pri not in
														(
															Select uniquenum_pri
															from	sys_sec_cip
															WHERE 	masterfn 	= '#cookie.cookmfnunique#'
															and 	tag_table_usage = 'ns_adduser_ex'
															and		tag_others04 = 'y'
														)
													and uniquenum_pri not in (
															Select uniquenum_pri
															from	sys_sec_cip
															WHERE 	masterfn 	= '#cookie.cookmfnunique#'
															and 	tag_table_usage = 'ns_adduser'
															and 	USERPREF_SET02 = 'GcMcVpUa'
														)
													and uniquenum_pri not in (
															Select uniquenum_pri
															from	sys_sec_cip
															WHERE 	masterfn 	= '#cookie.cookmfnunique#'
															and 	tag_table_usage = 'ns_adduser'
															and 	USERPREF_SET02 = 'GcMcArSu'
														)
													and tag_global01_yn='n'
													order by
													lower(staff_desc),lower(staff_code) 
												</cfquery>
												<cfif qs_sys_sec_cip.recordCount GT 0>
													<cfset loginUserUniq = qs_sys_sec_cip.staff_unique> 
												</cfif>
												<cfquery datasource="#cookie.cooksqlfilename#_active" name="qs_unread_count">
													SELECT	notes_memo
													FROM	flt_data
													WHERE 	masterfn = <cfqueryparam value="#cookie.cookmfnunique#" cfsqltype="cf_sql_varchar">
													AND 	notes_memo NOT ILIKE <cfqueryparam value="%#loginUserUniq#%" CFSQLType="CF_SQL_VARCHAR">
													AND   	var_25_004 = 'whatsapp_sync_read'
													AND  	tag_table_usage IN ('whatsapp_sync', 'whatsapp_sync_att')
													limit 100
												</cfquery>
												<cfset desc_title = Tlt("<cfif set_language is 'english'>WhatsApp Order</cfif>")>
												<table width="100%" border="0" cellspacing="0" cellpadding="0" class="butnlink3c bttRight" valign="middle" id="header_dkpan_whatsapp_order">
													<tr height="#bmm_panelhgt#">
														<td width="102" align="center" valign="middle" style="border-bottom:0px solid ##e7ecf9">
															<a style='cursor:pointer' onclick="setLinkUrl('whatsapp_order.cfm?fromlink=whatsapp_sync&fromtrans=whatsapp_sync&fromsegm=whatsapp_sync&','botmain','#desc_title#')" href="javascript:void(0);">
																<span style="color:##25D366;font-size:29pt;cursor:pointer"><i class="fa fa-whatsapp" aria-hidden="true"></i></span>
															</a>
														</td>
														<td width="72%" align="left" style="text-transform:uppercase;border-bottom:3px solid ##e7ecf9;cursor:pointer">
															<a style='cursor:pointer' onclick="setLinkUrl('whatsapp_order.cfm?fromlink=whatsapp_sync&fromtrans=whatsapp_sync&fromsegm=whatsapp_sync&','botmain','#desc_title#')"
																href="javascript:void(0);">
																<span style="font-size:12pt; font-family:Century Gothic; text-shadow:1px 1px ##efefef"><cfif set_language is 'english'>WhatsApp Order</cfif></span>
				
															</a>
															<span id="whatsapp_unread_count" class="blink" style="font-size:12pt; font-family:Century Gothic; background-color: ##386da9;color: ##fff;border-radius: 999px;padding: 0.25em 0.5em;"><cfif qs_unread_count.recordCount GT 99>99+<cfelse>#qs_unread_count.recordCount#</cfif></span>
														</td>
														<td width="5%" align="right" valign="middle" style="border-bottom:3px solid ##e7ecf9;padding-right:1px">
														</td>
														<td width="5%" align="center" valign="middle" style="border-bottom:3px solid ##e7ecf9;padding-right:1px">&nbsp;
				
														</td>
														<td width="*">&nbsp;</td>
													</tr>
												</table>
											</cfif>
											<!--- INSTANT CHAT --->
											<cfif activate_instant_chat_yn EQ 'y' and activate_websocket_yn EQ 'y'>
												<cfset loginUserUniq = ''>
												<cfquery datasource="#cookie.cooksqlfilename#_active" name="qs_sys_sec_cip">
													select 	ck_userloginid,uniquenum_pri,staff_code,staff_unique,staff_desc
													from 	sys_sec_cip
													where 	tag_table_usage ='ns_adduser'
													and 	masterfn = <cfqueryparam value="#cookie.cookmfnunique#" cfsqltype="cf_sql_varchar">
													and  	ck_userloginid = <cfqueryparam value="#cookie.COOKUSERLOGINID#" cfsqltype="cf_sql_varchar">
													and uniquenum_pri not in
														(
															Select uniquenum_pri
															from	sys_sec_cip
															WHERE 	masterfn 	= '#cookie.cookmfnunique#'
															and 	tag_table_usage = 'ns_adduser_ex'
															and		tag_others02 = 'y'
															and		ck_cpaunique <> ''
															and tag_global01_yn='n'
														)

													and uniquenum_pri not in
														(
															Select uniquenum_pri
															from	sys_sec_cip
															WHERE 	masterfn 	= '#cookie.cookmfnunique#'
															and 	tag_table_usage = 'ns_adduser_ex'
															and		tag_others04 = 'y'
														)
													and uniquenum_pri not in (
															Select uniquenum_pri
															from	sys_sec_cip
															WHERE 	masterfn 	= '#cookie.cookmfnunique#'
															and 	tag_table_usage = 'ns_adduser'
															and 	USERPREF_SET02 = 'GcMcVpUa'
														)
													and uniquenum_pri not in (
															Select uniquenum_pri
															from	sys_sec_cip
															WHERE 	masterfn 	= '#cookie.cookmfnunique#'
															and 	tag_table_usage = 'ns_adduser'
															and 	USERPREF_SET02 = 'GcMcArSu'
														)
													and tag_global01_yn='n'
													order by
													lower(staff_desc),lower(staff_code) 
												</cfquery>
												<cfif qs_sys_sec_cip.recordCount GT 0>
													<cfset loginUserUniq = qs_sys_sec_cip.staff_unique> 
												</cfif>
												<cfquery datasource="#cookie.cooksqlfilename#_active" name="qs_unread_count">
													SELECT 	DISTINCT ON (data.uniquenum_uniq) data.uniquenum_uniq,data.notes_memo
													FROM 	flt_data data
													left JOIN flt_main main ON main.uniquenum_pri = data.uniquenum_pri
													WHERE 	main.notes_memo ILIKE <cfqueryparam value="%#loginUserUniq#%" CFSQLType="CF_SQL_VARCHAR">
    													AND 	data.notes_memo NOT ILIKE <cfqueryparam value="%#loginUserUniq#%" CFSQLType="CF_SQL_VARCHAR">
													AND  	data.companyfn = <CFQUERYPARAM value="#cookie.cookcfnunique#" CFSQLTYPE="CF_SQL_VARCHAR">
													AND 	data.var_25_003 = <CFQUERYPARAM value="instant_chat_data" CFSQLTYPE="CF_SQL_VARCHAR"> 
													AND   	data.var_25_002 = <CFQUERYPARAM value="instant_chat_attachment" CFSQLTYPE="CF_SQL_VARCHAR">
													AND  	data.var_25_001 = <CFQUERYPARAM value="instantchat" CFSQLTYPE="CF_SQL_VARCHAR">
													limit 100
												</cfquery>

												<cfset desc_title = Tlt("<cfif set_language is 'english'>Instant Chat</cfif>")>
												<table width="100%" border="0" cellspacing="0" cellpadding="0" class="butnlink3c bttRight" valign="middle" id="header_dkpan_instant_chat">
													<tr height="#bmm_panelhgt#">
														<td width="102" align="center" valign="middle" style="border-bottom:0px solid ##e7ecf9">
															<a style='cursor:pointer' onclick="setLinkUrl('cen_instant_chat.cfm?fromlink=instantchat&fromtrans=&fromsegm=instant_chat&','botmain','#desc_title#')" href="javascript:void(0);">
																<span style="color:##0a65b6;font-size:29pt;cursor:pointer"><i class="fa-solid fa-comments" aria-hidden="true"></i></span>
															</a>
														</td>
														<td width="72%" align="left" style="text-transform:uppercase;border-bottom:3px solid ##e7ecf9;cursor:pointer">
															<a style='cursor:pointer' onclick="setLinkUrl('cen_instant_chat.cfm?fromlink=instantchat&fromtrans=&fromsegm=instant_chat&','botmain','#desc_title#')"
																href="javascript:void(0);">
																<span style="font-size:12pt; font-family:Century Gothic; text-shadow:1px 1px ##efefef"><cfif set_language is 'english'>Instant Chat</cfif></span>
				
															</a>
															<span id="instantchat_unread_count" class="blink" style="font-size:12pt; font-family:Century Gothic; background-color: ##386da9;color: ##fff;border-radius: 999px;padding: 0.25em 0.5em;"><cfif qs_unread_count.recordCount GT 99>99+<cfelse>#qs_unread_count.recordCount#</cfif></span>
														</td>
														<td width="5%" align="right" valign="middle" style="border-bottom:3px solid ##e7ecf9;padding-right:1px">
														</td>
														<td width="5%" align="center" valign="middle" style="border-bottom:3px solid ##e7ecf9;padding-right:1px">&nbsp;
				
														</td>
														<td width="*">&nbsp;</td>
													</tr>
												</table>
											</cfif>
											<table width="100%" border="0" cellspacing="0" cellpadding="0" class="butnlink3c_last bttRight" valign="middle">
												<tr height="50">
													<td>&nbsp;</td>
												</tr>
											</table>
										</td>
									</tr>
									
								</table>
							</td>
							<td class="rightbot_right"></td>
						</tr>
						<tr height="55"><td></td></tr>
					</table>
				</td>
			</tr>

			<tr height="38"><td align="center">

				<cfif cookie.cookuserloginid EQ "m8"><br>
					
					<cfinclude template="inc_chk_sync_rpt_datasource.cfm">

					<cfif vle_folder_style_color EQ "">
						<cfset vle_folder_style_color = "##eef2fc">
					</cfif>

					<span style="font-size:11pt;color:#vle_folder_style_color#">
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
