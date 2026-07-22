import json
from pathlib import Path
from typing import Any

from api.database import get_knowledge_conn
from api.utils import now_iso


VALID_MODULES = {
    "sales", "purchase", "inventory", "finance", "hr", "project",
    "analytics", "crm", "general",
}
VALID_SCOPE_TYPES = {"global", "company"}


def init_semantic_db(conn=None) -> None:
    own_conn = conn is None
    conn = conn or get_knowledge_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS semantic_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL UNIQUE,
            filename TEXT NOT NULL,
            scope_type TEXT NOT NULL,
            company_code TEXT NOT NULL DEFAULT '',
            masterfn TEXT NOT NULL DEFAULT '',
            companyfn TEXT NOT NULL DEFAULT '',
            module TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            error_message TEXT,
            reports_parsed INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            ingested_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS semantic_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            report_id TEXT NOT NULL,
            module TEXT NOT NULL,
            scope_type TEXT NOT NULL,
            company_code TEXT NOT NULL DEFAULT '',
            masterfn TEXT NOT NULL DEFAULT '',
            companyfn TEXT NOT NULL DEFAULT '',
            report_name TEXT NOT NULL,
            intent_type TEXT NOT NULL,
            description TEXT,
            business_keywords TEXT,
            tool_name TEXT NOT NULL,
            default_filters_json TEXT NOT NULL DEFAULT '{}',
            required_filters_json TEXT NOT NULL DEFAULT '[]',
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            UNIQUE(scope_type, company_code, module, report_id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS semantic_output_columns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            report_id TEXT NOT NULL,
            module TEXT NOT NULL,
            query_column TEXT NOT NULL,
            output_name TEXT NOT NULL,
            data_type TEXT,
            display_order INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS semantic_filters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            report_id TEXT NOT NULL,
            module TEXT NOT NULL,
            filter_column TEXT NOT NULL,
            ui_name TEXT,
            data_type TEXT,
            operator TEXT,
            required INTEGER NOT NULL DEFAULT 0,
            default_value TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS semantic_relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            module TEXT NOT NULL,
            parent_table TEXT NOT NULL,
            child_table TEXT NOT NULL,
            join_condition TEXT NOT NULL,
            join_type TEXT,
            business_meaning TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS semantic_synonyms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            module TEXT NOT NULL,
            business_term TEXT NOT NULL,
            technical_term TEXT NOT NULL,
            notes TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS semantic_sample_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            report_id TEXT NOT NULL,
            module TEXT NOT NULL,
            user_question TEXT NOT NULL,
            searchable_text TEXT NOT NULL DEFAULT '',
            embedding_indexed INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS semantic_business_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            report_id TEXT NOT NULL DEFAULT '',
            module TEXT NOT NULL,
            rule_name TEXT NOT NULL,
            rule_expression TEXT NOT NULL,
            description TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS semantic_field_mappings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            module TEXT NOT NULL,
            table_name TEXT NOT NULL,
            field_name TEXT NOT NULL,
            field_role TEXT,
            business_label TEXT NOT NULL,
            data_type TEXT,
            synonyms TEXT,
            description TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS semantic_mandatory_fields (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            module TEXT NOT NULL,
            table_name TEXT NOT NULL,
            field_name TEXT NOT NULL,
            rule TEXT NOT NULL,
            default_value TEXT,
            applies_to TEXT,
            description TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS semantic_child_tabs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            module TEXT NOT NULL,
            parent_document TEXT NOT NULL,
            child_tab TEXT NOT NULL,
            child_table TEXT NOT NULL,
            join_condition TEXT,
            business_meaning TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS semantic_sales_cycle (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            module TEXT NOT NULL,
            sequence INTEGER NOT NULL,
            document_name TEXT NOT NULL,
            tag_table_usage TEXT NOT NULL,
            source_table TEXT,
            next_document TEXT,
            business_state TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS semantic_sql_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            report_id TEXT NOT NULL,
            module TEXT NOT NULL,
            sql_template TEXT NOT NULL,
            parameters TEXT,
            notes TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS semantic_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            module TEXT NOT NULL,
            rule_name TEXT NOT NULL,
            rule_expression TEXT NOT NULL,
            description TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS semantic_engine_components (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            component TEXT NOT NULL,
            status TEXT NOT NULL,
            responsibility TEXT NOT NULL,
            implementation TEXT,
            notes TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS semantic_ingest_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            summary_json TEXT NOT NULL DEFAULT '{}',
            error_message TEXT,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS semantic_learned_queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scope_type TEXT NOT NULL DEFAULT 'global',
            company_code TEXT NOT NULL DEFAULT '',
            masterfn TEXT NOT NULL DEFAULT '',
            companyfn TEXT NOT NULL DEFAULT '',
            user_id TEXT NOT NULL DEFAULT '',
            session_id TEXT NOT NULL DEFAULT '',
            question_text TEXT NOT NULL,
            normalized_question TEXT NOT NULL,
            report_id TEXT NOT NULL,
            module TEXT NOT NULL,
            tool_name TEXT NOT NULL,
            filters_json TEXT NOT NULL DEFAULT '{}',
            confidence REAL NOT NULL DEFAULT 0,
            verified INTEGER NOT NULL DEFAULT 0,
            success_count INTEGER NOT NULL DEFAULT 1,
            feedback_up_count INTEGER NOT NULL DEFAULT 0,
            feedback_down_count INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            last_used_at TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_semantic_files_scope ON semantic_files(scope_type, company_code, module, status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_semantic_reports_scope ON semantic_reports(scope_type, company_code, module, report_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_semantic_reports_intent ON semantic_reports(module, intent_type)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_semantic_questions_report ON semantic_sample_questions(module, report_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_semantic_runs_file ON semantic_ingest_runs(file_id, created_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_semantic_learned_scope ON semantic_learned_queries(scope_type, company_code, module, verified)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_semantic_learned_norm ON semantic_learned_queries(normalized_question, report_id, module)")
    conn.commit()
    if own_conn:
        conn.close()


def normalize_scope(scope_type: str, company_code: str = "", masterfn: str = "", companyfn: str = "") -> dict[str, str]:
    scope_type = (scope_type or "global").strip().lower()
    if scope_type not in VALID_SCOPE_TYPES:
        raise ValueError("scope_type must be global or company")
    company_code = (company_code or "").strip().upper()
    masterfn = (masterfn or "").strip()
    companyfn = (companyfn or "").strip()
    if scope_type == "global":
        return {"scope_type": "global", "company_code": "", "masterfn": "", "companyfn": ""}
    if not company_code:
        raise ValueError("company_code is required for company scope")
    return {"scope_type": "company", "company_code": company_code, "masterfn": masterfn, "companyfn": companyfn}


def normalize_module(module: str) -> str:
    module = (module or "").strip().lower().replace(" ", "_")
    if module not in VALID_MODULES:
        raise ValueError(f"Invalid module. Choose from: {', '.join(sorted(VALID_MODULES))}")
    return module


def register_semantic_file(file_path: str, scope: dict[str, str], module: str) -> int:
    init_semantic_db()
    path = str(Path(file_path).resolve())
    now = now_iso()
    conn = get_knowledge_conn()
    row = conn.execute("SELECT id FROM semantic_files WHERE file_path=?", (path,)).fetchone()
    values = (
        Path(path).name, scope["scope_type"], scope["company_code"], scope["masterfn"],
        scope["companyfn"], module, "pending", None, now, path,
    )
    if row:
        conn.execute("""
            UPDATE semantic_files
               SET filename=?, scope_type=?, company_code=?, masterfn=?, companyfn=?,
                   module=?, status=?, error_message=?, updated_at=?
             WHERE file_path=?
        """, values)
        file_id = row["id"]
    else:
        cur = conn.execute("""
            INSERT INTO semantic_files
                (filename, scope_type, company_code, masterfn, companyfn, module,
                 status, error_message, created_at, file_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, values)
        file_id = cur.lastrowid
    conn.commit()
    conn.close()
    return int(file_id)


def update_file_status(file_id: int, status: str, error_message: str | None = None, reports_parsed: int | None = None) -> None:
    init_semantic_db()
    now = now_iso()
    fields = ["status=?", "error_message=?", "updated_at=?"]
    params: list[Any] = [status, error_message, now]
    if status == "done":
        fields.append("ingested_at=?")
        params.append(now)
    if reports_parsed is not None:
        fields.append("reports_parsed=?")
        params.append(int(reports_parsed))
    params.append(file_id)
    conn = get_knowledge_conn()
    conn.execute(f"UPDATE semantic_files SET {', '.join(fields)} WHERE id=?", params)
    conn.commit()
    conn.close()


def get_semantic_file(file_id: int) -> dict[str, Any] | None:
    init_semantic_db()
    conn = get_knowledge_conn()
    row = conn.execute("SELECT * FROM semantic_files WHERE id=?", (file_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def list_semantic_files(module: str = "", scope_type: str = "", company_code: str = "", limit: int = 100, offset: int = 0) -> dict[str, Any]:
    init_semantic_db()
    where, params = [], []
    if module:
        where.append("module=?")
        params.append(normalize_module(module))
    if scope_type:
        where.append("scope_type=?")
        params.append(scope_type.strip().lower())
    if company_code:
        where.append("company_code=?")
        params.append(company_code.strip().upper())
    clause = "WHERE " + " AND ".join(where) if where else ""
    conn = get_knowledge_conn()
    total = conn.execute(f"SELECT COUNT(*) FROM semantic_files {clause}", params).fetchone()[0]
    rows = conn.execute(f"""
        SELECT * FROM semantic_files {clause}
        ORDER BY created_at DESC LIMIT ? OFFSET ?
    """, params + [limit, offset]).fetchall()
    conn.close()
    return {"total": total, "items": [dict(r) for r in rows]}


def replace_metadata_for_file(file_id: int, payload: dict[str, list[dict[str, Any]]], file_row: dict[str, Any]) -> int:
    init_semantic_db()
    conn = get_knowledge_conn()
    try:
        for table in (
            "semantic_reports", "semantic_output_columns", "semantic_filters",
            "semantic_relationships", "semantic_synonyms",
            "semantic_sample_questions", "semantic_business_rules",
            "semantic_field_mappings", "semantic_mandatory_fields",
            "semantic_child_tabs", "semantic_sales_cycle",
            "semantic_sql_templates", "semantic_permissions",
            "semantic_engine_components",
        ):
            conn.execute(f"DELETE FROM {table} WHERE file_id=?", (file_id,))

        module = file_row["module"]
        scope_type = file_row["scope_type"]
        company_code = file_row["company_code"] or ""
        masterfn = file_row["masterfn"] or ""
        companyfn = file_row["companyfn"] or ""
        now = now_iso()
        report_count = 0

        for row in payload.get("report_catalog", []):
            conn.execute("""
                INSERT OR REPLACE INTO semantic_reports
                    (file_id, report_id, module, scope_type, company_code, masterfn, companyfn,
                     report_name, intent_type, description, business_keywords, tool_name,
                     default_filters_json, required_filters_json, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            """, (
                file_id, row["report_id"], module, scope_type, company_code, masterfn, companyfn,
                row["report_name"], row["intent_type"], row.get("description", ""),
                row.get("business_keywords", ""), row["tool_name"],
                json.dumps(row.get("default_filters", {}), ensure_ascii=False),
                json.dumps(row.get("required_filters", []), ensure_ascii=False),
                now,
            ))
            report_count += 1

        for row in payload.get("output_mapping", []):
            conn.execute("""
                INSERT INTO semantic_output_columns
                    (file_id, report_id, module, query_column, output_name, data_type, display_order)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (file_id, row["report_id"], module, row["query_column"], row["output_name"],
                  row.get("data_type", ""), int(row.get("display_order") or 0)))

        for row in payload.get("filter_mapping", []):
            conn.execute("""
                INSERT INTO semantic_filters
                    (file_id, report_id, module, filter_column, ui_name, data_type, operator, required, default_value)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (file_id, row["report_id"], module, row["filter_column"], row.get("ui_name", ""),
                  row.get("data_type", ""), row.get("operator", ""), 1 if row.get("required") else 0,
                  row.get("default_value", "")))

        for row in payload.get("join_relationship", []):
            conn.execute("""
                INSERT INTO semantic_relationships
                    (file_id, module, parent_table, child_table, join_condition, join_type, business_meaning)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (file_id, module, row["parent_table"], row["child_table"], row["join_condition"],
                  row.get("join_type", ""), row.get("business_meaning", "")))

        for row in payload.get("business_synonym", []):
            conn.execute("""
                INSERT INTO semantic_synonyms
                    (file_id, module, business_term, technical_term, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (file_id, module, row["business_term"], row["technical_term"], row.get("notes", "")))

        report_lookup = {r["report_id"]: r for r in payload.get("report_catalog", [])}
        for row in payload.get("sample_questions", []):
            report = report_lookup.get(row["report_id"], {})
            searchable = " | ".join([
                str(row.get("user_question", "")),
                str(report.get("report_name", "")),
                str(report.get("description", "")),
                str(report.get("business_keywords", "")),
            ])
            conn.execute("""
                INSERT INTO semantic_sample_questions
                    (file_id, report_id, module, user_question, searchable_text, embedding_indexed)
                VALUES (?, ?, ?, ?, ?, 0)
            """, (file_id, row["report_id"], module, row["user_question"], searchable))

        for row in payload.get("business_rules", []):
            conn.execute("""
                INSERT INTO semantic_business_rules
                    (file_id, report_id, module, rule_name, rule_expression, description)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (file_id, row.get("report_id") or "", module, row["rule_name"],
                  row["rule_expression"], row.get("description", "")))

        for row in payload.get("field_mapping", []):
            conn.execute("""
                INSERT INTO semantic_field_mappings
                    (file_id, module, table_name, field_name, field_role, business_label, data_type, synonyms, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (file_id, module, row["table"], row["field"], row.get("field_role", ""),
                  row["business_label"], row.get("data_type", ""), row.get("synonyms", ""),
                  row.get("description", "")))

        for row in payload.get("mandatory_fields", []):
            conn.execute("""
                INSERT INTO semantic_mandatory_fields
                    (file_id, module, table_name, field_name, rule, default_value, applies_to, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (file_id, module, row["table"], row["field"], row["rule"],
                  row.get("default_value", ""), row.get("applies_to", ""), row.get("description", "")))

        for row in payload.get("child_tabs", []):
            conn.execute("""
                INSERT INTO semantic_child_tabs
                    (file_id, module, parent_document, child_tab, child_table, join_condition, business_meaning)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (file_id, module, row["parent_document"], row["child_tab"], row["child_table"],
                  row.get("join_condition", ""), row.get("business_meaning", "")))

        for row in payload.get("sales_cycle", []):
            conn.execute("""
                INSERT INTO semantic_sales_cycle
                    (file_id, module, sequence, document_name, tag_table_usage, source_table, next_document, business_state)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (file_id, module, int(row["sequence"]), row["document_name"], row["tag_table_usage"],
                  row.get("source_table", ""), row.get("next_document", ""), row.get("business_state", "")))

        for row in payload.get("sql_templates", []):
            conn.execute("""
                INSERT INTO semantic_sql_templates
                    (file_id, report_id, module, sql_template, parameters, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (file_id, row["report_id"], module, row["sql_template"],
                  row.get("parameters", ""), row.get("notes", "")))

        for row in payload.get("permissions", []):
            conn.execute("""
                INSERT INTO semantic_permissions
                    (file_id, module, rule_name, rule_expression, description)
                VALUES (?, ?, ?, ?, ?)
            """, (file_id, module, row["rule_name"], row["rule_expression"], row.get("description", "")))

        for row in payload.get("engine_components", []):
            conn.execute("""
                INSERT INTO semantic_engine_components
                    (file_id, component, status, responsibility, implementation, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (file_id, row["component"], row["status"], row["responsibility"],
                  row.get("implementation", ""), row.get("notes", "")))

        conn.execute("""
            INSERT INTO semantic_ingest_runs (file_id, status, summary_json, created_at)
            VALUES (?, 'success', ?, ?)
        """, (file_id, json.dumps({"reports": report_count}, ensure_ascii=False), now_iso()))
        conn.commit()
        return report_count
    except Exception as exc:
        conn.rollback()
        conn.execute("""
            INSERT INTO semantic_ingest_runs (file_id, status, error_message, created_at)
            VALUES (?, 'failed', ?, ?)
        """, (file_id, str(exc), now_iso()))
        conn.commit()
        raise
    finally:
        conn.close()


def list_reports(module: str = "", scope_type: str = "", company_code: str = "") -> list[dict[str, Any]]:
    init_semantic_db()
    where = ["is_active=1"]
    params: list[Any] = []
    if module:
        where.append("module=?")
        params.append(normalize_module(module))
    if scope_type:
        where.append("scope_type=?")
        params.append(scope_type.strip().lower())
    if company_code:
        where.append("company_code=?")
        params.append(company_code.strip().upper())
    conn = get_knowledge_conn()
    rows = conn.execute(f"""
        SELECT * FROM semantic_reports
         WHERE {' AND '.join(where)}
         ORDER BY module, scope_type DESC, report_id
    """, params).fetchall()
    conn.close()
    items = []
    for row in rows:
        item = dict(row)
        item["default_filters"] = json.loads(item.pop("default_filters_json") or "{}")
        item["required_filters"] = json.loads(item.pop("required_filters_json") or "[]")
        items.append(item)
    return items


def semantic_stats() -> dict[str, Any]:
    init_semantic_db()
    conn = get_knowledge_conn()
    files = conn.execute("SELECT status, COUNT(*) cnt FROM semantic_files GROUP BY status").fetchall()
    modules = conn.execute("SELECT module, COUNT(*) cnt FROM semantic_reports WHERE is_active=1 GROUP BY module").fetchall()
    total_reports = conn.execute("SELECT COUNT(*) FROM semantic_reports WHERE is_active=1").fetchone()[0]
    total_files = conn.execute("SELECT COUNT(*) FROM semantic_files").fetchone()[0]
    conn.close()
    return {
        "files": total_files,
        "reports": total_reports,
        "files_by_status": {r["status"]: r["cnt"] for r in files},
        "reports_by_module": {r["module"]: r["cnt"] for r in modules},
    }


def save_learned_query_candidate(
    *,
    question_text: str,
    normalized_question: str,
    semantic_match: dict[str, Any],
    filters: dict[str, Any] | None = None,
    user_id: str = "",
    session_id: str = "",
    masterfn: str = "",
    companyfn: str = "",
    company_code: str = "",
) -> int | None:
    if not semantic_match.get("matched"):
        return None
    init_semantic_db()
    now = now_iso()
    scope_type = "company" if company_code else semantic_match.get("scope_used", "global") or "global"
    company_code = (company_code or semantic_match.get("company_code") or "").strip().upper()
    filters = filters or semantic_match.get("default_filters") or {}
    conn = get_knowledge_conn()
    row = conn.execute("""
        SELECT id, success_count FROM semantic_learned_queries
         WHERE normalized_question=? AND report_id=? AND module=?
           AND scope_type=? AND company_code=?
         ORDER BY verified DESC, id DESC LIMIT 1
    """, (
        normalized_question, semantic_match["report_id"], semantic_match["module"],
        scope_type, company_code,
    )).fetchone()
    if row:
        conn.execute("""
            UPDATE semantic_learned_queries
               SET success_count=success_count+1, confidence=?, filters_json=?,
                   question_text=?, user_id=?, session_id=?, masterfn=?, companyfn=?,
                   updated_at=?, last_used_at=?
             WHERE id=?
        """, (
            float(semantic_match.get("confidence") or 0),
            json.dumps(filters, ensure_ascii=False),
            question_text, user_id, session_id, masterfn, companyfn, now, now, row["id"],
        ))
        learned_id = int(row["id"])
    else:
        cur = conn.execute("""
            INSERT INTO semantic_learned_queries
                (scope_type, company_code, masterfn, companyfn, user_id, session_id,
                 question_text, normalized_question, report_id, module, tool_name,
                 filters_json, confidence, verified, created_at, updated_at, last_used_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
        """, (
            scope_type, company_code, masterfn, companyfn, user_id, session_id,
            question_text, normalized_question, semantic_match["report_id"],
            semantic_match["module"], semantic_match["tool_name"],
            json.dumps(filters, ensure_ascii=False),
            float(semantic_match.get("confidence") or 0), now, now, now,
        ))
        learned_id = int(cur.lastrowid)
    conn.commit()
    conn.close()
    return learned_id


def record_learned_feedback(question_text: str, rating: str, company_code: str = "") -> int:
    if not question_text or rating not in {"up", "down"}:
        return 0
    from api.semantic.retrieval import normalize_question_template

    normalized = normalize_question_template(question_text)
    company_code = (company_code or "").strip().upper()
    init_semantic_db()
    conn = get_knowledge_conn()
    where = ["normalized_question=?"]
    params: list[Any] = [normalized]
    if company_code:
        where.append("(company_code=? OR company_code='')")
        params.append(company_code)
    row = conn.execute(f"""
        SELECT id FROM semantic_learned_queries
         WHERE {' AND '.join(where)}
         ORDER BY company_code DESC, updated_at DESC LIMIT 1
    """, params).fetchone()
    if not row:
        conn.close()
        return 0
    if rating == "up":
        conn.execute("""
            UPDATE semantic_learned_queries
               SET feedback_up_count=feedback_up_count+1, verified=1, updated_at=?
             WHERE id=?
        """, (now_iso(), row["id"]))
    else:
        conn.execute("""
            UPDATE semantic_learned_queries
               SET feedback_down_count=feedback_down_count+1, verified=0, updated_at=?
             WHERE id=?
        """, (now_iso(), row["id"]))
    conn.commit()
    conn.close()
    return 1


def list_learned_queries(module: str = "", verified: bool | None = None) -> list[dict[str, Any]]:
    init_semantic_db()
    where = []
    params: list[Any] = []
    if module:
        where.append("module=?")
        params.append(normalize_module(module))
    if verified is not None:
        where.append("verified=?")
        params.append(1 if verified else 0)
    clause = "WHERE " + " AND ".join(where) if where else ""
    conn = get_knowledge_conn()
    rows = conn.execute(f"""
        SELECT * FROM semantic_learned_queries {clause}
        ORDER BY verified DESC, updated_at DESC LIMIT 100
    """, params).fetchall()
    conn.close()
    items = []
    for row in rows:
        item = dict(row)
        item["filters"] = json.loads(item.pop("filters_json") or "{}")
        items.append(item)
    return items
