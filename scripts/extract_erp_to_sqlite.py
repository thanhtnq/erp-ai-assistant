"""
ERP Extract — Multi-Scope PostgreSQL → SQLite
===============================================
Extract ERP data from Globe3 PostgreSQL to SQLite for AI Assistant fast queries.
Supports multi-company (scope = masterfn + companyfn).
Supports incremental extract (only fetch data since last run timestamp).

Usage:
    # Extract all scopes
    python scripts/extract_erp_to_sqlite.py

    # Extract specific scope
    python scripts/extract_erp_to_sqlite.py --masterfn banleong369878mfn --companyfn p23091210332792616

    # Incremental: only fetch data since last run
    python scripts/extract_erp_to_sqlite.py --incremental

    # Full re-extract (ignore last run timestamp)
    python scripts/extract_erp_to_sqlite.py --full

    # Dry run (count without inserting)
    python scripts/extract_erp_to_sqlite.py --dry-run

    # Verbose mode
    python scripts/extract_erp_to_sqlite.py --verbose
"""
import argparse
import json
import logging
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env", override=True)

try:
    import psycopg2
    import psycopg2.extras
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

# ─── Paths ────────────────────────────────────────────────────────────────────
SCOPES_FILE = PROJECT_ROOT / "data" / "erp_extract_scopes.json"
SQLITE_PATH = PROJECT_ROOT / "data" / "erp_extract.db"
SCHEMA_PATH = PROJECT_ROOT / "scripts" / "create_erp_extract_tables.sql"
LOG_FILE = PROJECT_ROOT / "logs" / "erp_extract.log"

# ─── Logging Setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(str(LOG_FILE), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("erp_extract")

# ─── Table Mapping ────────────────────────────────────────────────────────────
# Each entry: sqlite table, pg table, column mappings, where clause, order_by
# Tables with date_lastupdate or date_trans support incremental extraction.
TABLE_MAPPINGS = [
    # 1. Sales Header
    {
        "sqlite": "scm_sal_main",
        "pg": "scm_sal_main",
        "columns": [
            ("uniquenum_pri", "uniquenum_pri"),
            ("masterfn", "masterfn"),
            ("companyfn", "companyfn"),
            ("dnum_auto", "dnum_auto"),
            ("dnum_reference", "dnum_reference"),
            ("date_trans", "date_trans::text"),
            ("date_due", "date_due::text"),
            ("party_code", "party_code"),
            ("party_desc", "party_desc"),
            ("party_unique", "party_unique"),
            ("amount_forex", "amount_forex"),
            ("amount_local", "amount_local"),
            ("curr_short_forex", "curr_short_forex"),
            ("curr_rate_forex_f_calc", "curr_rate_forex_f_calc"),
            ("staff_code", "staff_code"),
            ("staff_desc", "staff_desc"),
            ("staff_unique", "staff_unique"),
            ("location_code", "location_code"),
            ("deptunit_code", "deptunit_code"),
            ("deptunit_desc", "deptunit_desc"),
            ("creditterm_desc", "creditterm_desc"),
            ("delivtype_desc", "delivtype_desc"),
            ("sendby_desc", "sendby_desc"),
            ("tag_void_yn", "tag_void_yn"),
            ("tag_table_usage", "tag_table_usage"),
            ("date_lastupdate", "date_lastupdate::text"),
        ],
        "where": "tag_deleted_yn = 'n'",
        "order_by": "date_lastupdate DESC NULLS LAST",
        "date_col": "date_lastupdate",  # for incremental
    },
    # 2. Sales Line Items
    {
        "sqlite": "scm_sal_data",
        "pg": "scm_sal_data",
        "columns": [
            ("uniquenum_pri", "uniquenum_pri"),
            ("masterfn", "masterfn"),
            ("companyfn", "companyfn"),
            ("tag_table_usage", "tag_table_usage"),
            ("stkcode_code", "stkcode_code"),
            ("stkcode_desc", "stkcode_desc"),
            ("stkcate_desc", "stkcate_desc"),
            ("qnty_total", "qnty_total"),
            ("amount_local", "amount_local"),
            ("location_code", "location_code"),
            ("tag_void_yn", "tag_void_yn"),
            ("date_trans", "date_trans::text"),
            ("qnty_uomstk", "qnty_uomstk"),
            ("bal_qnty_uomstk", "bal_qnty_uomstk"),
        ],
        "where": "tag_deleted_yn = 'n'",
        "order_by": "date_trans DESC NULLS LAST",
        "date_col": "date_trans",
    },
    # 3. Purchase Header
    {
        "sqlite": "scm_pur_main",
        "pg": "scm_pur_main",
        "columns": [
            ("uniquenum_pri", "uniquenum_pri"),
            ("masterfn", "masterfn"),
            ("companyfn", "companyfn"),
            ("dnum_auto", "dnum_auto"),
            ("dnum_docnum", "dnum_docnum"),
            ("dnum_reference", "dnum_reference"),
            ("date_trans", "date_trans::text"),
            ("date_due", "date_due::text"),
            ("date_delivery", "date_delivery::text"),
            ("party_code", "party_code"),
            ("party_desc", "party_desc"),
            ("amount_forex", "amount_forex"),
            ("amount_local", "amount_local"),
            ("subtot_forex", "subtot_forex"),
            ("subtot_local", "subtot_local"),
            ("nettot_forex", "nettot_forex"),
            ("nettot_local", "nettot_local"),
            ("curr_short_forex", "curr_short_forex"),
            ("staff_code", "staff_code"),
            ("location_code", "location_code"),
            ("tag_void_yn", "tag_void_yn"),
            ("tag_table_usage", "tag_table_usage"),
            ("tag_deleted_yn", "tag_deleted_yn"),
            ("tag_autogen_record_yn", "tag_autogen_record_yn"),
            ("tag_closed02_yn", "tag_closed02_yn"),
            ("tag_closed03_yn", "tag_closed03_yn"),
        ],
        "where": "tag_deleted_yn = 'n'",
        "order_by": "date_lastupdate DESC NULLS LAST",
        "date_col": "date_lastupdate",
    },
    # 4. Purchase Line Items
    {
        "sqlite": "scm_pur_data",
        "pg": "scm_pur_data",
        "columns": [
            ("uniquenum_pri", "uniquenum_pri"),
            ("masterfn", "masterfn"),
            ("companyfn", "companyfn"),
            ("tag_table_usage", "tag_table_usage"),
            ("stkcode_code", "stkcode_code"),
            ("bal_qnty_uomstk", "bal_qnty_uomstk"),
            ("tag_void_yn", "tag_void_yn"),
            ("var_25_003", "var_25_003"),
        ],
        "where": "tag_deleted_yn = 'n'",
        "order_by": "uniquenum_pri",
    },
    # 5. Stock Movement Header
    {
        "sqlite": "scm_stk_main",
        "pg": "scm_stk_main",
        "columns": [
            ("uniquenum_pri", "uniquenum_pri"),
            ("masterfn", "masterfn"),
            ("companyfn", "companyfn"),
            ("dnum_auto", "dnum_auto"),
            ("date_trans", "date_trans::text"),
            ("userid_cookie", "userid_cookie"),
            ("location_code", "location_code"),
            ("tag_table_usage", "tag_table_usage"),
            ("tag_void_yn", "tag_void_yn"),
        ],
        "where": "tag_deleted_yn = 'n'",
        "order_by": "date_trans DESC NULLS LAST",
        "date_col": "date_trans",
    },
    # 6. Stock Movement Line Items
    {
        "sqlite": "scm_stk_data",
        "pg": "scm_stk_data",
        "columns": [
            ("uniquenum_pri", "uniquenum_pri"),
            ("masterfn", "masterfn"),
            ("companyfn", "companyfn"),
            ("tag_table_usage", "tag_table_usage"),
            ("stkcode_code", "stkcode_code"),
            ("stkcode_desc", "stkcode_desc"),
            ("qnty_uomstk", "qnty_uomstk"),
            ("qnty_total", "qnty_total"),
            ("amount_local", "amount_local"),
            ("tag_void_yn", "tag_void_yn"),
        ],
        "where": "tag_deleted_yn = 'n'",
        "order_by": "uniquenum_pri",
    },
    # 7. Stock Item Master
    {
        "sqlite": "stk_code_main",
        "pg": "stk_code_main",
        "columns": [
            ("uniquenum_pri", "uniquenum_pri"),
            ("masterfn", "masterfn"),
            ("companyfn", "companyfn"),
            ("stkcode_code", "stkcode_code"),
            ("stkcode_desc_english", "stkcode_desc_english"),
            ("stkgrp_desc", "stkgrp_desc"),
            ("stkcate_desc", "stkcate_desc"),
            ("brand_desc", "brand_desc"),
            ("uom_stk_code", "uom_stk_code"),
            ("stkm_qnty_total", "stkm_qnty_total"),
            ("level_min", "level_min"),
            ("level_max", "level_max"),
            ("level_reorder", "level_reorder"),
            ("amt_cost_mostrecent", "amt_cost_mostrecent"),
            ("amt_cost_stdnormal", "amt_cost_stdnormal"),
            ("amt_price_stdnormal", "amt_price_stdnormal"),
            ("tag_active_yn", "tag_active_yn"),
            ("tag_void_yn", "tag_void_yn"),
            ("tag_assembly_yn", "tag_assembly_yn"),
            ("tag_taxable_yn", "tag_taxable_yn"),
            ("tag_batch_ctrl_yn", "tag_batch_ctrl_yn"),
            ("tag_serial_ctrl_yn", "tag_serial_ctrl_yn"),
            ("date_lastupdate", "date_lastupdate::text"),
        ],
        "where": "tag_deleted_yn = 'n'",
        "order_by": "date_lastupdate DESC NULLS LAST",
        "date_col": "date_lastupdate",
    },
    # 8. Stock Item Vendor Data
    {
        "sqlite": "stk_code_data",
        "pg": "stk_code_data",
        "columns": [
            ("uniquenum_pri", "uniquenum_pri"),
            ("masterfn", "masterfn"),
            ("companyfn", "companyfn"),
            ("stkcode_code", "stkcode_code"),
            ("party_code", "party_code"),
            ("location_code", "location_code"),
            ("vendor_leadtime_days", "vendor_leadtime_days"),
            ("num_20_4_d_001", "num_20_4_d_001"),
            ("tag_table_usage", "tag_table_usage"),
            ("tag_void_yn", "tag_void_yn"),
        ],
        "where": "tag_deleted_yn = 'n'",
        "order_by": "stkcode_code",
    },
    # 9. Customer/Party Master
    {
        "sqlite": "adm_cnt_main",
        "pg": "adm_cnt_main",
        "columns": [
            ("uniquenum_pri", "uniquenum_pri"),
            ("masterfn", "masterfn"),
            ("companyfn", "companyfn"),
            ("party_code", "party_code"),
            ("party_desc", "party_desc"),
            ("tag_client_vendor", "tag_client_vendor"),
            ("tag_active_yn", "tag_active_yn"),
            ("creditlimit_client", "creditlimit_client"),
            ("addr_main_nation", "addr_main_nation"),
            ("addr_main_state", "addr_main_state"),
        ],
        "where": "tag_deleted_yn = 'n'",
        "order_by": "party_code",
    },
    # 10. Customer Bank Data
    {
        "sqlite": "adm_cnt_data",
        "pg": "adm_cnt_data",
        "columns": [
            ("uniquenum_pri", "uniquenum_pri"),
            ("masterfn", "masterfn"),
            ("companyfn", "companyfn"),
            ("party_code", "party_code"),
            ("party_desc", "party_desc"),
            ("bankactnum", "bankactnum"),
            ("bankname", "bankname"),
            ("tag_table_usage", "tag_table_usage"),
            ("tag_active_yn", "tag_active_yn"),
        ],
        "where": "tag_deleted_yn = 'n'",
        "order_by": "party_code",
    },
    # 11. General Ledger Detail
    {
        "sqlite": "gen_ledger_detail",
        "pg": "gen_ledger_detail",
        "columns": [
            ("uniquenum_pri", "uniquenum_pri"),
            ("masterfn", "masterfn"),
            ("companyfn", "companyfn"),
            ("dnum_auto", "dnum_auto"),
            ("dnum_docnum", "dnum_docnum"),
            ("dnum_reference", "dnum_reference"),
            ("date_trans", "date_trans::text"),
            ("date_due", "date_due::text"),
            ("party_code", "party_code"),
            ("party_desc", "party_desc"),
            ("acctnumdisp", "acctnumdisp"),
            ("amount_forex", "amount_forex"),
            ("amount_local", "amount_local"),
            ("tag_table_usage", "tag_table_usage"),
            ("tag_wflow_app_yn", "tag_wflow_app_yn"),
            ("tag_actbudforma", "tag_actbudforma"),
            ("tag_void_yn", "tag_void_yn"),
            ("bankrec_marker", "bankrec_marker"),
            ("bankrec_date", "bankrec_date::text"),
        ],
        "where": "tag_deleted_yn = 'n'",
        "order_by": "date_trans DESC NULLS LAST",
        "date_col": "date_trans",
    },
    # 12. GL Master (AP/AR)
    {
        "sqlite": "gnl_maint_all",
        "pg": "gnl_maint_all",
        "columns": [
            ("uniquenum_pri", "uniquenum_pri"),
            ("masterfn", "masterfn"),
            ("companyfn", "companyfn"),
            ("dnum_auto", "dnum_auto"),
            ("dnum_reference", "dnum_reference"),
            ("maint_dnum_docnum", "maint_dnum_docnum"),
            ("maint_date_trans", "maint_date_trans::text"),
            ("maint_date_due", "maint_date_due::text"),
            ("maint_amount_local", "maint_amount_local"),
            ("maint_amount_forex", "maint_amount_forex"),
            ("maint_amount_orig", "maint_amount_orig"),
            ("maint_curr_short", "maint_curr_short"),
            ("maint_acctnumdisp", "maint_acctnumdisp"),
            ("maint_cslsegm", "maint_cslsegm"),
            ("party_code", "party_code"),
            ("party_desc", "party_desc"),
            ("date_trans", "date_trans::text"),
            ("tag_table_usage", "tag_table_usage"),
            ("tag_void_yn", "tag_void_yn"),
            ("tag_closed_yn", "tag_closed_yn"),
        ],
        "where": "tag_deleted_yn = 'n'",
        "order_by": "date_trans DESC NULLS LAST",
        "date_col": "date_trans",
    },
    # 13. Stock Ledger
    {
        "sqlite": "stkm_main_all",
        "pg": "stkm_main_all",
        "columns": [
            ("uniquenum_pri", "uniquenum_pri"),
            ("masterfn", "masterfn"),
            ("companyfn", "companyfn"),
            ("stkcode_code", "stkcode_code"),
            ("location_code", "location_code"),
            ("bin_code", "bin_code"),
            ("batchnum_code", "batchnum_code"),
            ("date_expiry", "date_expiry::text"),
            ("balance_qnty_uom_stk_code", "balance_qnty_uom_stk_code"),
            ("value_unitcost_local", "value_unitcost_local"),
            ("tag_void_yn", "tag_void_yn"),
            ("tag_stkm_valid_yn", "tag_stkm_valid_yn"),
        ],
        "where": "tag_deleted_yn = 'n'",
        "order_by": "stkcode_code",
    },
    # 14. Memo Long Table
    {
        "sqlite": "memo_long_table",
        "pg": "memo_long_table",
        "columns": [
            ("uniquenum_pri", "uniquenum_pri"),
            ("masterfn", "masterfn"),
            ("companyfn", "companyfn"),
            ("notes_memo", "notes_memo"),
            ("tag_memo_type", "tag_memo_type"),
        ],
        "where": "tag_deleted_yn = 'n'",
        "order_by": "uniquenum_pri",
    },
    # 15. Project Master (CRM Tickets)
    {
        "sqlite": "prj_pbill_main",
        "pg": "prj_pbill_main",
        "columns": [
            ("uniquenum_pri", "uniquenum_pri"),
            ("masterfn", "masterfn"),
            ("companyfn", "companyfn"),
        ],
        "where": "tag_deleted_yn = 'n'",
        "order_by": "uniquenum_pri",
    },
    # 16. Project Body (CRM Ticket details)
    {
        "sqlite": "prj_pbill_body",
        "pg": "prj_pbill_body",
        "columns": [
            ("uniquenum_pri", "uniquenum_pri"),
            ("masterfn", "masterfn"),
            ("companyfn", "companyfn"),
            ("entprojfn_code", "entprojfn_code"),
            ("notes_memo", "notes_memo"),
            ("tag_closed01_yn", "tag_closed01_yn"),
            ("tag_closed02_yn", "tag_closed02_yn"),
            ("tag_closed03_yn", "tag_closed03_yn"),
            ("tag_closed04_yn", "tag_closed04_yn"),
            ("var_25_001", "var_25_001"),
            ("var_25_002", "var_25_002"),
            ("var_25_003", "var_25_003"),
            ("var_25_004", "var_25_004"),
            ("num_20_4_d_001", "num_20_4_d_001"),
            ("num_20_4_d_002", "num_20_4_d_002"),
            ("num_20_4_d_003", "num_20_4_d_003"),
            ("num_20_4_d_004", "num_20_4_d_004"),
            ("date_001", "date_001::text"),
            ("date_002", "date_002::text"),
            ("date_003", "date_003::text"),
            ("date_004", "date_004::text"),
        ],
        "where": "tag_deleted_yn = 'n'",
        "order_by": "uniquenum_pri",
    },
    # 17. GL Stock Ledger
    {
        "sqlite": "gen_ledger_stk",
        "pg": "gen_ledger_stk",
        "columns": [
            ("uniquenum_pri", "uniquenum_pri"),
            ("masterfn", "masterfn"),
            ("companyfn", "companyfn"),
            ("acctnumdisp", "acctnumdisp"),
            ("party_code", "party_code"),
            ("party_desc", "party_desc"),
            ("date_trans", "date_trans::text"),
            ("date_post", "date_post::text"),
            ("fyearcfn", "fyearcfn"),
            ("periodmth_cfn", "periodmth_cfn"),
            ("staff_code", "staff_code"),
            ("deptunit_code", "deptunit_code"),
            ("location_code", "location_code"),
            ("cslsegm", "cslsegm"),
            ("amount_forex", "amount_forex"),
            ("amount_local", "amount_local"),
            ("tag_void_yn", "tag_void_yn"),
            ("tag_wflow_app_yn", "tag_wflow_app_yn"),
        ],
        "where": "tag_deleted_yn = 'n'",
        "order_by": "date_trans DESC NULLS LAST",
        "date_col": "date_trans",
    },
]


def get_pg_conn():
    """Get PostgreSQL connection."""
    if not HAS_PSYCOPG2:
        raise RuntimeError("psycopg2 not installed. Run: pip install psycopg2-binary")
    conn = psycopg2.connect(
        host=os.getenv("PG_HOST", "localhost"),
        port=int(os.getenv("PG_PORT", "5432")),
        dbname=os.getenv("PG_DBNAME", "v57udemo2011"),
        user=os.getenv("PG_USER", "postgres"),
        password=os.getenv("PG_PASSWORD", "123"),
    )
    conn.autocommit = False
    return conn


def get_sqlite_conn():
    """Get SQLite connection with optimized settings."""
    conn = sqlite3.connect(str(SQLITE_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=OFF")
    conn.execute("PRAGMA cache_size=-64000")  # 64MB cache
    conn.execute("PRAGMA temp_store=MEMORY")
    return conn


def ensure_schema(conn: sqlite3.Connection):
    """Ensure SQLite schema exists."""
    if SCHEMA_PATH.exists():
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        conn.commit()
        logger.info(f"Schema applied from {SCHEMA_PATH}")
    else:
        logger.warning(f"Schema file not found: {SCHEMA_PATH}")


def load_scopes() -> list[dict]:
    """Load scope config from JSON file."""
    if not SCOPES_FILE.exists():
        logger.warning(f"Scopes file not found: {SCOPES_FILE}")
        return []
    data = json.loads(SCOPES_FILE.read_text(encoding="utf-8"))
    return data.get("scopes", [])


def get_last_extract_time(sqlite_conn: sqlite3.Connection, masterfn: str, companyfn: str) -> Optional[str]:
    """
    Get the last successful extract timestamp for a scope from _extract_meta.
    Returns ISO datetime string or None if no previous extract.
    """
    try:
        row = sqlite_conn.execute(
            "SELECT value FROM _extract_meta WHERE key=?",
            (f"last_extract_{masterfn}_{companyfn}",)
        ).fetchone()
        if row:
            meta = json.loads(row["value"])
            return meta.get("timestamp")
    except Exception:
        pass
    return None


def extract_table(
    pg_conn,
    sqlite_conn: sqlite3.Connection,
    mapping: dict,
    masterfn: str,
    companyfn: str,
    batch_size: int = 5000,
    dry_run: bool = False,
    incremental: bool = False,
    last_extract_time: Optional[str] = None,
) -> dict:
    """
    Extract 1 table from PostgreSQL to SQLite for 1 scope.
    If incremental=True and last_extract_time is set, only fetch records
    with date_col >= last_extract_time (dedup by INSERT OR REPLACE).
    """
    sqlite_table = mapping["sqlite"]
    pg_table = mapping["pg"]
    columns = mapping["columns"]
    where_clause = mapping.get("where", "1=1")
    order_by = mapping.get("order_by", "1")
    date_col = mapping.get("date_col")

    # Build column lists
    sqlite_cols = [c[0] for c in columns]
    pg_exprs = [c[1] for c in columns]
    placeholders = ", ".join(["?"] * len(sqlite_cols))
    sqlite_cols_str = ", ".join(sqlite_cols)
    pg_cols_str = ", ".join(pg_exprs)

    # Build PG query with scope filter
    pg_params = [masterfn, companyfn]
    pg_where = f"{where_clause} AND masterfn = %s AND companyfn = %s"

    # Incremental: add date filter
    if incremental and last_extract_time and date_col:
        pg_where += f" AND {date_col} >= %s"
        pg_params.append(last_extract_time)
        logger.info(f"    [INCREMENTAL] {sqlite_table}: filtering {date_col} >= {last_extract_time}")

    pg_sql = f"""
        SELECT {pg_cols_str}
        FROM {pg_table}
        WHERE {pg_where}
        ORDER BY {order_by}
    """

    # Build SQLite INSERT (INSERT OR REPLACE handles dedup by PK)
    sqlite_insert = f"""
        INSERT OR REPLACE INTO {sqlite_table}
            (scope_masterfn, scope_companyfn, {sqlite_cols_str})
        VALUES (?, ?, {placeholders})
    """

    start = time.time()
    total_rows = 0
    error = None

    try:
        pg_cur = pg_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        pg_cur.execute(pg_sql, tuple(pg_params))

        if dry_run:
            for _ in pg_cur:
                total_rows += 1
            logger.info(f"  [DRY-RUN] {sqlite_table}: would insert {total_rows} rows")
        else:
            batch = []
            for row in pg_cur:
                values = [row.get(c) for c in sqlite_cols]
                batch.append((masterfn, companyfn, *values))
                total_rows += 1

                if len(batch) >= batch_size:
                    sqlite_conn.executemany(sqlite_insert, batch)
                    sqlite_conn.commit()
                    logger.debug(f"  {sqlite_table}: inserted {total_rows} rows so far...")
                    batch = []

            if batch:
                sqlite_conn.executemany(sqlite_insert, batch)
                sqlite_conn.commit()

        pg_cur.close()

    except Exception as e:
        error = str(e)
        logger.error(f"  ERROR {sqlite_table}: {error}")
        try:
            pg_conn.rollback()
        except Exception:
            pass

    duration = round(time.time() - start, 2)
    return {
        "table": sqlite_table,
        "rows": total_rows,
        "duration_sec": duration,
        "error": error,
    }


def extract_scope(
    scope: dict,
    batch_size: int = 5000,
    dry_run: bool = False,
    verbose: bool = False,
    incremental: bool = False,
) -> dict:
    """Extract all tables for 1 scope."""
    masterfn = scope["masterfn"]
    companyfn = scope["companyfn"]
    scope_name = scope.get("name", f"{masterfn}/{companyfn}")

    logger.info(f"{'='*60}")
    logger.info(f"Extracting scope: {scope_name} ({masterfn}/{companyfn})")
    logger.info(f"{'='*60}")

    start = time.time()
    pg_conn = None
    sqlite_conn = None
    table_results = []
    global_error = None

    try:
        pg_conn = get_pg_conn()
        sqlite_conn = get_sqlite_conn()
        ensure_schema(sqlite_conn)

        # Get last extract time for incremental mode
        last_extract_time = None
        if incremental:
            last_extract_time = get_last_extract_time(sqlite_conn, masterfn, companyfn)
            if last_extract_time:
                logger.info(f"  [INCREMENTAL] Last extract: {last_extract_time}")
            else:
                logger.info(f"  [INCREMENTAL] No previous extract found, doing full extract")

        for mapping in TABLE_MAPPINGS:
            table_name = mapping["sqlite"]
            logger.info(f"  Processing {table_name}...")

            result = extract_table(
                pg_conn=pg_conn,
                sqlite_conn=sqlite_conn,
                mapping=mapping,
                masterfn=masterfn,
                companyfn=companyfn,
                batch_size=batch_size,
                dry_run=dry_run,
                incremental=incremental,
                last_extract_time=last_extract_time,
            )
            table_results.append(result)

            if result["error"]:
                logger.warning(f"  WARNING {table_name}: {result['error']}")
            else:
                logger.info(f"  OK {table_name}: {result['rows']} rows in {result['duration_sec']}s")

    except Exception as e:
        global_error = str(e)
        logger.error(f"Scope {scope_name} failed: {global_error}")

    finally:
        if pg_conn:
            pg_conn.close()
        if sqlite_conn:
            sqlite_conn.close()

    total_duration = round(time.time() - start, 2)
    total_rows = sum(r["rows"] for r in table_results)

    logger.info(f"{'='*60}")
    if global_error:
        logger.error(f"Scope {scope_name}: FAILED after {total_duration}s ({total_rows} rows)")
    else:
        logger.info(f"Scope {scope_name}: {total_rows} rows in {total_duration}s")
    logger.info(f"{'='*60}")

    return {
        "scope": scope_name,
        "masterfn": masterfn,
        "companyfn": companyfn,
        "tables": table_results,
        "total_rows": total_rows,
        "total_duration": total_duration,
        "error": global_error,
    }


def main():
    parser = argparse.ArgumentParser(description="ERP Extract - Multi-Scope PostgreSQL to SQLite")
    parser.add_argument("--masterfn", help="Extract only this masterfn")
    parser.add_argument("--companyfn", help="Extract only this companyfn (requires --masterfn)")
    parser.add_argument("--dry-run", action="store_true", help="Count rows without inserting")
    parser.add_argument("--incremental", action="store_true", help="Only fetch data since last extract")
    parser.add_argument("--full", action="store_true", help="Full re-extract (ignore last extract time)")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    parser.add_argument("--batch-size", type=int, default=5000, help="Rows per batch (default: 5000)")
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Validate args
    if args.companyfn and not args.masterfn:
        logger.error("--companyfn requires --masterfn")
        sys.exit(1)

    # Load scopes
    scopes = load_scopes()
    if not scopes:
        logger.error("No scopes configured. Edit data/erp_extract_scopes.json")
        sys.exit(1)

    # Filter by masterfn if specified
    if args.masterfn:
        scopes = [s for s in scopes if s["masterfn"] == args.masterfn]
        if args.companyfn:
            scopes = [s for s in scopes if s["companyfn"] == args.companyfn]
        if not scopes:
            logger.error(f"No scope found for masterfn={args.masterfn}, companyfn={args.companyfn}")
            sys.exit(1)

    # Filter enabled scopes
    enabled_scopes = [s for s in scopes if s.get("enabled", True)]
    if not enabled_scopes:
        logger.warning("All scopes are disabled")
        sys.exit(0)

    # Determine mode
    is_incremental = args.incremental and not args.full
    mode = "INCREMENTAL" if is_incremental else ("DRY-RUN" if args.dry_run else "FULL")

    logger.info(f"Starting ERP Extract for {len(enabled_scopes)} scope(s)")
    logger.info(f"Mode: {mode}")
    logger.info(f"Batch size: {args.batch_size}")

    overall_start = time.time()
    all_results = []

    for scope in enabled_scopes:
        result = extract_scope(
            scope=scope,
            batch_size=args.batch_size,
            dry_run=args.dry_run,
            verbose=args.verbose,
            incremental=is_incremental,
        )
        all_results.append(result)

    # Summary
    overall_duration = round(time.time() - overall_start, 2)
    grand_total_rows = sum(r["total_rows"] for r in all_results)
    failed_scopes = [r for r in all_results if r["error"]]

    print(f"\n{'='*60}")
    print(f"EXTRACT SUMMARY")
    print(f"{'='*60}")
    print(f"  Scopes processed: {len(all_results)}")
    print(f"  Total rows:       {grand_total_rows:,}")
    print(f"  Total duration:   {overall_duration}s")
    print(f"  Failed scopes:    {len(failed_scopes)}")
    if failed_scopes:
        for fs in failed_scopes:
            print(f"    FAILED {fs['scope']}: {fs['error']}")
    print(f"{'='*60}")

    # Save summary to meta table if not dry-run
    if not args.dry_run:
        try:
            conn = get_sqlite_conn()
            ensure_schema(conn)
            for r in all_results:
                conn.execute(
                    "INSERT OR REPLACE INTO _extract_meta (key, value) VALUES (?, ?)",
                    (f"last_extract_{r['masterfn']}_{r['companyfn']}",
                     json.dumps({
                         "timestamp": datetime.now(timezone.utc).isoformat(),
                         "total_rows": r["total_rows"],
                         "duration_sec": r["total_duration"],
                         "error": r["error"],
                     }))
                )
            conn.execute(
                "INSERT OR REPLACE INTO _extract_meta (key, value) VALUES (?, ?)",
                ("last_extract_all", json.dumps({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "scopes": len(all_results),
                    "total_rows": grand_total_rows,
                    "duration_sec": overall_duration,
                    "failed_scopes": len(failed_scopes),
                }))
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Could not save extract summary: {e}")

    if failed_scopes:
        sys.exit(1)


if __name__ == "__main__":
    main()
