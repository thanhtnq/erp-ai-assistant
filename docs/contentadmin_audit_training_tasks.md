# Contentadmin Audit Logic — Training Task Plan

## Mục tiêu
Chuẩn bị tài liệu và task để huấn luyện AI/LLM dựa trên logic audit trong deployment `contentadmin`.

## Những file audit chính đã đọc
- `D:\tnosystems\v50foldersetadmin\v50stringg3new\v50master\contentadmin\audit_masterdata.cfm`
- `D:\tnosystems\v50foldersetadmin\v50stringg3new\v50master\contentadmin\audit_masterdata_v2.cfm`
- `D:\tnosystems\v50foldersetadmin\v50stringg3new\v50master\contentadmin\inc_ajax_update_auditlog.cfm`
- `D:\tnosystems\v50foldersetadmin\v50stringg3new\v50master\contentadmin\inc_get_audit_detail.cfm`
- `D:\tnosystems\v50foldersetadmin\v50stringg3new\v50master\contentadmin\inc_oup_ins_sys_sec_audit_logging.cfm`
- `D:\tnosystems\v50foldersetadmin\v50stringg3new\v50master\contentadmin\inc_oup_ins_sys_sec_audit.cfm`
- `D:\tnosystems\v50foldersetadmin\v50stringg3new\v50master\contentadmin\inc_oup_ins_sys_sec_audit_user.cfm`
- `D:\tnosystems\v50foldersetadmin\v50stringg3new\v50master\contentadmin\inc_trans_auditlog_listmain.cfm`

## Logic audit quan trọng

### 1. Bảng audit chính: `sys_sec_audit`
- Ghi nhật ký audit vào `sys_sec_audit`.
- Các trường khóa:
  - `masterfn`, `companyfn` — phạm vi tenant.
  - `uniquenum_pri`, `uniquenum_sec` — định danh đối tượng và chuỗi thay đổi.
  - `tag_table_usage` — phân loại audit: `enaudit`, `taudit`, `tnaudit`, `uaudit`, `tabaudit`.
  - `cslsegm`, `cslmodule`, `csltemplate` — xác định loại form/action.
  - `var_50_001`..`var_50_008` — chứa thông tin bổ sung, ví dụ `dnum_docnum`, giá trị, template, đối tượng.
  - `userid_cookie`, `date_lastupdate`, `remote_addr`, `party_code`, `party_desc`.

### 2. Cơ chế viết audit
- `inc_ajax_update_auditlog.cfm` xác định ngữ cảnh audit trước khi ghi record.
- Dùng `update_routine` để tìm audit đã tồn tại và tránh duplicate ghi log cho cùng một sự kiện.
- Gán `audit_action_type = 'vp'` trong nhiều trường hợp; một số hành vi chuyển đổi sang `ne`, `ed`, `rn` khi `frommode='new'` hoặc `fromrevise='y'`.
- Nếu cache audit query trả về 0 record, file sẽ include `inc_oup_ins_sys_sec_audit_logging.cfm` để chèn record mới.
- `inc_oup_ins_sys_sec_audit_logging.cfm` là lõi ghi log, thêm giá trị business-specific và mapping hành vi như:
  - `fromtrans` / `fromsegm` → `cslsegm` / `cslmodule`
  - `cntct_code` → customer/vendor/both handling
  - `audit_transaction_yn` → `tnaudit`
  - `from_tabsetting_audit_yn` → `tabaudit`
  - `fmi_dnum_auto` → transaction logic cho SO/PO/GRN/CRM.
- `inc_oup_ins_sys_sec_audit.cfm` chèn trực tiếp record `tag_table_usage = 'taudit'` khi `bm_this_audit_insert_yn = 'y'`.
  - `type_user_action` được xác định từ `frommode` / `fromaction` / `fromrevise` / `fromlock` / `fromunlock`.
  - `uniquenum_pri` dùng `fmi_uniquenum_pri_revise` hoặc `edit_uniq` khi `revise_pr` và chế độ edit.
  - `dnum_docnum` được chọn theo `fromtrans` và `check_lock`: `fmi_dnum_do`, `fmi_dnum_po`, `fmi_dnum_soe`, `fmi_dnum_grn`, ngược lại `fmi_dnum_auto`.
  - `fmi_dnum_auto` bản thân được map trong `inc_oup_ins_sys_sec_audit_logging.cfm` từ `fromtrans`:
    - `sal_soc` → `fmi_dnum_soe`
    - `sal_pmc` → `fmi_dnum_pmp`
    - `stk_doc` → `fmi_dnum_do`
    - `pur_poc` → `fmi_dnum_po`
    - `stk_gvn` → `fmi_dnum_grn`
    - `crm_int` (delete) → `fmi_dnum_crm_int`
    - `projtask` (delete) → `fmi_dnum_crm_projtask`
  - `mfn_trans_audit_trail_yn` và `audit_transaction_yn` quyết định có ghi `taudit` hay không.
- `inc_oup_ins_sys_sec_audit_user.cfm` xử lý audit user-rights riêng với `tag_table_usage = 'uaudit'`.
  - Nó dùng `cslmodule = type_audit_action` và `cslsegm = 'ns_adduser'`.
  - `uniquenum_sec` là `newuniquenum` nếu có, hoặc `audit_uniquenum_pri`.
  - `party_code`/`var_50_001` lưu `audit_audit_cnt` để theo dõi audit count.
- `inc_oup_ins_sys_sec_audit_logging.cfm` còn có rules chuyên biệt:
  - `fromsegm` thuộc nhóm `actifeature, genset, vindustry, compemail, jurisdiction, prilang, upricedecimal, vatgst, prjalcact, prjalccst, paysetwc` hoặc `from_tabsetting_audit_yn = y` hoặc `fromlink = prefeset` ép `audit_action_type = 'ed'`.
  - `frommode='new'` và `audit_action_type='ed'` đổi thành `ne`; nếu `fromrevise='y'` thì thành `rn`.
  - `fromsegm='cntylist'` chuyển `bme_fromsegm='countrylist'`.
  - `fromsegm='tnomenu'` và `fromtrans='setup'` chuyển `bme_fromsegm=fromtrans`.
  - Với contact audit, `adm_contact_oup.cfm` có thể sửa `cslsegm` từ existing `enaudit` row để chuyển `contact` sang `cust`/`vend`/`both`.
  - `audit_form_value` bị cắt ⌊24 ký tự nếu quá dài.
- `inc_oup_ins_sys_sec_audit_logging.cfm` chèn `sys_sec_audit` record với các trường business-specific như `co_code`, `tag_deleted_yn`, `party_orig_code`, `email_add`, `vle_type_grouping`.

### 3. Cơ chế đọc audit
- `audit_masterdata.cfm` và `audit_masterdata_v2.cfm` lấy audit từ `sys_sec_audit` với điều kiện: `masterfn`, `companyfn`, `tag_table_usage`, `fromsegm`/`fromtrans`, và `date_post >= 2 năm trước`.
- Ngoại lệ đặc biệt: tenant `lumchangmfn` trong HR (`hrm_employee` / `na`) mở rộng thành 5 năm.
- `inc_get_audit_detail.cfm` lấy chi tiết record, map `cslmodule` thành nhãn hành động và xử lý các trường hợp business-specific.

### 4. Mapping hành động audit
- Các giá trị action phổ biến:
  - `ne`, `new` → Create New
  - `ed`, `edit` → Edit
  - `de`, `delete` → Delete
  - `vo`, `void` → Void
  - `up`, `update` → Update
  - `rv`, `revise` → Revise
  - `lk`, `lock` → Locked
  - `un`, `unlock` → Unlocked
  - `ub`, `unpublish` → Unpublish
  - `pb`, `publish` → Publish
  - `cp` → Change Party
  - `cd` → Change DocNum
- `inc_get_audit_detail.cfm` cũng xử lý các giá trị đặc thù như `payrollclaim_e`, `payrollgl`, `ibgap`, `hrpayproc` khi `dnum_docnum` trống.

## Task để chuẩn bị training AI/LLM

### Task 1 — Xác định phạm vi audit model
- Ghi rõ `sys_sec_audit` là nguồn chính cho audit history.
- Làm rõ rằng logic audit phân tách theo tenant (`masterfn`, `companyfn`).
- Xác định các file logic cần huấn luyện: `audit_masterdata.cfm`, `audit_masterdata_v2.cfm`, `inc_ajax_update_auditlog.cfm`, `inc_get_audit_detail.cfm`, `inc_oup_ins_sys_sec_audit_logging.cfm`, `inc_oup_ins_sys_sec_audit.cfm`, `inc_oup_ins_sys_sec_audit_user.cfm`, `inc_trans_auditlog_listmain.cfm`.
- Ghi chú: `inc_oup_ins_sys_sec_audit.cfm` và `inc_oup_ins_sys_sec_audit_user.cfm` chứa cơ chế chèn audit tác vụ người dùng và transaction cụ thể.

### Task 2 — Trích xuất biến audit quan trọng
- `masterfn`, `companyfn`, `uniquenum_pri`, `uniquenum_sec`
- `tag_table_usage`, `cslsegm`, `cslmodule`, `csltemplate`
- `var_50_001`..`var_50_008`
- `userid_cookie`, `date_lastupdate`, `remote_addr`, `party_code`, `party_desc`

### Task 3 — Map intent sang hành động audit
- Tạo bảng mapping `cslmodule` → action label.
- Tạo bảng mapping `tag_table_usage` → phân loại audit.
- Tạo rule cho filter `fromsegm` / `fromtrans`.
- Chuẩn hóa cách model nhận biết khi cần show audit list so với audit detail.

### Task 4 — Xây dựng sample prompt/output
- Ví dụ prompt:
  - "Show audit history for this transaction."
  - "What changes were made to this vendor master record?"
  - "Audit detail for record ID X."
- Expected output:
  - filter by tenant scope
  - filter by timeframe
  - present action label và field thay đổi
  - drill into `sys_sec_audit` detail nếu cần

### Task 5 — Kiểm tra quy tắc thời gian
- Nhận diện rule `date_post >= 2 năm trước`.
- Nhận diện ngoại lệ `lumchangmfn` → 5 năm.
- Đảm bảo model không trả kết quả audit quá thời hạn.

### Task 6 — Kiểm tra nguồn dữ liệu phụ thuộc
- Xác định các include audit có thể liên quan: shared include và các template audit khác.
- Đảm bảo logic insert/update trong `sys_sec_audit` được xác nhận không chỉ qua một trang audit.

### Task 7 — Tìm và ghi nhận file chèn audit trực tiếp
- Quét toàn bộ `contentadmin` production để tìm các file chứa chuỗi `Insert Into sys_sec_audit`.
- Kết quả hiện tại: 39 file trực tiếp chèn audit cần được xác nhận và đưa vào scope training.
- Trong cùng production, 495 file có `cfinclude`/`cfinclude template` đến `inc_oup_ins_sys_sec_audit*`, cho thấy hầu hết audit entry flow đều qua shared include.
- File quan trọng gồm:
  - `appk_trans_delete.cfm`
  - `con_bom_mas_oup.cfm`
  - `crc_admin_upd.cfm`
  - `crc_undo_upd.cfm`
  - `crm_interaction_listmain_search_oup.cfm`
  - `ess_timesheet_listmain.cfm`
  - `ess_timesheet_oup.cfm`
  - `hrm_gencode_listmain.cfm`
  - `hrm_gencode_oup.cfm`
  - `hrm_generate_resume_oup.cfm`
  - `inc_ajax_sch_book_dtl.cfm`
  - `inc_cntct_trans_tab_section_oup.cfm`
  - `inc_crc_wflow_upd_audit.cfm`
  - `inc_hrm_payroll_list_delete.cfm`
  - `inc_hrm_payroll_salrate_oup_01.cfm`
  - `inc_lea_asset_search_oup.cfm`
  - `inc_oup_ins_sys_sec_audit.cfm`
  - `inc_oup_ins_sys_sec_audit_logging.cfm`
  - `inc_oup_ins_sys_sec_audit_user.cfm`
  - `inc_qs_set_listmain_search.cfm`
  - `inc_qs_set_listmain_taskmng.cfm`
  - `inc_qs_set_opportunity_search.cfm`
  - `inc_qs_set_stkcode_search.cfm`
  - `inc_sch_book_dtl_row_audit_oup.cfm`
  - `inc_tab_cntct_update_soap_carclub.cfm`
  - `inc_trans_common1_topmain_setting.cfm`
  - `scm_whs_util_oup.cfm`
  - `set_altappr_upd.cfm`
  - `set_cmdc_oup.cfm`
  - `set_coa_accpacactmap_oup.cfm`
  - `set_coa_sapactmap_oup.cfm`
  - `set_print_oup.cfm`
  - `set_prqoarel_oup.cfm`
  - `set_reset_password_oup.cfm`
  - `set_sysadmin_oup.cfm`
  - `set_transactiontype_init.cfm`
  - `sor_code_listmain_search_oup.cfm`
  - `train_application_oup.cfm`
  - `Upd_Print_Tag.cfm`
- Xác định xem những file này chèn trực tiếp hay gọi các include audit chung như `inc_oup_ins_sys_sec_audit.cfm`.
- Kiểm tra xác nhận cho thấy một số file chứa nhiều lần insert trực tiếp:
  - `inc_qs_set_listmain_search.cfm` — 2 lần insert
  - `inc_qs_set_listmain_taskmng.cfm` — 2 lần insert
  - `inc_tab_cntct_update_soap_carclub.cfm` — 4 lần insert
  - `Upd_Print_Tag.cfm` — 2 lần insert
- Đặc biệt chú ý 3 file core include có logic insert trực tiếp và mapping audit: `inc_oup_ins_sys_sec_audit.cfm`, `inc_oup_ins_sys_sec_audit_logging.cfm`, `inc_oup_ins_sys_sec_audit_user.cfm`.
- Nhóm 39 file trực tiếp theo nghiệp vụ:
  - `HR/Payroll` (7 file): `ess_timesheet_listmain.cfm`, `ess_timesheet_oup.cfm`, `hrm_gencode_listmain.cfm`, `hrm_gencode_oup.cfm`, `hrm_generate_resume_oup.cfm`, `inc_hrm_payroll_list_delete.cfm`, `inc_hrm_payroll_salrate_oup_01.cfm`
  - `User/Admin` (3 file): `set_reset_password_oup.cfm`, `set_sysadmin_oup.cfm`, `set_transactiontype_init.cfm`
  - `Transaction/ERP` (22 file): `appk_trans_delete.cfm`, `con_bom_mas_oup.cfm`, `crc_admin_upd.cfm`, `crc_undo_upd.cfm`, `crm_interaction_listmain_search_oup.cfm`, `inc_crc_wflow_upd_audit.cfm`, `inc_lea_asset_search_oup.cfm`, `inc_qs_set_listmain_search.cfm`, `inc_qs_set_listmain_taskmng.cfm`, `inc_qs_set_opportunity_search.cfm`, `inc_qs_set_stkcode_search.cfm`, `inc_sch_book_dtl_row_audit_oup.cfm`, `inc_tab_cntct_update_soap_carclub.cfm`, `scm_whs_util_oup.cfm`, `set_altappr_upd.cfm`, `set_cmdc_oup.cfm`, `set_coa_accpacactmap_oup.cfm`, `set_coa_sapactmap_oup.cfm`, `set_print_oup.cfm`, `set_prqoarel_oup.cfm`, `sor_code_listmain_search_oup.cfm`, `train_application_oup.cfm`
  - `Audit Shared Include` (3 file): `inc_oup_ins_sys_sec_audit.cfm`, `inc_oup_ins_sys_sec_audit_logging.cfm`, `inc_oup_ins_sys_sec_audit_user.cfm`
  - `Other` (4 file): `inc_ajax_sch_book_dtl.cfm`, `inc_cntct_trans_tab_section_oup.cfm`, `inc_trans_common1_topmain_setting.cfm`, `Upd_Print_Tag.cfm`

### Task 8 — Ký hiệu và phân loại file chèn audit
- Đánh dấu file chèn audit trực tiếp thành 3 nhóm: transaction update, HR/payroll và user/account management.
- Với mỗi nhóm, note lại cách `tag_table_usage`, `cslmodule`, `fromsegm`, `fromtrans` được gán.
- Nếu cần, mở thêm các file liên quan scan theo `sys_sec_audit` để trực quan hóa luồng dữ liệu.

## Ghi chú
- Tập trung vào source production `contentadmin` đã đọc trực tiếp tại deployment `D:\tnosystems\v50foldersetadmin\v50stringg3new\v50master\contentadmin`.
- Workspace repo hiện tại không tương đồng với deployment production; tài liệu này hướng vào logic audit deployment thực tế.
- Nếu cần, có thể mở rộng thêm bằng cách đọc các file audit khác trong `contentadmin`.
