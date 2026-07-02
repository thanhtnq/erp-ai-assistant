"""
ERP AI Assistant — Hybrid Search
Vector + Keyword + Reranker search over the knowledge base.
"""
import json
import os
import re
from pathlib import Path

from api.config import KNOWLEDGE_DB, MAX_ENTRIES, VECTOR_TOP_K, RERANK_TOP_N
from api.database import get_knowledge_conn, get_company_id_from_code

# ── Vector search + reranker (optional — graceful fallback if not installed) ──
try:
    from embedding_helper import (
        vector_search, rerank, CHROMA_AVAILABLE,
    )
    from ingest.ingest_config import VECTOR_TOP_K as _VTK, RERANK_TOP_N as _RTN
    VECTOR_TOP_K = _VTK
    RERANK_TOP_N = _RTN
    if CHROMA_AVAILABLE:
        print("[OK] Vector search ready; reranker loads on first search")
    else:
        print("[--] ChromaDB not available — using keyword search only")
except ImportError:
    CHROMA_AVAILABLE = False
    VECTOR_TOP_K = 20
    RERANK_TOP_N = 3

    def vector_search(*a, **kw):
        return []

    def rerank(_q, c, top_n=3):
        return c[:top_n]

    print("[--] embedding_helper not found — using keyword search only")


# ─── Intent Detection ─────────────────────────────────────────────────────────
_DOC_NUMBER_RE = re.compile(
    r'\b(soe|soc|sal_inv|inv|sal_quo|quo|sal_cn|cn|stk_do|do|stk_doc|po|grn|prj)[_\- ]?\d+\b'
    r'|#\s*\d{3,}',
    re.IGNORECASE,
)


def detect_intent(query: str) -> str:
    """
    Detect user intent from query to guide search strategy.
    Returns: 'data_query' | 'error_fix' | 'procedure' | 'faq' | 'reference' | 'any'
    """
    q = query.lower()

    PROCEDURAL_GUARD = {
        "how to", "how do i", "how do we", "steps to", "guide to",
        "cách", "hướng dẫn", "làm thế nào", "làm sao",
    }
    _has_procedural_guard = any(kw in q for kw in PROCEDURAL_GUARD)

    if not _has_procedural_guard:
        if _DOC_NUMBER_RE.search(query):
            return "data_query"

        STRONG_DATA_KW = {
            "tồn kho", "tồn hàng", "hàng tồn", "kiểm tra tồn",
            "stock on hand", "available stock", "current stock", "stock level",
            "công nợ", "dư nợ", "ar balance", "ap balance",
            "accounts receivable", "accounts payable",
            "chưa thanh toán", "quá hạn thanh toán",
            "overdue invoice", "outstanding invoice", "outstanding balance",
            "ar aging", "ap aging", "aging report", "tuổi nợ",
            "doanh thu", "doanh số", "revenue", "sales amount", "total sales",
            "sale price", "sales price", "best sale", "best sales",
            "best sale price", "best sales price", "highest sale", "highest sales",
            "highest sale price", "highest sales price", "largest sale", "largest sales",
            "top khách hàng", "top customer", "top clients",
            "top sản phẩm", "top product", "top item",
            "top nhân viên", "top salesperson", "top staff",
            "best selling", "hàng bán chạy",
            "chờ duyệt", "chứng từ chờ", "pending approval", "awaiting approval",
            "cần phê duyệt", "approval queue",
            "ticket của tôi", "my tickets", "my open ticket",
            "ticket đang mở", "open ticket", "pending ticket",
        }
        for kw in STRONG_DATA_KW:
            if kw in q:
                return "data_query"

        ANALYTICAL_KW = {
            "how many", "how much", "bao nhiêu", "mấy",
            "total", "tổng", "tổng cộng", "tổng số",
            "count", "đếm", "số lượng", "số lần",
            "sum", "average", "avg", "trung bình",
            "highest", "lowest", "largest", "smallest",
            "most", "least", "best", "worst",
            "top 5", "top 10", "top 3", "top 20",
            "report", "báo cáo", "phân tích", "thống kê",
            "summary", "tổng hợp", "breakdown", "chi tiết theo",
            "trend", "xu hướng", "so sánh", "compare",
            "this month", "tháng này", "last month", "tháng trước",
            "this year", "năm nay", "last year", "năm trước",
            "year to date", "ytd", "this quarter", "quý này",
            "today", "hôm nay", "this week", "tuần này", "last week",
            "q1", "q2", "q3", "q4",
        }
        ERP_ENTITY_KW = {
            "sales order", "đơn hàng", "đơn bán",
            "sales invoice", "hóa đơn bán", "invoice",
            "sales confirmation", "so confirmation",
            "quotation", "báo giá", "sales quote",
            "delivery", "phiếu xuất", "delivery order",
            "credit note", "giấy báo có",
            "purchase order", "đơn mua", "po",
            "purchase invoice", "hóa đơn mua",
            "goods receipt", "phiếu nhập", "grn",
            "customer", "khách hàng", "client",
            "vendor", "supplier", "nhà cung cấp",
            "salesperson", "nhân viên bán hàng", "sales staff",
            "product", "sản phẩm", "item", "hàng hóa",
            "brand", "thương hiệu", "category", "danh mục",
            "stock", "kho", "inventory", "warehouse",
            "payment", "thanh toán", "receipt", "bank",
        }
        _has_analytical = any(kw in q for kw in ANALYTICAL_KW)
        _has_entity = any(kw in q for kw in ERP_ENTITY_KW)
        if _has_analytical and _has_entity:
            return "data_query"

        RETRIEVAL_VERB_KW = {
            "show me", "show all", "show the", "show my",
            "list all", "list the", "list my",
            "find all", "find the", "find me",
            "get all", "get the", "get me", "fetch",
            "display", "pull up", "look up", "lookup",
            "search for", "give me",
            "xem", "xem tất cả", "xem các",
            "liệt kê", "lấy", "lấy danh sách",
            "tra cứu", "tìm kiếm đơn", "tìm hóa đơn",
            "cho tôi xem", "cho biết",
        }
        _has_retrieval = any(kw in q for kw in RETRIEVAL_VERB_KW)
        if _has_retrieval and _has_entity:
            return "data_query"

    ERROR_KEYWORDS = {
        "cannot", "can't", "cant", "unable", "couldn't", "couldnt",
        "won't", "wont", "doesn't work", "not working", "not work",
        "not able", "error", "errors", "failed", "fail", "failure",
        "issue", "issues", "problem", "problems", "trouble",
        "bug", "wrong", "incorrect", "invalid", "broken",
        "stuck", "blocked", "hanging", "frozen",
        "missing", "not found", "not showing", "not appear",
        "disappeared", "not display", "not visible", "can't see",
        "warning", "alert", "shows error", "getting error",
        "giving error", "popup", "exception",
        "cannot post", "cannot save", "cannot submit", "cannot approve",
        "cannot confirm", "cannot delete", "cannot edit", "cannot print",
        "cannot generate", "cannot create", "failed to", "fails to",
        "refuse", "rejected",
        "không thể", "không được", "lỗi", "báo lỗi", "bị lỗi",
        "không hoạt động", "không chạy", "bị kẹt", "sự cố",
        "không tìm thấy", "không hiển thị", "không in được",
    }
    for kw in ERROR_KEYWORDS:
        if kw in q:
            return "error_fix"

    FAQ_KEYWORDS = {
        "what is", "what are", "what does", "what do",
        "why is", "why are", "why does", "why do",
        "when is", "when are", "when do", "when should",
        "who is", "who are", "who should",
        "explain", "meaning of", "definition", "define",
        "difference between", "differ", " vs ", "versus",
        "what's the", "whats the", "how does", "how is", "how are",
        "purpose of", "reason for", "benefit of",
        "là gì", "nghĩa là", "tại sao", "khi nào",
        "giải thích", "khác nhau", "so sánh",
    }
    for kw in FAQ_KEYWORDS:
        if kw in q:
            return "faq"

    REFERENCE_KEYWORDS = {
        "list of", "types of", "options for", "values for",
        "field", "fields", "column", "columns", "parameter",
        "setting", "settings", "configuration", "configure",
        "status", "statuses", "code", "codes", "report", "format",
        "danh sách", "loại", "cài đặt", "cấu hình", "trường",
    }
    for kw in REFERENCE_KEYWORDS:
        if kw in q:
            return "reference"

    PROCEDURE_KEYWORDS = {
        "how to", "how do i", "steps to", "guide to",
        "create", "add", "enter", "input", "fill",
        "setup", "set up", "install", "process", "procedure",
        "submit", "approve", "post", "confirm", "issue",
        "revise", "edit", "update", "modify", "change",
        "print", "generate", "export", "import",
        "cancel", "void", "delete", "remove",
        "cách", "hướng dẫn", "tạo", "thêm", "nhập",
        "chỉnh sửa", "xóa", "in", "xuất",
    }
    for kw in PROCEDURE_KEYWORDS:
        if kw in q:
            return "procedure"

    return "any"


def build_chart_suggestion(query: str) -> dict | None:
    """Return a reusable chart suggestion payload for ranked/report-style answers."""
    q = (query or "").lower()
    rank_terms = {
        "top", "best", "highest", "largest", "most", "ranking", "ranked",
        "bestselling", "best selling", "hàng bán chạy", "bán chạy",
    }
    report_terms = {
        "report", "summary", "breakdown", "analysis", "analytics",
        "báo cáo", "tổng hợp", "phân tích", "thống kê",
    }
    if not any(term in q for term in rank_terms | report_terms):
        return None

    return {
        "question": "Would you like to display this as a chart?",
        "reason": "ranked_result" if any(term in q for term in rank_terms) else "report_result",
        "options": [
            {"type": "bar", "label": "Bar chart"},
            {"type": "column", "label": "Column chart"},
            {"type": "line", "label": "Line chart"},
            {"type": "pie", "label": "Pie chart"},
        ],
    }


# ─── Image Map Helper ─────────────────────────────────────────────────────────
_RE_IMG_REF = re.compile(r'!\[[^\]]*\]\(([^)]+)\)')


def _build_image_map(raw_content: str, img_folder: str) -> dict:
    """Map step_number → img_folder/filename using positional ordering."""
    images = []
    for line in raw_content.split('\n'):
        m = _RE_IMG_REF.search(line.strip())
        if m:
            fname = m.group(1)
            if fname and not fname.startswith('data:'):
                images.append(f"{img_folder}/{fname}")
    return {i + 1: path for i, path in enumerate(images)}


def build_step_image_map(entry: dict) -> dict:
    """Collect step-number -> image-path mappings from both step metadata and raw content."""
    img_folder = (entry or {}).get("img_folder", "")
    if not img_folder:
        return {}

    image_map: dict[int, str] = {}

    for step in (entry or {}).get("steps", []) or []:
        step_num = step.get("step_number")
        img_file = step.get("image")
        if step_num and img_file:
            image_map[int(step_num)] = f"{img_folder}/{img_file}"

    raw_content = (entry or {}).get("raw_content", "")
    if raw_content:
        for step_num, path in _build_image_map(raw_content, img_folder).items():
            image_map.setdefault(int(step_num), path)

    return image_map


# ─── Knowledge Search (Hybrid: Vector + Keyword + Reranker) ───────────────────
def search_knowledge(query: str, company_code: str = None, limit: int = MAX_ENTRIES,
                     topic_hint: str = None, intent: str = "any") -> list:
    """
    Hybrid search:
      1. Keyword tier1  — detect feature scope
      2. Intent detect  — pick source (ticket/document) + type filter
      3a. Vector search — ChromaDB top-K within scope  (if available)
      3b. Keyword SQL   — fallback if ChromaDB empty or unavailable
      4. Reranker       — CrossEncoder re-scores, picks top-N
      5. Flagged check  — ticket fallback for flagged entries
    """
    if not os.path.exists(KNOWLEDGE_DB):
        return []

    conn = get_knowledge_conn()
    company_id = get_company_id_from_code(conn, company_code)

    STOP_WORDS = {"can", "you", "show", "me", "how", "the", "to", "a", "an",
                  "is", "are", "was", "what", "where", "when", "why", "which",
                  "for", "and", "or", "in", "on", "at", "do", "did", "does",
                  "i", "my", "we", "our", "this", "that", "with", "from", "please"}

    keywords = [w for w in re.sub(r'[^\w\s]', '', query.lower()).split()
                if len(w) > 2 and w not in STOP_WORDS]
    if not keywords:
        conn.close()
        return []

    # ── Tier 1: Detect feature scope ─────────────────────────────────────────
    features = conn.execute("""
        SELECT f.id, f.name, d.name as domain, d.id as domain_id
        FROM features f JOIN domains d ON f.domain_id = d.id
    """).fetchall()

    def score_name(name):
        return sum(3 for kw in keywords if kw in (name or "").lower())

    feature_scores = sorted(
        [(f, score_name(f["name"]) + score_name(f["domain"])) for f in features],
        key=lambda x: x[1], reverse=True
    )
    feature_filter = domain_filter = None
    feature_name_f = domain_name_f = None
    best_feat, best_score = feature_scores[0] if feature_scores else (None, 0)
    if best_score >= 3:
        feature_filter = best_feat["id"]
        domain_filter = best_feat["domain_id"]
        feature_name_f = best_feat["name"]
        domain_name_f = best_feat["domain"]
        print(f"  [tier1] {best_feat['domain']} > {best_feat['name']} (score={best_score})")
    else:
        print(f"  [tier1] No strong feature match — searching all")

    # ── Intent type mapping ───────────────────────────────────────────────────
    INTENT_TYPE_SQL = {
        "error_fix": "e.type = 'error_fix'",
        "procedure": "e.type = 'procedure'",
        "faq":       "e.type IN ('faq', 'reference')",
        "reference": "e.type IN ('reference', 'faq')",
        "any":       None,
    }
    INTENT_TYPE_VEC = {
        "error_fix": ["error_fix"],
        "procedure": ["procedure"],
        "faq":       ["faq", "reference"],
        "reference": ["reference", "faq"],
        "any":       None,
    }
    type_sql = INTENT_TYPE_SQL.get(intent)
    type_vec = INTENT_TYPE_VEC.get(intent)
    print(f"  [intent] {intent}" + (f" -> {type_sql}" if type_sql else ""))

    # ── Build keyword where clause ────────────────────────────────────────────
    kw_conds, kw_params = [], []
    for kw in keywords[:6]:
        kw_conds.append("(e.name LIKE ? OR e.summary LIKE ? OR e.menu_path LIKE ?)")
        kw_params.extend([f"%{kw}%", f"%{kw}%", f"%{kw}%"])
    kw_where = f"({' OR '.join(kw_conds)})" if kw_conds else "1=1"

    def kw_sql_search(extra_scope="", extra_type_sql=None):
        scope = "e.is_active = 1"
        if feature_filter:
            scope += f" AND e.feature_id = {feature_filter}"
        elif domain_filter:
            scope += f" AND f.domain_id = {domain_filter}"
        if extra_scope:
            scope += f" AND {extra_scope}"
        ts = extra_type_sql or type_sql
        if ts:
            scope += f" AND {ts}"
        return conn.execute(f"""
            SELECT e.id, e.name, e.type, e.menu_path, e.summary,
                   f.name as feature, d.name as domain
            FROM entries e
            JOIN features f ON e.feature_id = f.id
            JOIN domains  d ON f.domain_id  = d.id
            WHERE {scope} AND {kw_where}
            ORDER BY e.sort_order LIMIT ?
        """, kw_params + [limit * 3]).fetchall()

    # ── Step A: error_fix → try tickets first via keyword ────────────────────
    rows = []
    use_vector = CHROMA_AVAILABLE

    if intent == "error_fix":
        scope_t = "e.is_active = 1"
        if feature_filter:
            scope_t += f" AND e.feature_id = {feature_filter}"
        elif domain_filter:
            scope_t += f" AND f.domain_id = {domain_filter}"
        rows = conn.execute(f"""
            SELECT DISTINCT e.id, e.name, e.type, e.menu_path, e.summary,
                   f.name as feature, d.name as domain
            FROM entries e
            JOIN features f ON e.feature_id = f.id
            JOIN domains  d ON f.domain_id  = d.id
            JOIN entry_versions ev ON ev.entry_id=e.id AND ev.is_current=1
            WHERE {scope_t} AND {kw_where} AND ev.source_type='ticket'
            ORDER BY ev.thumbs_up DESC, e.sort_order LIMIT ?
        """, kw_params + [limit]).fetchall()

        if rows:
            print(f"  [ticket] Found {len(rows)} ticket entries")
            use_vector = False
        else:
            print(f"  [ticket] No tickets found — trying vector/keyword")

    # ── Step B: Vector search ─────────────────────────────────────────────────
    chroma_version_map = {}

    if use_vector and not rows:
        print(f"  [vector] Searching ChromaDB...")
        candidates = vector_search(
            query=query,
            company_code=company_code,
            top_k=VECTOR_TOP_K,
            feature_name=feature_name_f,
            domain_name=domain_name_f,
            type_names=type_vec,
        )
        if candidates:
            print(f"  [vector] {len(candidates)} candidates -> reranking...")
            ranked = rerank(query, candidates, top_n=RERANK_TOP_N)
            for cand in ranked:
                vid = int(cand.get("version_id", 0))
                if not vid:
                    continue
                ver = conn.execute(
                    "SELECT * FROM entry_versions WHERE id=? AND is_current=1", (vid,)
                ).fetchone()
                if not ver:
                    continue
                eid = ver["entry_id"]
                row = conn.execute("""
                    SELECT e.id, e.name, e.type, e.menu_path, e.summary,
                           f.name as feature, d.name as domain
                    FROM entries e
                    JOIN features f ON e.feature_id=f.id
                    JOIN domains  d ON f.domain_id=d.id
                    WHERE e.id=?
                """, (eid,)).fetchone()
                if row and row["id"] not in [r["id"] for r in rows]:
                    rows.append(row)
                    chroma_version_map[row["id"]] = ver
        else:
            print(f"  [vector] No ChromaDB results — falling back to keyword")

    # ── Step C: Keyword SQL fallback ──────────────────────────────────────────
    if not rows:
        rows = kw_sql_search()
        if not rows and (feature_filter or type_sql):
            print(f"  [keyword] Relaxing filters...")
            rows = kw_sql_search(extra_type_sql="1=1")
        if not rows:
            print(f"  [keyword] Full fallback")
            rows = conn.execute(f"""
                SELECT e.id, e.name, e.type, e.menu_path, e.summary,
                       f.name as feature, d.name as domain
                FROM entries e
                JOIN features f ON e.feature_id=f.id
                JOIN domains  d ON f.domain_id=d.id
                WHERE e.is_active=1 AND {kw_where}
                ORDER BY e.sort_order LIMIT ?
            """, kw_params + [limit * 2]).fetchall()

        def score_row(row):
            nl, sl = (row["name"] or "").lower(), (row["summary"] or "").lower()
            s = sum(3 if kw in nl else (1 if kw in sl else 0) for kw in keywords)
            if topic_hint:
                t = topic_hint.lower()
                if t in nl:
                    s += 10
                if t in sl:
                    s += 5
                if t in (row["feature"] or "").lower():
                    s += 8
            return s

        rows = sorted(rows, key=score_row, reverse=True)
        best_s = score_row(rows[0]) if rows else 0
        min_s = max(1, best_s * 0.5) if best_s > 0 else 1
        rows = [r for r in rows if score_row(r) >= min_s]

    # ── Build results with version data ──────────────────────────────────────
    results = []
    seen = set()

    for row in rows:
        eid = row["id"]
        if eid in seen:
            continue
        seen.add(eid)

        version = chroma_version_map.get(eid)
        source = "global"

        if not version:
            if company_id:
                version = conn.execute("""
                    SELECT * FROM entry_versions
                    WHERE entry_id=? AND company_id=? AND is_current=1
                    ORDER BY version DESC LIMIT 1
                """, (eid, company_id)).fetchone()
                if version:
                    source = "company"
            if not version:
                version = conn.execute("""
                    SELECT * FROM entry_versions
                    WHERE entry_id=? AND company_id IS NULL AND is_current=1
                    ORDER BY version DESC LIMIT 1
                """, (eid,)).fetchone()

        if not version:
            continue

        is_flagged = bool(version["is_flagged"])
        flag_reason = version["flag_reason"] or ""

        # ── Flagged: ticket fallback ──────────────────────────────────────────
        if is_flagged:
            ticket_ver = conn.execute("""
                SELECT ev.*, e.id as eid, e.name as ename, e.type as etype,
                       e.menu_path as emenu, e.summary as esummary,
                       f.name as feature, d.name as domain
                FROM entry_versions ev
                JOIN entries e  ON ev.entry_id  = e.id
                JOIN features f ON e.feature_id = f.id
                JOIN domains  d ON f.domain_id  = d.id
                WHERE e.feature_id=(SELECT feature_id FROM entries WHERE id=?)
                AND ev.source_type='ticket' AND ev.is_current=1 AND e.is_active=1
                ORDER BY ev.thumbs_up DESC, ev.created_at DESC LIMIT 1
            """, (eid,)).fetchone()

            if ticket_ver:
                print(f"  [flag] '{row['name']}' flagged -> ticket: '{ticket_ver['ename']}'")
                doc_stem = (ticket_ver["source_ref"] or "").replace(".docx", "")
                company_seg = "_global" if source == "global" else f"clients/{company_code}"
                results.append({
                    "entry_id": ticket_ver["eid"],
                    "name": ticket_ver["ename"],
                    "type": ticket_ver["etype"],
                    "menu_path": ticket_ver["emenu"],
                    "summary": ticket_ver["esummary"],
                    "feature": ticket_ver["feature"],
                    "domain": ticket_ver["domain"],
                    "steps": json.loads(ticket_ver["steps"] or "[]"),
                    "notes": json.loads(ticket_ver["notes"] or "[]"),
                    "source": "ticket_fallback",
                    "version_id": ticket_ver["id"],
                    "img_folder": f"{company_seg}/{ticket_ver['domain']}/{doc_stem}",
                    "is_flagged": False,
                    "flag_reason": "",
                })
                if len(results) >= limit:
                    break
                continue
            else:
                print(f"  [flag] '{row['name']}' flagged, no ticket -> disclaimer")

        source_ref = version["source_ref"] or ""
        doc_stem = source_ref.replace(".docx", "").replace(".DOCX", "")
        company_seg = "_global" if source == "global" else f"clients/{company_code}"

        results.append({
            "entry_id": eid,
            "name": row["name"],
            "type": row["type"],
            "menu_path": row["menu_path"],
            "summary": row["summary"],
            "feature": row["feature"],
            "domain": row["domain"],
            "steps": json.loads(version["steps"] or "[]"),
            "notes": json.loads(version["notes"] or "[]"),
            "raw_content": version["raw_content"] or "",
            "source": source,
            "version_id": version["id"],
            "img_folder": f"{company_seg}/{row['domain']}/{doc_stem}",
            "is_flagged": is_flagged,
            "flag_reason": flag_reason,
        })

        if len(results) >= limit:
            break

    conn.close()
    return results


def format_knowledge_context(entries: list, target_step: int = None,
                             target_steps: list = None) -> str:
    if not entries:
        return ""
    parts = []
    for e in entries:
        part = f"### {e['domain']} > {e['feature']} > {e['name']}\nType: {e['type']}"

        steps_to_show = e["steps"]
        navigation_note = ""

        if target_steps is not None:
            steps_to_show = [s for s in e["steps"] if s.get("step_number") in target_steps]
            navigation_note = f"\n🎯 FOCUS: User requested steps {target_steps[0]} to {target_steps[-1]}."
        elif target_step is not None:
            steps_to_show = [s for s in e["steps"] if s.get("step_number") == target_step]
            if not steps_to_show:
                steps_to_show = e["steps"]
                navigation_note = f"\n⚠ NOTE: User asked for Step {target_step}, but not found. Showing full procedure."
            else:
                navigation_note = f"\n🎯 FOCUS: User requested detailed information for Step {target_step} ONLY."

        if navigation_note:
            part += navigation_note

        source = e.get("source", "")
        if source == "ticket_fallback":
            part += "\n📋 NOTE: This answer is based on a resolved support case (verified fix)."
        elif e.get("is_flagged"):
            part += "\n⚠ WARNING: This content has been flagged for review by users. Add a note in your response suggesting the user verify with support@globe3.com if unsure."
        if e["menu_path"]:
            part += f"\nMenu Path: {e['menu_path']}"
        if e["summary"]:
            part += f"\nSummary: {e['summary']}"

        raw_content = e.get("raw_content", "")
        if raw_content and not target_step and not target_steps:
            tagged = re.sub(
                r'!\[[^\]]*\]\(([^)]+)\)',
                lambda m: f"[IMG:{m.group(1)}]" if not m.group(1).startswith('data:') else '',
                raw_content
            )
            part += f"\nContent:\n{tagged[:5000]}"
        elif steps_to_show:
            part += "\nSteps:"
            for s in steps_to_show[:8]:
                action = s.get("action", "")[:80]
                desc = s.get("description", "")[:200]
                part += f"\n  {s.get('step_number', '')}. {action} — {desc}"
                if s.get("fields"):
                    part += f" [Fields: {', '.join(s['fields'][:5])}]"
                if s.get("image"):
                    part += f" [Image: {s['image']}]"

        text_notes = [n for n in e.get("notes", []) if not str(n).lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp"))]
        if text_notes:
            part += "\nNotes:\n" + "\n".join(f"  • {n[:120]}" for n in text_notes[:3])

        parts.append(part)
    return "\n\n---\n\n".join(parts)
