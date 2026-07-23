import json
import re
from typing import Any

from api.semantic import store


_TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)
_MONTH_NUM_RE = re.compile(r"\b(?:0?[1-9]|1[0-2])[/.-](?:19|20)\d{2}\b")
_YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")
_MONTH_WORD_RE = re.compile(
    r"\b(january|february|march|april|may|june|july|august|september|october|november|december|"
    r"jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)\b",
    re.IGNORECASE,
)
_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "i", "in",
    "is", "it", "me", "my", "need", "of", "on", "or", "please", "the", "this",
    "to", "want", "we", "with", "you",
}
_TOKEN_ALIASES = {
    "orders": "order",
    "invoices": "invoice",
    "customers": "customer",
    "clients": "customer",
    "client": "customer",
    "debtors": "customer",
    "debtor": "customer",
    "items": "item",
    "products": "product",
    "skus": "sku",
    "docs": "document",
    "documents": "document",
    "numbers": "number",
    "nos": "number",
    "quotes": "quotation",
    "quote": "quotation",
    "billings": "invoice",
    "billing": "invoice",
}
_TAG_ALIASES = {
    "sal_quo": {"quotation", "quote", "sales quotation", "customer quote"},
    "sal_soe": {"sales order", "sale order", "customer order", "order", "so", "soe", "booking"},
    "sal_soc": {"sales order confirmation", "so confirmation", "soc", "confirmed order"},
    "stk_do": {"delivery order", "do", "shipment", "dispatch"},
    "stk_doc": {"delivery confirmation", "do confirmation", "confirmed delivery"},
    "sal_inv": {"sales invoice", "invoice", "billing", "customer invoice"},
    "sal_cn": {"credit note", "sales credit note", "cn"},
    "sal_dn": {"debit note", "sales debit note", "dn"},
}
_LIST_RE = re.compile(r"\b(list|show|find|display|get|fetch|pull|which)\b", re.IGNORECASE)
_COUNT_RE = re.compile(r"\b(how many|count|number of|total number)\b", re.IGNORECASE)
_TOP_RE = re.compile(r"\b(top\s*\d*|largest|highest|biggest|best|most)\b", re.IGNORECASE)
_AGG_RE = re.compile(r"\b(sum|total|by customer|by product|group by|breakdown|summary)\b", re.IGNORECASE)
_DOC_NO_RE = re.compile(r"\b[A-Z]{2,}[A-Z0-9-]*\d{4,}[A-Z0-9-]*\b", re.IGNORECASE)


def _tokens(text: str) -> set[str]:
    tokens = set()
    for token in _TOKEN_RE.findall(text or ""):
        token = token.lower()
        if len(token) <= 1 or token in _STOPWORDS:
            continue
        tokens.add(_TOKEN_ALIASES.get(token, token))
    return tokens


def _score(query: str, text: str) -> float:
    qt = _tokens(query)
    tt = _tokens(text)
    if not qt or not tt:
        return 0.0
    overlap = len(qt & tt)
    return overlap / max(1, len(qt))


def _phrase_score(query: str, phrases: str) -> float:
    q = f" {(query or '').lower()} "
    hits = 0
    total = 0
    for raw in re.split(r"[,|=]", phrases or ""):
        phrase = raw.strip().lower()
        if not phrase or len(phrase) < 3:
            continue
        total += 1
        if f" {phrase} " in q:
            hits += 1
    if not total:
        return 0.0
    return min(0.25, hits * 0.08)


def _specific_phrase_score(query: str, text: str) -> float:
    """Boost reports that contain exact business field phrases from the user query."""
    q = f" {(query or '').lower()} "
    hits = 0
    for raw in re.split(r"[,|=]", text or ""):
        phrase = re.sub(r"\s+", " ", raw.strip().lower())
        if len(phrase) < 6 or "_" in phrase:
            continue
        if f" {phrase} " in q:
            hits += 1
    return min(0.4, hits * 0.18)


def _tag_score(query: str, tag_table_usage: str) -> float:
    q = f" {(query or '').lower()} "
    tag = (tag_table_usage or "").strip().lower()
    if not tag:
        return 0.0
    score = 0.0
    if tag in q:
        score += 0.2
    for alias in _TAG_ALIASES.get(tag, set()):
        if f" {alias} " in q:
            score += 0.3 if " " in alias else 0.14
    return min(score, 0.38)


def _intent_score(query: str, intent: str) -> float:
    intent = (intent or "").lower()
    if intent == "list" and _LIST_RE.search(query):
        return 0.16
    if intent in {"ranking", "top"} and _TOP_RE.search(query):
        return 0.2
    if intent in {"aggregate", "summary"} and _AGG_RE.search(query):
        return 0.18
    if intent == "count" and _COUNT_RE.search(query):
        return 0.2
    return 0.0


def _context_value(context_state: Any, key: str, default: str = "") -> str:
    if not context_state:
        return default
    if isinstance(context_state, dict):
        value = context_state.get(key, default)
    else:
        value = getattr(context_state, key, default)
    return str(value or default)


def _current_query_explicitly_selects_other_report(query: str, report_id: str, report_name: str) -> bool:
    q = f" {(query or '').lower()} "
    rid = (report_id or "").lower()
    name = f" {(report_name or '').lower()} "
    if rid and rid in q:
        return False
    explicit_terms = {
        "Driver Info": ["driver", "vehicle", "shipping by", "transportation cost"],
        "Detail Items": ["detail", "line item", "product", "service", "item"],
        "Sales Order Header": ["header", "listing", "sales order listing"],
    }
    for label, terms in explicit_terms.items():
        label_name = label.lower()
        query_hits_label = any(f" {term} " in q for term in terms)
        report_is_label = label_name in name or any(f" {term} " in name for term in terms)
        if query_hits_label and not report_is_label:
            return True
    return False


def _context_score(query: str, row: Any, context_state: Any) -> float:
    if not context_state:
        return 0.0
    report_id = row["report_id"] or ""
    report_name = row["report_name"] or ""
    if _current_query_explicitly_selects_other_report(query, report_id, report_name):
        return 0.0

    score = 0.0
    last_report_id = _context_value(context_state, "last_report_id")
    last_module = _context_value(context_state, "last_module")
    last_document_type = _context_value(context_state, "last_document_type")
    last_tab = _context_value(context_state, "last_tab")
    has_doc = bool(_context_value(context_state, "last_document_no"))

    if last_report_id and report_id == last_report_id:
        score += 0.45
    if last_module and row["module"] == last_module:
        score += 0.08
    if last_document_type == "sales_order" and _tag_score("sales order", _load_json(row["default_filters_json"], {}).get("tag_table_usage", "")):
        score += 0.08
    if last_tab and last_tab.lower() in report_name.lower():
        score += 0.25
    if has_doc and (row["intent_type"] or "").lower() in {"detail", "lookup"}:
        score += 0.12
    return min(score, 0.65)


def normalize_question_template(query: str) -> str:
    text = (query or "").lower().strip()
    text = _MONTH_NUM_RE.sub("{month}", text)
    text = _MONTH_WORD_RE.sub("{month_name}", text)
    text = _YEAR_RE.sub("{year}", text)
    text = re.sub(r"\btop\s+\d+\b", "top {n}", text)
    text = re.sub(r"\b\d+\b", "{number}", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _load_json(value: str, fallback):
    try:
        return json.loads(value or "")
    except Exception:
        return fallback


def load_semantic_report_runtime(match: dict[str, Any]) -> dict[str, Any]:
    """Load executable metadata for a selected semantic report."""
    if not match.get("matched"):
        return {}
    store.init_semantic_db()
    conn = store.get_knowledge_conn()
    params = [match["report_id"], match["module"]]
    scope_filter = ""
    if match.get("scope_used"):
        scope_filter = " AND r.scope_type=? AND r.company_code=?"
        params.extend([match.get("scope_used", "global"), match.get("company_code", "")])
    report = conn.execute(f"""
        SELECT r.*
          FROM semantic_reports r
         WHERE r.report_id=? AND r.module=? AND r.is_active=1 {scope_filter}
         ORDER BY r.scope_type DESC, r.id DESC
         LIMIT 1
    """, params).fetchone()
    if not report:
        conn.close()
        return {}

    file_id = report["file_id"]
    report_id = report["report_id"]
    module = report["module"]
    sql_row = conn.execute("""
        SELECT sql_template, parameters, notes
          FROM semantic_sql_templates
         WHERE file_id=? AND report_id=? AND module=?
         ORDER BY id DESC LIMIT 1
    """, (file_id, report_id, module)).fetchone()
    outputs = conn.execute("""
        SELECT query_column, output_name, data_type, display_order
          FROM semantic_output_columns
         WHERE file_id=? AND report_id=? AND module=?
         ORDER BY display_order, id
    """, (file_id, report_id, module)).fetchall()
    filters = conn.execute("""
        SELECT filter_column, ui_name, data_type, operator, required, default_value
          FROM semantic_filters
         WHERE file_id=? AND report_id=? AND module=?
         ORDER BY required DESC, id
    """, (file_id, report_id, module)).fetchall()
    conn.close()
    return {
        "sql_template": sql_row["sql_template"] if sql_row else "",
        "parameters": sql_row["parameters"] if sql_row else "",
        "sql_notes": sql_row["notes"] if sql_row else "",
        "output_columns": [dict(row) for row in outputs],
        "filters": [dict(row) for row in filters],
    }


def resolve_semantic_report(
    query: str,
    masterfn: str = "",
    companyfn: str = "",
    company_code: str = "",
    module_hint: str | None = None,
    context_state: Any = None,
    min_confidence: float = 0.35,
) -> dict[str, Any]:
    """Resolve a user query to a scoped semantic report definition.

    This first implementation is deterministic lexical retrieval over ingested
    semantic rows. It prefers company-specific metadata and falls back to global.
    """
    store.init_semantic_db()
    company_code = (company_code or "").strip().upper()
    module_hint = store.normalize_module(module_hint) if module_hint else ""
    learned = _resolve_learned_query(query, company_code=company_code, module_hint=module_hint)
    if learned.get("matched"):
        return learned
    where = ["r.is_active=1"]
    params: list[Any] = []
    if module_hint:
        where.append("r.module=?")
        params.append(module_hint)
    scope_clause = "r.scope_type='global'"
    if company_code:
        scope_clause = "(r.scope_type='global' OR (r.scope_type='company' AND r.company_code=?))"
        params.append(company_code)
    where.append(scope_clause)

    conn = store.get_knowledge_conn()
    rows = conn.execute(f"""
        SELECT r.*,
               COALESCE(GROUP_CONCAT(DISTINCT q.user_question), '') AS sample_questions,
               COALESCE(GROUP_CONCAT(DISTINCT s.business_term || '=' || s.technical_term), '') AS synonyms,
               COALESCE(GROUP_CONCAT(DISTINCT f.business_label || '=' || f.field_name || '=' || f.synonyms), '') AS fields
          FROM semantic_reports r
          LEFT JOIN semantic_sample_questions q
            ON q.file_id = r.file_id AND q.report_id = r.report_id
          LEFT JOIN semantic_synonyms s
            ON s.file_id = r.file_id AND s.module = r.module
          LEFT JOIN semantic_field_mappings f
            ON f.file_id = r.file_id AND f.module = r.module
         WHERE {' AND '.join(where)}
         GROUP BY r.id
    """, params).fetchall()
    conn.close()

    best = None
    best_score = 0.0
    candidates: list[dict[str, Any]] = []
    for row in rows:
        blob = " ".join([
            row["report_id"], row["module"], row["report_name"], row["intent_type"],
            row["description"] or "", row["business_keywords"] or "",
            row["tool_name"], row["sample_questions"] or "", row["synonyms"] or "",
            row["fields"] or "",
        ])
        default_filters = _load_json(row["default_filters_json"], {})
        score = _score(query, blob)
        score += _phrase_score(query, row["business_keywords"] or "")
        score += _phrase_score(query, row["sample_questions"] or "")
        score += _phrase_score(query, row["synonyms"] or "")
        specific_score = 0.0
        specific_score += _specific_phrase_score(query, row["business_keywords"] or "")
        specific_score += _specific_phrase_score(query, row["synonyms"] or "")
        specific_score += _specific_phrase_score(query, row["fields"] or "")
        score += specific_score
        score += _tag_score(query, default_filters.get("tag_table_usage", ""))
        ql = (query or "").lower()
        intent = (row["intent_type"] or "").lower()
        score += _intent_score(ql, intent)
        score += _context_score(query, row, context_state)
        if (
            specific_score > 0
            and _DOC_NO_RE.search(query or "")
            and intent in {"detail", "lookup"}
            and row["tool_name"] == "run_query"
        ):
            score += 0.55
        if intent == "count" and re.search(r"\b(do not|don't|dont|not)\s+(want|need)?\s*count\b", ql):
            score -= 0.25
        if row["scope_type"] == "company":
            score += 0.08
        candidates.append({
            "report_id": row["report_id"],
            "report_name": row["report_name"],
            "module": row["module"],
            "intent_type": row["intent_type"],
            "tool_name": row["tool_name"],
            "business_keywords": row["business_keywords"] or "",
            "default_filters": default_filters,
            "required_filters": _load_json(row["required_filters_json"], []),
            "confidence": round(min(score, 1.0), 3),
        })
        if score > best_score:
            best = row
            best_score = score

    candidates.sort(key=lambda item: item["confidence"], reverse=True)
    top_candidates = [item for item in candidates[:8] if item["confidence"] >= 0.2]
    if not best or best_score < min_confidence:
        return {"matched": False, "confidence": round(best_score, 3), "candidates": top_candidates}

    return {
        "matched": True,
        "confidence": round(min(best_score, 1.0), 3),
        "scope_used": best["scope_type"],
        "company_code": best["company_code"] or "",
        "masterfn": best["masterfn"] or masterfn or "",
        "companyfn": best["companyfn"] or companyfn or "",
        "report_id": best["report_id"],
        "module": best["module"],
        "report_name": best["report_name"],
        "intent_type": best["intent_type"],
        "description": best["description"] or "",
        "business_keywords": best["business_keywords"] or "",
        "tool_name": best["tool_name"],
        "default_filters": _load_json(best["default_filters_json"], {}),
        "required_filters": _load_json(best["required_filters_json"], []),
        "sample_questions": best["sample_questions"] or "",
        "candidates": top_candidates,
    }


def _resolve_learned_query(query: str, company_code: str = "", module_hint: str = "", min_confidence: float = 0.72) -> dict[str, Any]:
    normalized = normalize_question_template(query)
    where = ["l.verified=1"]
    params: list[Any] = []
    if module_hint:
        where.append("l.module=?")
        params.append(module_hint)
    if company_code:
        where.append("(l.company_code=? OR l.company_code='')")
        params.append(company_code)
    conn = store.get_knowledge_conn()
    rows = conn.execute(f"""
        SELECT l.*, r.report_name, r.intent_type, r.description, r.business_keywords,
               r.default_filters_json, r.required_filters_json
          FROM semantic_learned_queries l
          LEFT JOIN semantic_reports r
            ON r.report_id=l.report_id AND r.module=l.module
           AND (r.company_code=l.company_code OR r.scope_type='global')
         WHERE {' AND '.join(where)}
         ORDER BY l.company_code DESC, l.feedback_up_count DESC, l.success_count DESC, l.updated_at DESC
         LIMIT 100
    """, params).fetchall()
    conn.close()
    best = None
    best_score = 0.0
    for row in rows:
        score = 1.0 if row["normalized_question"] == normalized else _score(normalized, row["normalized_question"])
        if row["company_code"]:
            score += 0.05
        if score > best_score:
            best = row
            best_score = score
    if not best or best_score < min_confidence:
        return {"matched": False, "confidence": round(best_score, 3)}
    default_filters = _load_json(best["default_filters_json"], {})
    learned_filters = _load_json(best["filters_json"], {})
    return {
        "matched": True,
        "source": "learned_query",
        "confidence": round(min(best_score, 1.0), 3),
        "scope_used": best["scope_type"],
        "company_code": best["company_code"] or "",
        "masterfn": best["masterfn"] or "",
        "companyfn": best["companyfn"] or "",
        "report_id": best["report_id"],
        "module": best["module"],
        "report_name": best["report_name"] or best["report_id"],
        "intent_type": best["intent_type"] or "",
        "description": best["description"] or "",
        "business_keywords": best["business_keywords"] or "",
        "tool_name": best["tool_name"],
        "default_filters": {**default_filters, **learned_filters},
        "required_filters": _load_json(best["required_filters_json"], []),
        "sample_questions": best["question_text"],
        "learned_query_id": best["id"],
        "normalized_question": best["normalized_question"],
    }


def semantic_context_block(match: dict[str, Any]) -> str:
    if not match.get("matched"):
        return ""
    return (
        "\n\n## Selected Semantic Report\n"
        f"- Report ID: {match['report_id']}\n"
        f"- Report Name: {match['report_name']}\n"
        f"- Module: {match['module']}\n"
        f"- Intent: {match['intent_type']}\n"
        f"- Tool: {match['tool_name']}\n"
        f"- Default filters: {json.dumps(match.get('default_filters', {}), ensure_ascii=False)}\n"
        f"- Required filters: {json.dumps(match.get('required_filters', []), ensure_ascii=False)}\n"
        f"- Confidence: {match.get('confidence')}\n"
        f"- Source: {match.get('source', 'semantic_metadata')}\n"
        "Use this selected semantic report when choosing the skill tool. "
        "Do not answer from manuals when a semantic report is selected."
    )
