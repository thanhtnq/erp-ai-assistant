# ERP Extract Implementation Tasks & Deployment Options

> **Mục tiêu:** Implement ERP data extraction từ PostgreSQL → SQLite, tích hợp vào scheduler hiện có, quản lý multi-company, và deploy với nhiều phương án.

---

## 1. Tổng Quan Multi-Company

### Vấn đề
- ERP có **nhiều công ty**, mỗi công ty có thể có **công ty con**
- Mỗi company scope = 1 cặp `(masterfn, companyfn)`
- Extract cần chạy riêng cho từng scope
- Admin cần quản lý: scope nào đã extract, schedule riêng, log chi tiết

### Giải pháp
- **Multi-Scope Extract:** Mỗi scope extract riêng, lưu vào SQLite với scope tag
- **Admin CFM:** File CFM trong contentadmin để quản lý extract
- **Schedule riêng:** Mỗi scope có thể có schedule khác nhau
- **Audit Log:** Ghi log vào `sys_sec_audit` (theo pattern contentadmin hiện tại)

---

## 2. Task Implementation (Chi Tiết Từng Bước)

### Phase 1: Core Extract Engine (Day 1-2)

#### Task 1.1: Tạo SQL schema
- **File:** `scripts/create_erp_extract_tables.sql`
- **Nội dung:** 17 CREATE TABLE statements + indexes (đã có trong `docs/erp-db-extraction-plan.md`)
- **Thêm:** Mỗi table có thêm column `scope_masterfn` và `scope_companyfn` để phân biệt data của từng company

#### Task 1.2: Tạo multi-scope extract script
- **File:** `scripts/extract_erp_to_sqlite.py`
- **Nội dung:**
  ```python
  # Đọc danh sách scopes từ config
  SCOPES = [
      {"masterfn": "demo2011mfn", "companyfn": "p11011004464072155", "name": "Công ty A"},
      {"masterfn": "demo2011mfn", "companyfn": "p11011004464072156", "name": "Công ty B (con)"},
      {"masterfn": "lumchangmfn", "companyfn": "p11011004464072157", "name": "Công ty C"},
  ]
  
  # Với mỗi scope:
  for scope in SCOPES:
      # 1. Kết nối PostgreSQL với scope filter
      # 2. Extract data cho scope đó
      # 3. Ghi vào SQLite với scope_masterfn + scope_companyfn
      # 4. Log progress
  ```
- **Kiểm tra:** `python scripts/extract_erp_to_sqlite.py`

#### Task 1.3: Tạo scope config
- **File:** `data/erp_extract_scopes.json`
```json
{
  "scopes": [
    {
      "masterfn": "demo2011mfn",
      "companyfn": "p11011004464072155",
      "name": "Công ty A",
      "enabled": true,
      "schedule": {
        "interval": "weekly",
        "day": "sunday",
        "time": "00:00"
      }
    },
    {
      "masterfn": "demo2011mfn",
      "companyfn": "p11011004464072156",
      "name": "Công ty B (Công ty con của A)",
      "enabled": true,
      "schedule": {
        "interval": "weekly",
        "day": "sunday",
        "time": "01:00"
      }
    }
  ],
  "global_config": {
    "enabled": true,
    "sqlite_path": "data/erp_extract.db",
    "max_retries": 3,
    "timeout_minutes": 60,
    "notify_on_failure": true
  }
}
```

#### Task 1.4: Tạo incremental extract
- **File:** `scripts/extract_erp_incremental.py`
- **Nội dung:** Chỉ extract data mới từ lần chạy cuối (dùng `date_lastupdate`)
- **Lưu state:** File `data/extract_state.json` lưu `last_run_at` cho mỗi scope + table

### Phase 2: API Query Layer (Day 2-3)

#### Task 2.1: Tạo ERP query router
- **File:** `api/routers/erp_query.py`
- **Endpoints:**
  - `POST /erp/query` — Execute SELECT query (có scope filter)
  - `GET /erp/tables` — List available tables + row counts
  - `GET /erp/schema/{table}` — Get table schema (columns + types)
  - `GET /erp/status` — Extract status (last run, row counts, age)
  - `GET /erp/scopes` — List all scopes + their extract status

#### Task 2.2: Implement query safety
- **Safety checks:**
  - ✅ Only SELECT statements allowed
  - ✅ Table whitelist (chỉ 17 tables cho phép)
  - ✅ Scope injection (masterfn + companyfn bắt buộc từ cookie)
  - ✅ LIMIT enforced (max 100 rows)
  - ❌ Block: DROP, DELETE, INSERT, UPDATE, ALTER, CREATE, DETACH, ATTACH

#### Task 2.3: Đăng ký router trong main.py
- **File:** `api/main.py`
- Thêm: `app.include_router(erp_query_router)`

### Phase 3: Admin API + Scheduler (Day 3-4)

#### Task 3.1: Thêm ERP extract endpoints vào admin scheduler
- **File:** `api/routers/admin_scheduler.py`
- **Thêm endpoints:**
  - `GET /admin/scheduler/erp-extract/status` — Status tổng quan
  - `POST /admin/scheduler/erp-extract/run` — Run extract cho 1 scope hoặc all
  - `PUT /admin/scheduler/erp-extract/config` — Update global config
  - `GET /admin/scheduler/erp-extract/scopes` — List scopes + status
  - `PUT /admin/scheduler/erp-extract/scopes/{scope_id}` — Update scope config
  - `POST /admin/scheduler/erp-extract/scopes/{scope_id}/run` — Run extract cho 1 scope
  - `GET /admin/scheduler/erp-extract/logs` — Xem extract logs

#### Task 3.2: Thêm job vào scheduler
- **File:** `schedule/scheduler.py`
- Thêm job `erp_extract` — chạy theo lịch của từng scope
- Mỗi scope có thể có schedule riêng (VD: Công ty A chạy Chủ nhật, Công ty B chạy Thứ 7)

#### Task 3.3: Update state file
- **File:** `data/scheduler_state.json` — thêm section `erp_extract` với sub-state cho từng scope

### Phase 4: CFM Admin UI (Day 4-5)

#### Task 4.1: Tạo file CFM quản lý extract
- **File:** `cfml-examples/ai_erp_extract_admin.cfm` **[NEW]**
- **Pattern:** Theo `inc_ajax_ai_admin.cfm` — proxy pattern
- **Chức năng:**
  1. **Dashboard:** Tổng quan extract status cho tất cả scopes
  2. **Scope Management:** Thêm/sửa/xóa scope extract
  3. **Schedule Config:** Cấu hình lịch extract cho từng scope
  4. **Run Now:** Nút chạy extract ngay cho 1 scope hoặc all
  5. **Log Viewer:** Xem log extract gần nhất
  6. **Data Age:** Hiển thị data age cho từng scope

#### Task 4.2: Cấu trúc CFM file
```cfm
<cfparam name="action" default="">
<cfparam name="cookie.cookuserloginid" default="">
<cfparam name="cookie.cookmfnunique"   default="">
<cfparam name="cookie.cookcfnunique"   default="">

<cfinclude template="inc_syspathname.cfm">
<cfinclude template="sym_meta_lang_a.cfm">
<cfinclude template="inc_qs_set_co_main.cfm">

<cfscript>
    host_api_url = "http://localhost:8000";
    ai_api_key = "YJfgXD-P5WF9p3VCT1XN_ehsnB2KK_OfIYedBxz_J8M";
</cfscript>
<cftry>
    <cfinclude template="inc_ai_host_config.cfm">
    <cfcatch></cfcatch>
</cftry>

<cfswitch expression="#Trim(action)#">
    <cfcase value="get_dashboard">
        <!--- Gọi API /erp/status + /admin/scheduler/erp-extract/status --->
    </cfcase>
    <cfcase value="get_scopes">
        <!--- Gọi API /admin/scheduler/erp-extract/scopes --->
    </cfcase>
    <cfcase value="run_extract">
        <!--- Gọi API /admin/scheduler/erp-extract/run --->
    </cfcase>
    <cfcase value="update_scope">
        <!--- Gọi API /admin/scheduler/erp-extract/scopes/{id} --->
    </cfcase>
    <cfcase value="get_logs">
        <!--- Gọi API /admin/scheduler/erp-extract/logs --->
    </cfcase>
</cfswitch>
```

#### Task 4.3: Tạo HTML dashboard cho CFM
- **File:** `cfml-examples/ai_erp_extract_admin.cfm` (phần HTML)
- **Giao diện:**
  ```
  ┌─────────────────────────────────────────────┐
  │  ERP Extract Admin                          │
  ├─────────────────────────────────────────────┤
  │  [Global Config] [Scopes] [Logs] [Run Now]  │
  ├─────────────────────────────────────────────┤
  │  Scope Summary:                             │
  │  ┌──────────┬────────┬────────┬──────────┐ │
  │  │ Scope    │ Status │ Age    │ Last Run │ │
  │  ├──────────┼────────┼────────┼──────────┤ │
  │  │ Cty A    │ ✅ OK  │ 2 days │ 15/07/26 │ │
  │  │ Cty B    │ ⚠️ Old │ 8 days │ 09/07/26 │ │
  │  │ Cty C    │ ❌ Err │ -      │ -        │ │
  │  └──────────┴────────┴────────┴──────────┘ │
  │                                             │
  │  [Run Extract for Selected]                 │
  └─────────────────────────────────────────────┘
  ```

#### Task 4.4: Đồng bộ CFM với contentadmin
- **File:** `scripts/sync_cfml_examples.ps1` — thêm `ai_erp_extract_admin.cfm` vào danh sách sync
- **Kiểm tra:** Chạy sync và verify file đã có trong contentadmin

### Phase 5: Audit Logging (Day 5)

#### Task 5.1: Ghi audit log khi extract
- **Pattern:** Theo `inc_oup_ins_sys_sec_audit_logging.cfm` trong contentadmin
- **File:** `api/routers/erp_query.py` — thêm function `log_extract_audit()`
- **Ghi vào `sys_sec_audit`:**
  ```sql
  INSERT INTO sys_sec_audit (
      masterfn, companyfn, tag_table_usage, cslsegm, cslmodule,
      userid_cookie, date_lastupdate, remote_addr,
      var_50_001, var_50_002, var_50_003
  ) VALUES (
      'demo2011mfn', 'p11011004464072155', 'enaudit',
      'erp_extract', 'ai_assistant',
      'admin', NOW(), '127.0.0.1',
      'extract_started', 'scm_sal_main', '100 rows'
  );
  ```
- **Các action types:**
  - `extract_started` — Bắt đầu extract
  - `extract_completed` — Extract thành công
  - `extract_failed` — Extract thất bại
  - `extract_skipped` — Bỏ qua (đang chạy)
  - `scope_added` — Thêm scope mới
  - `scope_removed` — Xóa scope
  - `scope_updated` — Cập nhật scope config

#### Task 5.2: Lưu log vào file
- **File:** `logs/erp_extract.log`
- **Format:** `[2026-07-17 00:00:00] [INFO] [demo2011mfn/p11011004464072155] Extract started: scm_sal_main`
- **Rotation:** Log rotate hàng tuần (giữ 4 tuần)

### Phase 6: Integration với Skills (Day 6)

#### Task 6.1: Update orm-fetch.js
- **File:** `skills/_shared/orm-fetch.js`
- Thêm logic: nếu `USE_SQLITE_EXTRACT=true` thì query SQLite thay vì PostgreSQL
- Scope filter tự động thêm `scope_masterfn` và `scope_companyfn`

#### Task 6.2: Thêm config flag
- **File:** `.env`
```env
# Nếu true, skills server sẽ query SQLite extract thay vì PostgreSQL
USE_SQLITE_EXTRACT=false
# Đường dẫn đến SQLite extract file
SQLITE_EXTRACT_PATH=data/erp_extract.db
```

### Phase 7: Monitoring (Day 7)

#### Task 7.1: Health check
- **File:** `api/routers/erp_query.py` — thêm endpoint
- `GET /erp/health` — kiểm tra:
  - SQLite file tồn tại
  - Data không quá cũ (configurable threshold)
  - Row counts hợp lý
  - Từng scope có data không

#### Task 7.2: Alert khi extract fail
- **File:** `schedule/scheduler.py`
- Log error + ghi vào `sys_sec_audit` nếu extract fail 2 lần liên tiếp
- Gửi notification qua webhook (nếu config)

#### Task 7.3: Data age warning
- Khi query, nếu data age > threshold (VD: > 7 ngày), trả về warning:
```json
{
  "warning": "Data for scope demo2011mfn/p11011004464072155 is 8 days old. Last extract: 2026-07-09T00:00:00",
  "data": [...]
}
```

---

## 3. File Structure Changes

```
erp-ai-assistant/
├── scripts/
│   ├── create_erp_extract_tables.sql        # [NEW] SQL schema
│   ├── extract_erp_to_sqlite.py             # [NEW] Multi-scope extract
│   ├── extract_erp_incremental.py           # [NEW] Incremental extract
│   └── ...
├── api/
│   ├── routers/
│   │   ├── erp_query.py                     # [NEW] ERP query endpoints
│   │   └── admin_scheduler.py               # [MODIFIED] Add erp-extract endpoints
│   └── main.py                              # [MODIFIED] Add router
├── schedule/
│   ├── scheduler.py                         # [MODIFIED] Add erp_extract job
│   └── run_erp_extract.py                   # [NEW] Extract runner
├── data/
│   ├── erp_extract.db                       # [NEW] SQLite extract DB
│   ├── erp_extract_scopes.json              # [NEW] Scope config
│   ├── extract_state.json                   # [NEW] Incremental state
│   └── scheduler_state.json                 # [MODIFIED] Add erp_extract state
├── logs/
│   └── erp_extract.log                      # [NEW] Extract log
├── cfml-examples/
│   ├── ai_erp_extract_admin.cfm             # [NEW] Admin CFM
│   └── ...
├── skills/
│   └── _shared/
│       └── orm-fetch.js                     # [MODIFIED] SQLite fallback
└── .env                                     # [MODIFIED] New config vars
```

---

## 4. CFM Admin UI Design

### 4.1 File: `cfml-examples/ai_erp_extract_admin.cfm`

**Pattern:** Giống `inc_ajax_ai_admin.cfm` — proxy pattern, gọi API Python qua HTTP

**Actions:**
| Action | Method | API Endpoint | Description |
|--------|--------|-------------|-------------|
| `get_dashboard` | GET | `/erp/status` + `/admin/scheduler/erp-extract/status` | Tổng quan |
| `get_scopes` | GET | `/admin/scheduler/erp-extract/scopes` | Danh sách scope |
| `add_scope` | POST | `/admin/scheduler/erp-extract/scopes` | Thêm scope mới |
| `update_scope` | PUT | `/admin/scheduler/erp-extract/scopes/{id}` | Sửa scope |
| `delete_scope` | DELETE | `/admin/scheduler/erp-extract/scopes/{id}` | Xóa scope |
| `run_extract` | POST | `/admin/scheduler/erp-extract/run` | Chạy extract |
| `run_scope_extract` | POST | `/admin/scheduler/erp-extract/scopes/{id}/run` | Chạy extract 1 scope |
| `get_logs` | GET | `/admin/scheduler/erp-extract/logs` | Xem log |
| `update_config` | PUT | `/admin/scheduler/erp-extract/config` | Cập nhật global config |

### 4.2 Giao diện đề xuất

```
┌──────────────────────────────────────────────────────────────┐
│  🔄 ERP Extract Manager                    [Run All] [Refresh] │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  📊 Global Status                                            │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Total Scopes: 3   │ Active: 3   │ Failed: 0   │ OK: 2 │ │
│  │ Last Global Run: 2026-07-17 00:00:00 (2 days ago)      │ │
│  │ Next Scheduled: 2026-07-24 00:00:00 (Chủ nhật)         │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  📋 Scope List                                               │
│  ┌─────┬──────────────┬──────────┬────────┬──────────┬─────┐ │
│  │ #   │ Scope Name   │ Status   │ Age    │ Schedule │ Run │ │
│  ├─────┼──────────────┼──────────┼────────┼──────────┼─────┤ │
│  │ 1   │ Công ty A    │ ✅ OK    │ 2 days │ CN 00:00 │ ▶  │ │
│  │ 2   │ Công ty B    │ ⚠️ Old   │ 8 days │ CN 01:00 │ ▶  │ │
│  │ 3   │ Công ty C    │ ❌ Error │ -      │ T7 02:00 │ ▶  │ │
│  └─────┴──────────────┴──────────┴────────┴──────────┴─────┘ │
│                                                              │
│  📝 Recent Logs (last 5)                                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ [17/07 00:00] ✅ Công ty A — Completed (12s, 1,234 rows)│ │
│  │ [17/07 01:00] ✅ Công ty B — Completed (8s, 567 rows)   │ │
│  │ [16/07 00:00] ❌ Công ty C — Failed: Connection timeout  │ │
│  │ [16/07 00:05] 🔄 Công ty C — Retry 1/3...              │ │
│  │ [16/07 00:06] ❌ Công ty C — Failed: Connection timeout  │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ⚙️ Add New Scope                                            │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Masterfn: [______________]  Companyfn: [______________] │ │
│  │ Name:    [______________]  Schedule: [Weekly ▼] [__]:[__]│ │
│  │                                      [Add Scope]        │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

---

## 5. Weekly Training Schedule

### Hiện tại scheduler đã có:
| Job | Interval | Time | Description |
|-----|----------|------|-------------|
| `documents` | Daily | 02:00 | Ingest documents |
| `tickets` | Daily | 03:00 | Ingest tickets |
| `fraud` | Daily | 01:00 | Fraud detection |

### Thêm ERP Extract schedule:

**Global schedule** (mặc định cho tất cả scopes):
```python
"erp_extract": {
    "enabled":  True,
    "interval": "weekly",
    "time":     "00:00",
    "day":      "sunday",
    "last_run_at": None,
    "last_run_status": None,
    "last_run_duration_sec": None,
    "is_running": False,
}
```

**Per-scope schedule** (ghi đè global):
```json
{
  "scopes": [
    {
      "masterfn": "demo2011mfn",
      "companyfn": "p11011004464072155",
      "schedule": {
        "interval": "weekly",
        "day": "sunday",
        "time": "00:00"
      }
    },
    {
      "masterfn": "lumchangmfn",
      "companyfn": "p11011004464072157",
      "schedule": {
        "interval": "daily",
        "time": "04:00"
      }
    }
  ]
}
```

### Script chạy weekly:
```python
# schedule/run_erp_extract.py
"""
Run ERP extract — gọi từ scheduler.
Hỗ trợ multi-scope, mỗi scope chạy theo lịch riêng.
"""
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

SCOPES_FILE = Path(__file__).parent.parent / "data" / "erp_extract_scopes.json"
EXTRACT_SCRIPT = Path(__file__).parent.parent / "scripts" / "extract_erp_to_sqlite.py"

def run_erp_extract(scope_filter=None):
    """Run extract for all scopes or a specific scope."""
    scopes_config = json.loads(SCOPES_FILE.read_text())
    scopes = scopes_config.get("scopes", [])
    
    if scope_filter:
        scopes = [s for s in scopes if s["masterfn"] == scope_filter]
    
    results = []
    for scope in scopes:
        if not scope.get("enabled", True):
            continue
        
        start = datetime.now()
        try:
            result = subprocess.run(
                [sys.executable, str(EXTRACT_SCRIPT),
                 "--masterfn", scope["masterfn"],
                 "--companyfn", scope["companyfn"]],
                capture_output=True, text=True, timeout=7200
            )
            elapsed = (datetime.now() - start).seconds
            status = "success" if result.returncode == 0 else "failed"
            results.append({
                "scope": scope["name"],
                "masterfn": scope["masterfn"],
                "companyfn": scope["companyfn"],
                "status": status,
                "duration_sec": elapsed,
                "error": result.stderr if result.returncode != 0 else None
            })
        except Exception as e:
            results.append({
                "scope": scope["name"],
                "masterfn": scope["masterfn"],
                "companyfn": scope["companyfn"],
                "status": "failed",
                "error": str(e)
            })
    
    return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--masterfn", help="Run for specific masterfn only")
    args = parser.parse_args()
    
    results = run_erp_extract(args.masterfn)
    for r in results:
        print(f"[{r['status'].upper()}] {r['scope']}: {r.get('duration_sec', '?')}s")
        if r.get('error'):
            print(f"  Error: {r['error']}")
```

---

## 6. Audit Log Pattern (theo contentadmin)

### Pattern hiện tại trong contentadmin:
```sql
-- inc_oup_ins_sys_sec_audit_logging.cfm
INSERT INTO sys_sec_audit (
    masterfn, companyfn, uniquenum_pri, uniquenum_sec,
    tag_table_usage, cslsegm, cslmodule, csltemplate,
    userid_cookie, date_lastupdate, remote_addr,
    var_50_001, var_50_002, var_50_003, var_50_004, var_50_005,
    var_50_006, var_50_007, var_50_008,
    party_code, party_desc
) VALUES (
    <cfqueryparam value="#masterfn#" cfsqltype="cf_sql_varchar">,
    <cfqueryparam value="#companyfn#" cfsqltype="cf_sql_varchar">,
    <cfqueryparam value="#uniquenum_pri#" cfsqltype="cf_sql_varchar">,
    <cfqueryparam value="#uniquenum_sec#" cfsqltype="cf_sql_varchar">,
    'enaudit',  -- tag_table_usage
    'erp_extract',  -- cslsegm
    'ai_assistant',  -- cslmodule
    '',  -- csltemplate
    <cfqueryparam value="#userid_cookie#" cfsqltype="cf_sql_varchar">,
    NOW(), <cfqueryparam value="#remote_addr#" cfsqltype="cf_sql_varchar">,
    <cfqueryparam value="#var_50_001#" cfsqltype="cf_sql_varchar">,  -- action: extract_started/completed/failed
    <cfqueryparam value="#var_50_002#" cfsqltype="cf_sql_varchar">,  -- table name
    <cfqueryparam value="#var_50_003#" cfsqltype="cf_sql_varchar">,  -- row count / error message
    '', '', '', '', '',
    '', ''
);
```

### Mapping action → var_50:
| Action | var_50_001 | var_50_002 | var_50_003 |
|--------|-----------|-----------|-----------|
| Extract started | `extract_started` | `scm_sal_main` | `scope: demo2011mfn` |
| Extract completed | `extract_completed` | `scm_sal_main` | `100 rows in 5s` |
| Extract failed | `extract_failed` | `scm_sal_main` | `Connection timeout` |
| Scope added | `scope_added` | `demo2011mfn` | `Công ty A` |
| Scope removed | `scope_removed` | `demo2011mfn` | `p11011004464072155` |

---

## 7. Deployment Options

### Option A: Simple — SQLite trên cùng server (Khuyến nghị cho MVP)

```
┌─────────────────────────────────────┐
│         Application Server          │
│  ┌──────────┐  ┌──────────────────┐ │
│  │ FastAPI   │  │ Skills Server    │ │
│  │ (api.py)  │  │ (server.js)      │ │
│  └────┬─────┘  └────────┬─────────┘ │
│       │                 │           │
│  ┌────▼─────────────────▼─────────┐ │
│  │     SQLite (erp_extract.db)     │ │
│  │     + Chat DB + Knowledge DB    │ │
│  └────────────────────────────────┘ │
│       │                             │
│  ┌────▼──────────────────────────┐  │
│  │  PostgreSQL (Globe3 ERP)      │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

**Ưu điểm:** Đơn giản, không infra mới, latency thấp
**Nhược điểm:** Extract chạy cùng server, không scale

### Option B: Medium — Separate Extract Service

```
┌─────────────────────┐   ┌──────────────────────┐
│   Main App Server   │   │   Extract Service     │
│  ┌───────────────┐  │   │  ┌────────────────┐   │
│  │ FastAPI       │  │   │  │ extract_erp_   │   │
│  │ + Skills      │  │   │  │ to_sqlite.py   │   │
│  └───────┬───────┘  │   │  └───────┬────────┘   │
│          │          │   │          │             │
│  ┌───────▼───────┐  │   │  ┌───────▼────────┐   │
│  │ SQLite (read) │  │   │  │ SQLite (write)  │   │
│  └───────────────┘  │   │  └────────────────┘   │
└─────────────────────┘   └──────────────────────┘
         │                         │
         └─────────┬───────────────┘
                   │ (copy file via SCP/NFS/S3)
                   ▼
         ┌─────────────────┐
         │  PostgreSQL      │
         │  (Globe3 ERP)    │
         └─────────────────┘
```

### Option C: Advanced — PostgreSQL Read Replica

```
┌─────────────────────┐
│   Application       │
│  ┌───────────────┐  │
│  │ FastAPI       │  │
│  │ + Skills      │  │
│  └───┬───────┬───┘  │
│      │       │      │
│  ┌───▼───┐ ┌─▼────┐│
│  │SQLite │ │Redis  ││
│  │Cache  │ │Cache  ││
│  └───────┘ └──────┘│
└──────┬──────────────┘
       │
┌──────▼──────────────────┐
│  PostgreSQL Read Replica │ ← READ ONLY
└─────────────────────────┘
```

---

## 8. So Sánh & Khuyến Nghị

| Tiêu chí | Option A | Option B | Option C |
|----------|:--------:|:--------:|:--------:|
| **Độ phức tạp** | ⭐ Thấp | ⭐⭐ TB | ⭐⭐⭐⭐ Cao |
| **Chi phí infra** | $0 | $ | $$$ |
| **Data freshness** | Theo schedule | Theo schedule | Real-time |
| **Impact lên ERP** | Nhẹ | Nhẹ | Không |
| **Maintenance** | Thấp | TB | Cao |
| **Multi-company** | ✅ Tốt | ✅ Tốt | ✅ Tốt nhất |
| **Time to implement** | 3-4 ngày | 5-7 ngày | 1-2 tuần |

### Khuyến nghị:

**Giai đoạn 1 (MVP - 4 ngày):** Option A
- Implement multi-scope extract
- CFM admin UI cơ bản
- Schedule hàng tuần
- Audit log vào sys_sec_audit

**Giai đoạn 2 (1 tháng sau):** Option B
- Tách extract service riêng
- Incremental extract
- Alert + notification

**Giai đoạn 3 (3 tháng sau):** Option C (nếu cần real-time)

---

## 9. Implementation Order

### Week 1: Core Engine + API
1. ✅ Task 1.1 → SQL schema (17 tables + scope columns)
2. ✅ Task 1.2 → Multi-scope extract script
3. ✅ Task 1.3 → Scope config file
4. ✅ Task 2.1 → ERP query router
5. ✅ Task 2.2 → Query safety
6. ✅ Task 2.3 → Register router

### Week 2: Admin + Scheduler + CFM
7. ✅ Task 3.1 → Admin scheduler endpoints
8. ✅ Task 3.2 → Scheduler job
9. ✅ Task 4.1 → CFM admin file
10. ✅ Task 4.2 → CFM actions
11. ✅ Task 4.3 → HTML dashboard
12. ✅ Task 4.4 → Sync script

### Week 3: Audit + Integration + Monitoring
13. ✅ Task 5.1 → Audit log
14. ✅ Task 5.2 → File log
15. ✅ Task 6.1 → orm-fetch.js update
16. ✅ Task 7.1 → Health check
17. ✅ Task 7.2 → Alert
18. ✅ Task 7.3 → Data age warning

---

## 10. Rollback Plan

| Component | Rollback |
|-----------|----------|
| **API Router** | Comment `app.include_router(erp_query_router)` |
| **Scheduler** | Set `ERP_EXTRACT_ENABLED=false` |
| **Skills** | Set `USE_SQLITE_EXTRACT=false` |
| **CFM** | Xóa `ai_erp_extract_admin.cfm` khỏi contentadmin |
| **Data** | Xóa `data/erp_extract.db` |

---

## 11. Success Metrics

| Metric | Target | How to measure |
|--------|--------|----------------|
| Extract time per scope | < 15 phút | Log duration |
| Data age | < 7 ngày | Check `last_run_at` |
| Query latency | < 100ms | API response time |
| Query success rate | > 99% | Error count / total |
| Data accuracy | 100% | Compare PG vs SQLite |
| Audit log coverage | 100% | Check sys_sec_audit entries |
| CFM admin uptime | > 99.9% | Health check |
