<!---GLOBE3 MDUAL UPDATE RUN ON 20180215104312--->
<!---GLOBE3 MDUAL UPDATE RUN ON 20180207192350--->
<!---@ ###################################################################################################################
Version	5.0.1
File 	ns_wgp_AccessControl_1.cfm
SNO 	DATE		BY		LOG
1.	20071004	oliver		amend the stucture
2.	20071011	oliver		add Profit Distribution for Chinese Special Report (pdsacctnum)
3.	20071016	oliver		add VAT Payable Details Report for Chinese Special Report (vatacctnum)
4.	20071019	oliver		new report fr_fin_aip for chinese format reports (aipacctnum)
5.	20071019	oliver		add GST Currency and Rate
6.	20071109	lcw			add password control
7.	20071212	oliver		new report for chinese format reports (bstype,pltype)
8.	20071221	oliver		dd purterm for Tomoe
9.	20080103	ckt			correct upd_party_country_code.cfm.cfm to upd_party_country_code.cfm
10.	20080325	oliver		remove the label of GST
11.	20080302	Saravanan	added us states tax/country list
12.	20080403	Saravanan	et target for link documents
13.	20080404 	manik		GcFpPs - GcFpPq, GcFpPsAc - GcFpPqAc, GcFpRc - GcFpPqRc, GcFpRp - GcFpPqRp, GcFpPsRd - GcFpPqRd
							gcgcsoet - gcgcsoey wrong code replaced
14.	20080515	lcw			add new link for Transaction Datasource
15.	20080516 	manik 		fromlevel removed
16.	20080520	manik		GcMcPp added
16.	20080526	manik		GcMcPpUs link refined
17.	20080528	oliver		add price,payment,delivery,validity,warranty,otherItems,servicingWarranty,training for quotation H/F section
18.	20080529	manik		Tariff Code and End User, added
19.	20080606	lcw			add location group
17.	20080701	lcw			new markup code, internal forex rate
18.	20080707	lcw			add purchase price factor
19.	20080804	lcw			fix error for portal user
19.	20080918	Saravanan	added sms_simnthly, sms_siapp
20.	20080922	oliver		fix bug on amend users through All User List under Master Control
21.	20080924	Saravanan	added sms_sipksal
22.	20081107	oliver		gltype
23.	20081219	deepam		added GcCoCoDf - User Defined Dimensions And Fields - at company settings level
24.	20081224	oliver		def_reve
25.	20090102	oliver		fix bug of GcCoCoDf
26.	20090203	Saravanan	New Links for feedback and bulk sms
27.	20090209	Saravanan	added fromtrans to contact
28.	20090618	oliver		added System Utility (GcMcSu, pug_aud/pug_ned)
29.	20090707	oliver		purge data point to fin_glpost_topmain
30.	20090812	Saravanan	Share Register and entities owned
31.	20090820	Saravanan	Enhanced Organizational structrure
32.	20090923	Saravanan	New Menu for wflow
33.	20091009	oliver		new gencode modapp (Applicable Product) for Stock Code
34.	20091223	oliver		new gencode funapp (Applicable Function) for Stock Code
35.	20100126	Saravanan	print security for Sales Invoice
36.	20100324	Saravanan	added transaction type setting
37.	20100324	oliver		add soterm,sinvterm,spfinvterm
38.	20100706	maurice		add Magento Contact Sync
39.	20100713	oliver		new gencode stkadjpurpose for stock adjustment, store in contract field
40.	20100804	oliver		new fromsegm database to setup Globe3 companies data source
41.	20100915	oliver		hr_jobrole
42.	20101206	saravanan	vehicle number in gencode sales
43.	20110102	oliver		amend cctype label
44.	20110111	Maurice		Add multi-base currency
45.	20110112	Hai			add PO Purpose
46.	20110120	Saravnan	added wfappgrp
47.	20110120	Hai			added Company Control -> Reports section and 3 reports
48.	20110127	cmm			wemark : new gencode rowitem (row item breakdown type) for Sales Quotation New Tab Row Item Breakdown
49.	20110208	ckt			unmark Magento for translation
50.	20110211	Hai			change the title from workflow history to workflow status listing
51.	20110212	ckt			correct marking for translation (move 1,2,3,4 out of the marking)
52.	20110214	ckt			remove non-usefull codes
53.	20110223	Hai			add Vehicle Number under General Codes -> Inventory
54.	20110223	Hai			remove Vehicle Number under General Codes -> Sales
55.	20110224	ckt			correct marking for translation (move 1,2,3,4 out of marking of Level)
56.	20110225	sonny		add Variety on Inventory Section
57.	20110311	Maurice		Add Packing Type
58.	20110316	Sylvain		Add Sync function and Setup DB
59.	20110325	Sonny		Add Container Size
60.	20110331	Sonny		Add Sales Commission Rate
61.	20110412	cmm			sutl - add alcohol principal
62.	20110412	cmm			sutl - add alcohol label
63.	20110413	ckt			correct marking for trans (move A, B out for marking Item Box)
64.	20110426	Sonny		modify Sales Commission Rate
65.	20110506	tks			new entities, masdata for Central Master Data Control
66.	20110608	tks			new Group Forex And Rates
67.	20110616	Boris		New gen code, Delivery Status
68.	20110628	Sonny		Added shipsq (Shipping Sequence) for White Feather
69.	20110715	Boris		added location zone, hr_loczone (sutl)
70.	20110810	Saravanan	added the 9 parameter for functioncode
71.	20110811	Sonny		added functioncode
72.	20110908	Saravanan	added Set Function Code Link
73.	20110919	Sonny		added Transaction Attachment Report
74.	20110919	cmm			wemark - changed name of fromsegm and functionid
75.	20110927	Sonny		added Attachment Report
76.	20111012	tks			add matinoutpurpose
77.	20111101	Maurice		Add identity Indicator
78.	20111121	tks			add stockdimen
79.	20120104	Maurice		Added new gencode for terminal
80.	20120228	tks			add discbyitem
81.	20120416	sonny		add  seg_custvendboth (Segregate Customer, Vendor And Both Master Data)
82.	20120420	Boris		add  new section Credit Admin
83.	20120430	Vive		add new report user system log
84.	20120503	sonny		add Sync Data DB Server to DB Server
85.	20120503	Maurice		Add Sync with IB2k
86. 20120515	sonny		added Import/Export to CSV file
87.	20120518	KhaChong	Add Bank ID gencode in finance GcGcFiBi (GFD196)
88.	20120628	oliver		Incomet Statement Report Tool for Kazu (GRA107)
89.	20120628	oliver		minor adjustment
90.	20120724	KhaChong	Add Manual SMS
91. 20120727    Edmund      Add Entity Map link
92. 20120808    Edmund      Add Organizational Chart
93.	20120813	oliver		Move SAP Export to Company Control/System Integration
94.	20120821	chiaann		add report user_access_entity (GFM154)
95.	20120822	Vive		add contact gencode billing cycle (GFD197)
96.	20120822	oliver		retention_handling_yn (fmi_formset_yn06_set21)
97.	20121008	Vive		add contact listing fr_cnt_list (GFP111)
98.	20121009	Maurice		Added Miscellaneous Charges (GFD199)
99.	20121010	Maurice		added Letter Setup (GFD200)
100.	20121010	Vive		added QC Label (GFD201)
101.	20121015	Maurice		Remove GFD199 (Miscellaneous Charges)
102.	20121018	Vive		Amend fr_cnt_list to use report topmain
103.	20121023	oliver		add stktrnrpurpose for demo QC process (GFD202)
104.	20121030	oliver		add qcfalirsn (GFD203), qccortact (GFD204) for demo QC process
105.	20121101	Sonny		added Quotation Status (GcGcSaQu) - GFD205
106.	20121114	Edmund		added Item Type - GFD206
107.	20121205	Vive		added Transaction Print Audit - GRT106
108.	20121226	Saravanan	added Cache Settings
109.	20130325	KhaChong	added contact listing with personnel info - GFP112
110.	20130412	tks			add transfields (GFM156)
111.	20130530	Maurice		Added retail Sales security (GFF154)
112.	20130604	Maurice		Added filter to search document
113.	20130605	Maurice		Edit saech document
114.	20130611	KhaChong	Added door type (GFD207), fire rating (GFD208), Door Finishing (GFD209) (Suntech)
115.	20130612	Maurice		Added new Function Slidshow
116.	20130627	Saravanan	added rebateprd
117.	20130714	oliver		change description of entp_pbill to Progress Claim, entp_pcap to Certified Claim
118.	20130719	KhaChong	added door width formula (GFD211) and door height formula (GFD212) for Suntech
119.	20130722	Sonny		added MAC Address Control
120.	20131014	Sonny		added Shared Folder Settings (GFC150)
121.	20131014	Sonny		added Shared Folder Directory (GSF101)
122.	20131014	chiaann		added language (GFD213), License Type (GFD214)
123.	20131014	Maurice		added sales stage (GFD215)
124.	20131112	Saravanan	new link for Approval Range(GFW112)
125.	20131112	Maurice		added Area (GFD216)
126.	20131125	tks			add disccntdim
127.	20131230	Saravanan	new gencode po status
128.	20140207	Saravanan	new link price factor
129.	20140401	Sonny		added Sales Commission Reporting Account (GcGcSaSc)
130.	20140409	Saravanan	added treatsess
131.	20140414	Sonny 		Service Category (GcGcSaSv)- Nevigate
132.	20140730	Chien_Khmt	added customer/vendor statistic
133.	20140801	Chien_Khmt	change the label
134.	20140929	Ngoc Quan	Add Leads Dimentions
135.	20140930	Chien_Khmt 	test, update comment and check-in file for Ngoc Quan
136.	20141003	Ngoc Quan	Add CRM in Workflow
137.	20141006	Chien_Khmt 	update file for Ngoc Quan
138.	20141118	Trieu	 	add serreport
139.	20141119	Ngoc Quan	Add Document Required to Gen code behind Sales
140.	20141230	RucCV		added Quotation Category(quo_cat - GFD225), Quotation Internal Product(quo_intpro - GFD226), Quotation External Product(quo_extpro - GFD227)
141.	20150226	Chien_Khmt	Added fr_membership_status_list
142.	20150311	Saravanan	Added Restricted User Creation Type
143.	20150526	NhoNguyen	Added Discount Type (hr_discount_type - GFD228)
144.	20150603	MinhNQ		Added Print Form General Setting (sal_general_set - GFF155)
145.	20150629	Ngoc Quan	Added Account Mapping (One to Many) - GcChAm > Account Mapping - GRA108
146.	20150903	MinhNQ		Add Upload source file/Import for Print Form General Setting (GFF156 - GFF157)
147.	20150903	Ngoc Quan	Added General Codes > MRP
148.	20150910	Ngoc Quan	Moved Days Of Supply from "G3 Central > General Codes > MRP" to "SCM > Stock Master Control > General Code"
149.	20151109	NhoNguyen	Added CN/DN Purpose (cndn_purpose - GFD230)
150.	20151113	Maurice		Added Shipment Terms, Shipment Mode, Shipment No, Back Charges fro redwood (GFD231, GFD232, GFD233, GFD234)
151.	20160108	Saravanan	new links for central master data
152.	20160118	Edwin		Added Acct Tax Code (GFD235) for Rovski
153.	20160210	oliver		add Costing Statement Localizaiton report tools (csrptcol,cstype_acctnum,cstype_bu,cstype_prj,cstype_rptcol) for Aslan
154.	20160211	oliver		add general code payeename in petty cash and bank payment for K.A Building
155.	20160218	chiaann		add general code ent_grp in master setting for Yon Ming
156.	20160219	oliver		split to ns_wgp_AccessControl_1L.cfm due to file too long
157.	20160203	Maurice		Add e2open integration fro nittsu
158.	20160303	chiaann		added fromcmdc CMDC for Yon Ming
159.	20160406	chiaann		added cmdc_co for Yon Ming
160.	20160414	Maurice		Added WooCommerce
161.	20160513	chiaann		added stkcatlnk, stk_price_upd for Yon Ming
162.	20160620	deepam		added login attempt control functionality for Xin Networks - TSK-12900
163.	20160902	Lester		Added Report Section for COA Listing - TSK-13364 - checked in  Sara
164.	20160809	Maurice		Add new sync for ewineasia
165.	20161019	NhoNguyen	Added Database Backup (databasebk - GFD236) - TSK-14051
166.	20161025	csl			project maincon labelling _cstrmain
167.	20161027	chiaann		Add GST Currency Rates (GcMcFoGs) in CMD - TSK-14133
168.	201611118	Nick		Team(GcCoOrTm), added
169.	20161209	NgacTran	add User Defined Dimensions And Account Number for Self Help - TSK-14221
170.	20161217	Saravanan	add new link for timesheet approval
171.    20161229    LamKhieu    Open the "Header And Footer" tab in Job Order and related print setting in Forms & Printing (TSK-14580)
172.	20170111	Selvam		Added GcWmWcAm
173		20170111	Selvam		Added GcWmWcSm
174.	20170517	Selvam		New Link for MRP
175.	20170519	HungNV		TSK-15395	Auto user template creation
176.	20170525	NgacTran	new report fr_user_list_rpt for Yon Ming - TSK-15097
177.	20170606	Selvam		Added New link "Motor Asset Management".(GcWmWcMa)
178.	20170830	RucCV		Add new function import data for Bank Id Tab of Contact Master (TSK-15886)
179.	20170912	NgacTran	add statelist, citylist for Hai Au - TSK-16249
180.	20171025	Maurice		Add Service Setup
181.	20171031	Saravanan	addded new link for limited user
182.	20171031	Maurice		Change tite for service setup
183.	20171108	Saravanan	changes for limited licence user
184.	20171117	Alazeem		new report fr_interco_open_trans for YonMing (GcTtReIO) - TSK-16483
185.	20171204	Maurice		Added integration for Nippon
186.	201712-5	Maurice		Remove Stock and transaction Nippon Integartion
187.	20171206	Selvam		Added "CMD - Cash Flows Classification" section(GcMcCfCc,GcMcCfCa) - for YonMing - TSK-16413
188. 	20171208	Alazeem		add GcAmCrIc For YonMing
189. 	20171208	Mohd Hafiz	Add New Report - Customer Credit Facilities - GcAmCrCf (fr_prn_crdt_fclts) for YonMing TSK-16534.
190.	20171228	Maurice		Added Cross Entity Stock Adjustment for Nttsu
191.	20180110	Saravanan	remove unavl report
192.	20180320	Maurice		Added release for picking
193.	20180413	Saravanan	new link for user system labels
194.	20180423	Saravanan	remove old system label
195.	20180530	Saravanan	added usrlbl_ref
196.	20180702	Selvam		Create new links GcAmCmUu,GcAmCmUa,GcAmCmVu,GcAmCmVa,GcAmCmbu,GcAmCmba - for Airfoil - TSK-17223
197.	20180730	Saravanan	new links for contact approval
198.	20181109	vantran		add report fr_monthly_cnt_list - TSK-17701 (DUHAL INDUSTRIAL AND TRADING JSC CL1358)
199.	20190108	lopper		Added new link Calendar Update (GcMcCh) - for YonMing - TSK-18087
200.	20190220	Maurice		remove News feed
201.	20190227 	Worawit 	fix missing create new link in GcAmCmUc for YonMing
202.	20190326	Maurice		Added Thyehong Sync
203.	20190327	Maurice		Remove Thyehong
204.	20190424	oliver		add g3ctrlcode
205.	20190621	Saravanan	added new link for KST SAP integration
206.	20190710	lamkhieu	add Import Registration No, GFP131, GFP132 - Rovski - TSK-19039
207.	20190710	vantran		add Import HS Codes, GFP133, GFP134 - Rovski Sdn Bhd CL1259 / TSK-19040
208.	20190808	vantran		new report fr_email_log_rpt - TNO Systems Pte Ltd CL1188 / TSK-19217
209.	20190814	lamkhieu	add GcCoAuHr and GcCoAuBe - TNO - TSK-19067
210.	20191009	Anthony		add new report fr_wflw_control_lst for TSK-19345
211	20191009	Nick		Vendor + Trade Group, added
212.	20191218	Aaron		Added TMS Activation
213.	20191226	Lopper 		add Expenses Management(GcMcCl), Leave Management(GcMcCq) for TNO TSK-19336
214.	20191226	Edwin		add stkdimen05, stkdimen06, stkdimen07, stkdimen08
215.	20200309	Aaron		Added tms_mfn
216.	20200318	ThaiTran	Add print footer for Transfer Request for Spectrum Audio Visual - TSK-20166
217. 	20200403 	Tran Thanh 	add Price Management (GcMcPm) for Yongmin (TSK-20183)
218.	20200429	Aaron		Moved TMS Activation to Master Settings
219. 	20200512 	Tran Thanh 	add new report fr_cust_master_export_csv_rpt (GFP139) for Hoyu (TSK-20563)
220 	20200529	Nick 		Vendor Portal, section, added
221	20200603	Nick 		updated:: TNOAR V-Portal Mgmt
222.	20200610	DingYong	add new report fr_approval_control_lst for Dynaciate
223.	20200808	TranLuong	add new report fr_user_dimen01_export_csv for hoyu TSK-20641 
224.	20200813	Saravanan	fix key structure
225.	20200929 	NgacTran 	add import stockcode price (GcMcPmSp) for Yon ming - TSK-21243
226.	20201102	chiaann		add fromunapprove to cir link for listing display purpose for CTS
227.	20201125	Lopper 		add Service Record(GFF161) for FORTUNA TSK-21536
228.	20201126	ThaiTran	add Import User Access Rights (GFP140, GFP141) for Triumphal Associates - TSK-21467
229.	20210118	ThaiTran	add Update Contact Mgmt (GFP142) for Yonming - TSK-21692
230.	20210322	Aaron		Added changes for Support Portal
231.	20210330	lamkhieu	add IP address control (ipaddctrl) - TSK-22188
232.	20210330	Maurice		Added Esker Sync
234.	20210831	Saravanan		Changes for subm_rfasg,subm_rfasc,subm_rfast
235.	20210109	Saravanan	changes for submit rfa
236.	20210908	Saravanan	added Form C-S Account Mapping
237.	20210914	DingYong	add print header and footer for stk_mi & stk_mw - Yit Hong
238.	20210923	vantran		add forex_import (GFM269, GFC159) - TNO Systems Pte Ltd CL1188 / TSK-22920
239.	20211004	Weida		add Auto Email Report Process auto_email_rpt_proc (GFM270) for GS PRECISION
240.	20211230	Saravanna	changes for  for prtprtlstgns
241.	20220228	ThaiTran 	change code for Import User Access Rights(GFP140, GFP141) - TNA
242.	20220309	Saravanan	added VIP Users
243.	20220419	Saravanan	Changes for project alloc by cost
244.	20220425	Saravanan	Cost Code Allocation By Project
245.	20220726	PhatDo		Added ACCPAC ACCOUNT MAPPING(accpacactmap) - TSK-24422
246.	20220916	Saravanan	email setting at company level
247. 	20221110 	Tran Thanh 	add new report fr_gps_loc_count_rpt (GFM310) for RH (TSK-24982)
248.	20221117	Saravanan	my document folder
249.	20230214	oliver		add admfeature(subsegm from actifeature) to control on/off Activate Personalize for Hentick
250.	20230419	Saravanan	changes for app_review
251.	20230613	PhatDo		add Reset Password resetpwd(GFM159) for CSC - TSK-25766
252.	20230818	NamLee		add new report Contact Credit Insurance (GFP143) for HSHMetal (TSK-26333)
253.	20231018	Maurice		Added BU account Mapping (GFP144)
254.	20231117	ThanhHung	Added prnsecu_sal_soe for Release SO (GFF164) (TSK-NA-hshmetal)
255. 	20231117 	Vinh 		add tms_config - TSK-26785
256.	20240108		Saravanan		added GcMcUsU
257.	20240223	Jasen		Add "apisetup"
258.	20240229	Jasen		Enhance "apisetup"
259.	20240328	Jasen		Move"apisetup" to master setting
260.	20240624	Huy Phan 	Added vportalvendormng
261.	20240704	PhucNguyen 	Added Product and Service Categories, Industry, Currency, Company Size
262.	20240730	Maurice		Added Whatapps Settup
263.	20240912	Maurice		Added new function for dashboard
264.	20240916	Maurice		Added transaction dhasboard
265.	20240920	Huy Phan 	Added import vendor
266.	20240930	Jasen		Add "moddeskright"
267.	20240930	oliver		comment out obsolete modules\
268.	20241004	Maurice		Added trasnaction
269.	20241013	oliver		add new report fr_user_enti_trans (GFM311)
270.	20241114	oliver		fix typo error
271.	20241122	Weida		move apisetup to company level
272.	20241129	Thap		added GFF165, GFF166 for EHP TSK-29211
273.	20241212	Jasen		Enhance "apisetup"
274.	20250127	Yan		add GFM275
275.	20250218	Yan		add GcMcReWl (GFM312)
276.	20250313	sonny		EN:sonny add emailsetup
277.	20250623	Mauirce		Added Mass functions
278. 	20250714 	DingYong 		add GcMcPe
279.	20250804	Huy Phan	Added C-Portal (Customer Portal | GcMcCp) & TNOAR C-Portal Mgmt
280. 	20250910 	Yan 		add GcMcWaSu (whatsapp setup)
281. 	20250915 	Yan 		change whatappsetup to whatsappsetup
282. 	20260113 	sonny 		added added Microsoft 365 SMTP (m365)
283. 	20260203 	sonny 		change description from Microsoft 365 SMTP to Microsoft 365 OAuth 2.0
284. 	20260219 	sonny 		added Upload Control Parameters
285. 	20260305 	Tran Thanh 	add Getfly Setup (GFC163)
286. 	20260312 	PhucNguyen 	add gencode Project Tender Master (GFF164) TSK-31374
287. 	20260318 	Tran Thanh 	remove Getfly Setup (GFC163)
288.	20260318	NamLee		add alloc_prj (GFC163) for ID ARCHITECTS (TSK-30803)
289.	20260407	Maurice		Added Shengtai Sync (GFC164)
290.	20260722	Lopper		Added ai asistaint
################################################################################################################# @--->
<!-- fnm: ns_wgp_AccessControl_1.cfm -->

<!---om 20240930 comment out
fAy( Tlt("<cfif set_language is 'english'>SMS Manager</cfif>"),'0',fAy(
fAy( Tlt("<cfif set_language is 'english'>Service Industry</cfif>"),'0',fAy(
	fAy( Tlt("<cfif set_language is 'english'>SMS Appointment</cfif>"),'1','a','S','y','set_gencode_topmain.cfm?fromlink=gencode&frommode=edit&fromsegm=sms_siapp','topmain','GcSmSiAp','GFS101'),
	fAy( Tlt("<cfif set_language is 'english'>SMS Monthly Usage</cfif>"),'1','a','S','y','set_gencode_topmain.cfm?fromlink=gencode&frommode=edit&fromsegm=sms_simnthly','topmain','GcSmSiMu','GFS102'),
	fAy( Tlt("<cfif set_language is 'english'>SMS Package Sales</cfif>"),'1','a','S','y','set_gencode_topmain.cfm?fromlink=gencode&frommode=edit&fromsegm=sms_sipksal','topmain','GcSmSiPk','GFS103'),
	fAy( Tlt("<cfif set_language is 'english'>Bulk SMS</cfif>"),'1','a','S','y','set_si_company_topmain.cfm?fromlink=srvi_appnt&frommode=new&fromsegm=sms_blast&fromtrans=sms_blast','topmain','GcSmSiBs','GFS104')
),'S','y','ns_wgp_tnomodules.cfm','topmain','GcSmSi',''),
fAy( Tlt("<cfif set_language is 'english'>SMS Master</cfif>"),'0',fAy(
	fAy( Tlt("<cfif set_language is 'english'>Manual SMS</cfif>"),'1','a','S','y','set_gencode_topmain.cfm?fromlink=gencode&frommode=edit&fromsegm=sms_mnl','topmain','GcSmMsMl','GFS105')
),'S','y','ns_wgp_tnomodules.cfm','topmain','GcSmMs','')
),'S','y','ns_wgp_tnomodules.cfm','topmain','GcSm',''),
--->

<cfoutput>
	<cfinclude template="inc_config_vportal_vendor.cfm">
	<cfif comain_tag_vindustry EQ '_cstrmain'>
		<cfset labelswc_salesmgr = Tlt("<cfif set_language is 'english'>Project Sales Manager</cfif>") >
		<cfset labelswc_sal_quo = Tlt("<cfif set_language is 'english'>Project Quotation</cfif>") >
		<cfset labelswc_sal_quo_imp = Tlt("<cfif set_language is 'english'>Import Project Quotation Data</cfif>") >
		<cfset labelswc_sal_soe = Tlt("<cfif set_language is 'english'>Project Sales Order</cfif>") >
		<cfset labelswc_sal_soc = Tlt("<cfif set_language is 'english'>Project SO Confirmation</cfif>") >
		<cfset labelswc_sal_inv = Tlt("<cfif set_language is 'english'>Tax Invoice</cfif>") >
	<cfelse>
		<cfset labelswc_salesmgr = Tlt("<cfif set_language is 'english'>Sales Manager</cfif>") >
		<cfset labelswc_sal_quo = Tlt("<cfif set_language is 'english'>Sales Quotation</cfif>") >
		<cfset labelswc_sal_quo_imp = Tlt("<cfif set_language is 'english'>Import Sales Quotation Data</cfif>") >
		<cfset labelswc_sal_soe = Tlt("<cfif set_language is 'english'>Sales Order</cfif>") >
		<cfset labelswc_sal_soc = Tlt("<cfif set_language is 'english'>Sales Order Confirmation</cfif>") >
		<cfset labelswc_sal_inv = Tlt("<cfif set_language is 'english'>Sales Invoice</cfif>") >
	</cfif>
	
	
	<CFINCLUDE template="ns_wgp_AccessControl_1L.cfm">
	
	<cfset myAry1c[glb_ary] = fAy( Tlt("<cfif set_language is 'english'>Globe3 Central</cfif>"),'0',fAy(
	fAy( Tlt("<cfif set_language is 'english'>Master Control</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>System Configuration</cfif>"),'0',fAy(
			fAy( Tlt("<cfif set_language is 'english'>Network</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=sysadmin&frommode=new&fromsegm=network','topmain','GcMcScNe','GFM101'),
			fAy( Tlt("<cfif set_language is 'english'>Control Code</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=sysadmin&frommode=new&fromsegm=g3ctrlcode','topmain','GcMcScSg','GFM267'),
			fAy( Tlt("<cfif set_language is 'english'>Cache Settings</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=sysadmin&frommode=new&fromsegm=g3cache','topmain','GcMcScGc','GFM155'),
			fAy( Tlt("<cfif set_language is 'english'>EDM Settings</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=sysadmin&frommode=new&fromsegm=edm','topmain','GcMcScGc','GFM275'),
			fAy( Tlt("<cfif set_language is 'english'>Database</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=sysadmin&frommode=new&fromsegm=database','topmain','GcMcScDb','GFM102'),
			fAy( Tlt("<cfif set_language is 'english'>Activate Features</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=sysadmin&frommode=new&fromsegm=actifeature','topmain','GcMcScAf','GFM103'),
			fAy( Tlt("<cfif set_language is 'english'>Corporate Levels</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=sysadmin&frommode=new&fromsegm=corplevel','topmain','GcMcScCl','GFM104'),
			fAy( Tlt("<cfif set_language is 'english'>Department Level</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=sysadmin&frommode=new&fromsegm=deptlevel','topmain','GcMcScDl','GFM105'),
			fAy( Tlt("<cfif set_language is 'english'>Contact Dimension</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=sysadmin&frommode=new&fromsegm=contactdimen','topmain','GcMcScCd','GFM106'),
			fAy( Tlt("<cfif set_language is 'english'>Leads Dimensions</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=sysadmin&frommode=new&fromsegm=leaddimen','topmain','GcMcScNq','GFM173'),
			fAy( Tlt("<cfif set_language is 'english'>Stock Dimension</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=sysadmin&frommode=new&fromsegm=stockdimen','topmain','GcMcScSd','GFM146'),
			fAy( Tlt("<cfif set_language is 'english'>User Dimensions</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=sysadmin&frommode=new&fromsegm=userdimen','topmain','GcMcScUd','GFM107'),
			fAy( Tlt("<cfif set_language is 'english'>User Fields</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=sysadmin&frommode=new&fromsegm=userfield','topmain','GcMcScUf','GFM108'),
			fAy( Tlt("<cfif set_language is 'english'>Main Transaction Fields Setting</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=sysadmin&frommode=new&fromsegm=transfields','topmain','GcMcScMf','GFM156'),
			fAy( Tlt("<cfif set_language is 'english'>Database Backup</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=sysadmin&frommode=new&fromsegm=databasebk','topmain','GcMcScBk','GFD236'),
			fAy( Tlt("<cfif set_language is 'english'>Lock System Configuration</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=sysadmin&frommode=new&fromsegm=locksysconfig','topmain','GcMcScLs','GFM109'),
			fAy( Tlt("<cfif set_language is 'english'>Email Setup</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=sysadmin&frommode=new&fromsegm=emailsetup','topmain','GcMcScEs','GFM313'),
			fAy( Tlt("<cfif set_language is 'english'>Microsoft 365 OAuth 2.0</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=sysadmin&frommode=new&fromsegm=m365','topmain','GcMcScms','GFM314')
		),'S','y','ns_wgp_tnomodules.cfm','topmain','GcMcSc',''),
	
		fAy( Tlt("<cfif set_language is 'english'>System Utility</cfif>"),'0',fAy(
			fAy( Tlt("<cfif set_language is 'english'>Purge Audit Data</cfif>"),'1','a','L','y','fin_glpost_topmain.cfm?fromlink=master&fromsegm=pug_aud','topmain','GcMcSuPa','GFM110'),
			fAy( Tlt("<cfif set_language is 'english'>Purge Non-Essential Data</cfif>"),'1','a','L','y','fin_glpost_topmain.cfm?fromlink=master&fromsegm=pug_ned','topmain','GcMcSuPe','GFM111'),
			fAy( Tlt("<cfif set_language is 'english'>Sync Setup Database</cfif>"),'1','a','L','y','fin_glpost_topmain.cfm?fromlink=master&fromsegm=sync_setda','topmain','GcMcSuSe','GFM112'),
			fAy( Tlt("<cfif set_language is 'english'>Sync Data</cfif>"),'1','a','L','y','fin_glpost_topmain.cfm?fromlink=master&fromsegm=sync_da','topmain','GcMcSuSy','GFM113'),
			fAy( Tlt("<cfif set_language is 'english'>Sync Data DB Server to DB Server</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=company&frommode=new&fromsegm=syncdb2db','topmain','GcMcSuSc','GFM152')
		),'S','y','ns_wgp_tnomodules.cfm','topmain','GcMcSu',''),
	
		fAy( Tlt("<cfif set_language is 'english'>Master Settings</cfif>"),'0',fAy(
			fAy( Tlt("<cfif set_language is 'english'>Admin Features</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=sysadmin&frommode=new&fromsegm=actifeature&fromsubsegm=admfeature','topmain','GcMcMaAf','GFM178'),
			fAy( Tlt("<cfif set_language is 'english'>Entity Group</cfif>"),'1','a','L','y','set_gencode_topmain.cfm?fromlink=master&frommode=edit&fromsegm=ent_grp','topmain','GcMcMaEg','GFM248'),
			fAy( Tlt("<cfif set_language is 'english'>Add New Company</cfif>"),'1','a','L','y','set_addco_topmain.cfm?fromlink=master&frommode=edit&fromsegm=addco','topmain','GcMcMaAd','GFM114'),
			fAy( Tlt("<cfif set_language is 'english'>Entity Map</cfif>"),'1','a','L','y','wgp_tnorighttop.cfm?bmm_ck_modules=wmodules_entmap','topmain','GcMcMaEm','GFM153'),
			fAy( Tlt("<cfif set_language is 'english'>Multi-Base Currency</cfif>"),'1','a','L','y','set_addco_topmain.cfm?fromlink=master&frommode=edit&fromsegm=addmbc','topmain','GcMcMaMb','GFM115'),
			fAy( Tlt("<cfif set_language is 'english'>Limited License User Type</cfif>"),'1','a','L','y','set_adduser_topmain.cfm?fromlink=master&frommode=new&fromsegm=ltdlic','topmain','GcMcMaLu','GFM160'),
			fAy( Tlt("<cfif set_language is 'english'>Limited License User Creation</cfif>"),'1','a','L','y','set_adduser_topmain.cfm?fromlink=master&frommode=new&fromsegm=ltdusr','topmain','GcMcMaLr','GFM161'),
			fAy( Tlt("<cfif set_language is 'english'>Restricted User Creation Type</cfif>"),'1','a','L','y','set_adduser_topmain.cfm?fromlink=master&frommode=new&fromsegm=restrtyp','topmain','GcMcMaRt','GFM158'),
			fAy( Tlt("<cfif set_language is 'english'>VIP Users Mgmt</cfif>"),'1','a','L','y','set_adduser_topmain.cfm?fromlink=master&frommode=new&fromsegm=vipusers','topmain','GcMcMaVu','GFM165'),
			fAy( Tlt("<cfif set_language is 'english'>Master Users Mgmt</cfif>"),'1','a','L','y','set_adduser_topmain.cfm?fromlink=master&frommode=new&fromsegm=users','topmain','GcMcMaMa','GFM116'),
			fAy( Tlt("<cfif set_language is 'english'>All Users Listing</cfif>"),'1','a','L','y','set_adduser_topmain.cfm?fromlink=master&frommode=edit&fromsegm=allusers','topmain','GcMcMaAl','GFM117'),
			fAy( Tlt("<cfif set_language is 'english'>Reset Password</cfif>"),'1','a','L','y','set_adduser_topmain.cfm?fromlink=master&frommode=edit&fromsegm=resetpwd','topmain','GcMcMaRe','GFM159'),
			fAy( Tlt("<cfif set_language is 'english'>Auto User Creation</cfif>"),'1','a','L','y','set_adduser_topmain.cfm?fromlink=master&frommode=edit&fromsegm=autouser','topmain','GcMcMaAu','GFM271'),
			fAy( Tlt("<cfif set_language is 'english'>MAC Address Control</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=master&frommode=new&fromsegm=macaddctrl','topmain','GcMcMaMc','GFM157'),
			fAy( Tlt("<cfif set_language is 'english'>IP Address Control</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=master&frommode=new&fromsegm=ipaddctrl','topmain','GcMcMaIp','GFM164'),
			fAy( Tlt("<cfif set_language is 'english'>Password Control</cfif>"),'1','a','L','y','set_gencode_topmain.cfm?fromlink=master&frommode=edit&fromsegm=passctrl','topmain','GcMcMaPc','GFM118'),
			fAy( Tlt("<cfif set_language is 'english'>Login Attempt Control</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=master&frommode=new&fromsegm=loginattemptctrl','topmain','GcMcMaLa','GFM252'),
			fAy( Tlt("<cfif set_language is 'english'>Usage History</cfif>"),'1','a','R','y','set_adduser_topmain.cfm?fromlink=master&frommode=new&fromsegm=userhistory&fromsubsegm=access','topmain','GcMcMaUs','GFM119'),
			fAy( Tlt("<cfif set_language is 'english'>User System Log</cfif>"),'1','a','R','y','wgp_sitemap_topmain.cfm?fromlink=usersyslog','topmain','GcMcMaUl','GFM151'),
			fAy( Tlt("<cfif set_language is 'english'>Country List</cfif>"),'1','a','L','y','set_gencode_topmain.cfm?fromlink=master&fromsegm=countrylist','topmain','GcMcMaCo','GFM120'),
			fAy( Tlt("<cfif set_language is 'english'>State List</cfif>"),'1','a','L','y','set_gencode_topmain.cfm?fromlink=master&fromsegm=statelist','topmain','GcMcMaSt','GFM256'),
			fAy( Tlt("<cfif set_language is 'english'>City List</cfif>"),'1','a','L','y','set_gencode_topmain.cfm?fromlink=master&fromsegm=citylist','topmain','GcMcMaCt','GFM257'),
			fAy( Tlt("<cfif set_language is 'english'>Location Type</cfif>"),'1','a','L','y','set_master_topmain.cfm?fromlink=master&frommode=edit&fromsegm=loctype','topmain','GcMcMaLo','GFM121'),
			fAy( Tlt("<cfif set_language is 'english'>Lock Master Control</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=master&frommode=new&fromsegm=locksysctrl','topmain','GcMcMaLk','GFM122'),
			fAy( Tlt("<cfif set_language is 'english'>Set Function Code</cfif>"),'1','a','S','y','wgp_ctrl_module_topmain.cfm?fromlink=master&frommode=new&fromsegm=functioncode','topmain','GcMcMaFk','GFM145'),
			fAy( Tlt("<cfif set_language is 'english'>Webservice Setup</cfif>"),'1','a','S','y','stk_setup_topmain.cfm?fromlink=master&frommode=new&fromsegm=wsdl_setup&fromcmdc=y','topmain','GcMcMaSs','GFM246'),
			fAy( Tlt("<cfif set_language is 'english'>TMS Activation</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=sysadmin&frommode=new&fromsegm=tmsactivation','topmain','GcMcMaTa','GFM268'),
			fAy( Tlt("<cfif set_language is 'english'>TMS Masterfn List</cfif>"),'1','a','L','y','set_gencode_topmain.cfm?fromlink=master&fromsegm=tms_mfn','topmain','GcMcMaTm','GFD291'),
			fAy( Tlt("<cfif set_language is 'english'>TMS Config File</cfif>"),'1','a','L','y','set_gencode_topmain.cfm?fromlink=master&fromsegm=tms_config','topmain','GcMcMaCf','GFM272'),
			fAy( Tlt("<cfif set_language is 'english'>Support Portal</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=sysadmin&frommode=new&fromsegm=supportportal&fromtrans=supportportal','topmain','GcMcMaSp','GFD292'),
			fAy( Tlt("<cfif set_language is 'english'>Auto Email Report Process</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=master&frommode=new&fromsegm=auto_email_rpt_proc','topmain','GcMcMaAe','GFM270'),
			fAy( Tlt("<cfif set_language is 'english'>API Usage Setup</cfif>"),'1','a','S','y','set_gencode_topmain.cfm?fromlink=company&frommode=new&fromsegm=apisetup','topmain','GcMcMaAs','GFM273'),
			fAy( Tlt("<cfif set_language is 'english'>Module Desktop User Access Right</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=master&frommode=new&fromsegm=moddeskright','topmain','GcMcMaMr','GFM274')
		),'S','y','ns_wgp_tnomodules.cfm','topmain','GcMcMa',''),
	
		fAy( Tlt("<cfif set_language is 'english'>Central Master Data</cfif>"),'0',fAy(
			fAy( Tlt("<cfif set_language is 'english'>Entities To Control</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=sysadmin&frommode=new&fromsegm=entities','topmain','GcMcCeEn','GFM123'),
			fAy( Tlt("<cfif set_language is 'english'>Master Data To Control</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=sysadmin&frommode=new&fromsegm=masdata','topmain','GcMcCeMd','GFM124'),
			fAy( "CMD "&Tlt("<cfif set_language is 'english'>Entity List</cfif>"),'1','a','S','y','set_addco_topmain.cfm?fromlink=master&frommode=edit&fromsegm=cmdc_co','topmain','GcMcCeEl','GFM249')
		),'S','y','ns_wgp_tnomodules.cfm','topmain','GcMcCe',''),
	
	
		fAy( Tlt("<cfif set_language is 'english'>CMD - General Codes</cfif>"),'0',GcMcGc,'S','y','ns_wgp_tnomodules.cfm','topmain','GcMcGc',''),
	
		fAy( Tlt("<cfif set_language is 'english'>CMD - Org Structure</cfif>"),'0',fAy(
			fAy( Tlt("<cfif set_language is 'english'>Division</cfif>"),'1','a','L','y','set_codes_topmain.cfm?fromlink=company&frommode=edit&fromsegm=deptclas&fromcmdc=y','topmain','GcMcOrDi','GFM233'),
			fAy( Tlt("<cfif set_language is 'english'>Department</cfif>"),'1','a','L','y','set_codes_topmain.cfm?fromlink=company&frommode=edit&fromsegm=deptcode&fromcmdc=y','topmain','GcMcOrDe','GFM234'),
			fAy( Tlt("<cfif set_language is 'english'>Business Unit</cfif>"),'1','a','L','y','set_codes_topmain.cfm?fromlink=company&frommode=edit&fromsegm=deptunit&fromcmdc=y','topmain','GcMcOrBu','GFM235')
		),'S','y','ns_wgp_tnomodules.cfm','topmain','GcMcOr',''),
	
		fAy( Tlt("<cfif set_language is 'english'>CMD - Forex And Rates</cfif>"),'0',fAy(
			fAy( Tlt("<cfif set_language is 'english'>Base To Forex Rates</cfif>"),'1','a','L','y','set_forex_topmain.cfm?fromlink=company&frommode=new&fromsegm=baseforex&fromsubsegm=general&fromcmdc=y','topmain','GcMcFoBf','GFM236'),
			fAy( Tlt("<cfif set_language is 'english'>GST Currency Rates</cfif>"),'1','a','L','y','set_forex_topmain.cfm?fromlink=company&frommode=new&fromsegm=baseforex&fromsubsegm=gstcurr&grpforex=y&fromcmdc=y','topmain','GcMcFoGs','GFM253'),
			fAy( Tlt("<cfif set_language is 'english'>Forex Import</cfif>"),'1','a','L','y','set_sysadmin_topmain.cfm?fromlink=company&frommode=new&fromsegm=forex_import&fromsubsegm=cmdc','topmain','GcMcFoFi','GFM269')
		),'S','y','ns_wgp_tnomodules.cfm','topmain','GcMcFo',''),
	
		fAy( Tlt("<cfif set_language is 'english'>CMD - Contact</cfif>"),'0',fAy(
			fAy( Tlt("<cfif set_language is 'english'>Contact</cfif>"),'1','a','A','y','adm_contact_topmain.cfm?fromlink=adminmgr&frommode=new&fromsegm=contact&fromtrans=contact&fromcmdc=y','topmain','GcMcCmCm','GFM238')
		),'S','y','ns_wgp_tnomodules.cfm','topmain','GcMcCm',''),
	
		fAy( Tlt("<cfif set_language is 'english'>CMD - Stock</cfif>"),'0',fAy(
				fAy( Tlt("<cfif set_language is 'english'>Stock Setup</cfif>"),'0',fAy(
					fAy( Tlt("UOM"),'1','a','L','y','stk_setup_topmain.cfm?fromlink=scm_stk_setup&frommode=new&fromsegm=uomstk&fromcmdc=y','topmain','GcMcSkStUo','GFM239'),
					fAy( Tlt("<cfif set_language is 'english'>Stock Category - Acctnum Link</cfif>"),'1','a','L','y','stk_setup_topmain.cfm?fromlink=scm_stk_setup&frommode=new&fromsegm=stkcatlnk&fromcmdc=y','topmain','GcMcSkStAc','GFM251')
				),'R','y','ns_wgp_tnomodules.cfm?','topmain','GcMcSkSt',''),
	
				fAy( Tlt("<cfif set_language is 'english'>Stock Classification</cfif>"),'0',fAy(
					fAy( Tlt("<cfif set_language is 'english'>Stock Group</cfif>"),'1','a','L','y','stk_setup_topmain.cfm?fromlink=scm_stk_setup&frommode=new&fromsegm=stkgrp&fromcmdc=y','topmain','GcMcSkScSg','GFM240'),
					fAy( Tlt("<cfif set_language is 'english'>Stock Sub-Group</cfif>"),'1','a','L','y','stk_setup_topmain.cfm?fromlink=scm_stk_setup&frommode=new&fromsegm=stksubgrp&fromcmdc=y','topmain','GcMcSkScSh','GFM241'),
					fAy( Tlt("<cfif set_language is 'english'>Stock Category</cfif>"),'1','a','L','y','stk_setup_topmain.cfm?fromlink=scm_stk_setup&frommode=new&fromsegm=stkcate&fromcmdc=y','topmain','GcMcSkScSt','GFM242'),
					fAy( Tlt("<cfif set_language is 'english'>Stock Sub-Category</cfif>"),'1','a','L','y','stk_setup_topmain.cfm?fromlink=scm_stk_setup&frommode=new&fromsegm=stksubcate&fromcmdc=y','topmain','GcMcSkScSf','GFM243'),
					fAy( Tlt("<cfif set_language is 'english'>Stock Class</cfif>"),'1','a','L','y','stk_setup_topmain.cfm?fromlink=scm_stk_setup&frommode=new&fromsegm=stkclas&fromcmdc=y','topmain','GcMcSkScSc','GFM244'),
					fAy( Tlt("<cfif set_language is 'english'>Stock Code</cfif>"),'1','a','A','y','stk_code_topmain.cfm?fromlink=scm_stk_setup&fromtrans=stk_code&frommode=new&fromsegm=stkcode&fromcmdc=y','topmain','GcMcSkScSd','GFM245'),
					fAy( Tlt("HS Code"),'1','a','A','y','stk_setup_topmain.cfm?fromlink=scm_stk_setup&fromtrans=hscode&frommode=new&fromsegm=hscode&fromcmdc=y','topmain','GcMcSkScHc','GFM247')
				),'R','y','ns_wgp_tnomodules.cfm?','topmain','GcMcSkSc',''),
	
				fAy( Tlt("<cfif set_language is 'english'>Price Management</cfif>"),'0',fAy(
					fAy( Tlt("<cfif set_language is 'english'>Stock Price Update</cfif>"),'1','a','L','y','trans_common1_topmain.cfm?fromlink=scm_stk_setup&frommode=new&fromtrans=stk_price_upd&fromcmdc=y','topmain','GcMcSkPmPu','GFM250')
				),'S','y','ns_wgp_tnomodules.cfm','topmain','GcMcSkPm','')
	
		),'S','y','ns_wgp_tnomodules.cfm','topmain','GcMcSk',''),
	
		fAy( Tlt("<cfif set_language is 'english'>CMD - Cash Flows Classification</cfif>"),'0',fAy(
			fAy( Tlt("<cfif set_language is 'english'>Cash Flows Code</cfif>"),'1','a','S','y','set_coa_topmain.cfm?fromlink=chartacct&frommode=edit&fromsegm=cfccode&fromcmdc=y','topmain','GcMcCfCc','GFM258'),
			fAy( Tlt("<cfif set_language is 'english'>Cash Flows Acctnum</cfif>"),'1','a','S','y','set_coa_topmain.cfm?fromlink=chartacct&frommode=edit&fromsegm=cfcacct&fromcmdc=y','topmain','GcMcCfCa','GFM259')
		),'S','y','ns_wgp_tnomodules.cfm','topmain','GcMcCf',''),
	
		fAy( Tlt("<cfif set_language is 'english'>CMD - Calendar Update</cfif>"),'0',fAy(
			fAy( Tlt("<cfif set_language is 'english'>Calendar Appointments</cfif>"),'1','a','S','y','crm_entry_topmain.cfm?fromlink=crm_cln&frommode=new&fromtrans=crm_calevnts&fromsegm=crm_calevnts&fromcmdc=y','topmain','GcMcChLp','GFM307')
		),'S','y','ns_wgp_tnomodules.cfm','topmain','GcMcCh',''),
	
		fAy( Tlt("<cfif set_language is 'english'>CMD - Price Management</cfif>"),'0',fAy(
			fAy( Tlt("<cfif set_language is 'english'>Import StockCode Price</cfif>"),'0',fAy(
				fAy( Tlt("<cfif set_language is 'english'>Upload Source File</cfif>"),'1','a','T','y','set_imagemgmt_topmain.cfm?fromlink=scm_stk_setup&frommode=new&fromsegm=upload_srcfile&fromsubsegm=ext_stk_price&fromcmdc=y','topmain','GcMcPmSpUp',''),
				fAy( Tlt("<cfif set_language is 'english'>Import StockCode Price</cfif>"),'1','a','L','y','stk_setup_topmain.cfm?fromlink=scm_stk_setup&frommode=new&fromtrans=impstk_price&fromsegm=impstk_price&fromcmdc=y','topmain','GcMcPmSpIm','')
			),'R','y','ns_wgp_tnomodules.cfm?','topmain','GcMcPmSp',''),
			fAy( Tlt("<cfif set_language is 'english'>Import Customer Group Pricing</cfif>"),'0',fAy(
				fAy( Tlt("<cfif set_language is 'english'>Upload Source File</cfif>"),'1','a','T','y','set_imagemgmt_topmain.cfm?fromlink=scm_stk_setup&frommode=new&fromsegm=upload_srcfile&fromsubsegm=imp_grp_price&fromcmdc=y','topmain','GcMcPmIpUp',''),
				fAy( Tlt("<cfif set_language is 'english'>Import Customer Group Pricing</cfif>"),'1','a','T','y','scm_externaldata_topmain.cfm?fromlink=scm_stk_setup&frommode=new&fromtrans=imp_grp_price&fromsegm=imp_grp_price&fromcmdc=y','topmain','GcMcPmIpIm','')
			),'R','y','ns_wgp_tnomodules.cfm?','topmain','GcMcPmIp','')
		),'S','y','ns_wgp_tnomodules.cfm','topmain','GcMcPm',''),
	
		fAy( Tlt("<cfif set_language is 'english'>CMD - Expenses Management</cfif>"),'0',fAy(
			fAy( Tlt("<cfif set_language is 'english'>Expense Class</cfif>"),'1','a','L','y','set_gencode_topmain.cfm?fromlink=ess_time_setup&frommode=new&fromsegm=exp_class&fromcmdc=y','topmain','GcMcClEc','EFE101'),
			fAy( Tlt("<cfif set_language is 'english'>Expense Type</cfif>"),'1','a','L','y','set_gencode_topmain.cfm?fromlink=ess_time_setup&frommode=new&fromsegm=exp_type&fromcmdc=y','topmain','GcMcClEt','EFE102')
		),'S','y','ns_wgp_tnomodules.cfm','topmain','GcMcCl',''),
	
		fAy( Tlt("<cfif set_language is 'english'>CMD - Leave Management</cfif>"),'0',fAy(
			fAy( Tlt("<cfif set_language is 'english'>Leave Class</cfif>"),'1','a','L','y','set_gencode_topmain.cfm?fromlink=ess_lev_setup&frommode=edit&fromsegm=leave_class&fromcmdc=y','topmain','GcMcCqLc','EFL101'),
			fAy( Tlt("<cfif set_language is 'english'>Leave Type</cfif>"),'1','a','L','y','set_gencode_topmain.cfm?fromlink=ess_lev_setup&frommode=edit&fromsegm=leave_type&fromcmdc=y','topmain','GcMcCqLt','EFL102')
		),'S','y','ns_wgp_tnomodules.cfm','topmain','GcMcCq',''),
	
		fAy( Tlt("<cfif set_language is 'english'>Contact Dimension</cfif>"),'0',fAy(
			fAy( Tlt("<cfif set_language is 'english'>Contact Dimen<!---@ TTRLN Dimension @---></cfif>") & " 1",'1','a','L','y','set_dimen_topmain.cfm?fromlink=master&frommode=edit&fromsegm=cntdimen01','topmain','GcMcCoC1','GFM125'),
			fAy( Tlt("<cfif set_language is 'english'>Contact Dimen<!---@ TTRLN Dimension @---></cfif>") & " 2",'1','a','L','y','set_dimen_topmain.cfm?fromlink=master&frommode=edit&fromsegm=cntdimen02','topmain','GcMcCoC2','GFM126'),
			fAy( Tlt("<cfif set_language is 'english'>Contact Dimen<!---@ TTRLN Dimension @---></cfif>") & " 3",'1','a','L','y','set_dimen_topmain.cfm?fromlink=master&frommode=edit&fromsegm=cntdimen03','topmain','GcMcCoC3','GFM127'),
			fAy( Tlt("<cfif set_language is 'english'>Contact Dimen<!---@ TTRLN Dimension @---></cfif>") & " 4",'1','a','L','y','set_dimen_topmain.cfm?fromlink=master&frommode=edit&fromsegm=cntdimen04','topmain','GcMcCoC4','GFM128')
		),'S','y','ns_wgp_tnomodules.cfm','topmain','GcMcCo',''),
	
		fAy( Tlt("<cfif set_language is 'english'>Leads Dimensions</cfif>"),'0',fAy(
			fAy( Tlt("<cfif set_language is 'english'>Lead Dim</cfif>") & " 1",'1','a','L','y','set_dimen_topmain.cfm?fromlink=master&frommode=edit&fromsegm=leaddimen01','topmain','GcMcLeC1','GFM171'),
			fAy( Tlt("<cfif set_language is 'english'>Lead Dim</cfif>") & " 2",'1','a','L','y','set_dimen_topmain.cfm?fromlink=master&frommode=edit&fromsegm=leaddimen02','topmain','GcMcLeC2','GFM172'),
			fAy( Tlt("<cfif set_language is 'english'>Lead Dim</cfif>") & " 3",'1','a','L','y','set_dimen_topmain.cfm?fromlink=master&frommode=edit&fromsegm=leaddimen03','topmain','GcMcLeC3','GFM174'),
			fAy( Tlt("<cfif set_language is 'english'>Lead Dim</cfif>") & " 4",'1','a','L','y','set_dimen_topmain.cfm?fromlink=master&frommode=edit&fromsegm=leaddimen04','topmain','GcMcLeC4','GFM175')
		),'S','y','ns_wgp_tnomodules.cfm','topmain','GcMcLe',''),
	
		fAy( Tlt("<cfif set_language is 'english'>Stock Dimension</cfif>"),'0',fAy(
			fAy( Tlt("<cfif set_language is 'english'>Stock Dimension</cfif>") & " 1",'1','a','L','y','set_dimen_topmain.cfm?fromlink=master&frommode=edit&fromsegm=stkdimen01','topmain','GcMcStS1','GFM147'),
			fAy( Tlt("<cfif set_language is 'english'>Stock Dimension</cfif>") & " 2",'1','a','L','y','set_dimen_topmain.cfm?fromlink=master&frommode=edit&fromsegm=stkdimen02','topmain','GcMcStS2','GFM148'),
			fAy( Tlt("<cfif set_language is 'english'>Stock Dimension</cfif>") & " 3",'1','a','L','y','set_dimen_topmain.cfm?fromlink=master&frommode=edit&fromsegm=stkdimen03','topmain','GcMcStS3','GFM149'),
			fAy( Tlt("<cfif set_language is 'english'>Stock Dimension</cfif>") & " 4",'1','a','L','y','set_dimen_topmain.cfm?fromlink=master&frommode=edit&fromsegm=stkdimen04','topmain','GcMcStS4','GFM150'),
			fAy( Tlt("<cfif set_language is 'english'>Stock Dimension</cfif>") & " 5",'1','a','L','y','set_dimen_topmain.cfm?fromlink=master&frommode=edit&fromsegm=stkdimen05','topmain','GcMcStS5','GFP135'),
			fAy( Tlt("<cfif set_language is 'english'>Stock Dimension</cfif>") & " 6",'1','a','L','y','set_dimen_topmain.cfm?fromlink=master&frommode=edit&fromsegm=stkdimen06','topmain','GcMcStS6','GFP136'),
			fAy( Tlt("<cfif set_language is 'english'>Stock Dimension</cfif>") & " 7",'1','a','L','y','set_dimen_topmain.cfm?fromlink=master&frommode=edit&fromsegm=stkdimen07','topmain','GcMcStS7','GFP137'),
			fAy( Tlt("<cfif set_language is 'english'>Stock Dimension</cfif>") & " 8",'1','a','L','y','set_dimen_topmain.cfm?fromlink=master&frommode=edit&fromsegm=stkdimen08','topmain','GcMcStS8','GFP138')
		),'S','y','ns_wgp_tnomodules.cfm','topmain','GcMcSt',''),
	
		fAy( Tlt("<cfif set_language is 'english'>User Dimensions</cfif>"),'0',fAy(
			fAy( Tlt("<cfif set_language is 'english'>User Dimension</cfif>") & " 1",'1','a','L','y','set_dimen_topmain.cfm?fromlink=master&frommode=edit&fromsegm=udimen01','topmain','GcMcUsU1','GFM129'),
			fAy( Tlt("<cfif set_language is 'english'>User Dimension</cfif>") & " 2",'1','a','L','y','set_dimen_topmain.cfm?fromlink=master&frommode=edit&fromsegm=udimen02','topmain','GcMcUsU2','GFM130'),
			fAy( Tlt("<cfif set_language is 'english'>User Dimension</cfif>") & " 3",'1','a','L','y','set_dimen_topmain.cfm?fromlink=master&frommode=edit&fromsegm=udimen03','topmain','GcMcUsU3','GFM131'),
			fAy( Tlt("<cfif set_language is 'english'>User Dimension</cfif>") & " 4",'1','a','L','y','set_dimen_topmain.cfm?fromlink=master&frommode=edit&fromsegm=udimen04','topmain','GcMcUsU4','GFM132')
		),'S','y','ns_wgp_tnomodules.cfm','topmain','GcMcUs','')	,
	
	
	
		fAy( Tlt("<cfif set_language is 'english'>User Defined System Labels</cfif>"),'0',fAy(
			fAy( Tlt("<cfif set_language is 'english'>Developers Labels Reference</cfif>"),'1','a','A','y','set_sysadmin_topmain.cfm?fromlink=sysadmin&frommode=new&fromsegm=usrlbl_ref','topmain','GcMcUlRf','GFM162'),
			fAy( Tlt("<cfif set_language is 'english'>Edit System Labels</cfif>"),'1','a','A','y','set_sysadmin_topmain.cfm?fromlink=sysadmin&frommode=new&fromsegm=usrlbl_edit','topmain','GcMcUlEd','GFM162'),
			fAy( Tlt("<cfif set_language is 'english'>Restore System Labels</cfif>"),'1','a','A','y','set_sysadmin_topmain.cfm?fromlink=sysadmin&frommode=new&fromsegm=usrlbl_rstr','topmain','GcMcUlRs','GFM163')
		),'S','y','ns_wgp_tnomodules.cfm','topmain','GcMcUl',''),
	
		fAy( Tlt("<cfif set_language is 'english'>Partner Portal</cfif>"),'0',fAy(
			fAy( Tlt("<cfif set_language is 'english'>Settings</cfif>"),'1','a','L','y','set_sysadmin_topmain.cfm?fromlink=sysadmin&frommode=new&fromsegm=prtprtlstgns','topmain','GcMcPpSt','GFM176'),
			fAy( Tlt("<cfif set_language is 'english'>Portal MAC</cfif>"),'1','a','L','y','ns_fr_topmain.cfm?btmFyl=ns_wgp_ctrl_module_Filter.cfm','topmain','GcMcPpMc','GFM137'),
			fAy( Tlt("<cfif set_language is 'english'>Portal Schema</cfif>"),'1','a','L','y','set_adduser_topmain.cfm?fromlink=master&frommode=new&fromsegm=portalUsers','topmain','GcMcPpUs','GFM138'),
			fAy( Tlt("<cfif set_language is 'english'>Portal Users</cfif>"),'1','a','L','y','set_adduser_topmain.cfm?fromlink=master&frommode=new&fromsegm=prtlUsrlst','topmain','GcMcPpln','GFM177')
		),'S','y','ns_wgp_tnomodules.cfm','topmain','GcMcPp',''),
	
		fAy( Tlt("<cfif set_language is 'english'>Vendor Portal</cfif>"),'0',fAy(
			fAy( Tlt("<cfif set_language is 'english'>V-Portal MAC</cfif>"),'1','a','L','y', 'wgp_ctrl_module_topmain.cfm?btmFyl=ns_wgp_ctrl_module_Filter.cfm','topmain','GcMcVpMc',''),
			fAy( Tlt("<cfif set_language is 'english'>V-Portal UEN Access</cfif>"),'1','a','L','y', 'set_adduser_topmain.cfm?fromlink=master&frommode=new','topmain','GcMcVpUa',''),
			fAy( Tlt("<cfif set_language is 'english'>V-Portal Vendor Management</cfif>"),'1','a','L','y', 'set_adduser_topmain.cfm?fromlink=master&frommode=new&fromsegm=#vportalConfigs.fromsegm#','topmain','GcMcVpVm','')
		),'S','y','ns_wgp_tnomodules.cfm','topmain','GcMcVp',''),
	
		fAy( Tlt("<cfif set_language is 'english'>Customer Portal</cfif>"),'0',fAy(
			fAy( Tlt("<cfif set_language is 'english'>C-Portal MAC</cfif>"),'1','a','L','y', 'wgp_ctrl_module_topmain.cfm?btmFyl=ns_wgp_ctrl_module_Filter.cfm','topmain','GcMcCpMc',''),
			fAy( Tlt("<cfif set_language is 'english'>C-Portal UEN Access</cfif>"),'1','a','L','y', 'set_cportal_topmain.cfm?fromlink=master&frommode=new&fromsegm=cp_uen_access','topmain','GcMcCpUa',''),
			fAy( Tlt("<cfif set_language is 'english'>C-Portal Customer Management</cfif>"),'1','a','L','y', 'set_cportal_topmain.cfm?fromlink=master&frommode=new&fromsegm=cp_customer_mng','topmain','GcMcCpCm','')
		),'S','y','ns_wgp_tnomodules.cfm','topmain','GcMcCp',''),
	
		fAy( Tlt("<cfif set_language is 'english'>TNOAR V-Portal Mgmt</cfif>"),'0',fAy(
			fAy( Tlt("<cfif set_language is 'english'>V-Portal Host Network</cfif>"),'1','a','L','y', 'set_gencode_topmain.cfm?fromsegm=vp_host','topmain','GcMcArHn',''),
			fAy( Tlt("<cfif set_language is 'english'>V-Portal Subscriber Users</cfif>"),'1','a','L','y', 'set_adduser_topmain.cfm?fromsegm=vp_user','topmain','GcMcArSu',''),
			fAy( Tlt("<cfif set_language is 'english'>Product and Service Categories</cfif>"),'1','a','L','y','set_gencode_topmain.cfm?fromlink=gencode&frommode=edit&fromsegm=product_ser_cate&fromcmdc=y','topmain','GcMcArPs',''),
			fAy( Tlt("<cfif set_language is 'english'>Industry</cfif>"),'1','a','L','y','set_gencode_topmain.cfm?fromlink=gencode&frommode=edit&fromsegm=industry&fromcmdc=y','topmain','GcMcArIn',''),
			fAy( Tlt("<cfif set_language is 'english'>Currency</cfif>"),'1','a','L','y','set_gencode_topmain.cfm?fromlink=gencode&frommode=edit&fromsegm=currency&fromcmdc=y','topmain','GcMcArCc',''),
			fAy( Tlt("<cfif set_language is 'english'>Company Size</cfif>"),'1','a','L','y','set_gencode_topmain.cfm?fromlink=gencode&frommode=edit&fromsegm=company_size&fromcmdc=y','topmain','GcMcArCz',''),
			fAy( Tlt("<cfif set_language is 'english'>Import Vendor</cfif>"),'1','a','L','y','set_gencode_topmain.cfm?fromlink=gencode&frommode=edit&fromsegm=import_vendor&fromcmdc=y','topmain','GcMcArIv','')
		),'S','y','ns_wgp_tnomodules.cfm','topmain','GcMcAr',''),
		
		fAy( Tlt("<cfif set_language is 'english'>TNOAR C-Portal Mgmt</cfif>"),'0',fAy(
			fAy( Tlt("<cfif set_language is 'english'>C-Portal Host Network</cfif>"),'1','a','L','y', 'set_gencode_topmain.cfm?fromsegm=cp_host','topmain','GcMcCrHn',''),
			fAy( Tlt("<cfif set_language is 'english'>C-Portal Subscriber Users</cfif>"),'1','a','L','y', 'set_adduser_topmain.cfm?fromsegm=cp_user','topmain','GcMcCrSu','')
		),'S','y','ns_wgp_tnomodules.cfm','topmain','GcMcCr',''),
	
		fAy( Tlt("<cfif set_language is 'english'>Peppol Mgmt</cfif>"),'0',fAy(
			fAy( Tlt("<cfif set_language is 'english'>Settings</cfif>"),'1','a','T','y', 'set_gencode_topmain.cfm?frommode=new&fromsegm=peppol_set','topmain','GcMcPeSt','')
		),'S','y','ns_wgp_tnomodules.cfm','topmain','GcMcPe',''),

		fAy( Tlt("<cfif set_language is 'english'>WhatsApp Mgmt</cfif>"),'0',fAy(
			fAy( Tlt("<cfif set_language is 'english'>WhatsApp Setup</cfif>"),'1','a','L','y', 'set_gencode_topmain.cfm?fromsegm=whatsapp_setup','topmain','GcMcWaSu','')
		),'S','y','ns_wgp_tnomodules.cfm','topmain','GcMcWa',''),
		
		fAy( Tlt("<cfif set_language is 'english'>Report</cfif>"),'0',fAy(
			fAy( Tlt("<cfif set_language is 'english'>User Access By Entity</cfif>"),'1','a','L','y','wgp_sitemap_topmain.cfm?fromlink=user_access_entity&frommode=new&fromsegm=report&fromsubsegm=grphrpt','topmain','GcMcReUe','GFM154'),
			fAy( Tlt("<cfif set_language is 'english'>User Listing Report</cfif>"),'1','a','R','y','ns_fr_topmain.cfm?topHdr=Reports&btmFyl=fr_scm_prelim.cfm&fromlink=master&fromreport=fr_user_list_rpt','topmain','GcMcReUl','GFM255'),
			fAy( Tlt("<cfif set_language is 'english'>User Access Entity And Transaction</cfif>"),'1','a','R','y','ns_fr_topmain.cfm?topHdr=Reports&btmFyl=fr_scm_prelim.cfm&fromlink=master&fromreport=fr_user_enti_trans','topmain','GcMcReUt','GFM311'),
			fAy( Tlt("<cfif set_language is 'english'>Email Log Report</cfif>"),'1','a','R','y','ns_fr_topmain.cfm?topHdr=Reports&btmFyl=fr_scm_prelim.cfm&fromlink=master&fromreport=fr_email_log_rpt','topmain','GcMcReEl','GFM308'),
			fAy( Tlt("<cfif set_language is 'english'>WhatsApp Log Report</cfif>"),'1','a','R','y','ns_fr_topmain.cfm?topHdr=Reports&btmFyl=fr_scm_prelim.cfm&fromlink=master&fromreport=fr_whatsapp_log_rpt','topmain','GcMcReWl','GFM312'),
			fAy( Tlt("<cfif set_language is 'english'>Dimen01 Export To CSV</cfif>"),'1','a','R','y','ns_fr_topmain.cfm?topHdr=Reports&btmFyl=fr_scm_prelim.cfm&fromlink=master&fromreport=fr_user_dimen01_export_csv','topmain','GcMcReDm','GFM309'),
			fAy( Tlt("<cfif set_language is 'english'>GPS Location Count</cfif>") & ' (' & Tlt("<cfif set_language is 'english'>Google Map</cfif>") & ') ' & Tlt("<cfif set_language is 'english'>Report</cfif>"),'1','a','R','y','ns_fr_topmain.cfm?topHdr=Reports&btmFyl=fr_scm_prelim.cfm&fromlink=master&fromreport=fr_gps_loc_count_rpt','topmain','GcMcReGl','GFM310'),
			fAy( Tlt("<cfif set_language is 'english'>AI Assistant Dashboard</cfif>"),'1','a','R','y','ns_fr_topmain.cfm?topHdr=Reports&btmFyl=admin_dashboard.cfm&fromlink=master&fromreport=ai_assistant_dashboard','topmain','GcMcReAd','GFM315')
		),'S','y','ns_wgp_tnomodules.cfm','topmain','GcMcRe','')
	
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcMc',''),
	
	
	
	
	fAy( Tlt("<cfif set_language is 'english'>Holding Control</cfif>"),'0',fAy(
	fAy( Tlt("<cfif set_language is 'english'>Holding Control</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>Add New Company</cfif>"),'1','a','L','y','set_addco_topmain.cfm?fromlink=master&frommode=edit&fromsegm=addco','topmain','GcHcHcAd','GFM139'),
		fAy( Tlt("<cfif set_language is 'english'>Holding Users Mgmt</cfif>"),'1','a','L','y','set_adduser_topmain.cfm?fromlink=master&frommode=new&fromsegm=users','topmain','GcHcHcMa','GFM140'),
		fAy( Tlt("<cfif set_language is 'english'>Usage History</cfif>"),'1','a','R','y','set_adduser_topmain.cfm?fromlink=master&frommode=new&fromsegm=userhistory&fromsubsegm=access','topmain','GcHcHcUs','GFM141')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcHcHc','')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcHc',''),
	
	
	
	
	fAy( Tlt("<cfif set_language is 'english'>Group Control</cfif>"),'0',fAy(
	fAy( Tlt("<cfif set_language is 'english'>Group Control</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>Add New Company</cfif>"),'1','a','L','y','set_addco_topmain.cfm?fromlink=master&frommode=edit&fromsegm=addco','topmain','GcGrGcAd','GFM142'),
		fAy( Tlt("<cfif set_language is 'english'>Group Users Mgmt</cfif>"),'1','a','L','y','set_adduser_topmain.cfm?fromlink=master&frommode=new&fromsegm=users','topmain','GcGrGcMa','GFM143'),
		fAy( Tlt("<cfif set_language is 'english'>Usage History</cfif>"),'1','a','R','y','set_adduser_topmain.cfm?fromlink=master&frommode=new&fromsegm=userhistory&fromsubsegm=access','topmain','GcGrGcUs','GFM144')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcGrGc','')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcGr',''),
	
	
	
	
	fAy( Tlt("<cfif set_language is 'english'>Company Control</cfif>"),'0',fAy(
	fAy( Tlt("<cfif set_language is 'english'>Company Setting</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>Company Info</cfif>"),'1','a','S','y','set_company_topmain.cfm?fromlink=company&frommode=new&fromsegm=companyinfo','topmain','GcCoCoCo','GFC101'),
		fAy( Tlt("<cfif set_language is 'english'>Share Register</cfif>"),'1','a','S','y','set_company_topmain.cfm?fromlink=company&frommode=new&fromsegm=share_reg','topmain','GcCoCoSh','GFC102'),
		fAy( Tlt("<cfif set_language is 'english'>Entities Owned</cfif>"),'1','a','S','y','set_company_topmain.cfm?fromlink=company&frommode=new&fromsegm=ent_ownd','topmain','GcCoCoEn','GFC103'),
		fAy( Tlt("<cfif set_language is 'english'>Activate Features</cfif>"),'1','a','S','y','set_company_topmain.cfm?fromlink=company&frommode=new&fromsegm=actifeature','topmain','GcMcCoAc','GFC104'),
		fAy( Tlt("<cfif set_language is 'english'>Vertical Industry</cfif>"),'1','a','S','y','set_company_topmain.cfm?fromlink=company&frommode=new&fromsegm=vindustry','topmain','GcCoCoVe','GFC105'),
		fAy( Tlt("<cfif set_language is 'english'>National Jurisdiction</cfif>"),'1','a','S','y','set_company_topmain.cfm?fromlink=company&frommode=new&fromsegm=jurisdiction','topmain','GcCoCoNa','GFC106'),
		fAy( Tlt("<cfif set_language is 'english'>Primary Language<!---@ TTRLN G3 System Main Language @---></cfif>"),'1','a','S','y','set_company_topmain.cfm?fromlink=company&frommode=new&fromsegm=prilang','topmain','GcCoCoPr','GFC107'),
		fAy( Tlt("<cfif set_language is 'english'>Unit Price Decimal Place</cfif>"),'1','a','S','y','set_company_topmain.cfm?fromlink=company&frommode=new&fromsegm=upricedecimal','topmain','GcCoCoUn','GFC108'),
		fAy( Tlt("<cfif set_language is 'english'>Transaction Datasource</cfif>"),'1','a','S','y','set_gencode_topmain.cfm?fromlink=company&frommode=new&fromsegm=datasource','topmain','GcCoCoDs','GFC109'),
		fAy( Tlt("<cfif set_language is 'english'>Transaction Type</cfif>"),'1','a','S','y','set_gencode_topmain.cfm?fromlink=company&frommode=new&fromsegm=transactiontype','topmain','GcCoCoOp','GFC110'),
		fAy( Tlt("<cfif set_language is 'english'>Financial Year</cfif>"),'1','a','L','y','set_fyear_topmain.cfm?fromlink=company&frommode=edit&fromsegm=fyear','topmain','GcCoCoFi','GFC111'),
		fAy( Tlt("<cfif set_language is 'english'>Location Group</cfif>"),'1','a','L','y','set_gencode_topmain.cfm?fromlink=#fromlink#&frommode=new&fromsegm=locationgrp','topmain','GcCoCoLg','GFC112'),
		fAy( Tlt("<cfif set_language is 'english'>Location Name</cfif>"),'1','a','L','y','set_company_topmain.cfm?fromlink=company&frommode=new&fromsegm=location','topmain','GcCoCoLc','GFC113'),
		fAy( Tlt("<cfif set_language is 'english'>GL Allocation</cfif>"),'1','a','L','y','set_company_topmain.cfm?fromlink=company&frommode=new&fromsegm=alloc','topmain','GcCoCoGl','GFC114'),
		fAy( Tlt("<cfif set_language is 'english'>GL Allocation By Acctnum By Project</cfif>"),'1','a','L','y','set_company_topmain.cfm?fromlink=company&frommode=new&fromsegm=alloc_prj','topmain','GcCoCoAp','GFC163'),
		fAy( Tlt("<cfif set_language is 'english'>Recur Document</cfif>"),'1','a','S','y','set_company_topmain.cfm?fromlink=company&frommode=new&fromsegm=recur','topmain','GcCoCoRe','GFC115'),
		fAy( Tlt("<cfif set_language is 'english'>Lock Company Control</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=company&frommode=new&fromsegm=lockcoctrl','topmain','GcCoCoLo','GFC116'),
		fAy( Tlt("<cfif set_language is 'english'>User Defined Stock Dimensions</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=company&frommode=new&fromsegm=UdfStkDim','topmain','GcCoCoSd','GFC145'),
		fAy( Tlt("<cfif set_language is 'english'>User Defined Dimensions And Fields</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=company&frommode=new&fromsegm=UdfTrnSet','topmain','GcCoCoDf','GFC117'),
		fAy( Tlt("<cfif set_language is 'english'>User Defined Dimensions And Account Number</cfif>"),'1','a','S','y','set_company_topmain.cfm?fromlink=company&frommode=new&fromsegm=userdimacct','topmain','GcCoCoUa','GFC153'),
		fAy( Tlt("<cfif set_language is 'english'>Email Setup</cfif>"),'1','a','S','y','set_company_topmain.cfm?fromlink=company&frommode=new&fromsegm=compemail','topmain','GcCoCoEm','GFC160'),
		fAy( Tlt("<cfif set_language is 'english'>Whatsapp Setup</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=company&frommode=new&fromsegm=whatsappsetup','topmain','GcCoCoWs','GFC161'),
		fAy( Tlt("<cfif set_language is 'english'>API Usage Setup</cfif>"),'1','a','S','y','set_gencode_topmain.cfm?fromlink=company&frommode=new&fromsegm=apisetup','topmain','GcCoCoAs','GFC162')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcCoCo',''),
	
	fAy( Tlt("<cfif set_language is 'english'>Company System Utility</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>Import Data</cfif>"),'1','a','L','y','set_sysadmin_topmain.cfm?fromlink=company&fromsegm=sycn_import','topmain','GcCoSuId','GFC146'),
		fAy( Tlt("<cfif set_language is 'english'>Export Data</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=company&fromsegm=sycn_export','topmain','GcCoSuEd','GFC147'),
		fAy( Tlt("<cfif set_language is 'english'>Shared Folder Settings</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=company&fromsegm=shrdfldr','topmain','GcCoSuSf','GFC150'),
		fAy( Tlt("<cfif set_language is 'english'>Contact Master</cfif>"),'0',fAy(
			fAy( Tlt("<cfif set_language is 'english'>Mass Inactive / Delete Contacts</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=company&fromsegm=ar_clean_cnt','topmain','GcCoSuCmIc','GFC151')
		),'S','y','ns_wgp_tnomodules.cfm','topmain','GcCoSuCm',''),
		fAy( Tlt("<cfif set_language is 'english'>Stock Master</cfif>"),'0',fAy(
			fAy( Tlt("<cfif set_language is 'english'>Mass Inactive / Delete Stocks</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=company&fromsegm=ar_clean_sku','topmain','GcCoSuSmIc','GFC152')
		),'S','y','ns_wgp_tnomodules.cfm','topmain','GcCoSuSm',''),
		fAy( Tlt("<cfif set_language is 'english'>Project Master</cfif>"),'0',fAy(
			fAy( Tlt("<cfif set_language is 'english'>Mass Inactive / Closed Project</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=company&fromsegm=ar_clean_prj','topmain','GcCoSuPmIc','GFC153')
		),'S','y','ns_wgp_tnomodules.cfm','topmain','GcCoSuPm',''),
		fAy( Tlt("<cfif set_language is 'english'>Employee Master</cfif>"),'0',fAy(
			fAy( Tlt("<cfif set_language is 'english'>Mass Inactive / Delete Employee</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=company&fromsegm=ar_clean_emp','topmain','GcCoSuEmIc','GFC154')
		),'S','y','ns_wgp_tnomodules.cfm','topmain','GcCoSuEm',''),
			fAy( Tlt("<cfif set_language is 'english'>Transaction Management</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>Mass Closed Transactions</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=company&fromsegm=ar_clean_trans','topmain','GcCoSuTmIc','GFC155')
		),'S','y','ns_wgp_tnomodules.cfm','topmain','GcCoSuTm','')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcCoSu',''),
	
	fAy( Tlt("<cfif set_language is 'english'>System Integration</cfif>"),'0',fAy(
		fAy( Tlt("SAP"),'0',fAy(
		    fAy( Tlt("<cfif set_language is 'english'>Open PO</cfif>"),'1','A','R','y','ns_fr_topmain.cfm?topHdr=Reports&btmFyl=fr_scm_prelim.cfm&fromlink=scm_purc_report&fromreport=fr_poc_outsg_sap','topmain','GcCoSiSaPo','GFC148'),
		    fAy( Tlt("<cfif set_language is 'english'>Open SO</cfif>"),'1','A','R','y','ns_fr_topmain.cfm?topHdr=Reports&btmFyl=fr_scm_prelim.cfm&fromlink=scm_sales_report&fromreport=fr_soc_outsg1_sap','topmain','GcCoSiSaSo','GFC149')
		),'R','y','ns_wgp_tnomodules.cfm?','topmain','GcCoSiSa',''),
		fAy( Tlt("E2Open"),'0',fAy(
		    fAy( Tlt("<cfif set_language is 'english'>Import</cfif>"),'1','a','L','y','set_sysadmin_topmain.cfm?fromlink=company&fromsegm=e2open_inbox','topmain','GcCoSiEoIn','GFC151'),
		    fAy( Tlt("<cfif set_language is 'english'>Export<!---@ TTRLN To Excel @---></cfif>"),'1','a','L','y','set_sysadmin_topmain.cfm?fromlink=company&fromsegm=e2open_outbox','topmain','GcCoSiEoOu','GFC152')
		),'R','y','ns_wgp_tnomodules.cfm?','topmain','GcCoSiEo',''),
		fAy( Tlt("<cfif set_language is 'english'>Nippon Express</cfif>"),'0',fAy(
		    fAy( Tlt("<cfif set_language is 'english'>Import</cfif>"),'1','a','L','y','set_sysadmin_topmain.cfm?fromlink=company&fromsegm=nippon_inbox','topmain','GcCoSiNeIn','GFC154'),
		    fAy( Tlt("<cfif set_language is 'english'>Export<!---@ TTRLN To Excel @---></cfif>"),'1','a','L','y','set_sysadmin_topmain.cfm?fromlink=company&fromsegm=nippon_outbox','topmain','GcCoSiNeOu','GFC155')
		),'R','y','ns_wgp_tnomodules.cfm?','topmain','GcCoSiEo',''),
		fAy( Tlt("<cfif set_language is 'english'>Cross Entity Stock Adjustment</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=company&fromsegm=ce_stk_trans','topmain','GcCoSiSa','GFC156'),
		fAy( Tlt("<cfif set_language is 'english'>Esker Master Data Sync</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=company&fromsegm=esker_sync','topmain','GcCoSiSy','GFC158'),
		fAy( Tlt("<cfif set_language is 'english'>WMS Sync</cfif>"),'1','a','S','y','set_sysadmin_topmain.cfm?fromlink=company&fromsegm=wms_sync','topmain','GcCoSiWm','GFC164')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcCoSi',''),
	
	fAy( Tlt("GST / VAT"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>Settings</cfif>"),'1','a','S','y','set_company_topmain.cfm?fromlink=company&frommode=new&fromsegm=vatgst','topmain','GcCoGsGs','GFC118'),
		fAy( Tlt("<cfif set_language is 'english'>Sales Taxable</cfif>"),'1','a','L','y','set_gencode_topmain.cfm?fromlink=gencode&frommode=edit&fromsegm=gststax','topmain','GcCoGsSt','GFC119'),
		fAy( Tlt("<cfif set_language is 'english'>Sales Non-Taxable</cfif>"),'1','a','L','y','set_gencode_topmain.cfm?fromlink=gencode&frommode=edit&fromsegm=gstsntax','topmain','GcCoGsSn','GFC120'),
		fAy( Tlt("<cfif set_language is 'english'>Purc Taxable</cfif>"),'1','a','L','y','set_gencode_topmain.cfm?fromlink=gencode&frommode=edit&fromsegm=gstptax','topmain','GcCoGsPt','GFC121'),
		fAy( Tlt("<cfif set_language is 'english'>Purc Non-Taxable</cfif>"),'1','a','L','y','set_gencode_topmain.cfm?fromlink=gencode&frommode=edit&fromsegm=gstpntax','topmain','GcCoGsPn','GFC122')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcCoGs',''),
	
	
	fAy( Tlt("<cfif set_language is 'english'>US Sales Tax</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>US States</cfif>"),'1','a','L','y','set_gencode_topmain.cfm?fromlink=gencode&frommode=edit&fromsegm=usstates','topmain','GcCoUsSs','GFC123')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcCoUs',''),
	
	fAy( Tlt("<cfif set_language is 'english'>Group Forex And Rates</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>Base To Forex Rates</cfif>"),'1','a','L','y','set_forex_topmain.cfm?fromlink=company&frommode=new&fromsegm=baseforex&fromsubsegm=general&grpforex=y','topmain','GcCoGfBf','GFC124'),
		fAy( Tlt("<cfif set_language is 'english'>GST Currency Rates</cfif>"),'1','a','L','y','set_forex_topmain.cfm?fromlink=company&frommode=new&fromsegm=baseforex&fromsubsegm=gstcurr&grpforex=y','topmain','GcCoGfGs','GFC125'),
		fAy( Tlt("<cfif set_language is 'english'>Internal Forex Rates</cfif>"),'1','a','L','y','set_forex_topmain.cfm?fromlink=company&frommode=new&fromsegm=baseforex&fromsubsegm=intcurr&grpforex=y','topmain','GcCoGfIf','GFC126')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcCoGf',''),
	
	fAy( Tlt("<cfif set_language is 'english'>Forex And Rates</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>Base Currency</cfif>"),'1','a','S','y','set_forex_topmain.cfm?fromlink=company&frommode=edit&fromsegm=basecurr','topmain','GcCoFoBc','GFC127'),
		fAy( Tlt("<cfif set_language is 'english'>GST/VAT Currency</cfif>"),'1','a','S','y','set_forex_topmain.cfm?fromlink=company&frommode=edit&fromsegm=gstcurr','topmain','GcCoFoGc','GFC128'),
		fAy( Tlt("<cfif set_language is 'english'>Base To Forex Rates</cfif>"),'1','a','L','y','set_forex_topmain.cfm?fromlink=company&frommode=new&fromsegm=baseforex&fromsubsegm=general','topmain','GcCoFoBf','GFC129'),
		fAy( Tlt("<cfif set_language is 'english'>Forex To Forex Rates</cfif>"),'1','a','L','y','set_forex_topmain.cfm?fromlink=company&frommode=new&fromsegm=forexforex&fromsubsegm=general','topmain','GcCoFoFf','GFC130'),
		fAy( Tlt("<cfif set_language is 'english'>Customs Rates</cfif>"),'1','a','L','y','set_forex_topmain.cfm?fromlink=company&frommode=new&fromsegm=baseforex&fromsubsegm=customs','topmain','GcCoFoCu','GFC131'),
		fAy( Tlt("<cfif set_language is 'english'>GST Currency Rates</cfif>"),'1','a','L','y','set_forex_topmain.cfm?fromlink=company&frommode=new&fromsegm=baseforex&fromsubsegm=gstcurr','topmain','GcCoFoGs','GFC132'),
		fAy( Tlt("<cfif set_language is 'english'>Internal Forex Rates</cfif>"),'1','a','L','y','set_forex_topmain.cfm?fromlink=company&frommode=new&fromsegm=baseforex&fromsubsegm=intcurr','topmain','GcCoFoIf','GFC133'),
		fAy( Tlt("<cfif set_language is 'english'>Forex Import</cfif>"),'1','a','L','y','set_sysadmin_topmain.cfm?fromlink=company&frommode=new&fromsegm=forex_import','topmain','GcCoFoFi','GFC159')
	
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcCoFo',''),
	fAy( Tlt("<cfif set_language is 'english'>Org Structure</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>Level</cfif>") & " 1",'1','a','L','y','set_codes_topmain.cfm?fromlink=company&frommode=edit&fromsegm=deptorg1','topmain','GcCoOrL1','GFC134'),
		fAy( Tlt("<cfif set_language is 'english'>Level</cfif>") & " 2",'1','a','L','y','set_codes_topmain.cfm?fromlink=company&frommode=edit&fromsegm=deptorg2','topmain','GcCoOrL2','GFC135'),
		fAy( Tlt("<cfif set_language is 'english'>Level</cfif>") & " 3",'1','a','L','y','set_codes_topmain.cfm?fromlink=company&frommode=edit&fromsegm=deptorg3','topmain','GcCoOrL3','GFC136'),
		fAy( Tlt("<cfif set_language is 'english'>Division</cfif>"),'1','a','L','y','set_codes_topmain.cfm?fromlink=company&frommode=edit&fromsegm=deptclas','topmain','GcCoOrDi','GFC137'),
		fAy( Tlt("<cfif set_language is 'english'>Department</cfif>"),'1','a','L','y','set_codes_topmain.cfm?fromlink=company&frommode=edit&fromsegm=deptcode','topmain','GcCoOrDe','GFC138'),
		fAy( Tlt("<cfif set_language is 'english'>Business Unit</cfif>"),'1','a','L','y','set_codes_topmain.cfm?fromlink=company&frommode=edit&fromsegm=deptunit','topmain','GcCoOrBu','GFC139'),
		fAy( Tlt("<cfif set_language is 'english'>Team</cfif>"),'1','a','L','y','set_codes_topmain.cfm?fromlink=company&frommode=edit&fromsegm=deptteam','topmain','GcCoOrTm','')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcCoOr',''),
	
	fAy( Tlt("<cfif set_language is 'english'>Mapping (One to Many)</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>BU Account Mapping</cfif>"),'1','a','S','y','set_coa_topmain.cfm?fromlink=company&frommode=edit&fromsegm=bumapmultiple','topmain','GcCoMaBu','GFP144')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcCoMa',''),
	
	fAy( Tlt("<cfif set_language is 'english'>Auto Number Control</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>Finance</cfif>"),'1','a','S','y','set_transet_topmain.cfm?fromlink=company&frommode=new&fromsegm=autonum&fromsubsegm=fin','topmain','GcCoAuFi','GFC140'),
		fAy( Tlt("<cfif set_language is 'english'>Supply Chain</cfif>"),'1','a','S','y','set_transet_topmain.cfm?fromlink=company&frommode=new&fromsegm=autonum&fromsubsegm=scm','topmain','GcCoAuSu','GFC141'),
		fAy( Tlt("<cfif set_language is 'english'>Employee Self Service</cfif>"),'1','a','S','y','set_transet_topmain.cfm?fromlink=company&frommode=new&fromsegm=autonum&fromsubsegm=ess','topmain','GcCoAuEm','GFC142'),
		fAy( Tlt("<cfif set_language is 'english'>Enterprise Project</cfif>"),'1','a','S','y','set_transet_topmain.cfm?fromlink=company&frommode=new&fromsegm=autonum&fromsubsegm=entproj','topmain','GcCoAuEn','GFC143'),
		fAy( Tlt("<cfif set_language is 'english'>Fleet Management</cfif>"),'1','a','S','y','set_transet_topmain.cfm?fromlink=company&frommode=new&fromsegm=autonum&fromsubsegm=flt','topmain','GcCoAuFl','GFC144'),
		fAy( Tlt("<cfif set_language is 'english'>Human Resource</cfif>"),'1','a','S','y','set_transet_topmain.cfm?fromlink=company&frommode=new&fromsegm=autonum&fromsubsegm=hr','topmain','GcCoAuHr','GFC157'),
		fAy( Tlt("<cfif set_language is 'english'>Benefits Management</cfif>"),'1','a','S','y','set_transet_topmain.cfm?fromlink=company&frommode=new&fromsegm=autonum&fromsubsegm=ben','topmain','GcCoAuBe','GFC158')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcCoAu',''),
	
	fAy( Tlt("<cfif set_language is 'english'>User Dimensions</cfif>"),'0',fAy(
			fAy( Tlt("<cfif set_language is 'english'>User Dimension</cfif>") & " 1",'1','a','L','y','set_dimen_topmain.cfm?fromlink=company&frommode=edit&fromsegm=udimen01','topmain','GcCcUsU1','GFM129'),
			fAy( Tlt("<cfif set_language is 'english'>User Dimension</cfif>") & " 2",'1','a','L','y','set_dimen_topmain.cfm?fromlink=company&frommode=edit&fromsegm=udimen02','topmain','GcCcUsU2','GFM130'),
			fAy( Tlt("<cfif set_language is 'english'>User Dimension</cfif>") & " 3",'1','a','L','y','set_dimen_topmain.cfm?fromlink=company&frommode=edit&fromsegm=udimen03','topmain','GcCcUsU3','GFM131'),
			fAy( Tlt("<cfif set_language is 'english'>User Dimension</cfif>") & " 4",'1','a','L','y','set_dimen_topmain.cfm?fromlink=company&frommode=edit&fromsegm=udimen04','topmain','GcCcUsU4','GFM132')
		),'S','y','ns_wgp_tnomodules.cfm','topmain','GcCcUs','')	,
		
	fAy( Tlt("<cfif set_language is 'english'>Reports</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>Base To Forex Graphical Report</cfif>"),'1','a','R','y','ns_fr_topmain.cfm?topHdr=Reports&btmFyl=fr_common1_prelim.cfm&fromlink=company&frommode=new&fromsegm=report&fromsubsegm=grphrpt&fromreport=fr_forex_graph','topmain','GcCoReGr','GRC101'),
		fAy( Tlt("<cfif set_language is 'english'>Base To Forex Daily List</cfif>"),'1','a','R','y','ns_fr_topmain.cfm?topHdr=Reports&btmFyl=fr_common1_prelim.cfm&fromlink=company&frommode=new&fromsegm=report&fromsubsegm=dlylst&fromreport=fr_forex_daily','topmain','GcCoReDl','GRC102'),
		fAy( Tlt("<cfif set_language is 'english'>Base To Forex By Currency Listing</cfif>"),'1','a','R','y','ns_fr_topmain.cfm?topHdr=Reports&btmFyl=fr_common1_prelim.cfm&fromlink=company&frommode=new&fromsegm=report&fromsubsegm=crrlst&fromreport=fr_forex_curr','topmain','GcCoReCr','GRC103'),
		fAy( Tlt("<cfif set_language is 'english'>Organizational Chart</cfif>"),'1','a','R','y','wgp_sitemap_topmain.cfm?fromlink=entitymap_oc&co_unique=#cookie.cookcfnunique#','topmain','GcCoReOc','GRC104'),
		fAy( Tlt("<cfif set_language is 'english'>API Dashboard</cfif>"),'1','a','R','y','wgp_sitemap_topmain.cfm?fromlink=api_dash','topmain','GcCoReAp','GRC105'),
		fAy( Tlt("<cfif set_language is 'english'>Internal Control Dashboard</cfif>"),'1','a','R','y','wgp_sitemap_topmain.cfm?fromlink=trans_dash','topmain','GcCoReTr','GRC106')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcCoRe','')
	
	
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcCo',''),
	
	
	
	
	fAy( Tlt("<cfif set_language is 'english'>Chart Of Account</cfif>"),'0',fAy(
	fAy( Tlt("<cfif set_language is 'english'>Setup</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>Settings</cfif>"),'1','a','S','y','crc_admin_topmain.cfm?fromlink=chartacct&frommode=edit&fromsegm=setacctset','topmain','GcChSeSe','GFA101')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcChSe',''),
	
	fAy( Tlt("<cfif set_language is 'english'>Account Classification</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>Acct Type</cfif>"),'1','a','L','y','set_coa_topmain.cfm?fromlink=chartacct&frommode=edit&fromsegm=accttype','topmain','GcChAcAt','GFA102'),
		fAy( Tlt("<cfif set_language is 'english'>Acct Class</cfif>"),'1','a','L','y','set_coa_topmain.cfm?fromlink=chartacct&frommode=edit&fromsegm=acctclas','topmain','GcChAcAc','GFA103'),
		fAy( Tlt("<cfif set_language is 'english'>Acct Number</cfif>"),'1','a','L','y','set_coa_topmain.cfm?fromlink=chartacct&frommode=edit&fromsegm=acctnum','topmain','GcChAcAn','GFA104')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcChAc',''),
	
	fAy( Tlt("<cfif set_language is 'english'>Grouping</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>Main Types</cfif>"),'1','a','S','y','set_coa_topmain.cfm?fromlink=chartacct&frommode=new&fromsubsegm=main&fromsegm=coa_type','topmain','GcChGrMt','GFA105'),
		fAy( Tlt("<cfif set_language is 'english'>Main Groupings</cfif>"),'1','a','S','y','set_coa_topmain.cfm?fromlink=chartacct&frommode=new&fromsubsegm=main&fromsegm=coa_main','topmain','GcChGrMg','GFA106')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcChGr',''),
	
	fAy( Tlt("<cfif set_language is 'english'>Configuration</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>Bank Acct Currency</cfif>"),'1','a','S','y','set_coa_topmain.cfm?fromlink=chartacct&frommode=edit&fromsegm=bankacct','topmain','GcChCnBa','GFA107'),
		fAy( Tlt("<cfif set_language is 'english'>Petty Cash Currency</cfif>"),'1','a','S','y','set_coa_topmain.cfm?fromlink=chartacct&frommode=edit&fromsegm=pcash','topmain','GcChCnPe','GFA108'),
		fAy( Tlt("<cfif set_language is 'english'>Define Key Acctnum</cfif>"),'1','a','S','y','set_coa_topmain.cfm?fromlink=chartacct&frommode=new&fromsegm=keyacct&fromsubsegm=main','topmain','GcChCnDk','GFA109'),
		fAy( Tlt("<cfif set_language is 'english'>Designated Currency</cfif>"),'1','a','S','y','set_coa_topmain.cfm?fromlink=chartacct&frommode=edit&fromsegm=designatecurr','topmain','GcChCnDc','GFA110'),
		fAy( Tlt("<cfif set_language is 'english'>Acct Tax Code</cfif>"),'1','a','S','y','set_coa_topmain.cfm?fromlink=chartacct&frommode=edit&fromsegm=accttax','topmain','GcChCnTa','GFD235'),
		fAy( Tlt("<cfif set_language is 'english'>Revaluation Acctnum</cfif>"),'1','a','S','y','set_coa_topmain.cfm?fromlink=fin_frx_setup&frommode=edit&fromsegm=reval','topmain','GcChCnRa','GFA111'),
		fAy( Tlt("<cfif set_language is 'english'>Project Accounting</cfif>"),'1','a','S','y','set_coa_topmain.cfm?fromlink=chartacct&frommode=edit&fromsegm=prjacct','topmain','GcChCnPa','GFA112'),
		fAy( Tlt("<cfif set_language is 'english'>Simple GL Allocation</cfif>"),'1','a','S','y','set_coa_topmain.cfm?fromlink=chartacct&frommode=edit&fromsegm=allocacct','topmain','GcChCnSg','GFA113'),
		fAy( Tlt("<cfif set_language is 'english'>Cost Code Allocation By Project</cfif>"),'1','a','S','y','set_coa_topmain.cfm?fromlink=chartacct&frommode=edit&fromsegm=pallocacct','topmain','GcChCnPg','GFA128'),
		fAy( Tlt("<cfif set_language is 'english'>Manufacturing Acctnum</cfif>"),'1','a','S','y','set_coa_topmain.cfm?fromlink=chartacct&frommode=edit&fromsegm=manuacct','topmain','GcChCnMa','GFA114'),
		fAy( Tlt("<cfif set_language is 'english'>Forms Default Acctnum</cfif>"),'1','a','S','y','set_coa_topmain.cfm?fromlink=chartacct&frommode=edit&fromsegm=setdef','topmain','GcChCnFd','GFA115')
	
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcChCn',''),
	
	fAy( Tlt("<cfif set_language is 'english'>SAP</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>SAP Account Category</cfif>"),'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=sapactcat','topmain','GcChSaSc','GFA122'),
		fAy( Tlt("<cfif set_language is 'english'>SAP Datasource</cfif>"),'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=sapdatasrc','topmain','GcChSaSd','GFA123'),
		fAy( Tlt("<cfif set_language is 'english'>SAP Flow</cfif>"),'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=sapflow','topmain','GcChSaSl','GFA124'),
		fAy( Tlt("<cfif set_language is 'english'>SAP Freeline</cfif>"),'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=sapfree','topmain','GcChSaSf','GFA125'),
		fAy( Tlt("<cfif set_language is 'english'>SAP Activity</cfif>"),'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=sapactivity','topmain','GcChSaSa','GFA126'),
	    fAy( Tlt("<cfif set_language is 'english'>SAP Account Mapping</cfif>"),'1','a','S','y','set_coa_topmain.cfm?fromlink=chartacct&frommode=edit&fromsegm=sapactmap','topmain','GcChSaSm','GFA127')
	
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcChSa',''),
	fAy( Tlt("<cfif set_language is 'english'>ACCPAC</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>ACCPAC Account Mapping</cfif>"),'1','a','S','y','set_coa_topmain.cfm?fromlink=chartacct&frommode=edit&fromsegm=accpacactmap','topmain','GcChSaSm','GFA129')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcChAp',''),
	fAy( Tlt("<cfif set_language is 'english'>Mapping (One To One)</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>Mapping Acctnum</cfif>"),'1','a','S','y','set_coa_topmain.cfm?fromlink=chartacct&frommode=edit&fromsegm=mapsingle','topmain','GcChMaMa','GFA116'),
		fAy( Tlt("<cfif set_language is 'english'>Mapping Acct Class</cfif>"),'1','a','S','y','set_coa_topmain.cfm?fromlink=chartacct&frommode=edit&fromsegm=mapsingleclas','topmain','GcChMaMc','GFA117'),
		fAy( Tlt("<cfif set_language is 'english'>Mapping Acct Type</cfif>"),'1','a','S','y','set_coa_topmain.cfm?fromlink=chartacct&frommode=edit&fromsegm=mapsingletype','topmain','GcChMaMt','GFA118')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcChMa',''),
	
	fAy( Tlt("<cfif set_language is 'english'>Mapping (One to Many)</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>Account Mapping</cfif>"),'1','a','S','y','set_coa_topmain.cfm?fromlink=chartacct&frommode=edit&fromsegm=mapmultiple','topmain','GcChAmAm','GRA108')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcChAm',''),
	
	fAy( Tlt("<cfif set_language is 'english'>Cash Flows Classification</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>Cash Flows Code</cfif>"),'1','a','S','y','set_coa_topmain.cfm?fromlink=chartacct&frommode=edit&fromsegm=cfccode','topmain','GcChCfCd','GFA119'),
		fAy( Tlt("<cfif set_language is 'english'>Cash Flows Acctnum</cfif>"),'1','a','S','y','set_coa_topmain.cfm?fromlink=chartacct&frommode=edit&fromsegm=cfcacct','topmain','GcChCfAn','GFA120')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcChCf',''),
	
	fAy( Tlt("<cfif set_language is 'english'>Shareholder Equity Setup</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>Define Acct Type</cfif>"),'1','a','S','y','set_coa_topmain.cfm?fromlink=chartacct&frommode=edit&fromsegm=sestype','topmain','GcChSqDa','GFA121')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcChSq',''),
	fAy( Tlt("<cfif set_language is 'english'>Chinese Special Report</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>Profit Distribution</cfif>"),'1','a','S','y','set_coa_topmain.cfm?fromlink=chartacct&frommode=edit&fromsegm=pdsacctnum','topmain','GcChCsPd','GRA101'),
		fAy( Tlt("<cfif set_language is 'english'>VAT Payable Details<!---@ TTLRN GB/T QiYeYingJiaoZengZhiShuiMingXiBiao @---></cfif>"),'1','a','S','y','set_coa_topmain.cfm?fromlink=chartacct&frommode=edit&fromsegm=vatacctnum','topmain','GcChCsVp','GRA102'),
		fAy( Tlt("<cfif set_language is 'english'>Asset Impairment Provision</cfif>"),'1','a','S','y','set_coa_topmain.cfm?fromlink=chartacct&frommode=edit&fromsegm=aipacctnum','topmain','GcChCsAi','GRA103'),
		fAy( Tlt("<cfif set_language is 'english'>Income Statement</cfif>"),'1','a','S','y','set_coa_topmain.cfm?fromlink=chartacct&frommode=edit&fromsegm=pltype','topmain','GcChCsPl','GRA104'),
		fAy( Tlt("<cfif set_language is 'english'>Balance Sheet</cfif>"),'1','a','S','y','set_coa_topmain.cfm?fromlink=chartacct&frommode=edit&fromsegm=bstype','topmain','GcChCsBs','GRA105')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcChCs',''),
	fAy( Tlt("<cfif set_language is 'english'>Localization Report Tools</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>Income Statement</cfif>"),'1','a','S','y','set_coa_topmain.cfm?fromlink=chartacct&frommode=edit&fromsegm=istype','topmain','GcChRtIs','GRA106'),
		fAy( Tlt("<cfif set_language is 'english'>Balance Sheet</cfif>"),'1','a','S','y','set_coa_topmain.cfm?fromlink=chartacct&frommode=edit&fromsegm=bstype','topmain','GcChRtBs','GRA107'),
		fAy( Tlt("<cfif set_language is 'english'>Costing Statement</cfif>"),'1','a','S','y','set_coa_topmain.cfm?fromlink=chartacct&frommode=edit&fromsegm=cstype','topmain','GcChRtCs','GRA109'),
		fAy( Tlt("<cfif set_language is 'english'>Form C-S Account Mapping</cfif>"),'1','a','S','y','set_company_topmain.cfm?fromlink=fin_gst&frommode=new&fromsegm=formcsmap','topmain','GcChRtfc','GRA111')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcChRt',''),
	fAy( Tlt("<cfif set_language is 'english'>Reports</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>Chart of Account Listing</cfif>"),'1','a','S','y','set_coa_topmain.cfm?fromlink=chartacct&frommode=edit&fromsegm=fr_coalist&fromreport=fr_coalist','topmain','GcChReCl','GRA110')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcChRe','')
	
	
	
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcCh',''),
	
	
	
	
	fAy( Tlt("<cfif set_language is 'english'>Forms & Printing</cfif>"),'0',fAy(
	fAy( Tlt("<cfif set_language is 'english'>Forms Setting</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>Default Num Rows</cfif>"),'1','a','S','y','set_forms_default_topmain.cfm?fromlink=formset&frommode=new&fromsegm=defaultvalues','topmain','GcFpFsDn','GFF101'),
		fAy( Tlt("<cfif set_language is 'english'>Select Box Trigger</cfif>"),'1','a','S','y','set_forms_topmain.cfm?fromlink=formset&frommode=new&fromsegm=sbox_contact','topmain','GcFpFsSt','GFF102'),
		fAy( Tlt("<cfif set_language is 'english'>Select Box Settings</cfif>"),'1','a','S','y','set_forms_topmain.cfm?fromlink=formset&frommode=new&fromsegm=sbox_setting','topmain','GcFpFsSs','GFF103'),
	
		fAy( Tlt("<cfif set_language is 'english'>Tab Setting</cfif>"),'0',fAy(
		    fAy( Tlt("<cfif set_language is 'english'>Finance</cfif>"),'1','A','R','y','set_transet_topmain.cfm?fromlink=formset&frommode=new&fromsegm=tabset&fromsubsegm=fin','topmain','GcFpFsTsFi','GFF104'),
		    fAy( Tlt("<cfif set_language is 'english'>Supply Chain</cfif>"),'1','A','R','y','set_transet_topmain.cfm?fromlink=formset&frommode=new&fromsegm=tabset&fromsubsegm=scm','topmain','GcFpFsTsSc','GFF105'),
		    fAy( Tlt("<cfif set_language is 'english'>Employee Self Service</cfif>"),'1','A','R','y','set_transet_topmain.cfm?fromlink=formset&frommode=new&fromsegm=tabset&fromsubsegm=ess','topmain','GcFpFsTsEs','GFF106'),
		    fAy( Tlt("<cfif set_language is 'english'>Enterprise Project</cfif>"),'1','A','R','y','set_transet_topmain.cfm?fromlink=formset&frommode=new&fromsegm=tabset&fromsubsegm=entproj','topmain','GcFpFsTsEp','GFF107')
		),'R','y','ns_wgp_tnomodules.cfm?','topmain','GcFpFsTs','')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcFpFs',''),
	
	fAy( Tlt("<cfif set_language is 'english'>Print Setting</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>Print Form Format</cfif>"),'1','a','S','y','set_print_topmain.cfm?fromlink=documctrl&frommode=new&fromsegm=print_form','topmain','GcFpPsPr','GFF108'),
		fAy( Tlt("<cfif set_language is 'english'>Print Form General Setting</cfif>"),'1','a','S','y','set_print_topmain.cfm?fromlink=documctrl&frommode=new&fromsegm=sal_general_set','topmain','GcFpPsGs','GFF155'),
		fAy( Tlt("<cfif set_language is 'english'>Print Letterhead</cfif>"),'1','a','S','y','set_print_topmain.cfm?fromlink=documctrl&frommode=new&fromsegm=print_letterhead','topmain','GcFpPsPl','GFF109'),
	
		fAy( Tlt("<cfif set_language is 'english'>Print Header</cfif>"),'0',fAy(
		    fAy( #labelswc_sal_quo#,'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=header&fromsubsegm=sal_quo&fromtrans=sal_quo','topmain','GcFpPsPhSq','GFF110'),
		    fAy( #labelswc_sal_soe#,'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=header&fromsubsegm=sal_soe&fromtrans=sal_soe','topmain','GcFpPsPhSo','GFF111'),
		    fAy( #labelswc_sal_inv#,'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=header&fromsubsegm=sal_inv&fromtrans=sal_inv','topmain','GcFpPsPhSi','GFF112'),
		    fAy( Tlt("<cfif set_language is 'english'>Pro Forma Invoice</cfif>"),'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=header&fromsubsegm=sal_fma&fromtrans=sal_fma','topmain','GcFpPsPhPi','GFF113'),
		    fAy( Tlt("<cfif set_language is 'english'>Sales Debit Note</cfif>"),'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=header&fromsubsegm=sal_dn&fromtrans=sal_dn','topmain','GcFpPsPhSd','GFF114'),
		    fAy( Tlt("<cfif set_language is 'english'>Sales Credit Note</cfif>"),'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=header&fromsubsegm=sal_cn&fromtrans=sal_cn','topmain','GcFpPsPhSc','GFF115'),
		    fAy( Tlt("<cfif set_language is 'english'>Work Order</cfif>"),'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=header&fromsubsegm=wo_serv&fromtrans=wo_serv','topmain','GcFpPsPhWo','GFF116'),
		    fAy( Tlt("<cfif set_language is 'english'>Purchase Requisition</cfif>"),'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=header&fromsubsegm=pur_pr&fromtrans=pur_pr','topmain','GcFpPsPhPr','GFF165'),
		    fAy( Tlt("<cfif set_language is 'english'>Purchase Order</cfif>"),'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=header&fromsubsegm=pur_po&fromtrans=pur_po','topmain','GcFpPsPhPo','GFF117'),
		    fAy( Tlt("<cfif set_language is 'english'>Delivery Order</cfif>"),'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=header&fromsubsegm=stk_do&fromtrans=stk_do','topmain','GcFpPsPhDo','GFF118'),
		    fAy( Tlt("<cfif set_language is 'english'>Variation Order</cfif>"),'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=header&fromsubsegm=entp_vo&fromtrans=entp_vo','topmain','GcFpPsPhVo','GFF119'),
		    fAy( Tlt("<cfif set_language is 'english'>Progress Claim</cfif>"),'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=header&fromsubsegm=entp_pbill&fromtrans=entp_pbill','topmain','GcFpPsPhPb','GFF120'),
		fAy( Tlt("<cfif set_language is 'english'>Lease Quotation</cfif>"),'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=header&fromsubsegm=lea_quo&fromtrans=sal_quo','topmain','GcFpPsPhLq','GFF121'),
		    fAy( Tlt("<cfif set_language is 'english'>Lease Order</cfif>"),'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=header&fromsubsegm=lea_order&fromtrans=sal_soe','topmain','GcFpPsPhLo','GFF122'),
		    fAy( Tlt("<cfif set_language is 'english'>Job Order</cfif>"),'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=header&fromsubsegm=mrpone_jo&fromtrans=mrpone_jo','topmain','GcFpPsPhJo','GFF159'),
		    fAy( Tlt("<cfif set_language is 'english'>Material Stock In</cfif>"),'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=header&fromsubsegm=stk_mi&fromtrans=stk_mi','topmain','GcFpPsPhMi','GFF162'),
		    fAy( Tlt("<cfif set_language is 'english'>Material Stock Out</cfif>"),'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=header&fromsubsegm=stk_mw&fromtrans=stk_mw','topmain','GcFpPsPhMw','GFF163'),
		    fAy( Tlt("<cfif set_language is 'english'>Project Tender Master</cfif>"),'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=header&fromsubsegm=prj_master&fromtrans=prj_master','topmain','GcFpPsPhPt','GFF164')
		),'S','y','ns_wgp_tnomodules.cfm?','topmain','GcFpPsPh',''),
	
		fAy( Tlt("<cfif set_language is 'english'>Print Footer</cfif>"),'0',fAy(
		    fAy( #labelswc_sal_quo#,'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=footer&fromsubsegm=sal_quo&fromtrans=sal_quo','topmain','GcFpPsPfSq','GFF123'),
		    fAy( #labelswc_sal_soe#,'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=footer&fromsubsegm=sal_soe&fromtrans=sal_soe','topmain','GcFpPsPfSo','GFF124'),
		    fAy( #labelswc_sal_inv#,'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=footer&fromsubsegm=sal_inv&fromtrans=sal_inv','topmain','GcFpPsPfSi','GFF125'),
		    fAy( Tlt("<cfif set_language is 'english'>Pro Forma Invoice</cfif>"),'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=footer&fromsubsegm=sal_fma&fromtrans=sal_fma','topmain','GcFpPsPfPi','GFF126'),
		    fAy( Tlt("<cfif set_language is 'english'>Sales Debit Note</cfif>"),'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=footer&fromsubsegm=sal_dn&fromtrans=sal_dn','topmain','GcFpPsPfSd','GFF127'),
		    fAy( Tlt("<cfif set_language is 'english'>Sales Credit Note</cfif>"),'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=footer&fromsubsegm=sal_cn&fromtrans=sal_cn','topmain','GcFpPsPfSc','GFF128'),
		    fAy( Tlt("<cfif set_language is 'english'>Work Order</cfif>"),'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=footer&fromsubsegm=wo_serv&fromtrans=wo_serv','topmain','GcFpPsPfWo','GFF129'),
		    fAy( Tlt("<cfif set_language is 'english'>Purchase Requisition</cfif>"),'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=footer&fromsubsegm=pur_pr&fromtrans=pur_pr','topmain','GcFpPsPfPr','GFF166'),
		    fAy( Tlt("<cfif set_language is 'english'>Purchase Order</cfif>"),'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=footer&fromsubsegm=pur_po&fromtrans=pur_po','topmain','GcFpPsPfPo','GFF130'),
		    fAy( Tlt("<cfif set_language is 'english'>Delivery Order</cfif>"),'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=footer&fromsubsegm=stk_do&fromtrans=stk_do','topmain','GcFpPsPfDo','GFF131'),
		    fAy( Tlt("<cfif set_language is 'english'>Variation Order</cfif>"),'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=footer&fromsubsegm=entp_vo&fromtrans=entp_vo','topmain','GcFpPsPfVo','GFF132'),
		    fAy( Tlt("<cfif set_language is 'english'>Progress Claim</cfif>"),'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=footer&fromsubsegm=entp_pbill&fromtrans=entp_pbill','topmain','GcFpPsPfPb','GFF133'),
		fAy( Tlt("<cfif set_language is 'english'>Lease Quotation</cfif>"),'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=footer&fromsubsegm=lea_quo&fromtrans=sal_quo','topmain','GcFpPsPfLq','GFF134'),
		    fAy( Tlt("<cfif set_language is 'english'>Lease Order</cfif>"),'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=footer&fromsubsegm=lea_order&fromtrans=sal_soe','topmain','GcFpPsPfLo','GFF135'),
		    fAy( Tlt("<cfif set_language is 'english'>Job Order</cfif>"),'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=footer&fromsubsegm=mrpone_jo&fromtrans=mrpone_jo','topmain','GcFpPsPfJo','GFF158'),
		fAy( Tlt("<cfif set_language is 'english'>Transfer Request</cfif>"),'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=footer&fromsubsegm=stk_trnr&fromtrans=stk_trnr','topmain','GcFpPsPfTr','GFF159'),
		fAy( Tlt("<cfif set_language is 'english'>Service Record</cfif>"),'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=footer&fromsubsegm=srvrec&fromtrans=srvrec','topmain','GcFpPsPfLp','GFF161'),
		fAy( Tlt("<cfif set_language is 'english'>Material Stock In</cfif>"),'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=footer&fromsubsegm=stk_mi&fromtrans=stk_mi','topmain','GcFpPsPfMi','GFF162'),
		    fAy( Tlt("<cfif set_language is 'english'>Material Stock Out</cfif>"),'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=footer&fromsubsegm=stk_mw&fromtrans=stk_mw','topmain','GcFpPsPfMw','GFF163'),
		    fAy( Tlt("<cfif set_language is 'english'>Project Tender Master</cfif>"),'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=footer&fromsubsegm=prj_master&fromtrans=prj_master','topmain','GcFpPsPfPt','GFF164')
		),'S','y','ns_wgp_tnomodules.cfm?','topmain','GcFpPsPf',''),
	
		fAy( Tlt("<cfif set_language is 'english'>Print Dimension</cfif>"),'0',fAy(
		    fAy( #labelswc_sal_quo#,'1','A','S','y','set_print_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=prndim&fromtrans=prn_sal_quo','topmain','GcFpPsPdSq','GFF136'),
		    fAy( #labelswc_sal_soe#,'1','A','S','y','set_print_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=prndim&fromtrans=prn_sal_soe','topmain','GcFpPsPdSo','GFF137'),
		    fAy( #labelswc_sal_inv#,'1','A','S','y','set_print_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=prndim&fromtrans=prn_sal_inv','topmain','GcFpPsPdSi','GFF138'),
		    fAy( Tlt("<cfif set_language is 'english'>Pro Forma Invoice</cfif>"),'1','A','S','y','set_print_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=prndim&fromtrans=prn_sal_fma','topmain','GcFpPsPdPi','GFF139'),
		    fAy( Tlt("<cfif set_language is 'english'>Sales Debit Note</cfif>"),'1','A','S','y','set_print_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=prndim&fromtrans=prn_sal_dn','topmain','GcFpPsPdSd','GFF140'),
		    fAy( Tlt("<cfif set_language is 'english'>Sales Credit Note</cfif>"),'1','A','S','y','set_print_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=prndim&fromtrans=prn_sal_cn','topmain','GcFpPsPdSc','GFF141'),
		    fAy( Tlt("<cfif set_language is 'english'>Work Order</cfif>"),'1','A','S','y','set_gencode_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=footer&fromsubsegm=wo_serv&fromtrans=wo_serv','topmain','GcFpPsPdWo','GFF142'),
		    fAy( Tlt("<cfif set_language is 'english'>Purchase Order</cfif>"),'1','A','S','y','set_print_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=prndim&fromtrans=prn_pur_po','topmain','GcFpPsPdPo','GFF143'),
		    fAy( Tlt("<cfif set_language is 'english'>Delivery Order</cfif>"),'1','A','S','y','set_print_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=prndim&fromtrans=prn_stk_do','topmain','GcFpPsPdDo','GFF144'),
		    fAy( Tlt("<cfif set_language is 'english'>Variation Order</cfif>"),'1','A','S','y','set_print_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=prndim&fromtrans=prn_entp_vo','topmain','GcFpPsPdVo','GFF145'),
		    fAy( Tlt("<cfif set_language is 'english'>Progress Claim</cfif>"),'1','A','S','y','set_print_topmain.cfm?fromlink=documctrl&frommode=edit&fromsegm=prndim&fromtrans=prn_entp_pbill','topmain','GcFpPsPdPb','GFF146')
		),'S','y','ns_wgp_tnomodules.cfm?','topmain','GcFpPsPd',''),
	
		fAy( Tlt("<cfif set_language is 'english'>Import General Print Form Setting</cfif>"),'0',fAy(
			fAy( Tlt("<cfif set_language is 'english'>Upload Source File</cfif>"),'1','a','T','y','set_imagemgmt_topmain.cfm?fromlink=documctrl&frommode=new&fromsegm=upload_srcfile&fromsubsegm=ext_gen_setting','topmain','GcFpPsPdUp','GFF156'),
			fAy( Tlt("<cfif set_language is 'english'>Import General Print Form Setting</cfif>"),'1','a','L','y','scm_externaldata_topmain.cfm?fromlink=documctrl&frommode=new&fromtrans=impgen_setting&fromsegm=impgen_setting','topmain','GcFpPsPdIm','GFF157')
		),'R','y','ns_wgp_tnomodules.cfm?','topmain','MrOnSeBm','')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcFpPs',''),
	
	fAy( Tlt("<cfif set_language is 'english'>Print Security</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>Activate</cfif>"),'1','a','S','y','set_print_topmain.cfm?fromlink=documctrl&frommode=new&fromsegm=prnsecu&fromtrans=prnsecu','topmain','GcFpPqAc','GFF147'),
		fAy( Tlt("<cfif set_language is 'english'>Release CN</cfif>"),'1','a','S','y','set_print_topmain.cfm?fromlink=documctrl&frommode=new&fromsegm=prnsecu_rel&fromtrans=prnsecu_sal_cn','topmain','GcFpPqRc','GFF148'),
		fAy( Tlt("<cfif set_language is 'english'>Release Invoice</cfif>"),'1','a','S','y','set_print_topmain.cfm?fromlink=documctrl&frommode=new&fromsegm=prnsecu_rel&fromtrans=prnsecu_sal_inv','topmain','GcFpPqRi','GFF149'),
		fAy( Tlt("<cfif set_language is 'english'>Release PO</cfif>"),'1','a','S','y','set_print_topmain.cfm?fromlink=documctrl&frommode=new&fromsegm=prnsecu_rel&fromtrans=prnsecu_pur_po','topmain','GcFpPqRp','GFF150'),
		fAy( Tlt("<cfif set_language is 'english'>Release DO</cfif>"),'1','a','S','y','set_print_topmain.cfm?fromlink=documctrl&frommode=new&fromsegm=prnsecu_rel&fromtrans=prnsecu_stk_do','topmain','GcFpPqRd','GFF151'),
		fAy( Tlt("<cfif set_language is 'english'>Release Retail Sales</cfif>"),'1','a','S','y','set_print_topmain.cfm?fromlink=documctrl&frommode=new&fromsegm=prnsecu_rel&fromtrans=prnsecu_sal_rta','topmain','GcFpPqRe','GFF154'),
		fAy( Tlt("<cfif set_language is 'english'>Release PCK</cfif>"),'1','a','S','y','set_print_topmain.cfm?fromlink=documctrl&frommode=new&fromsegm=prnsecu_rel&fromtrans=prnsecu_stk_pick','topmain','GcFpPqRl','GFF160'),
		fAy( Tlt("<cfif set_language is 'english'>Release SO</cfif>"),'1','a','S','y','set_print_topmain.cfm?fromlink=documctrl&frommode=new&fromsegm=prnsecu_rel&fromtrans=prnsecu_sal_soe','topmain','GcFpPqRr','GFF164')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcFpPq',''),
	
	fAy( Tlt("<cfif set_language is 'english'>Ageing Format</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>Ageing Report Format</cfif>"),'1','a','S','y','set_print_topmain.cfm?fromlink=documctrl&frommode=new&fromsegm=age_report','topmain','GcFpAfAr','GFF152'),
		fAy( Tlt("<cfif set_language is 'english'>Stock Ageing Format</cfif>"),'1','a','S','y','set_print_topmain.cfm?fromlink=documctrl&frommode=new&fromsegm=stk_age','topmain','GcFpAfSa','GFF153')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcFpAf','')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcFp',''),
	
	
	
	
	fAy( Tlt("<cfif set_language is 'english'>Admin Manager</cfif>"),'0',fAy(
	fAy( Tlt("<cfif set_language is 'english'>Contact Mgmt</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>Unapproved Customer</cfif>"),'1','a','A','y','adm_contact_topmain.cfm?fromlink=adminmgr&frommode=new&fromsegm=cust&fromtrans=cust&fromunapprove=y','topmain','GcAmCmUt','GFP127'),
		fAy( Tlt("<cfif set_language is 'english'>Customer Master</cfif>"),'1','a','A','y','adm_contact_topmain.cfm?fromlink=adminmgr&frommode=new&fromsegm=cust&fromtrans=cust','topmain','GcAmCmCu','GFP104'),
		fAy( Tlt("<cfif set_language is 'english'>Unapproved Vendor</cfif>") ,'1','a','A','y','adm_contact_topmain.cfm?fromlink=adminmgr&frommode=new&fromsegm=vend&fromtrans=vend&fromunapprove=y','topmain','GcAmCmUv','GFP128'),
		fAy( Tlt("<cfif set_language is 'english'>Vendor Master</cfif>"),'1','a','A','y','adm_contact_topmain.cfm?fromlink=adminmgr&frommode=new&fromsegm=vend&fromtrans=vend','topmain','GcAmCmVm','GFP105'),
		fAy( Tlt("<cfif set_language is 'english'>Unapproved Both (Customer/Vendor)</cfif>"),'1','a','A','y','adm_contact_topmain.cfm?fromlink=adminmgr&frommode=new&fromsegm=both&fromtrans=both&fromunapprove=y','topmain','GcAmCmUb','GFP129'),
		fAy( Tlt("<cfif set_language is 'english'>Both (Customer/Vendor)</cfif>"),'1','a','A','y','adm_contact_topmain.cfm?fromlink=adminmgr&frommode=new&fromsegm=both&fromtrans=both','topmain','GcAmCmbh','GFP106'),
		fAy( Tlt("<cfif set_language is 'english'>Contact Mgmt</cfif>"),'1','a','A','y','adm_contact_topmain.cfm?fromlink=adminmgr&frommode=new&fromsegm=contact&fromtrans=contact','topmain','GcAmCmCm','GFP101'),
		fAy( Tlt("<cfif set_language is 'english'>Import Registration No.</cfif>"),'0',fAy(
			fAy( Tlt("<cfif set_language is 'english'>Upload Source File</cfif>"),'1','a','T','y','set_imagemgmt_topmain.cfm?fromlink=documctrl&frommode=new&fromsegm=upload_srcfile&fromsubsegm=reg_no','topmain','GcAmCmIrUp','GFP131'),
			fAy( Tlt("<cfif set_language is 'english'>Import Registration No. Details</cfif>"),'1','a','L','y','scm_externaldata_topmain.cfm?fromlink=documctrl&frommode=new&fromtrans=imp_reg_no&fromsegm=imp_reg_no','topmain','GcAmCmIrIm','GFP132')
		),'R','y','ns_wgp_tnomodules.cfm?','topmain','GcAmCmIr',''),
		fAy( Tlt("<cfif set_language is 'english'>Import HS Codes</cfif>"),'0',fAy(
			fAy( Tlt("<cfif set_language is 'english'>Upload Source File</cfif>"),'1','a','T','y','set_imagemgmt_topmain.cfm?fromlink=documctrl&frommode=new&fromsegm=upload_srcfile&fromsubsegm=hs_code','topmain','GcAmCmHsUp','GFP133'),
			fAy( Tlt("<cfif set_language is 'english'>Import contacts' Hs Code</cfif>"),'1','a','L','y','scm_externaldata_topmain.cfm?fromlink=documctrl&frommode=new&fromtrans=imp_hs_code&fromsegm=imp_hs_code','topmain','GcAmCmHsIm','GFP134')
		),'R','y','ns_wgp_tnomodules.cfm?','topmain','GcAmCmHs',''),
		fAy( Tlt("<cfif set_language is 'english'>Import User Access Rights</cfif>"),'0',fAy(
			fAy( Tlt("<cfif set_language is 'english'>Upload Source File</cfif>"),'1','a','T','y','set_imagemgmt_topmain.cfm?fromlink=documctrl&frommode=new&fromsegm=upload_srcfile&fromsubsegm=user_access','topmain','GcAmCmUrUp','GFP140'),
			fAy( Tlt("<cfif set_language is 'english'>Import User Access Rights</cfif>"),'1','a','L','y','scm_externaldata_topmain.cfm?fromlink=documctrl&frommode=new&fromtrans=imp_user_access&fromsegm=imp_user_access','topmain','GcAmCmUrIm','GFP141')
		),'R','y','ns_wgp_tnomodules.cfm?','topmain','GcAmCmUr',''),
		fAy( Tlt("<cfif set_language is 'english'>Import Contact Mgmt</cfif>"),'1','a','A','y','adm_contact_topmain.cfm?fromlink=adminmgr&frommode=new&fromsegm=imp_contact&fromtrans=contact','topmain','GcAmCmIp','GFP119'),
		fAy( Tlt("<cfif set_language is 'english'>Print Label</cfif>"),'1','a','S','y','adm_contact_topmain.cfm?fromlink=adminmgr&frommode=new&fromsegm=label','topmain','GcAmCmPL','GFP102'),
		fAy( Tlt("<cfif set_language is 'english'>Update Party's Country</cfif>"),'1','a','A','y','upd_party_country_code.cfm?fromlink=adminmgr&frommode=new&fromsegm=contactctryupd','botmain','GcAmCmup','GFP103'),
		fAy( Tlt("<cfif set_language is 'english'>Contact Mgmt</cfif>") & ' - ' & Tlt("<cfif set_language is 'english'>Unapproved</cfif>"),'1','a','A','y','adm_contact_topmain.cfm?fromlink=adminmgr&frommode=new&fromsegm=contact&fromtrans=contact&fromapprove=cir&fromunapprove=y','topmain','GcAmCmUc','GFP117'),
		fAy( Tlt("<cfif set_language is 'english'>Contact Mgmt</cfif>") & ' - ' & Tlt("<cfif set_language is 'english'>Approved</cfif>"),'1','a','A','y','adm_contact_topmain.cfm?fromlink=adminmgr&frommode=edit&fromsegm=contact&fromtrans=contact&fromapprove=app','topmain','GcAmCmAc','GFP118'),
		fAy( Tlt("<cfif set_language is 'english'>Customer Master</cfif>") & ' - ' & Tlt("<cfif set_language is 'english'>Unapproved</cfif>"),'1','a','A','y','adm_contact_topmain.cfm?fromlink=adminmgr&frommode=new&fromsegm=cust&fromtrans=cust&fromapprove=cir&fromunapprove=y','topmain','GcAmCmUu','GFP121'),
		fAy( Tlt("<cfif set_language is 'english'>Customer Master</cfif>") & ' - ' & Tlt("<cfif set_language is 'english'>Approved</cfif>"),'1','a','A','y','adm_contact_topmain.cfm?fromlink=adminmgr&frommode=new&fromsegm=cust&fromtrans=cust&fromapprove=app','topmain','GcAmCmUa','GFP122'),
		fAy( Tlt("<cfif set_language is 'english'>Vendor Master</cfif>") & ' - ' & Tlt("<cfif set_language is 'english'>Unapproved</cfif>"),'1','a','A','y','adm_contact_topmain.cfm?fromlink=adminmgr&frommode=new&fromsegm=vend&fromtrans=vend&fromapprove=cir&fromunapprove=y','topmain','GcAmCmVu','GFP123'),
		fAy( Tlt("<cfif set_language is 'english'>Vendor Master</cfif>") & ' - ' & Tlt("<cfif set_language is 'english'>Approved</cfif>"),'1','a','A','y','adm_contact_topmain.cfm?fromlink=adminmgr&frommode=new&fromsegm=vend&fromtrans=vend&fromapprove=app','topmain','GcAmCmVa','GFP124'),
		fAy( Tlt("<cfif set_language is 'english'>Both (Customer/Vendor)</cfif>") & ' - ' & Tlt("<cfif set_language is 'english'>Unapproved</cfif>"),'1','a','A','y','adm_contact_topmain.cfm?fromlink=adminmgr&frommode=new&fromsegm=both&fromtrans=both&fromapprove=cir&fromunapprove=y','topmain','GcAmCmbu','GFP125'),
		fAy( Tlt("<cfif set_language is 'english'>Both (Customer/Vendor)</cfif>") & ' - ' & Tlt("<cfif set_language is 'english'>Approved</cfif>"),'1','a','A','y','adm_contact_topmain.cfm?fromlink=adminmgr&frommode=new&fromsegm=both&fromtrans=both&fromapprove=app','topmain','GcAmCmba','GFP126'),
		fAy( Tlt("<cfif set_language is 'english'>Update Contact Mgmt</cfif>"),'1','a','A','y','adm_contact_topmain.cfm?fromlink=adminmgr&frommode=new&fromsegm=contact&fromtrans=contact&fromupdonly=y','topmain','GcAmCmUm','GFP142'),
		fAy( Tlt("<cfif set_language is 'english'>Sync With 3rd Party Software</cfif>"),'0',fAy(
		fAy( 'Magento','1','a','S','y','adm_sync_data_topmain.cfm?fromlink=adminmgr&frommode=new&fromsegm=sync_data&fromsubsegm=cnt','topmain','GcAmCmSyMa','GFP104'),
		fAy( 'IB2K','1','a','S','y','set_imagemgmt_topmain.cfm?fromlink=scm_stk_movement&frommode=new&fromsegm=upload_srcfile&fromsubsegm=cnt_ib2k','topmain','GcAmCmSyIb','GFP110'),
		fAy( 'WooCommerce','1','a','S','y','adm_sync_data_topmain.cfm?fromlink=adminmgr&frommode=new&fromsegm=sync_wo_data&fromsubsegm=cnt','topmain','GcAmCmSyWo','GFP115'),
		fAy( 'Wordpress (Ewineasia)','1','a','S','y','adm_sync_data_topmain.cfm?fromlink=adminmgr&frommode=new&fromsegm=wp_ewineasia&fromsubsegm=cnt','topmain','GcAmCmSyEw','GFP116')
		),'R','y','ns_wgp_tnomodules.cfm?','topmain','GcAmCmSy','')
	
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcAmCm',''),
	
	fAy( Tlt("<cfif set_language is 'english'>Reports</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>Contact Listing</cfif>"),'1','a','R','y','ns_fr_topmain.cfm?topHdr=Reports&btmFyl=fr_scm_prelim.cfm&fromlink=adminmgr&fromreport=fr_cnt_list','topmain','GcAmCrCu','GFP111'),
		fAy( Tlt("<cfif set_language is 'english'>Contact Listing With Personnel Info</cfif>"),'1','a','R','y','ns_fr_topmain.cfm?topHdr=Reports&btmFyl=fr_scm_prelim.cfm&fromlink=adminmgr&fromreport=fr_cnt_list_personnel','topmain','GcAmCrCp','GFP112'),
		fAy( Tlt("<cfif set_language is 'english'>Customer</cfif>") & "/" & Tlt("<cfif set_language is 'english'>Vendor Statistics</cfif>"),'1','a','R','y','ns_fr_topmain.cfm?topHdr=Reports&btmFyl=fr_scm_prelim.cfm&fromlink=adminmgr&fromreport=fr_customer_vendor_statistic','topmain','GcAmCrCt','GFP113'),
		fAy( Tlt("<cfif set_language is 'english'>Membership Status List</cfif>"),'1','a','R','y','ns_fr_topmain.cfm?topHdr=Reports&btmFyl=fr_scm_prelim.cfm&fromlink=adminmgr&fromreport=fr_membership_status_list','topmain','GcAmCrCm','GFP114'),
		fAy( Tlt("<cfif set_language is 'english'>Inactive Customer Listing</cfif>"),'1','a','R','y','ns_fr_topmain.cfm?topHdr=Reports&btmFyl=fr_scm_prelim.cfm&fromlink=adminmgr&fromreport=fr_inc_cust','topmain','GcAmCrIc','GFP119'),
		fAy( Tlt("<cfif set_language is 'english'>Customer Credit Facilities</cfif>"),'1','a','R','y','ns_fr_topmain.cfm?topHdr=Reports&btmFyl=fr_common1_prelim.cfm&fromlink=fin_gl_report&fromreport=fr_prn_crdt_fclts','topmain','GcAmCrCf','GFP120'),
		fAy( Tlt("<cfif set_language is 'english'>Vendor + Trade Group</cfif>"),'1','a','R','y','wgp_sitemap_topmain.cfm?fromreport=fr_prn_trade_group','topmain','GcAmCrTg',''),
		fAy( Tlt("<cfif set_language is 'english'>Monthly Contact Listing</cfif>"),'1','a','R','y','ns_fr_topmain.cfm?topHdr=Reports&btmFyl=fr_scm_prelim.cfm&fromlink=adminmgr&fromreport=fr_monthly_cnt_list','topmain','GcAmCrCl','GFP130'),
		fAy( Tlt("<cfif set_language is 'english'>Customer Master</cfif>")&" - "&Tlt("<cfif set_language is 'english'>Export to CSV</cfif>"),'1','a','R','y','ns_fr_topmain.cfm?topHdr=Reports&btmFyl=fr_scm_prelim.cfm&fromlink=adminmgr&fromreport=fr_cust_master_export_csv_rpt','topmain','GcAmCrCe','GFP139'),
		fAy( Tlt("<cfif set_language is 'english'>Contact Credit Insurance</cfif>"),'1','a','R','y','ns_fr_topmain.cfm?topHdr=Reports&btmFyl=fr_scm_prelim.cfm&fromlink=adminmgr&fromreport=fr_cnt_crd_ins','topmain','GcAmCrCc','GFP143')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcAmCr',''),
	
	fAy( Tlt("<cfif set_language is 'english'>Credit Admin</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>Credit Terms Request</cfif>"),'1','a','A','y','adm_contact_topmain.cfm?fromlink=adminmgr&frommode=new&fromsegm=ctreq&fromtrans=ctreq','topmain','GcAmCaCr','GFP107'),
		fAy( Tlt("<cfif set_language is 'english'>Credit Terms Approval</cfif>"),'1','a','A','y','adm_contact_topmain.cfm?fromlink=adminmgr&frommode=new&fromsegm=ctapp&fromtrans=ctapp','topmain','GcAmCaCa','GFP108'),
		fAy( Tlt("<cfif set_language is 'english'>Credit Terms Admin</cfif>"),'1','a','A','y','adm_contact_topmain.cfm?fromlink=adminmgr&frommode=new&fromsegm=ctadmin&fromtrans=ctadmin','topmain','GcAmCaCn','GFP109')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcAmCa',''),
	
	fAy( Tlt("<cfif set_language is 'english'>User Mgmt</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>Company Users Mgmt</cfif>"),'1','a','L','y','set_adduser_topmain.cfm?fromlink=adminmgr&frommode=new&fromsegm=users','topmain','GcAmUmCu','GFP105'),
		fAy( Tlt("<cfif set_language is 'english'>Usage History</cfif>"),'1','a','R','y','set_adduser_topmain.cfm?fromlink=adminmgr&frommode=new&fromsegm=userhistory&fromsubsegm=access','topmain','GcAmUmUh','GFP106')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcAmUm','')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcAm',''),
	
	
	
	
	fAy( Tlt("<cfif set_language is 'english'>Workflow Manager</cfif>"),'0',fAy(
	
	fAy( Tlt("<cfif set_language is 'english'>Approval Submission</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>Submission Group</cfif>"),'1','a','S','y','set_gencode_topmain.cfm?fromlink=gencode&frommode=new&fromsegm=subm_rfasg','topmain','GcWmAsSg','GFW113'),
		fAy( Tlt("<cfif set_language is 'english'>Submission Category</cfif>"),'1','a','S','y','set_gencode_topmain.cfm?fromlink=gencode&frommode=new&fromsegm=subm_rfasc','topmain','GcWmAsSc','GFW114'),
		fAy( Tlt("<cfif set_language is 'english'>Submission Type</cfif>"),'1','a','S','y','set_gencode_topmain.cfm?fromlink=gencode&frommode=new&fromsegm=subm_rfast','topmain','GcWmAsSt','GFW115'),
		fAy( Tlt("<cfif set_language is 'english'>Submit RFA Admin</cfif>"),'1','a','T','y','trans_common1_topmain.cfm?fromlink=scm_purc_pr&frommode=new&fromtrans=subm_rfa&admin_yn=y','topmain','GcWmAsAa','GFW117')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcWmAs',''),
	
	fAy( Tlt("<cfif set_language is 'english'>Workflow Control</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>Finance</cfif>"),'1','a','S','y','set_transet_topmain.cfm?fromlink=company&frommode=new&fromsegm=wflow&fromsubsegm=fin','topmain','GcWmWcFi','GFW101'),
		fAy( Tlt("<cfif set_language is 'english'>Supply Chain</cfif>"),'1','a','S','y','set_transet_topmain.cfm?fromlink=company&frommode=new&fromsegm=wflow&fromsubsegm=scm','topmain','GcWmWcSc','GFW102'),
		fAy( Tlt("<cfif set_language is 'english'>Employee Self Service</cfif>"),'1','a','S','y','set_transet_topmain.cfm?fromlink=company&frommode=new&fromsegm=wflow&fromsubsegm=ess','topmain','GcWmWcEs','GFW103'),
		fAy( Tlt("<cfif set_language is 'english'>Enterprise Project</cfif>"),'1','a','S','y','set_transet_topmain.cfm?fromlink=company&frommode=new&fromsegm=wflow&fromsubsegm=entproj','topmain','GcWmWcEp','GFW104'),
		fAy( Tlt("CRM"),'1','a','S','y','set_transet_topmain.cfm?fromlink=company&frommode=new&fromsegm=wflow&fromsubsegm=crm','topmain','GcWmWcNq','GFW173'),
		fAy( Tlt("<cfif set_language is 'english'>Human Resource</cfif>"),'1','a','S','y','set_transet_topmain.cfm?fromlink=company&frommode=new&fromsegm=wflow&fromsubsegm=hrm','topmain','GcWmWcHr','GFW174'),
		fAy( Tlt("<cfif set_language is 'english'>Admin Manager</cfif>"),'1','a','S','y','set_transet_topmain.cfm?fromlink=company&frommode=new&fromsegm=wflow&fromsubsegm=admnmgr','topmain','GcWmWcAm','GFW175'),
		fAy( Tlt("MRP"),'1','a','S','y','set_transet_topmain.cfm?fromlink=company&frommode=new&fromsegm=wflow&fromsubsegm=mrp','topmain','GcWmWcMr','GFW176'),
		fAy( Tlt("<cfif set_language is 'english'>Motor Asset Management</cfif>"),'1','a','S','y','set_transet_topmain.cfm?fromlink=company&frommode=new&fromsegm=wflow&fromsubsegm=motas','topmain','GcWmWcMa','GFW177'),
		fAy( Tlt("<cfif set_language is 'english'>Approval Submission</cfif>"),'1','a','S','y','set_transet_topmain.cfm?fromlink=company&frommode=new&fromsegm=wflow&fromsubsegm=subm_rfa','topmain','GcWmWcSr','GFW178')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcWmWc',''),
	
	
	
	fAy( Tlt("<cfif set_language is 'english'>Alternate Approver</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>Approver Group</cfif>"),'1','a','S','y','set_gencode_topmain.cfm?fromlink=gencode&frommode=new&fromsegm=wfappgrp','topmain','GcWmAaAg','GFW105'),
		fAy( Tlt("<cfif set_language is 'english'>Approval Range</cfif>"),'1','a','S','y','set_gencode_topmain.cfm?fromlink=gencode&frommode=new&fromsegm=wfapprng','topmain','GcWmAaAr','GFW112'),
		fAy( Tlt("<cfif set_language is 'english'>Set As Unavailable</cfif>"),'1','a','S','y','set_adminmgr_topmain.cfm?fromlink=company&frommode=new&fromsegm=appr_unavail','topmain','GcWmAaSu','GFW106'),
		fAy( Tlt("<cfif set_language is 'english'>Set As Available</cfif>"),'1','a','S','y','set_adminmgr_topmain.cfm?fromlink=company&frommode=new&fromsegm=appr_avail','topmain','GcWmAaSa','GFW107'),
		fAy( Tlt("<cfif set_language is 'english'>Unavailable Listing</cfif>"),'1','a','S','y','set_adminmgr_topmain.cfm?fromlink=company&frommode=new&fromreport=fr_wflw_unavl_lst','topmain','GcWmAaUl','GFW108')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcWmAa',''),
	
	fAy( Tlt("<cfif set_language is 'english'>Process</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>Amend Single Transaction</cfif>"),'1','a','S','y','set_adminmgr_topmain.cfm?fromlink=company&frommode=new&fromsegm=amend_single','topmain','GcWmPrSt','GFW109'),
		fAy( Tlt("<cfif set_language is 'english'>Amend Single Approver</cfif>"),'1','a','S','y','set_adminmgr_topmain.cfm?fromlink=company&frommode=new&fromsegm=amend_appr','topmain','GcWmPrSa','GFW110'),
		fAy( Tlt("<cfif set_language is 'english'>Admin Rejection</cfif>"),'1','a','S','y','set_adminmgr_topmain.cfm?fromlink=company&frommode=new&fromsegm=admin_rej','topmain','GcWmPrAr','GFW111'),
		fAy( Tlt("<cfif set_language is 'english'>Approval Transaction Review</cfif>"),'1','a','S','y','set_adminmgr_topmain.cfm?fromlink=company&frommode=new&fromsegm=app_review','topmain','GcWmPrRv','GFW117')
		
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcWmPr',''),
	
	
	fAy( Tlt("<cfif set_language is 'english'>Reports</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>Pending Approval List</cfif>"),'1','a','S','y','set_adminmgr_topmain.cfm?fromlink=company&frommode=new&fromreport=fr_wflw_pending_approval_lst','topmain','GcWmRpPa','GRW101'),
		fAy( Tlt("<cfif set_language is 'english'>Workflow Status Listing</cfif>"),'1','a','S','y','set_adminmgr_topmain.cfm?fromlink=company&frommode=new&fromreport=fr_wflw_history_lst','topmain','GcWmRpWh','GRW102'),
		fAy( Tlt("<cfif set_language is 'english'>Workflow Control Listing</cfif>"),'1','a','S','y','set_adminmgr_topmain.cfm?fromlink=company&frommode=new&fromreport=fr_wflw_control_lst','topmain','GcWmRpWc','GRW103'),
		fAy( Tlt("<cfif set_language is 'english'>Approval Control Listing</cfif>"),'1','a','S','y','set_adminmgr_topmain.cfm?fromlink=company&frommode=new&fromreport=fr_approval_control_lst','topmain','GcWmRpAc','GRW104')
		),'S','y','ns_wgp_tnomodules.cfm','topmain','GcWmRp','')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcWm',''),
	
	
	fAy( Tlt("<cfif set_language is 'english'>General Code</cfif>"),'0',GcGc,'S','y','ns_wgp_tnomodules.cfm','topmain','GcGc',''),
	
	
	fAy( Tlt("<cfif set_language is 'english'>Transaction Tracking</cfif>"),'0',fAy(
	fAy( Tlt("<cfif set_language is 'english'>Reports</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>Transaction Listing</cfif>"),'1','a','R','y','ns_fr_topmain.cfm?topHdr=Reports&btmFyl=fr_trx_prelim.cfm&fromlink=fr_trx_list&fromreport=fr_trx_list','topmain','GcTtReTl','GRT101'),
		fAy( Tlt("<cfif set_language is 'english'>Daily Entry Listing</cfif>"),'1','a','R','y','ns_fr_topmain.cfm?topHdr=Reports&btmFyl=fr_trx_prelim.cfm&fromlink=fr_trx_list&fromreport=fr_daily_entry','topmain','GcTtReDe','GRT102'),
		fAy( Tlt("<cfif set_language is 'english'>Transaction Tracking</cfif>"),'1','a','R','y','ns_fr_topmain.cfm?topHdr=Reports&btmFyl=fr_scm_prelim.cfm&fromlink=mgmtconsole&fromreport=fr_scm_track','topmain','GcTtReTt','GRT103'),
		fAy( Tlt("<cfif set_language is 'english'>Open Transaction Flow</cfif>"),'1','a','R','y','ns_fr_topmain.cfm?topHdr=Reports&btmFyl=fr_common2_prelim.cfm&fromlink=mgmtconsole&fromreport=fr_open_trans','topmain','GcTtReOt','GRT104'),
		fAy( Tlt("<cfif set_language is 'english'>Interco Open Transaction Flow</cfif>"),'1','a','R','y','ns_fr_topmain.cfm?topHdr=Reports&btmFyl=fr_common2_prelim.cfm&fromlink=mgmtconsole&fromreport=fr_interco_open_trans','topmain','GcTtReIO','GRT107'),
		fAy( Tlt("<cfif set_language is 'english'>Transaction Detail Report</cfif>"),'1','A','R','y','ns_fr_topmain.cfm?topHdr=Reports&btmFyl=fr_scm_prelim.cfm&fromlink=mgmtconsole&fromreport=fr_trx_dtl_rep','topmain','GcTtReTd','GRT105'),
		fAy( Tlt("<cfif set_language is 'english'>Attachment Report</cfif>"),'1','a','R','y','ns_fr_topmain.cfm?topHdr=Reports&btmFyl=fr_scm_prelim.cfm&fromlink=fr_trx_list&fromreport=fr_att_list','topmain','GcTtReSr','GFU104'),
		fAy( Tlt("<cfif set_language is 'english'>Transaction Print Audit</cfif>"),'1','a','R','y','ns_fr_topmain.cfm?topHdr=Reports&btmFyl=fr_trx_prelim.cfm&fromlink=fr_trx_list&fromreport=fr_print_audit','topmain','GcTtRePa','GRT106')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcTtRe','')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcTt',''),
	
	
	
	
	fAy( Tlt("<cfif set_language is 'english'>Document Mgmt</cfif>"),'0',fAy(
	fAy( Tlt("<cfif set_language is 'english'>Document Mgmt</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>Link Document</cfif>"),'1','a','L','y','set_imagemgmt_topmain.cfm?fromlink=#fromlink#&frommode=new&fromsegm=link_img','topmain','GcDmDmLd','GFU101'),
		fAy( Tlt("<cfif set_language is 'english'>Upload Documents</cfif>"),'1','a','L','y','set_imagemgmt_topmain.cfm?fromlink=#fromlink#&frommode=new&fromsegm=upload_img','topmain','GcDmDmUd','GFU102'),
		fAy( Tlt("<cfif set_language is 'english'>Upload Company Logo</cfif>"),'1','a','L','y','set_imagemgmt_topmain.cfm?fromlink=#fromlink#&frommode=new&fromsegm=upload_logo','topmain','GcDmDmCl','GFU103'),
		fAy( Tlt("<cfif set_language is 'english'>Search Documents</cfif>"),'1','a','L','y','set_imagemgmt_topmain.cfm?fromlink=adminmgr&frommode=new&fromsegm=search_doc','topmain','GcDmDmSr','GFU104'),
		fAy( Tlt("<cfif set_language is 'english'>Documents Slideshow</cfif>"),'1','a','L','y','set_imagemgmt_topmain.cfm?fromlink=adminmgr&frommode=new&fromsegm=doc_slide','topmain','GcDmDmSl','GFU105'),
		fAy( Tlt("<cfif set_language is 'english'>Upload Control Parameters</cfif>"),'1','a','L','y','set_imagemgmt_topmain.cfm?fromlink=adminmgr&frommode=new&fromsegm=upcontrol','topmain','GcDmDmUc','GFU106')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcDmDm',''),
	fAy( Tlt("<cfif set_language is 'english'>Shared Folder</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>Shared Folder Directory</cfif>"),'1','a','L','y','set_imagemgmt_topmain.cfm?fromlink=#fromlink#&frommode=new&fromsegm=shrddir','topmain','GcDmSfDr','GSF101')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcDmSf',''),
	
	fAy( Tlt("<cfif set_language is 'english'>My Documents</cfif>"),'0',fAy(
		fAy( Tlt("<cfif set_language is 'english'>My Document Folders</cfif>"),'1','a','S','y','set_gencode_topmain.cfm?fromlink=gencode&frommode=new&fromsegm=mydocfldr','topmain','GcDmMdFl','GSF102')
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcDmMd','')
	
	),'S','y','ns_wgp_tnomodules.cfm','topmain','GcDm','')
	
	),'S','y','ns_wgp_tnomodules.cfm','topmain','Gc','') >
	
	</cfoutput>
	
	