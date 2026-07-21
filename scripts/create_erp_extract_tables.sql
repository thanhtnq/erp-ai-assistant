-- =============================================================================
-- ERP Extract Database for AI Assistant
-- Extracted from Globe3 PostgreSQL → SQLite
-- Version: 1.0.0
-- Created: 2026-07-17
-- 
-- Mỗi table có thêm scope_masterfn và scope_companyfn để hỗ trợ multi-company.
-- Tất cả queries PHẢI có WHERE scope_masterfn=? AND scope_companyfn=?
-- =============================================================================

-- 1. Sales Header
CREATE TABLE IF NOT EXISTS scm_sal_main (
    uniquenum_pri      TEXT PRIMARY KEY,
    scope_masterfn     TEXT NOT NULL,
    scope_companyfn    TEXT NOT NULL,
    masterfn           TEXT NOT NULL,
    companyfn          TEXT NOT NULL,
    dnum_auto          TEXT,
    dnum_reference     TEXT,
    date_trans         TEXT,
    date_due           TEXT,
    party_code         TEXT,
    party_desc         TEXT,
    party_unique       TEXT,
    amount_forex       REAL,
    amount_local       REAL,
    curr_short_forex   TEXT,
    curr_rate_forex_f_calc REAL,
    staff_code         TEXT,
    staff_desc         TEXT,
    staff_unique       TEXT,
    location_code      TEXT,
    deptunit_code      TEXT,
    deptunit_desc      TEXT,
    creditterm_desc    TEXT,
    delivtype_desc     TEXT,
    sendby_desc        TEXT,
    tag_void_yn        TEXT DEFAULT 'n',
    tag_table_usage    TEXT NOT NULL,
    date_lastupdate    TEXT
);

-- 2. Sales Line Items
CREATE TABLE IF NOT EXISTS scm_sal_data (
    uniquenum_pri      TEXT NOT NULL,
    scope_masterfn     TEXT NOT NULL,
    scope_companyfn    TEXT NOT NULL,
    masterfn           TEXT NOT NULL,
    companyfn          TEXT NOT NULL,
    tag_table_usage    TEXT,
    stkcode_code       TEXT,
    stkcode_desc       TEXT,
    stkcate_desc       TEXT,
    qnty_total         REAL,
    amount_local       REAL,
    location_code      TEXT,
    tag_void_yn        TEXT DEFAULT 'n',
    date_trans         TEXT,
    qnty_uomstk        REAL,
    bal_qnty_uomstk    REAL,
    PRIMARY KEY (uniquenum_pri, stkcode_code, scope_masterfn, scope_companyfn)
);

-- 3. Purchase Header
CREATE TABLE IF NOT EXISTS scm_pur_main (
    uniquenum_pri      TEXT PRIMARY KEY,
    scope_masterfn     TEXT NOT NULL,
    scope_companyfn    TEXT NOT NULL,
    masterfn           TEXT NOT NULL,
    companyfn          TEXT NOT NULL,
    dnum_auto          TEXT,
    dnum_docnum        TEXT,
    dnum_reference     TEXT,
    date_trans         TEXT,
    date_due           TEXT,
    date_delivery      TEXT,
    party_code         TEXT,
    party_desc         TEXT,
    amount_forex       REAL,
    amount_local       REAL,
    subtot_forex       REAL,
    subtot_local       REAL,
    nettot_forex       REAL,
    nettot_local       REAL,
    curr_short_forex   TEXT,
    staff_code         TEXT,
    location_code      TEXT,
    tag_void_yn        TEXT DEFAULT 'n',
    tag_table_usage    TEXT NOT NULL,
    tag_deleted_yn     TEXT DEFAULT 'n',
    tag_autogen_record_yn TEXT DEFAULT 'n',
    tag_closed02_yn    TEXT DEFAULT 'n',
    tag_closed03_yn    TEXT DEFAULT 'n'
);

-- 4. Purchase Line Items
CREATE TABLE IF NOT EXISTS scm_pur_data (
    uniquenum_pri      TEXT NOT NULL,
    scope_masterfn     TEXT NOT NULL,
    scope_companyfn    TEXT NOT NULL,
    masterfn           TEXT NOT NULL,
    companyfn          TEXT NOT NULL,
    tag_table_usage    TEXT,
    stkcode_code       TEXT,
    bal_qnty_uomstk    REAL,
    tag_void_yn        TEXT DEFAULT 'n',
    var_25_003         TEXT,
    PRIMARY KEY (uniquenum_pri, stkcode_code, scope_masterfn, scope_companyfn)
);

-- 5. Stock Movement Header
CREATE TABLE IF NOT EXISTS scm_stk_main (
    uniquenum_pri      TEXT PRIMARY KEY,
    scope_masterfn     TEXT NOT NULL,
    scope_companyfn    TEXT NOT NULL,
    masterfn           TEXT NOT NULL,
    companyfn          TEXT NOT NULL,
    dnum_auto          TEXT,
    date_trans         TEXT,
    userid_cookie      TEXT,
    location_code      TEXT,
    tag_table_usage    TEXT NOT NULL,
    tag_void_yn        TEXT DEFAULT 'n'
);

-- 6. Stock Movement Line Items
CREATE TABLE IF NOT EXISTS scm_stk_data (
    uniquenum_pri      TEXT NOT NULL,
    scope_masterfn     TEXT NOT NULL,
    scope_companyfn    TEXT NOT NULL,
    masterfn           TEXT NOT NULL,
    companyfn          TEXT NOT NULL,
    tag_table_usage    TEXT,
    stkcode_code       TEXT,
    stkcode_desc       TEXT,
    qnty_uomstk        REAL,
    qnty_total         REAL,
    amount_local       REAL,
    tag_void_yn        TEXT DEFAULT 'n',
    PRIMARY KEY (uniquenum_pri, stkcode_code, scope_masterfn, scope_companyfn)
);

-- 7. Stock Item Master
CREATE TABLE IF NOT EXISTS stk_code_main (
    uniquenum_pri      TEXT PRIMARY KEY,
    scope_masterfn     TEXT NOT NULL,
    scope_companyfn    TEXT NOT NULL,
    masterfn           TEXT NOT NULL,
    companyfn          TEXT NOT NULL,
    stkcode_code       TEXT,
    stkcode_desc_english TEXT,
    stkgrp_desc        TEXT,
    stkcate_desc       TEXT,
    brand_desc         TEXT,
    uom_stk_code       TEXT,
    stkm_qnty_total    REAL,
    level_min          REAL,
    level_max          REAL,
    level_reorder      REAL,
    amt_cost_mostrecent REAL,
    amt_cost_stdnormal REAL,
    amt_price_stdnormal REAL,
    tag_active_yn      TEXT DEFAULT 'y',
    tag_void_yn        TEXT DEFAULT 'n',
    tag_assembly_yn    TEXT DEFAULT 'n',
    tag_taxable_yn     TEXT DEFAULT 'n',
    tag_batch_ctrl_yn  TEXT DEFAULT 'n',
    tag_serial_ctrl_yn TEXT DEFAULT 'n',
    date_lastupdate    TEXT
);

-- 8. Stock Item Vendor Data
CREATE TABLE IF NOT EXISTS stk_code_data (
    uniquenum_pri      TEXT PRIMARY KEY,
    scope_masterfn     TEXT NOT NULL,
    scope_companyfn    TEXT NOT NULL,
    masterfn           TEXT NOT NULL,
    companyfn          TEXT NOT NULL,
    stkcode_code       TEXT,
    party_code         TEXT,
    location_code      TEXT,
    vendor_leadtime_days TEXT,
    num_20_4_d_001     REAL,
    tag_table_usage    TEXT,
    tag_void_yn        TEXT DEFAULT 'n'
);

-- 9. Customer/Party Master
CREATE TABLE IF NOT EXISTS adm_cnt_main (
    uniquenum_pri      TEXT PRIMARY KEY,
    scope_masterfn     TEXT NOT NULL,
    scope_companyfn    TEXT NOT NULL,
    masterfn           TEXT NOT NULL,
    companyfn          TEXT NOT NULL,
    party_code         TEXT,
    party_desc         TEXT,
    tag_client_vendor  TEXT,
    tag_active_yn      TEXT DEFAULT 'y',
    creditlimit_client REAL,
    addr_main_nation   TEXT,
    addr_main_state    TEXT
);

-- 10. Customer Bank Data
CREATE TABLE IF NOT EXISTS adm_cnt_data (
    uniquenum_pri      TEXT NOT NULL,
    scope_masterfn     TEXT NOT NULL,
    scope_companyfn    TEXT NOT NULL,
    masterfn           TEXT NOT NULL,
    companyfn          TEXT NOT NULL,
    party_code         TEXT,
    party_desc         TEXT,
    bankactnum         TEXT,
    bankname           TEXT,
    tag_table_usage    TEXT,
    tag_active_yn      TEXT DEFAULT 'y',
    PRIMARY KEY (uniquenum_pri, bankactnum, scope_masterfn, scope_companyfn)
);

-- 11. General Ledger Detail
CREATE TABLE IF NOT EXISTS gen_ledger_detail (
    uniquenum_pri      TEXT PRIMARY KEY,
    scope_masterfn     TEXT NOT NULL,
    scope_companyfn    TEXT NOT NULL,
    masterfn           TEXT NOT NULL,
    companyfn          TEXT NOT NULL,
    dnum_auto          TEXT,
    dnum_docnum        TEXT,
    dnum_reference     TEXT,
    date_trans         TEXT,
    date_due           TEXT,
    party_code         TEXT,
    party_desc         TEXT,
    acctnumdisp        TEXT,
    amount_forex       REAL,
    amount_local       REAL,
    tag_table_usage    TEXT,
    tag_wflow_app_yn   TEXT DEFAULT 'n',
    tag_actbudforma    TEXT DEFAULT 'act',
    tag_void_yn        TEXT DEFAULT 'n',
    bankrec_marker     TEXT DEFAULT 'n',
    bankrec_date       TEXT
);

-- 12. GL Master (AP/AR)
CREATE TABLE IF NOT EXISTS gnl_maint_all (
    uniquenum_pri      TEXT PRIMARY KEY,
    scope_masterfn     TEXT NOT NULL,
    scope_companyfn    TEXT NOT NULL,
    masterfn           TEXT NOT NULL,
    companyfn          TEXT NOT NULL,
    dnum_auto          TEXT,
    dnum_reference     TEXT,
    maint_dnum_docnum  TEXT,
    maint_date_trans   TEXT,
    maint_date_due     TEXT,
    maint_amount_local REAL,
    maint_amount_forex REAL,
    maint_amount_orig  REAL,
    maint_curr_short   TEXT,
    maint_acctnumdisp  TEXT,
    maint_cslsegm      TEXT,
    party_code         TEXT,
    party_desc         TEXT,
    date_trans         TEXT,
    tag_table_usage    TEXT,
    tag_void_yn        TEXT DEFAULT 'n',
    tag_closed_yn      TEXT DEFAULT 'n'
);

-- 13. Stock Ledger
CREATE TABLE IF NOT EXISTS stkm_main_all (
    uniquenum_pri           TEXT PRIMARY KEY,
    scope_masterfn          TEXT NOT NULL,
    scope_companyfn         TEXT NOT NULL,
    masterfn                TEXT NOT NULL,
    companyfn               TEXT NOT NULL,
    stkcode_code            TEXT,
    location_code           TEXT,
    bin_code                TEXT,
    batchnum_code           TEXT,
    date_expiry             TEXT,
    balance_qnty_uom_stk_code REAL,
    value_unitcost_local    REAL,
    tag_void_yn             TEXT DEFAULT 'n',
    tag_stkm_valid_yn       TEXT DEFAULT 'y'
);

-- 14. Memo Long Table
CREATE TABLE IF NOT EXISTS memo_long_table (
    uniquenum_pri      TEXT PRIMARY KEY,
    scope_masterfn     TEXT NOT NULL,
    scope_companyfn    TEXT NOT NULL,
    masterfn           TEXT NOT NULL,
    companyfn          TEXT NOT NULL,
    notes_memo         TEXT,
    tag_memo_type      TEXT
);

-- 15. Project Master (CRM Tickets)
CREATE TABLE IF NOT EXISTS prj_pbill_main (
    uniquenum_pri      TEXT PRIMARY KEY,
    scope_masterfn     TEXT NOT NULL,
    scope_companyfn    TEXT NOT NULL,
    masterfn           TEXT NOT NULL,
    companyfn          TEXT NOT NULL
);

-- 16. Project Body (CRM Ticket details)
CREATE TABLE IF NOT EXISTS prj_pbill_body (
    uniquenum_pri      TEXT PRIMARY KEY,
    scope_masterfn     TEXT NOT NULL,
    scope_companyfn    TEXT NOT NULL,
    masterfn           TEXT NOT NULL,
    companyfn          TEXT NOT NULL,
    entprojfn_code     TEXT,
    notes_memo         TEXT,
    tag_closed01_yn    TEXT DEFAULT 'n',
    tag_closed02_yn    TEXT DEFAULT 'n',
    tag_closed03_yn    TEXT DEFAULT 'n',
    tag_closed04_yn    TEXT DEFAULT 'n',
    var_25_001         TEXT,
    var_25_002         TEXT,
    var_25_003         TEXT,
    var_25_004         TEXT,
    num_20_4_d_001     REAL,
    num_20_4_d_002     REAL,
    num_20_4_d_003     REAL,
    num_20_4_d_004     REAL,
    date_001           TEXT,
    date_002           TEXT,
    date_003           TEXT,
    date_004           TEXT
);


-- 17. GL Stock Ledger
CREATE TABLE IF NOT EXISTS gen_ledger_stk (
    uniquenum_pri      TEXT PRIMARY KEY,
    scope_masterfn     TEXT NOT NULL,
    scope_companyfn    TEXT NOT NULL,
    masterfn           TEXT NOT NULL,
    companyfn          TEXT NOT NULL,
    acctnumdisp        TEXT,
    party_code         TEXT,
    party_desc         TEXT,
    date_trans         TEXT,
    date_post          TEXT,
    fyearcfn           TEXT,
    periodmth_cfn      TEXT,
    staff_code         TEXT,
    deptunit_code      TEXT,
    location_code      TEXT,
    cslsegm            TEXT,
    amount_forex       REAL,
    amount_local       REAL,
    tag_void_yn        TEXT DEFAULT 'n',
    tag_wflow_app_yn   TEXT DEFAULT 'n'
);


-- =============================================================================
-- INDEXES for performance
-- =============================================================================

-- Scope indexes (bắt buộc cho mọi query)
CREATE INDEX IF NOT EXISTS idx_sal_main_scope ON scm_sal_main(scope_masterfn, scope_companyfn);
CREATE INDEX IF NOT EXISTS idx_sal_data_scope ON scm_sal_data(scope_masterfn, scope_companyfn);
CREATE INDEX IF NOT EXISTS idx_pur_main_scope ON scm_pur_main(scope_masterfn, scope_companyfn);
CREATE INDEX IF NOT EXISTS idx_pur_data_scope ON scm_pur_data(scope_masterfn, scope_companyfn);
CREATE INDEX IF NOT EXISTS idx_stk_main_scope ON scm_stk_main(scope_masterfn, scope_companyfn);
CREATE INDEX IF NOT EXISTS idx_stk_data_scope ON scm_stk_data(scope_masterfn, scope_companyfn);
CREATE INDEX IF NOT EXISTS idx_stk_code_main_scope ON stk_code_main(scope_masterfn, scope_companyfn);
CREATE INDEX IF NOT EXISTS idx_stk_code_data_scope ON stk_code_data(scope_masterfn, scope_companyfn);
CREATE INDEX IF NOT EXISTS idx_cnt_main_scope ON adm_cnt_main(scope_masterfn, scope_companyfn);
CREATE INDEX IF NOT EXISTS idx_cnt_data_scope ON adm_cnt_data(scope_masterfn, scope_companyfn);
CREATE INDEX IF NOT EXISTS idx_gl_detail_scope ON gen_ledger_detail(scope_masterfn, scope_companyfn);
CREATE INDEX IF NOT EXISTS idx_gnl_maint_scope ON gnl_maint_all(scope_masterfn, scope_companyfn);
CREATE INDEX IF NOT EXISTS idx_stkm_scope ON stkm_main_all(scope_masterfn, scope_companyfn);
CREATE INDEX IF NOT EXISTS idx_memo_scope ON memo_long_table(scope_masterfn, scope_companyfn);
CREATE INDEX IF NOT EXISTS idx_prj_main_scope ON prj_pbill_main(scope_masterfn, scope_companyfn);
CREATE INDEX IF NOT EXISTS idx_prj_body_scope ON prj_pbill_body(scope_masterfn, scope_companyfn);
CREATE INDEX IF NOT EXISTS idx_gl_stk_scope ON gen_ledger_stk(scope_masterfn, scope_companyfn);

-- Date indexes (cho time-range queries)
CREATE INDEX IF NOT EXISTS idx_sal_main_date ON scm_sal_main(date_trans);
CREATE INDEX IF NOT EXISTS idx_pur_main_date ON scm_pur_main(date_trans);
CREATE INDEX IF NOT EXISTS idx_gl_detail_date ON gen_ledger_detail(date_trans);
CREATE INDEX IF NOT EXISTS idx_gl_stk_date ON gen_ledger_stk(date_trans);


-- Business key indexes
CREATE INDEX IF NOT EXISTS idx_sal_main_party ON scm_sal_main(party_code);
CREATE INDEX IF NOT EXISTS idx_sal_main_usage ON scm_sal_main(tag_table_usage);
CREATE INDEX IF NOT EXISTS idx_sal_data_sku ON scm_sal_data(stkcode_code);
CREATE INDEX IF NOT EXISTS idx_pur_main_party ON scm_pur_main(party_code);
CREATE INDEX IF NOT EXISTS idx_pur_main_usage ON scm_pur_main(tag_table_usage);
CREATE INDEX IF NOT EXISTS idx_stk_code_main_code ON stk_code_main(stkcode_code);
CREATE INDEX IF NOT EXISTS idx_stk_code_data_code ON stk_code_data(stkcode_code);
CREATE INDEX IF NOT EXISTS idx_cnt_main_party ON adm_cnt_main(party_code);
CREATE INDEX IF NOT EXISTS idx_gnl_maint_party ON gnl_maint_all(party_code);
CREATE INDEX IF NOT EXISTS idx_stkm_sku ON stkm_main_all(stkcode_code);
CREATE INDEX IF NOT EXISTS idx_gl_stk_account ON gen_ledger_stk(acctnumdisp);


-- =============================================================================
-- META TABLE: lưu thông tin extract
-- =============================================================================
CREATE TABLE IF NOT EXISTS _extract_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Insert default meta
INSERT OR IGNORE INTO _extract_meta (key, value) VALUES ('schema_version', '1.0.0');
INSERT OR IGNORE INTO _extract_meta (key, value) VALUES ('created_at', datetime('now'));
INSERT OR IGNORE INTO _extract_meta (key, value) VALUES ('description', 'ERP Extract DB for AI Assistant - Multi-company support');
