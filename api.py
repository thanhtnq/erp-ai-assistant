"""
Globe3 ERP AI Assistant — API Server V2
- ROLE.md based system prompt
- 4-tier knowledge DB (SQLite)
- User preferences (language, response length)
- Per-company knowledge (global + company-specific)
- SSE streaming with incremental JSON parsing
- Feedback loop with auto-flagging
- Context-aware query rewriting for follow-up questions
- Topic tracking for multi-turn conversations
"""

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from google import genai
from google.genai import types as genai_types
from tqdm import tqdm

import asyncio, json, re, os, sqlite3, urllib.request, subprocess, sys, threading
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# ─── Config ─────────────────────────────────────────────────────────────────

KNOWLEDGE_DB    = "./data/erp_knowledge.db"
CHAT_DB         = "./data/chat_history.db"
ROLE_MD         = "./ROLE.md"
IMAGES_DIR      = "./document_images"
LLM_MODEL       = "gemini-2.5-flash"
API_KEY         = os.getenv("CHAT_API_KEY", "erp-ai-secret-key-change-me")
MAX_ENTRIES     = 5
try:
    from ingest.ingest_config import GEMINI_API_KEY
except ImportError:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
SKILLS_URL           = os.getenv("SKILLS_SERVER_URL", "http://localhost:3001")
SCHEDULER_STATE_FILE = Path("./schedule/scheduler_state.json")
INGEST_DIR           = Path("./ingest")

# ── Vector search + reranker (optional — graceful fallback if not installed) ──
try:
    from embedding_helper import (
        vector_search, rerank, get_reranker, CHROMA_AVAILABLE,
    )
    from ingest.ingest_config import VECTOR_TOP_K, RERANK_TOP_N
    if CHROMA_AVAILABLE:
        get_reranker()   # pre-load at startup to avoid cold start on first query
        print("[OK] Vector search + reranker ready")
    else:
        print("[--] ChromaDB not available — using keyword search only")
except ImportError:
    CHROMA_AVAILABLE = False
    VECTOR_TOP_K     = 20
    RERANK_TOP_N     = 3
    def vector_search(*a, **kw): return []
    def rerank(_q, c, top_n=3): return c[:top_n]
    print("[--] embedding_helper not found — using keyword search only")

app = FastAPI(title="Globe3 ERP AI Assistant V2")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

if os.path.exists(IMAGES_DIR):
    app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

# ─── Auth ─────────────────────────────────────────────────────────────────────

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(key: str = Depends(api_key_header)):
    if key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    return key

# ─── LLM ──────────────────────────────────────────────────────────────────────

_gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# ─── ROLE.md ──────────────────────────────────────────────────────────────────

def load_role_md() -> str:
    try:
        return Path(ROLE_MD).read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"[WARN] ROLE.md not found at {ROLE_MD}")
        return "You are a helpful ERP assistant for Globe3 ERP by TNO Systems Pte Ltd."

ROLE_CONTENT = load_role_md()
print(f"[OK] ROLE.md loaded ({len(ROLE_CONTENT)} chars)")

# ─── Knowledge DB Helpers ─────────────────────────────────────────────────────

def get_knowledge_conn():
    conn = sqlite3.connect(KNOWLEDGE_DB)
    conn.row_factory = sqlite3.Row
    return conn


def get_company_id_from_code(conn, company_code: str):
    if not company_code:
        return None
    row = conn.execute("SELECT id FROM companies WHERE code = ?", (company_code,)).fetchone()
    return row["id"] if row else None


# ─── Intent Detection ─────────────────────────────────────────────────────────

# Compiled once at module load — matches ERP document numbers and ticket refs
_DOC_NUMBER_RE = re.compile(
    r'\b(soe|soc|sal_inv|inv|sal_quo|quo|sal_cn|cn|stk_do|do|stk_doc|po|grn|prj)[_\- ]?\d+\b'
    r'|#\s*\d{3,}',
    re.IGNORECASE,
)

def detect_intent(query: str) -> str:
    """
    Detect user intent from query to guide search strategy.
    Returns: 'data_query' | 'error_fix' | 'procedure' | 'faq' | 'reference' | 'any'

    data_query fires first — it routes to live ERP database, not the knowledge base.
    """
    q = query.lower()

    # ── Layer 0: Guard — strong procedural signals skip data_query entirely ────
    # "how to", "cách" etc. signal a procedure request, not a data lookup.
    PROCEDURAL_GUARD = {
        "how to", "how do i", "how do we", "steps to", "guide to",
        "cách", "hướng dẫn", "làm thế nào", "làm sao",
    }
    _has_procedural_guard = any(kw in q for kw in PROCEDURAL_GUARD)

    if not _has_procedural_guard:

        # ── Layer 1: Document number regex — highest confidence ────────────────
        # Matches: SOE00123, PO-001, INV-2024-05, DO001, GRN 123, #12345
        if _DOC_NUMBER_RE.search(query):
            return "data_query"

        # ── Layer 2: Standalone live-data keywords (no entity needed) ──────────
        STRONG_DATA_KW = {
            # Inventory
            "tồn kho", "tồn hàng", "hàng tồn", "kiểm tra tồn",
            "stock on hand", "available stock", "current stock", "stock level",
            # AR / AP
            "công nợ", "dư nợ", "ar balance", "ap balance",
            "accounts receivable", "accounts payable",
            "chưa thanh toán", "quá hạn thanh toán",
            "overdue invoice", "outstanding invoice", "outstanding balance",
            "ar aging", "ap aging", "aging report", "tuổi nợ",
            # Revenue / KPI
            "doanh thu", "doanh số", "revenue", "sales amount", "total sales",
            "top khách hàng", "top customer", "top clients",
            "top sản phẩm", "top product", "top item",
            "top nhân viên", "top salesperson", "top staff",
            "best selling", "hàng bán chạy",
            # Approvals / workflow
            "chờ duyệt", "chứng từ chờ", "pending approval", "awaiting approval",
            "cần phê duyệt", "approval queue",
            # CRM tickets
            "ticket của tôi", "my tickets", "my open ticket",
            "ticket đang mở", "open ticket", "pending ticket",
        }
        for kw in STRONG_DATA_KW:
            if kw in q:
                return "data_query"

        # ── Layer 3: Analytical signal + ERP entity ────────────────────────────
        # Both must be present together (e.g. "total orders this month")
        ANALYTICAL_KW = {
            # Quantity / aggregation
            "how many", "how much", "bao nhiêu", "mấy",
            "total", "tổng", "tổng cộng", "tổng số",
            "count", "đếm", "số lượng", "số lần",
            "sum", "average", "avg", "trung bình",
            "highest", "lowest", "largest", "smallest",
            "most", "least", "best", "worst",
            "top 5", "top 10", "top 3", "top 20",
            # Reporting / analysis
            "report", "báo cáo", "phân tích", "thống kê",
            "summary", "tổng hợp", "breakdown", "chi tiết theo",
            "trend", "xu hướng", "so sánh", "compare",
            # Time context (signals live data, not procedure)
            "this month", "tháng này", "last month", "tháng trước",
            "this year", "năm nay", "last year", "năm trước",
            "year to date", "ytd", "this quarter", "quý này",
            "today", "hôm nay", "this week", "tuần này", "last week",
            "q1", "q2", "q3", "q4",
        }
        ERP_ENTITY_KW = {
            # Sales
            "sales order", "đơn hàng", "đơn bán",
            "sales invoice", "hóa đơn bán", "invoice",
            "sales confirmation", "so confirmation",
            "quotation", "báo giá", "sales quote",
            "delivery", "phiếu xuất", "delivery order",
            "credit note", "giấy báo có",
            # Purchase
            "purchase order", "đơn mua", "po",
            "purchase invoice", "hóa đơn mua",
            "goods receipt", "phiếu nhập", "grn",
            # Parties
            "customer", "khách hàng", "client",
            "vendor", "supplier", "nhà cung cấp",
            "salesperson", "nhân viên bán hàng", "sales staff",
            # Products
            "product", "sản phẩm", "item", "hàng hóa",
            "brand", "thương hiệu", "category", "danh mục",
            # Warehouse
            "stock", "kho", "inventory", "warehouse",
            # Finance
            "payment", "thanh toán", "receipt", "bank",
        }
        _has_analytical = any(kw in q for kw in ANALYTICAL_KW)
        _has_entity     = any(kw in q for kw in ERP_ENTITY_KW)
        if _has_analytical and _has_entity:
            return "data_query"

        # ── Layer 4: Retrieval verb + ERP entity ───────────────────────────────
        # "show me all invoices", "list customers", "find order SOE..."
        # Guard already excludes "show me how to..." via PROCEDURAL_GUARD above.
        RETRIEVAL_VERB_KW = {
            # English
            "show me", "show all", "show the", "show my",
            "list all", "list the", "list my",
            "find all", "find the", "find me",
            "get all", "get the", "get me", "fetch",
            "display", "pull up", "look up", "lookup",
            "search for", "give me",
            # Vietnamese
            "xem", "xem tất cả", "xem các",
            "liệt kê", "lấy", "lấy danh sách",
            "tra cứu", "tìm kiếm đơn", "tìm hóa đơn",
            "cho tôi xem", "cho biết",
        }
        _has_retrieval = any(kw in q for kw in RETRIEVAL_VERB_KW)
        if _has_retrieval and _has_entity:
            return "data_query"

    # ── Existing intents (RAG knowledge base) ─────────────────────────────────

    # Error / cannot / troubleshoot signals
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
        # Vietnamese
        "không thể", "không được", "lỗi", "báo lỗi", "bị lỗi",
        "không hoạt động", "không chạy", "bị kẹt", "sự cố",
        "không tìm thấy", "không hiển thị", "không in được",
    }
    for kw in ERROR_KEYWORDS:
        if kw in q:
            return "error_fix"

    # FAQ / explanation signals
    FAQ_KEYWORDS = {
        "what is", "what are", "what does", "what do",
        "why is", "why are", "why does", "why do",
        "when is", "when are", "when do", "when should",
        "who is", "who are", "who should",
        "explain", "meaning of", "definition", "define",
        "difference between", "differ", " vs ", "versus",
        "what's the", "whats the", "how does", "how is", "how are",
        "purpose of", "reason for", "benefit of",
        # Vietnamese
        "là gì", "nghĩa là", "tại sao", "khi nào",
        "giải thích", "khác nhau", "so sánh",
    }
    for kw in FAQ_KEYWORDS:
        if kw in q:
            return "faq"

    # Reference / config / field signals
    REFERENCE_KEYWORDS = {
        "list of", "types of", "options for", "values for",
        "field", "fields", "column", "columns", "parameter",
        "setting", "settings", "configuration", "configure",
        "status", "statuses", "code", "codes", "report", "format",
        # Vietnamese
        "danh sách", "loại", "cài đặt", "cấu hình", "trường",
    }
    for kw in REFERENCE_KEYWORDS:
        if kw in q:
            return "reference"

    # Procedure / how-to signals
    PROCEDURE_KEYWORDS = {
        "how to", "how do i", "steps to", "guide to",
        "create", "add", "enter", "input", "fill",
        "setup", "set up", "install", "process", "procedure",
        "submit", "approve", "post", "confirm", "issue",
        "revise", "edit", "update", "modify", "change",
        "print", "generate", "export", "import",
        "cancel", "void", "delete", "remove",
        # Vietnamese
        "cách", "hướng dẫn", "tạo", "thêm", "nhập",
        "chỉnh sửa", "xóa", "in", "xuất",
    }
    for kw in PROCEDURE_KEYWORDS:
        if kw in q:
            return "procedure"

    return "any"


def build_chart_suggestion(query: str) -> dict | None:
    """
    Return a reusable chart suggestion payload for ranked/report-style answers.
    The frontend owns chart rendering; this event is intentionally generic so
    report endpoints can emit the same shape later.
    """
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


# ─── Image Map Helper ────────────────────────────────────────────────────────

_RE_IMG_REF = re.compile(r'!\[[^\]]*\]\(([^)]+)\)')


def _build_image_map(raw_content: str, img_folder: str) -> dict:
    """Map step_number → img_folder/filename using positional ordering.

    Collects all images from raw_content in document order, then assigns
    image N to step N. This is more robust than step-based heuristics because:
    - ERP manuals mix numbered lists, bold fields, and prose unpredictably
    - The LLM generates steps in the same top-to-bottom order as the document
    - Positional matching survives numbering conflicts (sub-lists vs main steps)
    """
    images = []
    for line in raw_content.split('\n'):
        m = _RE_IMG_REF.search(line.strip())
        if m:
            fname = m.group(1)
            if fname and not fname.startswith('data:'):
                images.append(f"{img_folder}/{fname}")
    return {i + 1: path for i, path in enumerate(images)}


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

    conn       = get_knowledge_conn()
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
        domain_filter  = best_feat["domain_id"]
        feature_name_f = best_feat["name"]
        domain_name_f  = best_feat["domain"]
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
        if feature_filter: scope_t += f" AND e.feature_id = {feature_filter}"
        elif domain_filter: scope_t += f" AND f.domain_id = {domain_filter}"
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
    chroma_version_map = {}   # version_id → full row data for later lookup

    if use_vector and not rows:
        print(f"  [vector] Searching ChromaDB...")
        candidates = vector_search(
            query        = query,
            company_code = company_code,
            top_k        = VECTOR_TOP_K,
            feature_name = feature_name_f,
            domain_name  = domain_name_f,
            type_names   = type_vec,
        )
        if candidates:
            print(f"  [vector] {len(candidates)} candidates -> reranking...")
            ranked = rerank(query, candidates, top_n=RERANK_TOP_N)
            # Load SQLite rows for reranked results
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
            rows = kw_sql_search(extra_type_sql="1=1")   # relax type filter
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

        # Score and filter keyword results
        def score_row(row):
            nl, sl = (row["name"] or "").lower(), (row["summary"] or "").lower()
            s = sum(3 if kw in nl else (1 if kw in sl else 0) for kw in keywords)
            if topic_hint:
                t = topic_hint.lower()
                if t in nl: s += 10
                if t in sl: s += 5
                if t in (row["feature"] or "").lower(): s += 8
            return s
        rows     = sorted(rows, key=score_row, reverse=True)
        best_s   = score_row(rows[0]) if rows else 0
        min_s    = max(1, best_s * 0.5) if best_s > 0 else 1
        rows     = [r for r in rows if score_row(r) >= min_s]

    # ── Build results with version data ──────────────────────────────────────
    results = []
    seen    = set()

    for row in rows:
        eid = row["id"]
        if eid in seen:
            continue
        seen.add(eid)

        # Use pre-fetched version from vector path if available
        version = chroma_version_map.get(eid)
        source  = "global"

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

        is_flagged  = bool(version["is_flagged"])
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
                doc_stem    = (ticket_ver["source_ref"] or "").replace(".docx","")
                company_seg = "_global" if source == "global" else f"clients/{company_code}"
                results.append({
                    "entry_id":    ticket_ver["eid"],
                    "name":        ticket_ver["ename"],
                    "type":        ticket_ver["etype"],
                    "menu_path":   ticket_ver["emenu"],
                    "summary":     ticket_ver["esummary"],
                    "feature":     ticket_ver["feature"],
                    "domain":      ticket_ver["domain"],
                    "steps":       json.loads(ticket_ver["steps"] or "[]"),
                    "notes":       json.loads(ticket_ver["notes"] or "[]"),
                    "source":      "ticket_fallback",
                    "version_id":  ticket_ver["id"],
                    "img_folder":  f"{company_seg}/{ticket_ver['domain']}/{doc_stem}",
                    "is_flagged":  False,
                    "flag_reason": "",
                })
                if len(results) >= limit:
                    break
                continue
            else:
                print(f"  [flag] '{row['name']}' flagged, no ticket -> disclaimer")

        source_ref  = version["source_ref"] or ""
        doc_stem    = source_ref.replace(".docx","").replace(".DOCX","")
        company_seg = "_global" if source == "global" else f"clients/{company_code}"

        results.append({
            "entry_id":    eid,
            "name":        row["name"],
            "type":        row["type"],
            "menu_path":   row["menu_path"],
            "summary":     row["summary"],
            "feature":     row["feature"],
            "domain":      row["domain"],
            "steps":       json.loads(version["steps"] or "[]"),
            "notes":       json.loads(version["notes"] or "[]"),
            "raw_content": version["raw_content"] or "",
            "source":      source,
            "version_id":  version["id"],
            "img_folder":  f"{company_seg}/{row['domain']}/{doc_stem}",
            "is_flagged":  is_flagged,
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

        steps_to_show   = e["steps"]
        navigation_note = ""

        if target_steps is not None:
            steps_to_show   = [s for s in e["steps"] if s.get("step_number") in target_steps]
            navigation_note = f"\n🎯 FOCUS: User requested steps {target_steps[0]} to {target_steps[-1]}."
        elif target_step is not None:
            steps_to_show = [s for s in e["steps"] if s.get("step_number") == target_step]
            if not steps_to_show:
                steps_to_show   = e["steps"]
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

        # Prefer raw_content markdown when available (new ingest format)
        raw_content = e.get("raw_content", "")
        if raw_content and not target_step and not target_steps:
            # Replace image markdown with explicit [IMG:filename] tags so LLM
            # can copy the exact filename into image_keyword for each step.
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
                desc   = s.get("description", "")[:200]
                part  += f"\n  {s.get('step_number', '')}. {action} — {desc}"
                if s.get("fields"):
                    part += f" [Fields: {', '.join(s['fields'][:5])}]"
                if s.get("image"):
                    part += f" [Image: {s['image']}]"

        # Only show notes when they are text (not image filenames from new ingest format)
        text_notes = [n for n in e.get("notes", []) if not str(n).lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp"))]
        if text_notes:
            part += "\nNotes:\n" + "\n".join(f"  • {n[:120]}" for n in text_notes[:3])

        parts.append(part)
    return "\n\n---\n\n".join(parts)

# ─── Chat DB & Preferences ────────────────────────────────────────────────────

def init_chat_db():
    conn = sqlite3.connect(CHAT_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    TEXT NOT NULL,
            company_id TEXT NOT NULL DEFAULT '',
            role       TEXT NOT NULL,
            content    TEXT NOT NULL,
            timestamp  TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_preferences (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      TEXT NOT NULL,
            company_id   TEXT NOT NULL DEFAULT '',
            language     TEXT NOT NULL DEFAULT 'auto',
            response_len TEXT NOT NULL DEFAULT 'normal',
            updated_at   TEXT NOT NULL,
            UNIQUE(user_id, company_id)
        )
    """)
    conn.commit()
    conn.close()

init_chat_db()


def get_chat_conn():
    conn = sqlite3.connect(CHAT_DB)
    conn.row_factory = sqlite3.Row
    return conn


def get_user_prefs(user_id: str, company_id: str) -> dict:
    conn = get_chat_conn()
    row  = conn.execute(
        "SELECT language, response_len FROM user_preferences WHERE user_id=? AND company_id=?",
        (user_id, company_id)
    ).fetchone()
    conn.close()
    return dict(row) if row else {"language": "auto", "response_len": "normal"}


def update_user_prefs(user_id: str, company_id: str, **kwargs):
    conn  = get_chat_conn()
    prefs = get_user_prefs(user_id, company_id)
    prefs.update(kwargs)
    conn.execute("""
        INSERT INTO user_preferences (user_id, company_id, language, response_len, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id, company_id) DO UPDATE SET
            language=excluded.language, response_len=excluded.response_len,
            updated_at=excluded.updated_at
    """, (user_id, company_id, prefs["language"], prefs["response_len"],
          datetime.now().isoformat()))
    conn.commit()
    conn.close()


def detect_pref_change(text: str) -> dict:
    t      = text.lower()
    changes = {}
    if any(p in t for p in ["reply in vietnamese", "trả lời tiếng việt", "dùng tiếng việt"]):
        changes["language"] = "vi"
    elif any(p in t for p in ["reply in english", "answer in english", "use english"]):
        changes["language"] = "en"
    if any(p in t for p in ["keep it short", "shorter", "be brief", "ngắn gọn", "ngắn thôi"]):
        changes["response_len"] = "short"
    elif any(p in t for p in ["more detail", "detailed", "explain more", "chi tiết hơn"]):
        changes["response_len"] = "detailed"
    return changes


def get_history(user_id: str, company_id: str, limit: int = 10) -> list:
    conn = get_chat_conn()
    rows = conn.execute("""
        SELECT role, content, timestamp FROM chat_history
        WHERE user_id=? AND company_id=?
        ORDER BY id DESC LIMIT ?
    """, (user_id, company_id, limit)).fetchall()
    conn.close()
    return list(reversed(rows))


def save_message(user_id: str, company_id: str, role: str, content: str):
    conn = get_chat_conn()
    conn.execute("""
        INSERT INTO chat_history (user_id, company_id, role, content, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, company_id, role, content, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def format_history(rows: list) -> str:
    if not rows:
        return "No previous conversation."
    # Tăng từ 300 lên 800 ký tự để giữ lại menu path và topic
    return "\n".join([
        f"{'User' if r['role']=='user' else 'Assistant'}: {r['content'][:800]}"
        for r in rows
    ])

# ─── Query Rewriter ───────────────────────────────────────────────────────────

_FOLLOWUP_RE = re.compile(
    r'\b(step\s*\d+|bước\s*\d+|more\s+detail|explain\s+more|tell\s+me\s+more'
    r'|what\s+about\s+(that|this|it)|how\s+about\s+(that|this|it)'
    r'|and\s+then|after\s+that|what\s+next|what\s+if'
    r'|chi\s+tiết|giải\s+thích\s+thêm|tiếp\s+theo|sau\s+đó'
    r'|tại\s+sao|why\s+is\s+that|what\s+does\s+that\s+mean'
    r'|can\s+you\s+elaborate|go\s+deeper|expand\s+on'
    r'|hơn\s+nữa|ngoài\s+ra|ví\s+dụ|for\s+example)\b',
    re.IGNORECASE
)

def _is_short(text: str) -> bool:
    return len(text.split()) <= 6

def _extract_last_user_topic(history_text: str) -> str:
    lines = history_text.splitlines()
    for line in reversed(lines):
        if line.startswith("User:"):
            topic = line[5:].strip()
            for skip in ["how", "to", "can", "i", "you", "please", "what", "is", "the", "a", "an"]:
                topic = re.sub(rf'\b{skip}\b', '', topic, flags=re.IGNORECASE)
            return " ".join(topic.split())[:80]
    return ""


# ─── Navigation Patterns ──────────────────────────────────────────────────────

_STEP_RE = re.compile(r'(?:step|bước)\s*(\d+(?:\.\d+)?)', re.IGNORECASE)

_NEXT_STEP_RE = re.compile(
    r'\b(next\s*(step|one)?|tiếp\s*(theo)?|sau\s*(đó)?|what\s*(about)?\s*next|'
    r'and\s*then|move\s*on|proceed|continue|following|sau\s*này|kế\s*tiếp|'
    r'bước\s*sau|gì\s*tiếp|tiếp\s*tục)\b',
    re.IGNORECASE
)

_PREV_STEP_RE = re.compile(
    r'\b(previous|prior|before\s*(that)?|go\s*back|back\s*to|earlier|'
    r'trước\s*(đó)?|quay\s*lại|lùi|bước\s*trước|phía\s*trước|trở\s*lại|'
    r'step\s*before|step\s*prior)\b',
    re.IGNORECASE
)

_FIRST_STEP_RE = re.compile(
    r'\b(first|start\s*over|from\s*beginning|beginning|restart|'
    r'đầu\s*tiên|bắt\s*đầu|từ\s*đầu|lại\s*từ|khởi\s*đầu|step\s*1|bước\s*1)\b',
    re.IGNORECASE
)

_LAST_STEP_RE = re.compile(
    r'\b(last|final|end|conclude|finish|'
    r'cuối\s*cùng|kết\s*thúc|sau\s*cùng|bước\s*cuối|chót)\b',
    re.IGNORECASE
)

_JUMP_STEP_RE = re.compile(
    r'\b(go\s*to|jump\s*to|skip\s*to|move\s*to|switch\s*to|'
    r'đến|chuyển\s*(sang)?|nhảy\s*(tới)?|qua\s*bước)\s*(?:step|bước)?\s*(\d+)',
    re.IGNORECASE
)

_REPEAT_STEP_RE = re.compile(
    r'\b(show\s*again|repeat|one\s*more\s*time|revisit|'
    r'lặp\s*lại|xem\s*lại|làm\s*lại|lại\s*một\s*lần|nhắc\s*lại)\b',
    re.IGNORECASE
)

_RANGE_STEP_RE = re.compile(
    r'\b(steps?|bước)\s*(\d+)\s*(?:to|through|until|đến|tới|sang)\s*(\d+)',
    re.IGNORECASE
)


def extract_last_step_from_history(history_text: str) -> tuple:
    if not history_text or history_text == "No previous conversation.":
        return None, None
    
    marker_pattern = re.compile(r'\[STEP:(\d+)\]')
    marker_matches = marker_pattern.findall(history_text)
    if marker_matches:
        last_step = int(marker_matches[-1])
        print(f"  [history] Found STEP marker: {last_step}")
        return last_step, None
    
    step_pattern = re.compile(r'(?:step|bước)\s*(\d+)', re.IGNORECASE)
    matches = step_pattern.findall(history_text)
    
    if matches:
        last_step = int(matches[-1])
        print(f"  [history] Last discussed step: {last_step}")
        return last_step, None
    
    number_pattern = re.compile(r'^\s*(\d+)\.\s+', re.MULTILINE)
    number_matches = number_pattern.findall(history_text)
    
    if number_matches:
        last_step = int(number_matches[-1])
        max_steps = len(number_matches)
        print(f"  [history] Last numbered step: {last_step}/{max_steps}")
        return last_step, max_steps
    
    return None, None


def extract_topic_from_history(history_text: str) -> str:
    """
    Extract the main ERP topic/feature from conversation history.
    Updated with more flexible patterns to catch topic from various formats.
    """
    if not history_text or history_text == "No previous conversation.":
        return ""
    
    # Pattern 1: Menu path with > separator (Sales > Sales Order > Creating)
    menu_pattern = re.compile(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*>\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*>\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)')
    
    # Pattern 2: "Sales Order" as standalone topic (common ERP terms)
    erp_topic_pattern = re.compile(
        r'\b(Sales\s*Order|Purchase\s*Order|Sales\s*Quotation|Purchase\s*Quotation|'
        r'Delivery\s*Order|Goods\s*Receipt|Invoice|Payment|Receipt|'
        r'Sales\s*Manager|Purchase\s*Manager|Inventory|Stock|'
        r'General\s*Ledger|Account\s*Receivable|Account\s*Payable|'
        r'Human\s*Resources|Employee|Payroll|Leave|'
        r'Project|Asset|Fleet|CRM|Customer|Vendor)\b',
        re.IGNORECASE
    )
    
    # Pattern 3: "Creating X" or "How to X"
    creating_pattern = re.compile(r'(?:Creating|Create|How\s*to|Procedure\s*for)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', re.IGNORECASE)
    
    lines = history_text.split('\n')
    assistant_lines = [l for l in lines if l.startswith('Assistant:')]
    
    # Check last 5 assistant messages (increased from 3)
    for line in reversed(assistant_lines[-5:]):
        # Try menu pattern first (most reliable)
        menu_match = menu_pattern.search(line)
        if menu_match:
            # Return the feature (second part of menu path)
            topic = menu_match.group(2).strip()
            print(f"  [topic] Extracted from menu path: {topic}")
            return topic
        
        # Try ERP topic pattern (catches standalone terms)
        topic_match = erp_topic_pattern.search(line)
        if topic_match:
            topic = topic_match.group(1).strip()
            print(f"  [topic] Extracted from ERP term: {topic}")
            return topic
        
        # Try creating pattern
        create_match = creating_pattern.search(line)
        if create_match:
            topic = create_match.group(1).strip()
            print(f"  [topic] Extracted from action: {topic}")
            return topic
    
    print(f"  [topic] No topic found in history")
    return ""


def rewrite_query(user_text: str, history_text: str) -> dict:
    result = {
        "query": user_text,
        "target_step": None,
        "target_steps": None,
        "is_followup": False,
        "navigation_type": None,
        "max_steps": None,
        "topic": ""
    }

    if not history_text or history_text == "No previous conversation.":
        step_match = _STEP_RE.search(user_text)
        if step_match:
            result["target_step"] = int(float(step_match.group(1)))
            result["navigation_type"] = "jump"
        return result

    text_lower = user_text.lower().strip()
    is_followup = bool(_FOLLOWUP_RE.search(text_lower)) or _is_short(user_text)
    
    if not is_followup:
        result["topic"] = extract_topic_from_history(history_text)
        return result

    result["is_followup"] = True
    
    last_step, max_steps = extract_last_step_from_history(history_text)
    result["max_steps"] = max_steps
    
    previous_topic = extract_topic_from_history(history_text)
    result["topic"] = previous_topic
    
    print(f"  [context] Last step: {last_step}, Max steps: {max_steps}, Topic: {previous_topic}")

    # ── PRIORITY 1: Explicit step number ─────────────────────────
    step_match = _STEP_RE.search(user_text)
    if step_match and not _JUMP_STEP_RE.search(user_text):
        explicit_step = int(float(step_match.group(1)))
        if not _NEXT_STEP_RE.search(user_text) and not _PREV_STEP_RE.search(user_text):
            result["target_step"] = explicit_step
            result["navigation_type"] = "jump"
            if previous_topic:
                result["query"] = f"{previous_topic} step {explicit_step}"
            else:
                result["query"] = f"step {explicit_step}"
            print(f"  [nav] Explicit step: {explicit_step} with topic: {previous_topic}")
            return result

    # ── PRIORITY 2: Jump to specific step ────────────────────────
    jump_match = _JUMP_STEP_RE.search(user_text)
    if jump_match:
        jump_step = int(jump_match.group(2))
        result["target_step"] = jump_step
        result["navigation_type"] = "jump"
        if previous_topic:
            result["query"] = f"{previous_topic} step {jump_step}"
        print(f"  [nav] Jump to step: {jump_step} with topic: {previous_topic}")
        return result

    # ── PRIORITY 3: Range query ──────────────────────────────────
    range_match = _RANGE_STEP_RE.search(user_text)
    if range_match:
        start_step = int(range_match.group(2))
        end_step = int(range_match.group(3))
        result["target_steps"] = list(range(start_step, end_step + 1))
        result["navigation_type"] = "range"
        if previous_topic:
            result["query"] = f"{previous_topic} steps {start_step} to {end_step}"
        print(f"  [nav] Range: {start_step} to {end_step} with topic: {previous_topic}")
        return result

    # ── PRIORITY 4: Navigation commands ──────────────────────────
    
    if _NEXT_STEP_RE.search(user_text):
        if last_step is not None:
            next_step = last_step + 1
            if max_steps and next_step > max_steps:
                next_step = max_steps
            result["target_step"] = next_step
            result["navigation_type"] = "next"
            if previous_topic:
                result["query"] = f"{previous_topic} step {next_step}"
            else:
                result["query"] = f"step {next_step}"
            print(f"  [nav] Next: {last_step} -> {next_step} with topic: {previous_topic}")
        return result

    if _PREV_STEP_RE.search(user_text):
        if last_step is not None:
            prev_step = max(1, last_step - 1)
            result["target_step"] = prev_step
            result["navigation_type"] = "prev"
            if previous_topic:
                result["query"] = f"{previous_topic} step {prev_step}"
            print(f"  [nav] Previous: {last_step} -> {prev_step} with topic: {previous_topic}")
        return result

    if _FIRST_STEP_RE.search(user_text):
        result["target_step"] = 1
        result["navigation_type"] = "first"
        if previous_topic:
            result["query"] = f"{previous_topic} step 1"
        print(f"  [nav] First step: 1 with topic: {previous_topic}")
        return result

    if _LAST_STEP_RE.search(user_text):
        if max_steps:
            result["target_step"] = max_steps
            result["navigation_type"] = "last"
            if previous_topic:
                result["query"] = f"{previous_topic} step {max_steps}"
        else:
            result["navigation_type"] = "last"
            if previous_topic:
                result["query"] = f"{previous_topic} final step"
        print(f"  [nav] Last step with topic: {previous_topic}")
        return result

    if _REPEAT_STEP_RE.search(user_text):
        if last_step is not None:
            result["target_step"] = last_step
            result["navigation_type"] = "repeat"
            if previous_topic:
                result["query"] = f"{previous_topic} step {last_step}"
            print(f"  [nav] Repeat step: {last_step} with topic: {previous_topic}")
        return result

    # ── PRIORITY 5: LLM rewrite with topic context ───────────────
    prompt = f"""You are a search-query rewriter for an ERP knowledge base assistant.
Conversation: {history_text}
User's follow-up: "{user_text}"
Previous Topic: {previous_topic or "Unknown"}

Task: Rewrite into ONE standalone search query (≤ 12 words) to retrieve the ERP documentation.

Rules:
- MUST include the previous topic "{previous_topic}" in the query if known
- Include step number if user is asking about a specific step
- Return ONLY the rewritten query.

Examples:
  Topic: "Sales Order" | Follow-up: "step 3" → "Sales Order step 3 procedure"
  Topic: "Purchase Invoice" | Follow-up: "next step" → "Purchase Invoice next step"
"""

    try:
        rewritten = _gemini_client.models.generate_content(model=LLM_MODEL, contents=prompt).text.strip().strip('"').strip("'")
        if 1 <= len(rewritten.split()) <= 20:
            result["query"] = rewritten
            print(f"  [rewrite] LLM: '{user_text}' -> '{rewritten}' (topic: {previous_topic})")
    except Exception as e:
        print(f"  [rewrite] LLM error: {e}")
        topic = _extract_last_user_topic(history_text)
        if topic:
            result["query"] = f"{topic} {user_text}"
        elif previous_topic:
            result["query"] = f"{previous_topic} {user_text}"

    return result

# ─── System Prompt ────────────────────────────────────────────────────────────

def build_system_prompt(prefs: dict) -> str:
    lang_map = {
        "auto": "Respond in the same language the user writes in.",
        "en":   "Always respond in English.",
        "vi":   "Luôn trả lời bằng tiếng Việt.",
    }
    len_map = {
        "short":    "Keep responses concise — max 5 steps, no lengthy explanations.",
        "normal":   "Provide complete step-by-step guidance.",
        "detailed": "Provide detailed explanations for each step, including field descriptions and tips.",
    }
    pref_block = f"""
---
## Active User Preferences
- {lang_map.get(prefs['language'], lang_map['auto'])}
- {len_map.get(prefs['response_len'], len_map['normal'])}
"""
    return ROLE_CONTENT + pref_block

# ─── Prompts ──────────────────────────────────────────────────────────────────

MAIN_PROMPT = """{system_prompt}

---
## Conversation History
{history}

---
## Relevant Knowledge Base Content
{context}

---
## User Question
{question}

---
## Navigation Context
Target Step: {target_step}
Target Steps Range: {target_steps}
Navigation Type: {navigation_type}

### NAVIGATION BEHAVIOR:

**IF Navigation Type = "next":**
- User wants the step AFTER the previously discussed step
- Use transitional language: "Now, let's move to Step {target_step}...", "Next, you'll need to..."
- Provide ONLY Step {target_step}

**IF Navigation Type = "prev":**
- User wants to go BACK to the previous step
- Use language like: "Let's go back to Step {target_step}...", "Previously, in Step {target_step}..."
- Provide ONLY Step {target_step}

**IF Navigation Type = "first":**
- User wants to START OVER from the beginning
- Use language like: "Let's start from Step 1...", "First, you need to..."
- Provide ONLY Step 1

**IF Navigation Type = "last":**
- User wants the FINAL step of the procedure
- Use language like: "Finally, in Step {target_step}...", "The last step is..."
- Provide ONLY Step {target_step}

**IF Navigation Type = "jump":**
- User wants to go to a SPECIFIC step
- Use language like: "Let's go to Step {target_step}...", "For Step {target_step}..."
- Provide ONLY Step {target_step}

**IF Navigation Type = "repeat":**
- User wants to SEE AGAIN the same step
- Use language like: "Let me show you Step {target_step} again...", "Here's Step {target_step} once more..."
- Provide ONLY Step {target_step} with same detail level

**IF Navigation Type = "range":**
- User wants MULTIPLE steps ({target_steps})
- Provide ALL steps in the range in order
- Use transitional language between steps

**IF Navigation Type = "None" (general query):**
- Provide the FULL procedure with all steps
- Each step should be concise (1-2 sentences)

---
## Response Format (STRICT JSON)
Return ONLY valid JSON with this exact structure:

{{
  "intro": "1-2 sentence warm introduction",
  "steps": [
    {{
      "step_number": 1,
      "text": "Clear instruction for this step (1-2 sentences)",
      "image_keyword": "exact filename from [IMG:filename] tag near this step, or empty string if none"
    }}
  ],
  "closing": "Friendly closing with offer to help more"
}}

CRITICAL RULES:
1. Return ONLY JSON - no markdown, no code blocks, no explanations outside JSON
2. step_number must match the Target Step(s) specified above
3. Escape all quotes in text values with backslash
4. Do NOT include newlines (\\n) inside text values - use spaces instead
5. steps array length:
   - Single step navigation: 1 step
   - Range navigation: multiple steps in range
   - General query: all steps in procedure
6. image_keyword: copy the EXACT filename from the nearest [IMG:filename] tag in the content for that step. If no image is near this step, use empty string "".

---
Answer based on the knowledge base content above.
"""

GREETING_PROMPT = """{system_prompt}

The user just opened the chat. Write a short warm greeting (1-2 sentences).
- No history: greet warmly and offer help
- Has history: welcome back, briefly mention their last topic

History: {history}

Reply in the same language as history (default English). Plain text only, no JSON:"""

# ─── Response Parser ──────────────────────────────────────────────────────────

def parse_response(raw: str) -> dict:
    raw = re.sub(r'^```json\s*|^```\s*|\s*```$', '', raw.strip(), flags=re.MULTILINE)
    
    try:
        d = json.loads(raw)
        return {
            "intro": d.get("intro", ""),
            "steps": d.get("steps", []),
            "closing": d.get("closing", "")
        }
    except:
        pass
    
    m = re.search(r'\{[\s\S]*"steps"[\s\S]*\}', raw)
    if m:
        try:
            d = json.loads(m.group())
            return {
                "intro": d.get("intro", ""),
                "steps": d.get("steps", []),
                "closing": d.get("closing", "")
            }
        except:
            pass
    
    steps = []
    step_pattern = re.compile(
        r'"step_number"\s*:\s*(\d+)\s*,\s*"text"\s*:\s*"((?:[^"\\]|\\.)*)"\s*,\s*"image_keyword"\s*:\s*"((?:[^"\\]|\\.)*)"'
    )
    for sm in step_pattern.finditer(raw):
        steps.append({
            "step_number": int(sm.group(1)),
            "text": sm.group(2).replace('\\"', '"').replace('\\n', '\n'),
            "image_keyword": sm.group(3)
        })
    
    intro_match = re.search(r'"intro"\s*:\s*"((?:[^"\\]|\\.)*)"', raw)
    closing_match = re.search(r'"closing"\s*:\s*"((?:[^"\\]|\\.)*)"', raw)
    
    return {
        "intro": intro_match.group(1).replace('\\"', '"').replace('\\n', '\n') if intro_match else "",
        "steps": steps,
        "closing": closing_match.group(1).replace('\\"', '"').replace('\\n', '\n') if closing_match else ""
    }

# ─── Skills / Data-Query Pipeline ────────────────────────────────────────────

def _http_get(url: str, timeout: int = 5) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read())

def _http_post(url: str, payload: dict, timeout: int = 30) -> dict:
    data = json.dumps(payload, ensure_ascii=False).encode()
    req  = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())

def get_skill_tools() -> list:
    """Return Ollama-format tool definitions from the skills server. Empty list if server is down."""
    try:
        return _http_get(f"{SKILLS_URL}/tools", timeout=3)
    except Exception as e:
        print(f"  [skills] Server unreachable: {e}")
        return []

def execute_skill_tool(name: str, arguments: dict, masterfn: str, companyfn: str) -> dict:
    """Call a skill tool on the Node.js server. Returns the tool result dict."""
    return _http_post(
        f"{SKILLS_URL}/execute",
        {"name": name, "arguments": arguments, "masterfn": masterfn, "companyfn": companyfn},
        timeout=15,
    )

def call_gemini_chat(messages: list, tools: list | None = None, timeout: int = 120, retries: int = 2) -> dict:
    """Call Gemini generateContent (supports tool calling). Returns Ollama-compatible message dict."""
    system_msg = next((m.get("content") for m in messages if m.get("role") == "system"), None)

    contents = [
        {"role": "model" if m["role"] == "assistant" else "user",
         "parts": [{"text": m.get("content") or ""}]}
        for m in messages
        if m.get("role") not in ("system",) and m.get("content") is not None
    ]

    config = genai_types.GenerateContentConfig(
        system_instruction=system_msg,
        tools=[genai_types.Tool(function_declarations=[
            genai_types.FunctionDeclaration(
                name=t["function"]["name"],
                description=t["function"].get("description", ""),
                parameters=t["function"].get("parameters", {}),
            )
            for t in tools
        ])] if tools else None,
    )

    last_err = None
    for attempt in range(1, retries + 2):
        try:
            resp = _gemini_client.models.generate_content(
                model=LLM_MODEL, contents=contents, config=config,
            )
            part = resp.candidates[0].content.parts[0]
            if part.function_call and part.function_call.name:
                fc = part.function_call
                return {"role": "assistant", "tool_calls": [{"function": {"name": fc.name, "arguments": dict(fc.args)}}]}
            return {"content": resp.text}
        except Exception as e:
            last_err = e
            print(f"  [gemini] Attempt {attempt}/{retries + 1}: {e}")
            if attempt > retries:
                raise
    raise last_err

# Prompt injected before the user query for data_query requests
_DATA_QUERY_SYSTEM = (
    "You are a Globe3 ERP data analyst with tools to query live sales, inventory, and CRM data.\n\n"
    "## CRITICAL — Tool calling rules\n"
    "- You MUST call a tool for EVERY user query. NEVER respond with text before calling a tool.\n"
    "- NEVER ask the user for clarification (document number, date, customer, etc.) before calling a tool.\n"
    "- For 'how many' / 'count' / 'total records' → call count_sales_documents IMMEDIATELY.\n"
    "  - If a year is mentioned (e.g. '2010'), set date_from='{year}-01-01' and date_to='{year+1}-01-01'.\n"
    "  - If document type is not explicitly named, infer from context (e.g. 'sales order' → tag_table_usage='sal_soe').\n"
    "- NEVER call get_sales_document when the user asked a counting question.\n\n"
    "## Document type → tag_table_usage mapping\n"
    "sales order / SO = sal_soe | SO confirmation = sal_soc | sales invoice = sal_inv | "
    "quotation = sal_quo | credit note = sal_cn | debit note = sal_dn | "
    "delivery order = stk_do | delivery confirmation = stk_doc | retail sales = sal_rta | "
    "pro forma invoice = sal_fma\n\n"
    "## Tool selection rules\n"
    "- 'how many' / 'count' / 'total records' → count_sales_documents\n"
    "- 'list' / 'show me' / 'find' → list_sales_documents\n"
    "- 'total amount' / 'sum' / 'average' / 'by customer' → aggregate_sales_documents\n"
    "- single document lookup by number → get_sales_document\n"
    "- NEVER call get_sales_document for count/quantity questions\n"
    "- ALWAYS include tag_table_usage in filters — infer it from the document type name above\n\n"
    "For top products, best selling products, revenue by product, product category, brand, "
    "retention, or churn-style analysis, use run_query.\n"
    "For stock-on-hand, current stock, overstock, slow-moving stock, reorder suggestions, "
    "items that need purchase, purchase receipts, goods received, supplier delivery, "
    "or late supplier delivery analysis, use run_inventory_query.\n"
    "For forecast, demand prediction, future sales, customer churn, retention risk, "
    "potential products, or product trend scoring, use run_scm_model so trained SCM "
    "artifacts are used when available.\n"
    "For broad SCM performance summaries or SCM overview over a period, use get_scm_overview.\n"
    "For internet/social/online market trend questions, use analyze_market_trends and never invent trends.\n"
    "For run_query SQL, use PostgreSQL SELECT only, use table aliases for joins, "
    "filter voided records with tag_void_yn = 'n', and do not add masterfn/companyfn; "
    "the skills server injects scope automatically.\n\n"
    "## Live SQL schema for run_query\n"
    "scm_sal_main columns: uniquenum_pri, dnum_auto, dnum_reference, date_trans, party_code, "
    "party_desc, amount_local, amount_forex, curr_short_forex, staff_code, staff_desc, "
    "location_code, deptunit_code, deptunit_desc, tag_void_yn, tag_table_usage, masterfn, companyfn.\n"
    "scm_sal_data columns: uniquenum_pri, stkcode_code, stkcode_desc, stkcate_desc, brand_desc, "
    "qnty_total, price_unitrate_local, amount_local, amount_forex, party_code, party_desc, "
    "date_trans, tag_void_yn, tag_table_usage, masterfn, companyfn.\n"
    "Join sales header and lines with: FROM scm_sal_main m JOIN scm_sal_data d "
    "ON d.uniquenum_pri = m.uniquenum_pri AND d.tag_table_usage = m.tag_table_usage "
    "AND d.companyfn = m.companyfn.\n\n"
    "## Inventory / purchase SQL schema for run_inventory_query\n"
    "stk_code_main columns: uniquenum_pri, stkcode_code, stkcode_unique, stkcode_desc_english, "
    "stkcate_desc, brand_desc, uom_stk_code, stkm_qnty_total, level_min, level_max, "
    "level_reorder, level_slowdays, tag_active_yn, tag_void_yn, masterfn, companyfn. "
    "Use stkm_qnty_total for stock-on-hand, level_reorder/level_min for replenishment, "
    "and level_max for overstock.\n"
    "stk_code_data columns: uniquenum_pri, stkcode_code, stkcode_desc, location_code, "
    "party_code, party_desc, vendor_leadtime_days, amount_unitcost_local, tag_active_yn, "
    "tag_void_yn, masterfn, companyfn.\n"
    "scm_pur_main columns: uniquenum_pri, dnum_auto, date_trans, date_due, date_eta, "
    "date_delivery, party_code, party_desc, location_code, amount_local, amount_forex, "
    "tag_void_yn, tag_table_usage, masterfn, companyfn. Purchase document types: "
    "pur_po=Purchase Order, pur_poc=PO Confirmation, stk_grn/stk_gvn=Goods Received, pur_inv=Purchase Invoice.\n"
    "scm_pur_data columns: uniquenum_pri, uniquenum_uniq, date_trans, date_due, party_code, "
    "party_desc, stkcode_code, stkcode_unique, stkcode_desc, skucode_code, stkcate_desc, "
    "brand_desc, location_code, qnty_total, qnty_uomstk, bal_qnty_total, bal_qnty_uomstk, "
    "amount_local, price_unitrate_local, tag_void_yn, tag_table_usage, masterfn, companyfn.\n"
    "scm_stk_main/scm_stk_data are for stock transfers, adjustments, reclassifications, "
    "and assemblies; do not use them for Delivery Orders or Goods Received Notes.\n\n"
    "## Trained SCM model tool\n"
    "run_scm_model tasks: forecast uses sales_forecaster.pkl, churn uses churn_predictor.pkl, "
    "demand_forecast forecasts product/category demand from extracted product artifacts, "
    "product_trend uses product trend scoring. Always pass the original user question as query. "
    "If a trained artifact is missing, say training must be run for the current masterfn/companyfn scope.\n\n"
    "## SCM overview and market trend tools\n"
    "get_scm_overview returns sales, inventory, reorder, overstock, and late-supplier metrics with chart data. "
    "analyze_market_trends only uses configured external trend files; if not configured, clearly say external trend data is not available yet.\n\n"
    "## Follow-up handling\n"
    "If the current query is vague (e.g. 'show me', 'total', 'how many', 'records'), "
    "extract the document type and date/time filters from the conversation history "
    "and apply them to the current query automatically.\n\n"
    "## Column header aliases (ALWAYS use in tables — NEVER expose raw field names)\n"
    "dnum_auto=Document No. | dnum_reference=Reference No. | date_trans=Date | date_due=Due Date | "
    "party_code=Customer Code | party_desc=Customer | staff_code=Salesperson Code | staff_desc=Salesperson | "
    "amount_local=Amount (Local) | amount_forex=Amount | curr_short_forex=Currency | "
    "location_code=Location | deptunit_code=Dept. Code | deptunit_desc=Department | "
    "creditterm_desc=Payment Terms | delivtype_desc=Delivery Type | sendby_desc=Ship Method | "
    "tag_table_usage=Doc Type | COUNT(*)=Count | count=Count | "
    "SUM(amount_forex)=Total Amount | SUM(amount_local)=Total (Local)\n\n"
    "## Output rules\n"
    "- NEVER show raw snake_case field names as table headers or in plain-text results.\n"
    "- NEVER include in output: masterfn, companyfn, uniquenum_pri, uniquenum_uniq, "
    "tag_void_yn, tag_closedmain_yn, party_unique, staff_unique.\n"
    "- For aggregate/group-by results, rename the group-by column using the alias above.\n"
    "- Unknown fields: use clean Title Case (e.g. salestaxpct → Tax %).\n"
    "- Present multiple-row results as a concise markdown table. "
    "If tool results contain a charts array, include one matching ```g3chart JSON block. "
    "Never invent data. Respond in the same language the user used."
)

def _lang_code(lang: str) -> str:
    """Map cookie.cooklang value to short code ('en' or 'vi')."""
    m = {"english": "en", "vietnamese": "vi", "viet": "vi", "en": "en", "vi": "vi"}
    return m.get((lang or "").lower().strip(), "en")


def is_scm_training_query(query: str) -> bool:
    """Queries answered from precomputed SCM training/analytics artifacts."""
    q = (query or "").lower()
    keywords = {
        "churn", "retention", "customer segment", "customer segments",
        "forecast", "predict", "projection", "next 30 days", "next 90 days",
        "potential product", "potential products", "top products", "top 10 products",
        "bestselling products", "best selling products",
        "revenue for", "revenue by month", "revenue by date",
        "xu hướng", "triển vọng", "tiềm năng", "dự báo", "doanh thu tháng",
    }
    return any(kw in q for kw in keywords)


def run_scm_training_query(query: str, masterfn: str, companyfn: str, lang: str = "en") -> str:
    """Answer from SCM training artifacts for the chat request scope."""
    if not masterfn:
        return (
            "Không tìm thấy `masterfn` từ phiên chat, nên chưa thể đọc dữ liệu training đúng client."
            if lang == "vi"
            else "No `masterfn` was provided by the chat session, so I cannot load the correct training data scope."
        )

    try:
        from scm_training.query.ai_query_interface import AIQueryInterface

        interface = AIQueryInterface(masterfn=masterfn, companyfn=companyfn or None)
        return interface.format_response(interface.process_query(query, {
            "masterfn": masterfn,
            "companyfn": companyfn,
        }))
    except FileNotFoundError:
        scope = f"masterfn={masterfn}" + (f", companyfn={companyfn}" if companyfn else "")
        return (
            f"Chưa có dữ liệu SCM training cho scope `{scope}`. Hãy chạy extract/train cho scope này trước."
            if lang == "vi"
            else f"No SCM training data exists for `{scope}` yet. Run extract/train for this scope first."
        )
    except Exception as e:
        return (
            f"Không thể đọc dữ liệu SCM training: {e}"
            if lang == "vi"
            else f"Could not read SCM training data: {e}"
        )


def run_data_query(
    query: str,
    history_text: str,
    masterfn: str,
    companyfn: str,
    lang: str = "en",
) -> str:
    """
    Full data_query pipeline:
      1. Fetch tool definitions from skills server
      2. Call Ollama with tools → LLM picks the right tool
      3. Execute chosen tool(s) via skills server
      4. Call Ollama again with tool results → get formatted answer
    Returns markdown string ready to stream to the frontend.
    """
    tools = get_skill_tools()
    if not tools:
        return (
            "⚠️ Skills server không khả dụng. "
            "Vui lòng kiểm tra `node skills/server.js` đang chạy trên port 3001."
        )

    messages: list[dict] = [{"role": "system", "content": _DATA_QUERY_SYSTEM}]
    if history_text:
        messages.append({
            "role": "user",
            "content": f"[Conversation history — use for context]\n{history_text}",
        })
    messages.append({"role": "user", "content": query})

    # ── Round 1: LLM chooses tool ─────────────────────────────────────────────
    print(f"  [data_query] Sending to Gemini with {len(tools)} tools...")
    msg = call_gemini_chat(messages, tools=tools)

    tool_calls = msg.get("tool_calls", [])
    if not tool_calls:
        # LLM answered directly without a tool (e.g. clarification question)
        return msg.get("content", "Không thể xử lý câu hỏi này.")

    # ── Round 2: Execute each tool call ──────────────────────────────────────
    messages.append(msg)  # add assistant turn that contains tool_calls

    for tc in tool_calls:
        fn        = tc.get("function", {})
        tool_name = fn.get("name", "")
        args      = fn.get("arguments", {})
        if isinstance(args, str):          # Ollama sometimes returns JSON string
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                args = {}

        print(f"  [data_query] -> {tool_name}({args})")
        try:
            result = execute_skill_tool(tool_name, args, masterfn, companyfn)
        except Exception as e:
            result = {"ok": False, "error": str(e)}

        messages.append({
            "role":    "tool",
            "content": json.dumps(result.get("result", result), ensure_ascii=False),
        })

    # ── Round 3: LLM formats the final answer ─────────────────────────────────
    if lang == "vi":
        round3 = (
            "Dựa trên dữ liệu trả về, hãy viết phản hồi ngắn gọn và tự nhiên:\n"
            "- Nêu kết quả trong 1–2 câu (KHÔNG dùng bold label kiểu '**Tổng: 123**' nếu đã nêu trong câu).\n"
            "- Mọi số tiền PHẢI kèm mã tiền tệ phía sau (ví dụ: 66,197,143.79 SGD). "
            "Lấy mã tiền tệ từ trường curr_short_forex trong dữ liệu. Nếu có nhiều loại tiền, ghi rõ từng loại.\n"
            "- Nếu có nhiều dòng dữ liệu, thêm bảng markdown sau câu mở đầu.\n"
            "- Nếu kết quả count = 0, nêu thẳng (ví dụ: 'Không có đơn hàng nào trong năm 2010.'). KHÔNG hỏi thêm thông tin hay yêu cầu số chứng từ.\n"
            "- Để 1 dòng trống, rồi kết thúc bằng đúng 1 câu hỏi ngắn thân thiện gợi ý bước tiếp theo "
            "(ví dụ: 'Bạn có muốn xem chi tiết từng hóa đơn không? 😊'). KHÔNG dùng bullet list.\n"
            "Trả lời bằng tiếng Việt."
        )
    else:
        round3 = (
            "Based on the data, write a concise natural response:\n"
            "- State the result in 1–2 plain sentences (do NOT repeat data as a bold 'Label: value' if already stated).\n"
            "- ALL monetary amounts MUST include the currency code after the number "
            "(e.g. 66,197,143.79 SGD). Take the currency from the curr_short_forex field in the data. "
            "If multiple currencies exist, state each separately.\n"
            "- If there are multiple rows, add a markdown table after the opening sentence.\n"
            "- If the result shows count = 0, state it directly (e.g. 'There are 0 sales orders in 2010.'). Do NOT ask for document numbers or more information.\n"
            "- Leave one blank line, then end with exactly ONE short friendly question suggesting a next step "
            "(e.g. 'Would you like to see a breakdown by customer? 😊'). NO bullet list.\n"
            "Respond in English. Tone: friendly ERP assistant."
        )
    messages.append({"role": "user", "content": round3})
    final = call_gemini_chat(messages)
    return final.get("content", "Unable to format results.")

# ─── Models ──────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    user_id:      str
    company_id:   str = ""
    company_code: str = ""
    masterfn:     str = ""   # client scope  (cookie: cookmfnunique)
    companyfn:    str = ""   # entity scope  (cookie: cookcfnunique)
    lang:         str = ""   # UI language   (cookie: cooklang) — "english" | "vietnamese"
    text:         str

class GreetingRequest(BaseModel):
    user_id:      str
    company_id:   str = ""
    company_code: str = ""

class FeedbackRequest(BaseModel):
    user_id:          str
    company_id:       str = ""
    entry_version_id: int | None = None
    rating:           str          # 'up' | 'down'
    reason:           str = ""     # why not helpful (selected option)
    comment:          str = ""     # free-text comment from user
    query_text:       str = ""     # original question

class ScmTrainingRunRequest(BaseModel):
    admin_user_id: str = "admin"
    masterfn:      str
    companyfn:     str
    model:         str = "all"     # all | forecast | churn
    date_from:     str = ""
    date_to:       str = ""

def check_ambiguity(query: str, history_text: str, intent: str, lang: str) -> dict:
    """Returns {"ambiguous": bool, "question": str | None}. Fails open on any error."""
    prompt = (
        "You are deciding whether a user's question about Globe3 ERP is specific enough to answer.\n\n"
        "IMPORTANT CONTEXT: This is the Globe3 ERP assistant by TNO Systems. "
        "Every user is a Globe3 ERP user. NEVER treat questions as ambiguous just because they don't specify "
        "which ERP system — it is always Globe3 ERP. Terms like 'sales order', 'invoice', 'quotation', "
        "'delivery order', 'purchase order', 'credit note' always refer to Globe3 ERP modules.\n\n"
        f"Conversation history:\n{history_text}\n\n"
        f'Current question: "{query}"\n'
        f"Detected intent: {intent}\n\n"
        "A question is AMBIGUOUS only if:\n"
        '- Completely content-free: only "error", "không được", "lỗi", "it doesn\'t work" with zero other detail\n'
        '- References "it"/"that"/"cái đó"/"cái này" with no prior mention anywhere in history\n\n'
        "A question is CLEAR if:\n"
        "- Mentions any Globe3 ERP module, document type, feature, or menu (sales order, invoice, SO, DO, PO, etc.)\n"
        "- Is a how-to or procedure question, even if phrased informally or with grammar errors\n"
        "- History provides enough context to understand the topic\n"
        '- Examples that are CLEAR: "how create sales order", "tạo sales order", "cannot post invoice", '
        '"sales quotation step", "how do I void a DO", "delivery order error"\n\n'
        "Respond with JSON only (no explanation):\n"
        '{{"ambiguous": true or false, "question": "one short clarifying question in '
        f"{'Vietnamese' if lang == 'vi' else 'English'}\"" + ' or null}}'
    )
    try:
        msg = call_gemini_chat([{"role": "user", "content": prompt}], timeout=30, retries=0)
        content = msg.get("content", "").strip()
        if content.startswith("```"):
            content = re.sub(r"^```[a-z]*\n?", "", content)
            content = re.sub(r"\n?```$", "", content.strip())
        data = json.loads(content)
        return {"ambiguous": bool(data.get("ambiguous", False)), "question": data.get("question") or None}
    except Exception as e:
        print(f"  [ambiguity] check failed ({e}), defaulting to clear")
        return {"ambiguous": False, "question": None}

# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.post("/chat/stream")
async def chat_stream(q: ChatRequest, _key: str = Depends(verify_api_key)):
    history_rows  = get_history(q.user_id, q.company_id, limit=6)
    history_text  = format_history(history_rows)
    prefs         = get_user_prefs(q.user_id, q.company_id)

    changes = detect_pref_change(q.text)
    if changes:
        update_user_prefs(q.user_id, q.company_id, **changes)
        prefs.update(changes)
        print(f"  [prefs] Updated: {changes}")

    system_prompt = build_system_prompt(prefs)

    async def generate():
        yield f"event: status\ndata: {json.dumps({'text': 'Searching knowledge base...'})}\n\n"

        search_query = await asyncio.get_running_loop().run_in_executor(
            None, rewrite_query, q.text, history_text
        )

        topic_hint = search_query.get("topic", "")
        chart_suggestion = build_chart_suggestion(search_query.get("query") or q.text)

        # Detect intent — try original query first
        intent = detect_intent(q.text)

        # Follow-up queries lose entity keywords ("so what is the total amount?" has no ERP entity).
        # If the rewritten query resolves them (e.g. "total amount sales orders 2014"), use that intent.
        _rewritten_q = search_query["query"]
        if intent != "data_query" and search_query.get("is_followup") and _rewritten_q != q.text:
            intent_rewrite = detect_intent(_rewritten_q)
            if intent_rewrite == "data_query":
                intent = "data_query"
                print(f"  [intent] data_query via rewrite: '{_rewritten_q}'")

        # ── Data query branch: bypass RAG, call skills server ─────────────────
        if intent == "data_query":
            _lc        = _lang_code(q.lang)
            _status    = "Đang truy vấn dữ liệu ERP..." if _lc == "vi" else "Querying ERP data..."
            yield f"event: status\ndata: {json.dumps({'text': _status})}\n\n"
            _masterfn  = q.masterfn  or q.company_code or ""
            _companyfn = q.companyfn or q.company_id   or ""
            # Use rewritten query for follow-ups so LLM has full context (e.g. "total amount sales orders 2014")
            _data_query = _rewritten_q if search_query.get("is_followup") and _rewritten_q != q.text else q.text
            try:
                result_md = await asyncio.get_running_loop().run_in_executor(
                    None, run_data_query, _data_query, history_text, _masterfn, _companyfn, _lc
                )
            except (TimeoutError, OSError) as e:
                print(f"  [data_query] Timeout: {e}")
                result_md = (
                    "⚠️ The AI model took too long to respond. Please try again in a moment.\n\n"
                    "If this keeps happening, the model may be overloaded — wait 30 seconds and retry."
                ) if _lc != "vi" else (
                    "⚠️ Mô hình AI phản hồi quá chậm. Vui lòng thử lại sau giây lát.\n\n"
                    "Nếu lỗi tiếp tục xảy ra, hãy đợi 30 giây rồi thử lại."
                )
            # Split on last blank line → main content + closing question (mirrors RAG path structure)
            parts = result_md.rsplit('\n\n', 1)
            _intro_text   = parts[0].strip() if len(parts) == 2 else result_md.strip()
            _closing_text = parts[1].strip() if len(parts) == 2 else ""
            yield f"event: intro\ndata: {json.dumps({'text': _intro_text})}\n\n"
            if _closing_text:
                yield f"event: closing\ndata: {json.dumps({'text': _closing_text})}\n\n"
            if chart_suggestion:
                yield f"event: chart_suggestion\ndata: {json.dumps(chart_suggestion, ensure_ascii=False)}\n\n"
            save_message(q.user_id, q.company_id, "user",      q.text)
            save_message(q.user_id, q.company_id, "assistant", result_md)
            yield f"event: total\ndata: {json.dumps({'total': 0})}\n\n"
            yield f"event: meta\ndata: {json.dumps({'sources': [], 'version_ids': []})}\n\n"
            yield f"event: done\ndata: {{}}\n\n"
            return

        entries = search_knowledge(
            query        = search_query["query"],
            company_code = q.company_code or q.company_id,
            topic_hint   = topic_hint,
            intent       = intent,
        )

        if not entries and search_query["query"] != q.text:
            print(f"  [rewrite] No results for rewritten query, retrying with original")
            entries = search_knowledge(
                query        = q.text,
                company_code = q.company_code or q.company_id,
                topic_hint   = topic_hint,
                intent       = intent,
            )

        # ── Ambiguity check — only when search found nothing and no step navigation ──
        if not entries and not search_query.get("navigation_type"):
            _lc_check = _lang_code(q.lang)
            _amb = await asyncio.get_running_loop().run_in_executor(
                None, check_ambiguity, _rewritten_q, history_text, intent, _lc_check
            )
            if _amb["ambiguous"] and _amb["question"]:
                _q_text = _amb["question"]
                _status_amb = "Cần thêm thông tin..." if _lc_check == "vi" else "Need more information..."
                yield f"event: status\ndata: {json.dumps({'text': _status_amb})}\n\n"
                yield f"event: intro\ndata: {json.dumps({'text': _q_text})}\n\n"
                save_message(q.user_id, q.company_id, "user",      q.text)
                save_message(q.user_id, q.company_id, "assistant", _q_text)
                yield f"event: total\ndata: {json.dumps({'total': 0})}\n\n"
                yield f"event: meta\ndata: {json.dumps({'sources': [], 'version_ids': []})}\n\n"
                yield f"event: done\ndata: {{}}\n\n"
                return
        # ─────────────────────────────────────────────────────────────────────

        target_step     = search_query.get("target_step")
        target_steps    = search_query.get("target_steps")
        navigation_type = search_query.get("navigation_type")

        step_image_map = {}
        for e in entries:
            img_folder  = e.get("img_folder", "")
            raw_content = e.get("raw_content", "")
            if raw_content and img_folder:
                # Primary: parse raw_content markdown (positional, handles image-before/after-step)
                step_image_map.update(_build_image_map(raw_content, img_folder))
            elif img_folder:
                # Fallback: use SQLite steps data (ticket entries without raw_content)
                for s in e.get("steps", []):
                    step_num = s.get("step_number")
                    img_file = s.get("image")
                    if step_num and img_file:
                        step_image_map[step_num] = f"{img_folder}/{img_file}"

        # Filter to requested step range when navigating
        if target_step is not None:
            step_image_map = {k: v for k, v in step_image_map.items() if k == target_step}
        elif target_steps is not None:
            step_image_map = {k: v for k, v in step_image_map.items() if k in target_steps}

        print(f"  [img-map] Mapped {len(step_image_map)} images for steps: {sorted(step_image_map.keys())}")

        context = format_knowledge_context(entries, target_step=target_step, target_steps=target_steps)
        sources = [f"{e['domain']} > {e['feature']} > {e['name']}" for e in entries]
        ver_ids = [e["version_id"] for e in entries if e.get("version_id")]

        print(f"\n[search] original={q.text[:50]!r} | query={search_query['query'][:50]!r} -> {len(entries)} entries")
        for e in entries:
            print(f"  [{e['type']}] {e['domain']} > {e['feature']} > {e['name']} ({e['source']})")

        prompt_text = MAIN_PROMPT.format(
            system_prompt     = system_prompt,
            history           = history_text,
            context           = context or "No relevant content found in the knowledge base.",
            question          = q.text,
            target_step       = target_step if target_step else "None",
            target_steps      = target_steps if target_steps else "None",
            navigation_type   = navigation_type if navigation_type else "None"
        )

        yield f"event: status\ndata: {json.dumps({'text': 'Generating answer...'})}\n\n"

        import concurrent.futures
        from tqdm import tqdm

        loop  = asyncio.get_running_loop()
        queue = asyncio.Queue()
        DONE  = object()

        def stream_in_thread():
            try:
                stream_resp = _gemini_client.models.generate_content_stream(
                    model=LLM_MODEL,
                    contents=[{"role": "user", "parts": [{"text": prompt_text}]}],
                )
                with tqdm(desc="  LLM tokens", unit=" tok", ncols=60,
                          bar_format="{l_bar}{bar}| {n_fmt}{unit} [{elapsed}]") as pbar:
                    for chunk in stream_resp:
                        if chunk.text:
                            asyncio.run_coroutine_threadsafe(queue.put(chunk.text), loop).result(timeout=10)
                            pbar.update(1)
            except Exception as e:
                print(f"  [LLM thread error] {e}")
                asyncio.run_coroutine_threadsafe(queue.put(f"__ERROR__:{e}"), loop).result()
            finally:
                asyncio.run_coroutine_threadsafe(queue.put(DONE), loop).result()

        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        executor.submit(stream_in_thread)

        buffer       = ""
        intro_sent   = False
        closing_sent = False
        steps_sent   = []
        sent_images  = set()
        plain_lines  = []

        step_pattern = re.compile(
            r'"step_number"\s*:\s*(\d+)\s*,\s*"text"\s*:\s*"((?:[^"\\]|\\.)*)"\s*,\s*"image_keyword"\s*:\s*"((?:[^"\\]|\\.)*)"'
        )

        while True:
            token = await queue.get()
            if token is DONE:
                break
            if isinstance(token, str) and token.startswith("__ERROR__:"):
                print(f"  [LLM error] {token}")
                break

            buffer += token

            if not intro_sent:
                m = re.search(r'"intro"\s*:\s*"((?:[^"\\]|\\.)*)"', buffer)
                if m:
                    text = m.group(1).replace('\\"', '"').replace('\\n', '\n')
                    if text.strip():
                        yield f"event: intro\ndata: {json.dumps({'text': text})}\n\n"
                        plain_lines.append(text)
                    intro_sent = True

            for sm in step_pattern.finditer(buffer):
                step_num      = int(sm.group(1))
                step_text     = sm.group(2).replace('\\"', '"').replace('\\n', '\n')
                image_keyword = sm.group(3).replace('\\"', '"').strip()
                step_pos      = sm.start()

                if step_pos in [s["pos"] for s in steps_sent]:
                    continue

                # Primary: use LLM-assigned image_keyword (exact filename from [IMG:] tag)
                # Fallback: positional step_image_map
                image_file = None
                if image_keyword:
                    candidate = f"{entries[0].get('img_folder', '')}/{image_keyword}" if entries else None
                    if candidate and os.path.exists(f"./document_images/{candidate}"):
                        image_file = candidate
                    else:
                        print(f"  [WARN] image_keyword '{image_keyword}' not found, using positional fallback")
                if not image_file:
                    image_file = step_image_map.get(step_num)

                if image_file and not os.path.exists(f"./document_images/{image_file}"):
                    print(f"  [WARN] Image not found on disk: {image_file}")
                    image_file = None

                if image_file in sent_images:
                    image_file = None
                elif image_file:
                    sent_images.add(image_file)

                steps_sent.append({"pos": step_pos, "step_number": step_num, "text": step_text})
                plain_lines.append(f"{step_num}. {step_text}")
                
                _step_payload = json.dumps({
                    'index': len(steps_sent) - 1,
                    'step_number': step_num,
                    'text': step_text,
                    'image': image_file,
                    'total': -1
                })
                yield f"event: step\ndata: {_step_payload}\n\n"

            if not closing_sent:
                cm = re.search(r'"closing"\s*:\s*"((?:[^"\\]|\\.)*)"', buffer)
                if cm:
                    text = cm.group(1).replace('\\"', '"').replace('\\n', '\n')
                    if text.strip():
                        yield f"event: closing\ndata: {json.dumps({'text': text})}\n\n"
                    closing_sent = True

        result = parse_response(buffer)

        if not steps_sent and result["steps"]:
            for i, s in enumerate(result["steps"]):
                st = s.get("text", "")
                step_num = s.get("step_number", i + 1)
                image_file = step_image_map.get(step_num)
                if image_file in sent_images:
                    image_file = None
                elif image_file:
                    sent_images.add(image_file)
                plain_lines.append(f"{step_num}. {st}")
                yield f"event: step\ndata: {json.dumps({'index': i, 'step_number': step_num, 'text': st, 'image': image_file, 'total': len(result['steps'])})}\n\n"

        if not closing_sent and result.get("closing"):
            yield f"event: closing\ndata: {json.dumps({'text': result['closing']})}\n\n"

        if chart_suggestion:
            yield f"event: chart_suggestion\ndata: {json.dumps(chart_suggestion, ensure_ascii=False)}\n\n"

        total = len(steps_sent) if steps_sent else len(result["steps"])
        yield f"event: total\ndata: {json.dumps({'total': total})}\n\n"

        last_step_num = steps_sent[-1]["step_number"] if steps_sent else None
        assistant_content = "\n".join(plain_lines)
        if last_step_num:
            assistant_content += f"\n[STEP:{last_step_num}]"

        save_message(q.user_id, q.company_id, "user", q.text)
        save_message(q.user_id, q.company_id, "assistant", assistant_content)

        yield f"event: meta\ndata: {json.dumps({'sources': sources, 'version_ids': ver_ids})}\n\n"
        yield f"event: done\ndata: {{}}\n\n"
        print("  Done")

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )

@app.post("/greeting")
async def greeting(req: GreetingRequest, _key: str = Depends(verify_api_key)):
    history_rows  = get_history(req.user_id, req.company_id, limit=6)
    prefs         = get_user_prefs(req.user_id, req.company_id)
    system_prompt = build_system_prompt(prefs)
    message = _gemini_client.models.generate_content(
        model=LLM_MODEL,
        contents=GREETING_PROMPT.format(
            system_prompt=system_prompt,
            history=format_history(history_rows),
        ),
    ).text
    return {"message": message.strip()}


def process_feedback_comment(comment: str, query_text: str, reason: str) -> dict:
    if not comment.strip():
        return {
            "comment_type": None,
            "comment_normalized": None,
            "content_issue": None,
            "preference_change": None,
            "is_actionable": False,
        }

    prompt = f"""You are an ERP support feedback analyzer.

A user gave negative feedback on an AI-generated ERP help response.

Original question: "{query_text}"
Selected reason: "{reason}"
User comment: "{comment}"

Analyze this comment and return ONLY valid JSON:
{{
  "comment_type": "content" | "preference" | "both",
  "comment_normalized": "professional 1-2 sentence summary of the feedback",
  "content_issue": "specific issue with the answer content, or null if none",
  "preference_change": {{
    "response_len": "short" | "normal" | "detailed"
  }} or {{
    "language": "en" | "vi"
  }} or null,
  "is_actionable": true | false
}}

Rules:
- "content": user says the answer is wrong, incomplete, outdated, or irrelevant
- "preference": user wants shorter/longer/different style responses
- "both": user mentions both content issue AND style preference
- comment_normalized: rewrite in professional English, remove emotion/slang
- is_actionable: true if content_issue contains specific useful info for fixing the answer
- If comment is too vague (e.g. "bad answer"), set is_actionable=false
"""

    raw = _gemini_client.models.generate_content(model=LLM_MODEL, contents=prompt).text.strip()
    raw = re.sub(r'^```json\s*|^```\s*|\s*```$', '', raw, flags=re.MULTILINE)

    try:
        data = json.loads(raw)
        return {
            "comment_type":       data.get("comment_type"),
            "comment_normalized": data.get("comment_normalized"),
            "content_issue":      data.get("content_issue"),
            "preference_change":  data.get("preference_change"),
            "is_actionable":      bool(data.get("is_actionable", False)),
        }
    except:
        return {
            "comment_type": "content",
            "comment_normalized": comment[:500],
            "content_issue": comment[:500],
            "preference_change": None,
            "is_actionable": False,
        }


@app.post("/feedback")
async def feedback(fb: FeedbackRequest, _key: str = Depends(verify_api_key)):
    import asyncio
    loop = asyncio.get_running_loop()

    result = {"status": "saved", "preference_updated": False, "flagged": False}

    if fb.entry_version_id and os.path.exists(KNOWLEDGE_DB):
        kconn = get_knowledge_conn()
        field = "thumbs_up" if fb.rating == "up" else "thumbs_down"
        kconn.execute(
            f"UPDATE entry_versions SET {field} = {field} + 1 WHERE id = ?",
            (fb.entry_version_id,)
        )
        kconn.execute("""
            UPDATE entry_versions
            SET score = CAST(thumbs_up AS REAL) / NULLIF(thumbs_up + thumbs_down, 0)
            WHERE id = ?
        """, (fb.entry_version_id,))

        ver = kconn.execute(
            "SELECT thumbs_up, thumbs_down FROM entry_versions WHERE id=?",
            (fb.entry_version_id,)
        ).fetchone()
        if ver:
            total = ver["thumbs_up"] + ver["thumbs_down"]
            if total >= 5 and ver["thumbs_down"] / total > 0.3:
                kconn.execute(
                    """UPDATE entry_versions
                       SET is_flagged=1, flag_status='pending', flag_reason=?
                       WHERE id=?""",
                    (f"thumbs_down rate > 30% ({ver['thumbs_down']}/{total})",
                     fb.entry_version_id)
                )
                result["flagged"] = True

        # Auto-flag immediately for high-severity user-reported reasons
        _AUTO_FLAG_REASONS = {"wrong_answer", "incomplete", "outdated"}
        if (fb.rating == "down"
                and fb.reason in _AUTO_FLAG_REASONS
                and not result.get("flagged")):
            kconn.execute(
                """UPDATE entry_versions
                   SET is_flagged=1, flag_status='pending', flag_reason=?
                   WHERE id=?""",
                (f"Auto-flagged: user reported '{fb.reason}'", fb.entry_version_id)
            )
            result["flagged"] = True

        kconn.commit()
        kconn.close()

    analyzed = {
        "comment_type": None,
        "comment_normalized": None,
        "content_issue": None,
        "preference_change": None,
        "is_actionable": False,
    }

    if fb.rating == "down" and fb.comment.strip():
        print(f"  [feedback] Processing comment from {fb.user_id}...")
        analyzed = await loop.run_in_executor(
            None,
            lambda: process_feedback_comment(
                fb.comment, fb.query_text,
                fb.reason
            )
        )
        print(f"  [feedback] type={analyzed['comment_type']} "
              f"actionable={analyzed['is_actionable']}")

        if analyzed["preference_change"]:
            pref = analyzed["preference_change"]
            valid = {k: v for k, v in pref.items()
                     if k in {"language", "response_len"}}
            if valid:
                update_user_prefs(fb.user_id, fb.company_id, **valid)
                result["preference_updated"] = True
                result["preference_change"]  = valid
                print(f"  [feedback] Preference updated: {valid}")

        if (analyzed["comment_type"] in ("content", "both")
                and analyzed["is_actionable"]
                and fb.entry_version_id
                and os.path.exists(KNOWLEDGE_DB)):
            kconn = get_knowledge_conn()
            flag_reason = analyzed["content_issue"] or fb.reason or "User reported issue"
            kconn.execute(
                "UPDATE entry_versions SET is_flagged=1, flag_reason=? WHERE id=?",
                (flag_reason[:500], fb.entry_version_id)
            )
            kconn.commit()
            kconn.close()
            result["flagged"] = True

    cconn = get_chat_conn()
    cconn.execute("""
        CREATE TABLE IF NOT EXISTS feedback_log (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id             TEXT NOT NULL,
            company_id          TEXT NOT NULL DEFAULT '',
            entry_version_id    INTEGER,
            rating              TEXT NOT NULL,
            reason              TEXT,
            comment_raw         TEXT,
            comment_normalized  TEXT,
            comment_type        TEXT,
            content_issue       TEXT,
            preference_change   TEXT,
            is_actionable       INTEGER DEFAULT 0,
            query_text          TEXT,
            created_at          TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    cconn.execute("""
        INSERT INTO feedback_log
            (user_id, company_id, entry_version_id, rating, reason,
             comment_raw, comment_normalized, comment_type,
             content_issue, preference_change, is_actionable, query_text)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        fb.user_id, fb.company_id, fb.entry_version_id,
        fb.rating, fb.reason or None,
        fb.comment or None,
        analyzed["comment_normalized"],
        analyzed["comment_type"],
        analyzed["content_issue"],
        json.dumps(analyzed["preference_change"]) if analyzed["preference_change"] else None,
        1 if analyzed["is_actionable"] else 0,
        fb.query_text or None,
    ))
    cconn.commit()
    cconn.close()

    return result


@app.get("/history/{company_id}/{user_id}")
async def get_chat_history(company_id: str, user_id: str,
                           limit: int = 50, _key: str = Depends(verify_api_key)):
    rows = get_history(user_id, company_id, limit)
    return {"history": [
        {"role": r["role"], "content": r["content"], "timestamp": r["timestamp"]}
        for r in rows
    ]}


@app.delete("/history/{company_id}/{user_id}")
async def clear_history(company_id: str, user_id: str, _key: str = Depends(verify_api_key)):
    conn = get_chat_conn()
    conn.execute("DELETE FROM chat_history WHERE user_id=? AND company_id=?",
                 (user_id, company_id))
    conn.commit()
    conn.close()
    return {"status": "cleared"}


@app.get("/preferences/{company_id}/{user_id}")
async def get_prefs(company_id: str, user_id: str, _key: str = Depends(verify_api_key)):
    return get_user_prefs(user_id, company_id)


@app.put("/preferences/{company_id}/{user_id}")
async def update_prefs(company_id: str, user_id: str,
                       body: dict, _key: str = Depends(verify_api_key)):
    changes = {k: v for k, v in body.items() if k in {"language", "response_len"}}
    if changes:
        update_user_prefs(user_id, company_id, **changes)
    return {"status": "updated", "preferences": get_user_prefs(user_id, company_id)}


@app.get("/health")
async def health():
    domains = []
    if os.path.exists(KNOWLEDGE_DB):
        conn    = get_knowledge_conn()
        domains = [r["name"] for r in conn.execute("SELECT name FROM domains ORDER BY name").fetchall()]
        entries = conn.execute("SELECT COUNT(*) FROM entries WHERE is_active=1").fetchone()[0]
        conn.close()
    else:
        entries = 0

    return {
        "status":       "running",
        "llm_model":    LLM_MODEL,
        "reranker":     get_reranker() is not None,
        "role_md":      os.path.exists(ROLE_MD),
        "knowledge_db": os.path.exists(KNOWLEDGE_DB),
        "domains":      domains,
        "total_entries": entries,
    }


# ─── Admin Helpers ────────────────────────────────────────────────────────────

def _ensure_admin_tables(conn):
    """Ensure admin_action_log and flag columns exist (auto-migrate on first use)."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS admin_action_log (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_user_id TEXT    NOT NULL,
            action        TEXT    NOT NULL,
            target_type   TEXT,
            target_id     TEXT,
            note          TEXT,
            meta          TEXT,
            ip_address    TEXT,
            created_at    TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    for column, col_type in [
        ("flag_status",          "TEXT"),
        ("flag_resolved_at",     "TEXT"),
        ("flag_resolved_by",     "TEXT"),
        ("flag_resolution_note", "TEXT"),
    ]:
        try:
            conn.execute(f"ALTER TABLE entry_versions ADD COLUMN {column} {col_type}")
        except Exception:
            pass
    conn.commit()


def log_admin_action(conn, admin_user_id: str, action: str,
                     target_type: str = None, target_id: str = None,
                     note: str = None, meta: dict = None, ip: str = None):
    """Write one row to admin_action_log. Never raises — log failures are silent."""
    try:
        conn.execute("""
            INSERT INTO admin_action_log
                (admin_user_id, action, target_type, target_id, note, meta, ip_address)
            VALUES (?,?,?,?,?,?,?)
        """, (
            admin_user_id, action, target_type, target_id,
            note, json.dumps(meta) if meta else None, ip,
        ))
        conn.commit()
    except Exception as e:
        print(f"[WARN] log_admin_action failed: {e}")


def _get_client_ip(request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ─── Admin Pydantic Models ────────────────────────────────────────────────────

class AdminFlagAction(BaseModel):
    admin_user_id: str
    note: str = ""

class AdminFlagManual(BaseModel):
    admin_user_id: str
    reason: str
    note: str = ""

class AdminSchedulerAction(BaseModel):
    admin_user_id: str

class AdminSchedulerConfig(BaseModel):
    admin_user_id: str
    interval: str   # hourly | daily | weekly
    time: str       # HH:MM
    day: str = "monday"


# ─── Admin: Feedback Endpoints ────────────────────────────────────────────────

from fastapi import Request
from typing import Optional

@app.get("/admin/feedback/stats")
async def admin_feedback_stats(
    company_id: Optional[str] = None,
    _key: str = Depends(verify_api_key),
):
    """Aggregate feedback stats for the overview dashboard."""
    if not os.path.exists(CHAT_DB):
        return {"total": 0, "thumbs_up": 0, "thumbs_down": 0, "positive_rate": 0,
                "flagged_pending": 0, "flagged_resolved": 0, "actionable_count": 0, "recent_7d": 0}

    cconn = get_chat_conn()
    where, params = [], []
    if company_id:
        where.append("company_id = ?")
        params.append(company_id)
    w = ("WHERE " + " AND ".join(where)) if where else ""

    row = cconn.execute(f"""
        SELECT
            COUNT(*)                                   AS total,
            SUM(rating = 'up')                         AS thumbs_up,
            SUM(rating = 'down')                       AS thumbs_down,
            SUM(is_actionable = 1)                     AS actionable_count,
            SUM(created_at >= datetime('now', '-7 days')) AS recent_7d
        FROM feedback_log {w}
    """, params).fetchone()
    cconn.close()

    total     = row["total"] or 0
    thumbs_up = row["thumbs_up"] or 0
    pos_rate  = round(thumbs_up / total * 100, 1) if total else 0

    # Flagged counts come from knowledge DB
    flagged_pending = flagged_resolved = 0
    if os.path.exists(KNOWLEDGE_DB):
        kconn = get_knowledge_conn()
        _ensure_admin_tables(kconn)
        fp = kconn.execute(
            "SELECT COUNT(*) FROM entry_versions WHERE is_flagged=1 AND (flag_status IS NULL OR flag_status='pending')"
        ).fetchone()[0]
        fr = kconn.execute(
            "SELECT COUNT(*) FROM entry_versions WHERE is_flagged=1 AND flag_status='resolved'"
        ).fetchone()[0]
        flagged_pending, flagged_resolved = fp, fr
        kconn.close()

    return {
        "total":            total,
        "thumbs_up":        thumbs_up,
        "thumbs_down":      row["thumbs_down"] or 0,
        "positive_rate":    pos_rate,
        "flagged_pending":  flagged_pending,
        "flagged_resolved": flagged_resolved,
        "actionable_count": row["actionable_count"] or 0,
        "recent_7d":        row["recent_7d"] or 0,
    }


@app.get("/admin/feedback")
async def admin_feedback_list(
    company_id:    Optional[str] = None,
    rating:        Optional[str] = None,
    is_actionable: Optional[int] = None,
    flag_status:   Optional[str] = None,   # 'pending' | 'resolved' | 'all'
    date_from:     Optional[str] = None,
    date_to:       Optional[str] = None,
    limit:         int = 50,
    offset:        int = 0,
    _key: str = Depends(verify_api_key),
):
    """
    List feedback_log rows with optional filters.
    Enriches each row with entry_name / feature / domain from knowledge DB.
    """
    if not os.path.exists(CHAT_DB):
        return {"total": 0, "items": []}

    cconn = get_chat_conn()
    where, params = [], []
    if company_id:
        where.append("fl.company_id = ?"); params.append(company_id)
    if rating in ("up", "down"):
        where.append("fl.rating = ?"); params.append(rating)
    if is_actionable is not None:
        where.append("fl.is_actionable = ?"); params.append(is_actionable)
    if date_from:
        where.append("fl.created_at >= ?"); params.append(date_from)
    if date_to:
        where.append("fl.created_at <= ?"); params.append(date_to + " 23:59:59")
    w = ("WHERE " + " AND ".join(where)) if where else ""

    total = cconn.execute(f"SELECT COUNT(*) FROM feedback_log fl {w}", params).fetchone()[0]
    rows  = cconn.execute(f"""
        SELECT fl.id, fl.entry_version_id, fl.user_id, fl.company_id,
               fl.rating, fl.reason, fl.comment_raw, fl.comment_normalized,
               fl.comment_type, fl.content_issue, fl.preference_change,
               fl.is_actionable, fl.query_text, fl.created_at
        FROM feedback_log fl {w}
        ORDER BY fl.created_at DESC
        LIMIT ? OFFSET ?
    """, params + [limit, offset]).fetchall()
    cconn.close()

    # Enrich with entry info from knowledge DB
    items = []
    if os.path.exists(KNOWLEDGE_DB):
        kconn = get_knowledge_conn()
        _ensure_admin_tables(kconn)

        for r in rows:
            item = dict(r)
            ev_id = item.get("entry_version_id")
            entry_name = feature_name = domain_name = None
            is_flagged = flag_st = flag_resolved_at = flag_resolved_by = flag_resolution_note = None

            if ev_id:
                ev = kconn.execute("""
                    SELECT ev.is_flagged, ev.flag_reason, ev.flag_status,
                           ev.flag_resolved_at, ev.flag_resolved_by, ev.flag_resolution_note,
                           e.name as entry_name,
                           f.name as feature_name,
                           d.name as domain_name
                    FROM entry_versions ev
                    JOIN entries e  ON ev.entry_id   = e.id
                    JOIN features f ON e.feature_id  = f.id
                    JOIN domains d  ON f.domain_id   = d.id
                    WHERE ev.id = ?
                """, (ev_id,)).fetchone()
                if ev:
                    entry_name           = ev["entry_name"]
                    feature_name         = ev["feature_name"]
                    domain_name          = ev["domain_name"]
                    is_flagged           = ev["is_flagged"]
                    flag_st              = ev["flag_status"]
                    flag_resolved_at     = ev["flag_resolved_at"]
                    flag_resolved_by     = ev["flag_resolved_by"]
                    flag_resolution_note = ev["flag_resolution_note"]

                # Apply flag_status filter (post-join)
                if flag_status and flag_status != "all":
                    if flag_status == "pending" and flag_st != "pending" and flag_st is not None:
                        continue
                    if flag_status == "resolved" and flag_st != "resolved":
                        continue

            item.update({
                "entry_name":           entry_name,
                "feature":              feature_name,
                "domain":               domain_name,
                "is_flagged":           is_flagged,
                "flag_status":          flag_st,
                "flag_resolved_at":     flag_resolved_at,
                "flag_resolved_by":     flag_resolved_by,
                "flag_resolution_note": flag_resolution_note,
            })
            items.append(item)
        kconn.close()
    else:
        items = [dict(r) for r in rows]

    return {"total": total, "items": items}


@app.delete("/admin/feedback/all")
async def admin_clear_all_feedback(
    body: AdminSchedulerAction,
    request: Request,
    _key: str = Depends(verify_api_key),
):
    """Delete all feedback_log rows and reset entry_version scores/flags. For testing/demo use."""
    deleted_count = 0
    if os.path.exists(CHAT_DB):
        cconn = get_chat_conn()
        deleted_count = cconn.execute("SELECT COUNT(*) FROM feedback_log").fetchone()[0]
        cconn.execute("DELETE FROM feedback_log")
        cconn.commit()
        cconn.close()

    reset_count = 0
    if os.path.exists(KNOWLEDGE_DB):
        kconn = get_knowledge_conn()
        _ensure_admin_tables(kconn)
        reset_count = kconn.execute(
            "SELECT COUNT(*) FROM entry_versions WHERE thumbs_up > 0 OR thumbs_down > 0 OR is_flagged = 1"
        ).fetchone()[0]
        kconn.execute("""
            UPDATE entry_versions
            SET thumbs_up=0, thumbs_down=0, score=NULL,
                is_flagged=0, flag_status=NULL, flag_reason=NULL,
                flag_resolved_at=NULL, flag_resolved_by=NULL, flag_resolution_note=NULL
        """)
        kconn.commit()
        log_admin_action(kconn, body.admin_user_id, "clear_feedback",
                         target_type="feedback_log",
                         note=f"Cleared {deleted_count} feedback records, reset {reset_count} entry versions",
                         meta={"deleted_count": deleted_count, "reset_count": reset_count},
                         ip=_get_client_ip(request))
        kconn.close()

    return {"status": "cleared", "deleted_count": deleted_count, "reset_count": reset_count}


# ─── Admin: Flag Management Endpoints ────────────────────────────────────────

@app.post("/admin/entries/{entry_version_id}/resolve-flag")
async def admin_resolve_flag(
    entry_version_id: int,
    body: AdminFlagAction,
    request: Request,
    _key: str = Depends(verify_api_key),
):
    if not os.path.exists(KNOWLEDGE_DB):
        raise HTTPException(status_code=404, detail="Knowledge DB not found")

    kconn = get_knowledge_conn()
    _ensure_admin_tables(kconn)

    ev = kconn.execute(
        "SELECT id, is_flagged FROM entry_versions WHERE id=?", (entry_version_id,)
    ).fetchone()
    if not ev:
        kconn.close()
        raise HTTPException(status_code=404, detail="Entry version not found")

    now = datetime.now().isoformat()
    kconn.execute("""
        UPDATE entry_versions
        SET flag_status='resolved', flag_resolved_at=?, flag_resolved_by=?, flag_resolution_note=?
        WHERE id=?
    """, (now, body.admin_user_id, body.note or None, entry_version_id))

    entry_name = kconn.execute("""
        SELECT e.name FROM entries e
        JOIN entry_versions ev ON ev.entry_id = e.id
        WHERE ev.id = ?
    """, (entry_version_id,)).fetchone()

    log_admin_action(kconn, body.admin_user_id, "resolve_flag",
                     target_type="entry_version", target_id=str(entry_version_id),
                     note=body.note or None,
                     meta={"entry_name": entry_name["name"] if entry_name else None},
                     ip=_get_client_ip(request))
    kconn.close()
    return {"status": "resolved"}


@app.post("/admin/entries/{entry_version_id}/unflag")
async def admin_unflag(
    entry_version_id: int,
    body: AdminFlagAction,
    request: Request,
    _key: str = Depends(verify_api_key),
):
    if not os.path.exists(KNOWLEDGE_DB):
        raise HTTPException(status_code=404, detail="Knowledge DB not found")

    kconn = get_knowledge_conn()
    _ensure_admin_tables(kconn)

    ev = kconn.execute(
        "SELECT id FROM entry_versions WHERE id=?", (entry_version_id,)
    ).fetchone()
    if not ev:
        kconn.close()
        raise HTTPException(status_code=404, detail="Entry version not found")

    kconn.execute("""
        UPDATE entry_versions
        SET is_flagged=0, flag_status=NULL, flag_reason=NULL,
            flag_resolved_at=NULL, flag_resolved_by=NULL, flag_resolution_note=NULL
        WHERE id=?
    """, (entry_version_id,))

    entry_name = kconn.execute("""
        SELECT e.name FROM entries e
        JOIN entry_versions ev ON ev.entry_id = e.id
        WHERE ev.id = ?
    """, (entry_version_id,)).fetchone()

    log_admin_action(kconn, body.admin_user_id, "unflag",
                     target_type="entry_version", target_id=str(entry_version_id),
                     note=body.note or None,
                     meta={"entry_name": entry_name["name"] if entry_name else None},
                     ip=_get_client_ip(request))
    kconn.close()
    return {"status": "unflagged"}


@app.post("/admin/entries/{entry_version_id}/flag")
async def admin_manual_flag(
    entry_version_id: int,
    body: AdminFlagManual,
    request: Request,
    _key: str = Depends(verify_api_key),
):
    if not os.path.exists(KNOWLEDGE_DB):
        raise HTTPException(status_code=404, detail="Knowledge DB not found")

    kconn = get_knowledge_conn()
    _ensure_admin_tables(kconn)

    ev = kconn.execute(
        "SELECT id FROM entry_versions WHERE id=?", (entry_version_id,)
    ).fetchone()
    if not ev:
        kconn.close()
        raise HTTPException(status_code=404, detail="Entry version not found")

    kconn.execute("""
        UPDATE entry_versions
        SET is_flagged=1, flag_reason=?, flag_status='pending',
            flag_resolved_at=NULL, flag_resolved_by=NULL, flag_resolution_note=NULL
        WHERE id=?
    """, (body.reason, entry_version_id))

    entry_name = kconn.execute("""
        SELECT e.name FROM entries e
        JOIN entry_versions ev ON ev.entry_id = e.id
        WHERE ev.id = ?
    """, (entry_version_id,)).fetchone()

    log_admin_action(kconn, body.admin_user_id, "manual_flag",
                     target_type="entry_version", target_id=str(entry_version_id),
                     note=body.note or None,
                     meta={"flag_reason": body.reason,
                           "entry_name": entry_name["name"] if entry_name else None},
                     ip=_get_client_ip(request))
    kconn.close()
    return {"status": "flagged"}


# ─── Admin: Action Log ────────────────────────────────────────────────────────

@app.get("/admin/action-log")
async def admin_action_log(
    admin_user_id: Optional[str] = None,
    action:        Optional[str] = None,
    target_type:   Optional[str] = None,
    target_id:     Optional[str] = None,
    date_from:     Optional[str] = None,
    date_to:       Optional[str] = None,
    limit:         int = 50,
    offset:        int = 0,
    _key: str = Depends(verify_api_key),
):
    if not os.path.exists(KNOWLEDGE_DB):
        return {"total": 0, "items": []}

    kconn = get_knowledge_conn()
    _ensure_admin_tables(kconn)

    where, params = [], []
    if admin_user_id:
        where.append("admin_user_id = ?"); params.append(admin_user_id)
    if action:
        where.append("action = ?"); params.append(action)
    if target_type:
        where.append("target_type = ?"); params.append(target_type)
    if target_id:
        where.append("target_id = ?"); params.append(target_id)
    if date_from:
        where.append("created_at >= ?"); params.append(date_from)
    if date_to:
        where.append("created_at <= ?"); params.append(date_to + " 23:59:59")
    w = ("WHERE " + " AND ".join(where)) if where else ""

    total = kconn.execute(f"SELECT COUNT(*) FROM admin_action_log {w}", params).fetchone()[0]
    rows  = kconn.execute(f"""
        SELECT id, admin_user_id, action, target_type, target_id,
               note, meta, ip_address, created_at
        FROM admin_action_log {w}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """, params + [limit, offset]).fetchall()
    kconn.close()

    return {
        "total": total,
        "items": [dict(r) for r in rows],
    }


# ─── Admin: Document Management ───────────────────────────────────────────────

@app.get("/admin/documents/stats")
async def admin_document_stats(_key: str = Depends(verify_api_key)):
    if not os.path.exists(KNOWLEDGE_DB):
        return {"total": 0, "done": 0, "failed": 0, "pending": 0, "processing": 0, "total_entries": 0}
    kconn = get_knowledge_conn()
    row = kconn.execute("""
        SELECT
            COUNT(*)                                                     AS total,
            SUM(CASE WHEN status='done'       THEN 1 ELSE 0 END)        AS done,
            SUM(CASE WHEN status='failed'     THEN 1 ELSE 0 END)        AS failed,
            SUM(CASE WHEN status='pending'    THEN 1 ELSE 0 END)        AS pending,
            SUM(CASE WHEN status='processing' THEN 1 ELSE 0 END)        AS processing,
            SUM(CASE WHEN status='done' THEN entries_parsed ELSE 0 END) AS total_entries
        FROM document_registry
    """).fetchone()
    kconn.close()
    return dict(row)


@app.get("/admin/documents")
async def admin_documents(
    status:     Optional[str] = None,
    company_id: Optional[str] = None,
    domain:     Optional[str] = None,
    search:     Optional[str] = None,
    limit:      int = 20,
    offset:     int = 0,
    _key: str = Depends(verify_api_key),
):
    if not os.path.exists(KNOWLEDGE_DB):
        return {"total": 0, "items": []}
    kconn = get_knowledge_conn()
    where, params = [], []
    if status:
        where.append("dr.status = ?");     params.append(status)
    if company_id == "global":
        where.append("dr.company_id IS NULL")
    elif company_id:
        where.append("c.code = ?");        params.append(company_id)
    if domain:
        where.append("d.name = ?");        params.append(domain)
    if search:
        where.append("dr.file_path LIKE ?"); params.append(f"%{search}%")
    w = ("WHERE " + " AND ".join(where)) if where else ""

    base = f"""
        FROM document_registry dr
        LEFT JOIN companies c ON c.id = dr.company_id
        LEFT JOIN domains   d ON d.id = dr.domain_id
        {w}
    """
    total = kconn.execute(f"SELECT COUNT(*) {base}", params).fetchone()[0]
    rows  = kconn.execute(f"""
        SELECT dr.id, dr.file_path, dr.entries_parsed,
               dr.status, dr.error_message, dr.ingested_at, dr.created_at,
               c.code AS company_code, c.name AS company_name,
               d.name AS domain_name
        {base}
        ORDER BY dr.ingested_at DESC, dr.created_at DESC
        LIMIT ? OFFSET ?
    """, params + [limit, offset]).fetchall()
    kconn.close()
    return {"total": total, "items": [dict(r) for r in rows]}


@app.post("/admin/documents/{doc_id}/reingest")
async def admin_document_reingest(
    doc_id: int,
    body: AdminFlagAction,
    request: Request,
    _key: str = Depends(verify_api_key),
):
    if not os.path.exists(KNOWLEDGE_DB):
        raise HTTPException(status_code=404, detail="Knowledge DB not found")
    kconn = get_knowledge_conn()
    doc = kconn.execute(
        "SELECT id, file_path FROM document_registry WHERE id = ?", (doc_id,)
    ).fetchone()
    if not doc:
        kconn.close()
        raise HTTPException(status_code=404, detail="Document not found")
    kconn.execute(
        "UPDATE document_registry SET status='pending', error_message=NULL WHERE id=?",
        (doc_id,)
    )
    kconn.commit()
    log_admin_action(kconn, body.admin_user_id, "reingest_queued",
                     target_type="document", target_id=str(doc_id),
                     meta={"file_path": doc["file_path"]},
                     ip=_get_client_ip(request))
    kconn.close()
    return {"status": "queued"}


_VALID_DOMAINS = [
    "Sales", "Purchase", "Finance", "Inventory", "CRM",
    "Human Resources", "Project", "Fixed Assets", "Service Manager", "General",
]
_DOCS_ROOT = Path("./documents")


def _auto_detect_domain(file_bytes: bytes, filename: str) -> str:
    import tempfile, os as _os
    suffix = Path(filename).suffix or ".tmp"
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name
        from markitdown import MarkItDown
        text = MarkItDown().convert(tmp_path).text_content[:5000]
    except Exception:
        text = ""
    finally:
        if tmp_path and _os.path.exists(tmp_path):
            _os.unlink(tmp_path)

    if not text.strip():
        print(f"  [auto-detect] No text extracted from {filename}, defaulting to General")
        return "General"

    prompt = (
        "Classify this ERP document excerpt into exactly ONE domain from this list:\n"
        f"{', '.join(_VALID_DOMAINS)}\n\n"
        f"Document excerpt:\n{text}\n\n"
        "Reply with ONLY the domain name, nothing else."
    )
    try:
        resp = genai.GenerativeModel(LLM_MODEL).generate_content(prompt)
        detected = resp.text.strip()
        for valid in _VALID_DOMAINS:
            if detected.lower() == valid.lower():
                return valid
        return "General"
    except Exception:
        return "General"


@app.post("/admin/documents/upload")
async def admin_document_upload(
    request: Request,
    file: UploadFile = File(...),
    domain: str = Form(...),
    company_code: str = Form(""),
    admin_user_id: str = Form("admin"),
    _key: str = Depends(verify_api_key),
):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in (".docx", ".pdf"):
        raise HTTPException(status_code=400, detail="Only .docx and .pdf files are supported")

    content = await file.read()

    domain = domain.strip()
    auto_detected = False
    if domain == "auto":
        domain = _auto_detect_domain(content, file.filename or ("file" + ext))
        auto_detected = True
    elif domain not in _VALID_DOMAINS:
        raise HTTPException(status_code=400, detail=f"Invalid domain. Choose from: {', '.join(_VALID_DOMAINS)}")

    company_code = company_code.strip().upper()
    safe_name = Path(file.filename).name
    if company_code:
        target = _DOCS_ROOT / "clients" / company_code / domain / safe_name
    else:
        target = _DOCS_ROOT / "_global" / domain / safe_name

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)

    file_path_str = str(target.resolve())
    kconn = get_knowledge_conn()
    existing = kconn.execute(
        "SELECT id FROM document_registry WHERE file_path = ?", (file_path_str,)
    ).fetchone()
    if existing:
        kconn.execute(
            "UPDATE document_registry SET status='pending', error_message=NULL WHERE id=?",
            (existing["id"],)
        )
        kconn.commit()
        doc_id = existing["id"]
    else:
        cur = kconn.execute(
            "INSERT INTO document_registry (file_path, status) VALUES (?, 'pending')",
            (file_path_str,)
        )
        kconn.commit()
        doc_id = cur.lastrowid

    log_admin_action(kconn, admin_user_id, "document_uploaded",
                     target_type="document", target_id=str(doc_id),
                     meta={"file_path": file_path_str},
                     ip=_get_client_ip(request))
    kconn.close()
    return {"id": doc_id, "file_path": file_path_str, "status": "pending",
            "domain": domain, "auto_detected": auto_detected}


@app.delete("/admin/documents/{doc_id}")
async def admin_document_delete(
    doc_id: int,
    request: Request,
    admin_user_id: str = "",
    _key: str = Depends(verify_api_key),
):
    kconn = get_knowledge_conn()
    doc = kconn.execute(
        "SELECT id, file_path FROM document_registry WHERE id = ?", (doc_id,)
    ).fetchone()
    if not doc:
        kconn.close()
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = doc["file_path"]
    try:
        Path(file_path).unlink(missing_ok=True)
    except Exception:
        pass

    kconn.execute("DELETE FROM document_registry WHERE id = ?", (doc_id,))
    kconn.commit()
    log_admin_action(kconn, admin_user_id or "admin", "document_deleted",
                     target_type="document", target_id=str(doc_id),
                     meta={"file_path": file_path},
                     ip=_get_client_ip(request))
    kconn.close()
    return {"status": "deleted"}


def _run_ingest_file(file_path: str, doc_id: int):
    """Background thread: run ingest for a single file, then update DB status."""
    try:
        abs_path = str(Path(file_path).resolve())
        # Normalize stored path to absolute so ingest script can find the existing row
        try:
            _kc = get_knowledge_conn()
            _kc.execute("UPDATE document_registry SET file_path=? WHERE id=? AND file_path!=?",
                        (abs_path, doc_id, abs_path))
            _kc.commit()
            _kc.close()
        except Exception:
            pass
        result = subprocess.run(
            [sys.executable, "ingest_knowledge.py", "--file", abs_path, "--force"],
            cwd=str(INGEST_DIR),
            capture_output=True,
            text=True,
            timeout=3600,
        )
        status = "done" if result.returncode == 0 else "failed"
        error_msg = None if status == "done" else (result.stderr or result.stdout or "Unknown error")[-2000:]
    except subprocess.TimeoutExpired:
        status, error_msg = "failed", "Ingest timed out"
    except Exception as e:
        status, error_msg = "failed", str(e)

    try:
        kconn = get_knowledge_conn()
        kconn.execute(
            "UPDATE document_registry SET status=?, error_message=? WHERE id=?",
            (status, error_msg, doc_id)
        )
        kconn.commit()
        kconn.close()
    except Exception:
        pass


@app.post("/admin/documents/{doc_id}/run-now")
async def admin_document_run_now(
    doc_id: int,
    body: AdminFlagAction,
    request: Request,
    _key: str = Depends(verify_api_key),
):
    kconn = get_knowledge_conn()
    doc = kconn.execute(
        "SELECT id, file_path FROM document_registry WHERE id = ?", (doc_id,)
    ).fetchone()
    if not doc:
        kconn.close()
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = doc["file_path"]
    if not Path(file_path).exists():
        kconn.close()
        raise HTTPException(status_code=400, detail="File not found on disk")

    kconn.execute(
        "UPDATE document_registry SET status='processing', error_message=NULL WHERE id=?",
        (doc_id,)
    )
    kconn.commit()
    log_admin_action(kconn, body.admin_user_id, "ingest_run_now",
                     target_type="document", target_id=str(doc_id),
                     meta={"file_path": file_path},
                     ip=_get_client_ip(request))
    kconn.close()

    t = threading.Thread(target=_run_ingest_file, args=(file_path, doc_id), daemon=True)
    t.start()
    return {"status": "started"}


# ─── Scheduler State Helpers ─────────────────────────────────────────────────

_SCHED_DEFAULTS = {
    "documents": {"enabled": True,  "interval": "daily", "time": "02:00", "day": "monday"},
    "tickets":   {"enabled": True,  "interval": "daily", "time": "03:00", "day": "monday"},
}

def _read_sched_state() -> dict:
    """Read state file; fill missing keys from ingest_config.SCHEDULE defaults."""
    try:
        from ingest.ingest_config import SCHEDULE as _SC
        defaults = {
            "documents": {
                "enabled":  _SC.get("ingest_documents", {}).get("enabled",  True),
                "interval": _SC.get("ingest_documents", {}).get("interval", "daily"),
                "time":     _SC.get("ingest_documents", {}).get("time",     "02:00"),
                "day":      _SC.get("ingest_documents", {}).get("day",      "monday"),
            },
            "tickets": {
                "enabled":  _SC.get("ingest_tickets", {}).get("enabled",  True),
                "interval": _SC.get("ingest_tickets", {}).get("interval", "daily"),
                "time":     _SC.get("ingest_tickets", {}).get("time",     "03:00"),
                "day":      _SC.get("ingest_tickets", {}).get("day",      "monday"),
            },
        }
    except Exception:
        import copy
        defaults = copy.deepcopy(_SCHED_DEFAULTS)

    for job in ("documents", "tickets"):
        defaults[job].setdefault("last_run_at",          None)
        defaults[job].setdefault("last_run_status",      None)
        defaults[job].setdefault("last_run_duration_sec",None)
        defaults[job].setdefault("is_running",           False)

    if SCHEDULER_STATE_FILE.exists():
        try:
            saved = json.loads(SCHEDULER_STATE_FILE.read_text(encoding="utf-8"))
            for job, cfg in saved.items():
                if job in defaults:
                    defaults[job].update(cfg)
        except Exception:
            pass

    return defaults


def _write_sched_state(state: dict):
    SCHEDULER_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    SCHEDULER_STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


_sched_lock = threading.Lock()

_VALID_JOBS = {"documents", "tickets"}
_JOB_SCRIPTS = {
    "documents": "ingest_knowledge.py",
    "tickets":   "ingest_tickets.py",
}


def _run_ingest_background(job: str, admin_user_id: str):
    """Run an ingest script in a daemon thread, update state file before/after."""
    script = _JOB_SCRIPTS[job]
    with _sched_lock:
        state = _read_sched_state()
        if state[job].get("is_running"):
            return   # already running
        state[job]["is_running"] = True
        _write_sched_state(state)

    start = datetime.now()
    status = "failed"
    duration = None
    try:
        result = subprocess.run(
            [sys.executable, script],
            cwd=str(INGEST_DIR),
            capture_output=True,
            text=True,
            timeout=7200,
        )
        status = "success" if result.returncode == 0 else "failed"
    except subprocess.TimeoutExpired:
        status = "failed"
    except Exception:
        status = "failed"
    finally:
        duration = int((datetime.now() - start).total_seconds())
        with _sched_lock:
            state = _read_sched_state()
            state[job]["is_running"]            = False
            state[job]["last_run_at"]           = start.isoformat()
            state[job]["last_run_status"]       = status
            state[job]["last_run_duration_sec"] = duration
            _write_sched_state(state)

        # log to admin_action_log
        try:
            kconn = get_knowledge_conn()
            _ensure_admin_tables(kconn)
            action = "ingest_completed" if status == "success" else "ingest_failed"
            log_admin_action(kconn, admin_user_id, action,
                             target_type="scheduler_job", target_id=job,
                             meta={"job": job, "duration_sec": duration, "trigger": "run_now"})
            kconn.close()
        except Exception:
            pass


# ─── Admin: Scheduler Endpoints ──────────────────────────────────────────────

@app.get("/admin/scheduler/status")
async def admin_scheduler_status(_key: str = Depends(verify_api_key)):
    with _sched_lock:
        state = _read_sched_state()
    return state


@app.post("/admin/scheduler/jobs/{job}/enable")
async def admin_scheduler_enable(
    job: str,
    body: AdminSchedulerAction,
    request: Request,
    _key: str = Depends(verify_api_key),
):
    if job not in _VALID_JOBS:
        raise HTTPException(status_code=404, detail="Unknown job")
    with _sched_lock:
        state = _read_sched_state()
        state[job]["enabled"] = True
        _write_sched_state(state)
    kconn = get_knowledge_conn()
    _ensure_admin_tables(kconn)
    log_admin_action(kconn, body.admin_user_id, "scheduler_enable",
                     target_type="scheduler_job", target_id=job,
                     ip=_get_client_ip(request))
    kconn.close()
    return {"status": "enabled"}


@app.post("/admin/scheduler/jobs/{job}/disable")
async def admin_scheduler_disable(
    job: str,
    body: AdminSchedulerAction,
    request: Request,
    _key: str = Depends(verify_api_key),
):
    if job not in _VALID_JOBS:
        raise HTTPException(status_code=404, detail="Unknown job")
    with _sched_lock:
        state = _read_sched_state()
        state[job]["enabled"] = False
        _write_sched_state(state)
    kconn = get_knowledge_conn()
    _ensure_admin_tables(kconn)
    log_admin_action(kconn, body.admin_user_id, "scheduler_disable",
                     target_type="scheduler_job", target_id=job,
                     ip=_get_client_ip(request))
    kconn.close()
    return {"status": "disabled"}


@app.post("/admin/scheduler/jobs/{job}/run-now")
async def admin_scheduler_run_now(
    job: str,
    body: AdminSchedulerAction,
    request: Request,
    _key: str = Depends(verify_api_key),
):
    if job not in _VALID_JOBS:
        raise HTTPException(status_code=404, detail="Unknown job")
    with _sched_lock:
        state = _read_sched_state()
        if state[job].get("is_running"):
            raise HTTPException(status_code=409, detail="Job is already running")

    t = threading.Thread(
        target=_run_ingest_background,
        args=(job, body.admin_user_id),
        daemon=True,
        name=f"admin-ingest-{job}",
    )
    t.start()

    kconn = get_knowledge_conn()
    _ensure_admin_tables(kconn)
    log_admin_action(kconn, body.admin_user_id, "scheduler_run_now",
                     target_type="scheduler_job", target_id=job,
                     ip=_get_client_ip(request))
    kconn.close()
    return {"status": "started"}


@app.put("/admin/scheduler/jobs/{job}/config")
async def admin_scheduler_update_config(
    job: str,
    body: AdminSchedulerConfig,
    request: Request,
    _key: str = Depends(verify_api_key),
):
    if job not in _VALID_JOBS:
        raise HTTPException(status_code=404, detail="Unknown job")
    if body.interval not in ("hourly", "daily", "weekly"):
        raise HTTPException(status_code=400, detail="interval must be hourly|daily|weekly")

    with _sched_lock:
        state = _read_sched_state()
        state[job]["interval"] = body.interval
        state[job]["time"]     = body.time
        state[job]["day"]      = body.day
        _write_sched_state(state)

    kconn = get_knowledge_conn()
    _ensure_admin_tables(kconn)
    log_admin_action(kconn, body.admin_user_id, "scheduler_update_time",
                     target_type="scheduler_job", target_id=job,
                     meta={"interval": body.interval, "time": body.time, "day": body.day},
                     ip=_get_client_ip(request))
    kconn.close()
    return {"status": "updated"}


# ─── Admin: Knowledge Base Browser ────────────────────────────────────────────

@app.get("/admin/knowledge/stats")
async def admin_knowledge_stats(_key: str = Depends(verify_api_key)):
    if not os.path.exists(KNOWLEDGE_DB):
        return {"domains": 0, "features": 0, "entries": 0, "versions": 0,
                "flagged": 0, "by_type": {}, "by_source": {}}
    kconn = get_knowledge_conn()
    domains  = kconn.execute("SELECT COUNT(*) FROM domains").fetchone()[0]
    features = kconn.execute("SELECT COUNT(*) FROM features").fetchone()[0]
    entries  = kconn.execute("SELECT COUNT(*) FROM entries WHERE is_active=1").fetchone()[0]
    versions = kconn.execute("SELECT COUNT(*) FROM entry_versions WHERE is_current=1").fetchone()[0]
    flagged  = kconn.execute(
        "SELECT COUNT(*) FROM entry_versions WHERE is_flagged=1 AND is_current=1"
    ).fetchone()[0]
    by_type = {r[0]: r[1] for r in kconn.execute(
        "SELECT type, COUNT(*) FROM entries WHERE is_active=1 GROUP BY type"
    ).fetchall()}
    by_source = {r[0]: r[1] for r in kconn.execute(
        "SELECT source_type, COUNT(*) FROM entry_versions WHERE is_current=1 GROUP BY source_type"
    ).fetchall()}
    kconn.close()
    return {"domains": domains, "features": features, "entries": entries,
            "versions": versions, "flagged": flagged,
            "by_type": by_type, "by_source": by_source}


@app.get("/admin/knowledge/entries")
async def admin_knowledge_entries(
    domain:     Optional[str] = None,
    feature_id: Optional[int] = None,
    entry_type: Optional[str] = None,
    company:    Optional[str] = None,   # 'global' | company code
    flagged:    Optional[int] = None,   # 1 = flagged only
    search:     Optional[str] = None,
    limit:      int = 20,
    offset:     int = 0,
    _key: str = Depends(verify_api_key),
):
    if not os.path.exists(KNOWLEDGE_DB):
        return {"total": 0, "items": [], "domains": []}
    kconn = get_knowledge_conn()
    where, params = ["e.is_active = 1"], []
    if domain:
        where.append("d.name = ?");             params.append(domain)
    if feature_id:
        where.append("e.feature_id = ?");       params.append(feature_id)
    if entry_type:
        where.append("e.type = ?");             params.append(entry_type)
    if flagged == 1:
        where.append("ev.is_flagged = 1")
    if company == "global":
        where.append("ev.company_id IS NULL")
    elif company:
        where.append("co.code = ?");            params.append(company)
    if search:
        where.append("(e.name LIKE ? OR e.summary LIKE ? OR f.name LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
    w = "WHERE " + " AND ".join(where)
    total = kconn.execute(f"""
        SELECT COUNT(DISTINCT e.id)
        FROM entries e
        JOIN features f  ON e.feature_id  = f.id
        JOIN domains d   ON f.domain_id   = d.id
        LEFT JOIN entry_versions ev ON ev.entry_id = e.id AND ev.is_current = 1
        LEFT JOIN companies co      ON ev.company_id = co.id
        {w}
    """, params).fetchone()[0]
    rows = kconn.execute(f"""
        SELECT
            e.id, e.name, e.type, e.menu_path, e.summary,
            f.id AS feature_id, f.name AS feature,
            d.name AS domain,
            COUNT(DISTINCT ev.id)                              AS version_count,
            COALESCE(SUM(ev.thumbs_up),   0)                  AS thumbs_up,
            COALESCE(SUM(ev.thumbs_down), 0)                  AS thumbs_down,
            MAX(ev.score)                                      AS score,
            SUM(CASE WHEN ev.is_flagged=1 THEN 1 ELSE 0 END)  AS flagged_count,
            GROUP_CONCAT(DISTINCT ev.source_type)              AS source_types,
            GROUP_CONCAT(DISTINCT co.code)                     AS company_codes
        FROM entries e
        JOIN features f  ON e.feature_id  = f.id
        JOIN domains d   ON f.domain_id   = d.id
        LEFT JOIN entry_versions ev ON ev.entry_id = e.id AND ev.is_current = 1
        LEFT JOIN companies co      ON ev.company_id = co.id
        {w}
        GROUP BY e.id, e.name, e.type, e.menu_path, e.summary,
                 f.id, f.name, d.name
        ORDER BY d.name, f.sort_order, e.sort_order
        LIMIT ? OFFSET ?
    """, params + [limit, offset]).fetchall()
    domains_list = [r[0] for r in kconn.execute(
        "SELECT name FROM domains ORDER BY name"
    ).fetchall()]
    kconn.close()
    items = []
    for r in rows:
        items.append({
            "id":            r[0],
            "name":          r[1],
            "type":          r[2],
            "menu_path":     r[3],
            "summary":       r[4],
            "feature_id":    r[5],
            "feature":       r[6],
            "domain":        r[7],
            "version_count": r[8] or 0,
            "thumbs_up":     r[9],
            "thumbs_down":   r[10],
            "score":         round(r[11] * 100, 1) if r[11] else None,
            "flagged_count": r[12] or 0,
            "source_types":  r[13].split(",") if r[13] else [],
            "company_codes": r[14].split(",") if r[14] else [],
        })
    return {"total": total, "items": items, "domains": domains_list}


@app.get("/admin/knowledge/entries/{entry_id}")
async def admin_knowledge_entry_detail(
    entry_id: int,
    _key: str = Depends(verify_api_key),
):
    if not os.path.exists(KNOWLEDGE_DB):
        raise HTTPException(status_code=404, detail="Knowledge DB not found")
    kconn = get_knowledge_conn()
    row = kconn.execute("""
        SELECT e.id, e.name, e.type, e.menu_path, e.summary,
               f.name AS feature, d.name AS domain, e.created_at
        FROM entries e
        JOIN features f ON e.feature_id = f.id
        JOIN domains d  ON f.domain_id  = d.id
        WHERE e.id = ?
    """, (entry_id,)).fetchone()
    if not row:
        kconn.close()
        raise HTTPException(status_code=404, detail="Entry not found")
    versions = kconn.execute("""
        SELECT ev.id, ev.version, ev.source_type, ev.source_ref,
               ev.steps, ev.notes,
               ev.thumbs_up, ev.thumbs_down, ev.score,
               ev.is_flagged, ev.flag_reason, ev.flag_status,
               ev.flag_resolution_note,
               COALESCE(c.code, 'global') AS company_code,
               ev.created_at
        FROM entry_versions ev
        LEFT JOIN companies c ON ev.company_id = c.id
        WHERE ev.entry_id = ? AND ev.is_current = 1
        ORDER BY ev.company_id NULLS FIRST, ev.version DESC
    """, (entry_id,)).fetchall()
    kconn.close()
    vers_list = []
    for v in versions:
        steps, notes = [], []
        try:
            if v[4]: steps = json.loads(v[4])
        except Exception:
            pass
        try:
            if v[5]: notes = json.loads(v[5])
        except Exception:
            pass
        vers_list.append({
            "id":                   v[0],
            "version":              v[1],
            "source_type":          v[2],
            "source_ref":           v[3],
            "steps":                steps,
            "notes":                notes,
            "thumbs_up":            v[6],
            "thumbs_down":          v[7],
            "score":                round(v[8] * 100, 1) if v[8] else None,
            "is_flagged":           bool(v[9]),
            "flag_reason":          v[10],
            "flag_status":          v[11],
            "flag_resolution_note": v[12],
            "company_code":         v[13],
            "created_at":           v[14],
        })
    return {
        "id":         row[0],
        "name":       row[1],
        "type":       row[2],
        "menu_path":  row[3],
        "summary":    row[4],
        "feature":    row[5],
        "domain":     row[6],
        "created_at": row[7],
        "versions":   vers_list,
    }


@app.delete("/admin/knowledge/entries/{entry_id}")
async def admin_delete_knowledge_entry(
    entry_id: int,
    body: AdminFlagAction,
    request: Request,
    _key: str = Depends(verify_api_key),
):
    if not os.path.exists(KNOWLEDGE_DB):
        raise HTTPException(status_code=404, detail="Knowledge DB not found")
    kconn = get_knowledge_conn()
    _ensure_admin_tables(kconn)
    row = kconn.execute(
        "SELECT id, name FROM entries WHERE id = ? AND is_active = 1", (entry_id,)
    ).fetchone()
    if not row:
        kconn.close()
        raise HTTPException(status_code=404, detail="Entry not found or already deleted")
    entry_name = row["name"]
    kconn.execute("UPDATE entries SET is_active = 0 WHERE id = ?", (entry_id,))
    log_admin_action(kconn, body.admin_user_id, "delete_entry",
                     target_type="entry", target_id=str(entry_id),
                     note=entry_name, ip=_get_client_ip(request))
    kconn.close()
    return {"deleted": True, "entry_id": entry_id, "name": entry_name}


@app.delete("/admin/knowledge/entries")
async def admin_delete_all_knowledge_entries(
    body: AdminFlagAction,
    request: Request,
    _key: str = Depends(verify_api_key),
):
    if not os.path.exists(KNOWLEDGE_DB):
        return {"deleted": True, "count": 0}
    kconn = get_knowledge_conn()
    _ensure_admin_tables(kconn)
    count = kconn.execute(
        "SELECT COUNT(*) FROM entries WHERE is_active = 1"
    ).fetchone()[0]
    kconn.execute("UPDATE entries SET is_active = 0 WHERE is_active = 1")
    log_admin_action(kconn, body.admin_user_id, "delete_all_entries",
                     target_type="entry",
                     note=f"Deactivated {count} entries",
                     ip=_get_client_ip(request))
    kconn.close()
    return {"deleted": True, "count": count}


# ─── Admin: System Health ─────────────────────────────────────────────────────

@app.get("/admin/health")
async def admin_system_health(_key: str = Depends(verify_api_key)):
    import time as _time
    checked_at = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    # ── Gemini API ─────────────────────────────────────────────────────────────
    t0 = _time.time()
    try:
        list(_gemini_client.models.list())
        gemini_ms, gemini_status = round((_time.time() - t0) * 1000), "ok"
    except Exception:
        gemini_ms, gemini_status = None, "down"

    # ── ChromaDB ───────────────────────────────────────────────────────────────
    chroma_status = "ok" if CHROMA_AVAILABLE else "down"

    # ── PostgreSQL ─────────────────────────────────────────────────────────────
    try:
        from ingest.ingest_config import PG_CONFIG as _PG
        import psycopg2
        t0 = _time.time()
        _c = psycopg2.connect(**_PG, connect_timeout=3)
        _c.close()
        pg_ms, pg_status = round((_time.time() - t0) * 1000), "ok"
    except ImportError:
        pg_ms, pg_status = None, "skip"
    except Exception:
        pg_ms, pg_status = None, "down"

    # ── Skills server ──────────────────────────────────────────────────────────
    t0 = _time.time()
    try:
        _http_get(f"{SKILLS_URL}/tools", timeout=3)
        skills_ms, skills_status = round((_time.time() - t0) * 1000), "ok"
    except Exception:
        skills_ms, skills_status = None, "down"

    # ── Models ─────────────────────────────────────────────────────────────────
    try:
        from ingest.ingest_config import LLM_MODEL_INGEST as _LMI, EMBEDDING_MODEL as _EMB
    except ImportError:
        _LMI, _EMB = "gemini-2.0-flash", "text-embedding-004"

    _reranker_ok = False
    try:
        _reranker_ok = get_reranker() is not None
    except Exception:
        pass

    models = [
        {"role": "Chat",      "name": LLM_MODEL, "available": gemini_status == "ok"},
        {"role": "Ingest",    "name": _LMI,       "available": gemini_status == "ok"},
        {"role": "Embedding", "name": _EMB,        "available": gemini_status == "ok"},
        {"role": "Reranker",  "name": "ms-marco-MiniLM-L-6-v2", "available": _reranker_ok},
    ]

    # ── Databases ──────────────────────────────────────────────────────────────
    def _db_info(path, kind):
        p = Path(path)
        info = {"path": str(p), "exists": p.exists()}
        if not p.exists():
            return info
        info["size_mb"] = round(p.stat().st_size / 1_048_576, 2)
        try:
            c = sqlite3.connect(path)
            c.row_factory = sqlite3.Row
            if kind == "knowledge":
                info["entries"]  = c.execute("SELECT COUNT(*) FROM entries WHERE is_active=1").fetchone()[0]
                info["versions"] = c.execute("SELECT COUNT(*) FROM entry_versions WHERE is_current=1").fetchone()[0]
                info["flagged"]  = c.execute("SELECT COUNT(*) FROM entry_versions WHERE is_flagged=1 AND is_current=1").fetchone()[0]
            elif kind == "chat":
                info["messages"] = c.execute("SELECT COUNT(*) FROM chat_history").fetchone()[0]
            c.close()
        except Exception:
            pass
        return info

    # ── Scheduler ──────────────────────────────────────────────────────────────
    sched = {}
    try:
        if SCHEDULER_STATE_FILE.exists():
            raw = json.loads(SCHEDULER_STATE_FILE.read_text())
            for job, data in raw.items():
                sched[job] = {k: data.get(k) for k in
                    ("enabled", "is_running", "last_run_status", "last_run_at", "last_run_duration_sec")}
    except Exception:
        pass

    return {
        "checked_at": checked_at,
        "services": {
            "api":           {"status": "ok"},
            "gemini":        {"status": gemini_status, "model": LLM_MODEL, "response_ms": gemini_ms},
            "chromadb":      {"status": chroma_status},
            "postgres":      {"status": pg_status,    "response_ms": pg_ms},
            "skills_server": {"status": skills_status, "url": SKILLS_URL,   "response_ms": skills_ms},
        },
        "models":    models,
        "databases": {
            "knowledge":   _db_info(KNOWLEDGE_DB, "knowledge"),
            "chat_history": _db_info(CHAT_DB,      "chat"),
        },
        "scheduler": sched,
    }


# ═══════════════════════════════════════════════════════════════════════════════
def _scm_scope_status(masterfn: str, companyfn: str) -> dict:
    from scm_training.config import analysis_dir, models_dir, processed_dir, scope_dir

    root = scope_dir(masterfn, companyfn)
    p_dir = processed_dir(masterfn, companyfn)
    m_dir = models_dir(masterfn, companyfn)
    a_dir = analysis_dir(masterfn, companyfn)

    def _file(path: Path) -> dict:
        return {
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else 0,
            "updated_at": datetime.fromtimestamp(path.stat().st_mtime).isoformat() if path.exists() else None,
        }

    processed_files = {
        name: _file(p_dir / f"{name}.parquet")
        for name in [
            "sales_trend",
            "product_analysis",
            "customer_retention",
            "sales_data",
            "sales_main",
            "revenue_report_by_date",
        ]
    }
    model_files = {
        "sales_forecaster": _file(m_dir / "sales_forecaster.pkl"),
        "churn_predictor": _file(m_dir / "churn_predictor.pkl"),
    }

    return {
        "masterfn": masterfn,
        "companyfn": companyfn,
        "root": str(root),
        "exists": root.exists(),
        "processed_dir": str(p_dir),
        "models_dir": str(m_dir),
        "analysis_dir": str(a_dir),
        "processed": processed_files,
        "models": model_files,
        "ready": {
            "forecast": model_files["sales_forecaster"]["exists"] and processed_files["sales_trend"]["exists"],
            "churn": model_files["churn_predictor"]["exists"] and processed_files["customer_retention"]["exists"],
            "demand_forecast": processed_files["product_analysis"]["exists"],
            "product_trend": True,
        },
    }


@app.get("/admin/scm-training/status")
async def admin_scm_training_status(
    masterfn: str = "",
    companyfn: str = "",
    _key: str = Depends(verify_api_key),
):
    from scm_training.config import ARTIFACT_DIR

    if masterfn and companyfn:
        return _scm_scope_status(masterfn, companyfn)

    scopes = []
    if ARTIFACT_DIR.exists():
        for db_dir in ARTIFACT_DIR.iterdir():
            if not db_dir.is_dir():
                continue
            for master_dir in db_dir.iterdir():
                if not master_dir.is_dir():
                    continue
                for company_dir in master_dir.iterdir():
                    if company_dir.is_dir():
                        scopes.append(_scm_scope_status(master_dir.name, company_dir.name))

    return {"scopes": scopes, "count": len(scopes)}


@app.post("/admin/scm-training/run")
async def admin_scm_training_run(
    body: ScmTrainingRunRequest,
    request: Request,
    _key: str = Depends(verify_api_key),
):
    model = body.model if body.model in {"all", "forecast", "churn"} else "all"

    if body.masterfn == "*":
        args = [sys.executable, "-m", "scm_training.main", "train-db", "--model", model]
        if body.date_from:
            args += ["--date-from", body.date_from]
        if body.date_to:
            args += ["--date-to", body.date_to]
        subprocess.Popen(args, cwd=str(Path(__file__).parent))
        return {"queued": True, "mode": "train_db", "model": model}

    extract_args = [
        sys.executable, "-m", "scm_training.main", "extract",
        "--masterfn", body.masterfn,
        "--companyfn", body.companyfn,
    ]
    if body.date_from:
        extract_args += ["--date-from", body.date_from]
    if body.date_to:
        extract_args += ["--date-to", body.date_to]

    train_args = [
        sys.executable, "-m", "scm_training.main", "train",
        "--model", model,
        "--masterfn", body.masterfn,
        "--companyfn", body.companyfn,
    ]

    def _run_extract_train():
        subprocess.run(extract_args, cwd=str(Path(__file__).parent), check=False)
        subprocess.run(train_args, cwd=str(Path(__file__).parent), check=False)

    threading.Thread(target=_run_extract_train, daemon=True, name="scm-training-run").start()

    kconn = get_knowledge_conn()
    _ensure_admin_tables(kconn)
    log_admin_action(kconn, body.admin_user_id, "scm_training_run",
                     target_type="scm_training",
                     target_id=f"{body.masterfn}/{body.companyfn}",
                     note=f"Queued extract + train model={model}",
                     ip=_get_client_ip(request))
    kconn.close()
    return {"queued": True, "mode": "extract_then_train", "model": model, "masterfn": body.masterfn, "companyfn": body.companyfn}


# PHASE 6 — User Analytics
# ═══════════════════════════════════════════════════════════════════════════════

def _anl_date_threshold(days: int) -> str:
    """ISO date string N days ago, for use in SQLite WHERE clauses."""
    from datetime import timedelta
    return (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")


@app.get("/admin/analytics/overview")
async def analytics_overview(
    company_id: Optional[str] = None,
    days:       int = 30,
    _key: str = Depends(verify_api_key),
):
    if not os.path.exists(CHAT_DB):
        return {"active_users": 0, "total_messages": 0, "feedback_given": 0,
                "positive_rate": 0.0, "companies": [], "language_dist": {},
                "response_len_dist": {}}

    since = _anl_date_threshold(days)
    cconn = get_chat_conn()

    co_filter_ch = ""
    co_filter_fb = ""
    co_params_ch: list = [since]
    co_params_fb: list = [since]
    if company_id:
        co_filter_ch = " AND company_id = ?"
        co_filter_fb = " AND company_id = ?"
        co_params_ch.append(company_id)
        co_params_fb.append(company_id)

    active_users = cconn.execute(
        f"SELECT COUNT(DISTINCT user_id) FROM chat_history "
        f"WHERE role='user' AND timestamp >= ?{co_filter_ch}",
        co_params_ch,
    ).fetchone()[0]

    total_messages = cconn.execute(
        f"SELECT COUNT(*) FROM chat_history "
        f"WHERE role='user' AND timestamp >= ?{co_filter_ch}",
        co_params_ch,
    ).fetchone()[0]

    fb_row = cconn.execute(
        f"SELECT COUNT(*) AS total, "
        f"SUM(CASE WHEN rating='up' THEN 1 ELSE 0 END) AS up "
        f"FROM feedback_log WHERE created_at >= ?{co_filter_fb}",
        co_params_fb,
    ).fetchone()
    feedback_given = fb_row["total"] or 0
    positive_rate  = round((fb_row["up"] or 0) / feedback_given * 100, 1) if feedback_given else 0.0

    # per-company breakdown
    comp_rows = cconn.execute(
        f"SELECT company_id, COUNT(*) AS messages, COUNT(DISTINCT user_id) AS users "
        f"FROM chat_history WHERE role='user' AND timestamp >= ?"
        f"{co_filter_ch} GROUP BY company_id ORDER BY messages DESC",
        co_params_ch,
    ).fetchall()
    companies = [{"code": r["company_id"] or "—", "messages": r["messages"], "users": r["users"]}
                 for r in comp_rows]

    # language distribution (all-time, from user_preferences)
    lang_rows = cconn.execute(
        "SELECT language, COUNT(*) AS cnt FROM user_preferences GROUP BY language"
    ).fetchall()
    language_dist = {r["language"]: r["cnt"] for r in lang_rows}

    rlen_rows = cconn.execute(
        "SELECT response_len, COUNT(*) AS cnt FROM user_preferences GROUP BY response_len"
    ).fetchall()
    response_len_dist = {r["response_len"]: r["cnt"] for r in rlen_rows}

    cconn.close()
    return {
        "active_users":      active_users,
        "total_messages":    total_messages,
        "feedback_given":    feedback_given,
        "positive_rate":     positive_rate,
        "companies":         companies,
        "language_dist":     language_dist,
        "response_len_dist": response_len_dist,
    }


@app.get("/admin/analytics/messages")
async def analytics_messages(
    company_id: Optional[str] = None,
    days:       int = 14,
    _key: str = Depends(verify_api_key),
):
    if not os.path.exists(CHAT_DB):
        return {"labels": [], "messages": [], "users": []}

    since = _anl_date_threshold(days)
    cconn = get_chat_conn()

    params: list = [since]
    co_filter = ""
    if company_id:
        co_filter = " AND company_id = ?"
        params.append(company_id)

    rows = cconn.execute(
        f"SELECT date(timestamp) AS day, "
        f"COUNT(*) AS messages, COUNT(DISTINCT user_id) AS users "
        f"FROM chat_history WHERE role='user' AND timestamp >= ?{co_filter} "
        f"GROUP BY day ORDER BY day",
        params,
    ).fetchall()
    cconn.close()

    # fill in missing dates with zeros
    from datetime import timedelta, date as date_type
    start = date_type.fromisoformat(since)
    end   = datetime.utcnow().date()
    day_map = {r["day"]: r for r in rows}
    labels, messages, users = [], [], []
    cur = start
    while cur <= end:
        key = cur.isoformat()
        labels.append(cur.strftime("%m/%d"))
        r = day_map.get(key)
        messages.append(r["messages"] if r else 0)
        users.append(r["users"] if r else 0)
        cur += timedelta(days=1)

    return {"labels": labels, "messages": messages, "users": users}


@app.get("/admin/analytics/feedback-trend")
async def analytics_feedback_trend(
    company_id: Optional[str] = None,
    days:       int = 30,
    _key: str = Depends(verify_api_key),
):
    if not os.path.exists(CHAT_DB):
        return {"labels": [], "thumbs_up": [], "thumbs_down": []}

    since = _anl_date_threshold(days)
    cconn = get_chat_conn()

    params: list = [since]
    co_filter = ""
    if company_id:
        co_filter = " AND company_id = ?"
        params.append(company_id)

    rows = cconn.execute(
        f"SELECT date(created_at) AS day, "
        f"SUM(CASE WHEN rating='up'   THEN 1 ELSE 0 END) AS up, "
        f"SUM(CASE WHEN rating='down' THEN 1 ELSE 0 END) AS down "
        f"FROM feedback_log WHERE created_at >= ?{co_filter} "
        f"GROUP BY day ORDER BY day",
        params,
    ).fetchall()
    cconn.close()

    from datetime import timedelta, date as date_type
    start = date_type.fromisoformat(since)
    end   = datetime.utcnow().date()
    day_map = {r["day"]: r for r in rows}
    labels, ups, downs = [], [], []
    cur = start
    while cur <= end:
        key = cur.isoformat()
        labels.append(cur.strftime("%m/%d"))
        r = day_map.get(key)
        ups.append(r["up"] if r else 0)
        downs.append(r["down"] if r else 0)
        cur += timedelta(days=1)

    return {"labels": labels, "thumbs_up": ups, "thumbs_down": downs}


@app.get("/admin/analytics/top-queries")
async def analytics_top_queries(
    company_id: Optional[str] = None,
    days:       int = 30,
    limit:      int = 10,
    _key: str = Depends(verify_api_key),
):
    empty = {"domains": [], "reasons": [], "queries": []}
    if not os.path.exists(CHAT_DB):
        return empty

    since = _anl_date_threshold(days)
    cconn = get_chat_conn()

    params_base: list = [since]
    co_filter = ""
    if company_id:
        co_filter = " AND company_id = ?"
        params_base.append(company_id)

    # downvote reasons
    reason_rows = cconn.execute(
        f"SELECT reason, COUNT(*) AS cnt FROM feedback_log "
        f"WHERE rating='down' AND reason IS NOT NULL AND created_at >= ?{co_filter} "
        f"GROUP BY reason ORDER BY cnt DESC",
        params_base,
    ).fetchall()
    reasons = [{"reason": r["reason"], "count": r["cnt"]} for r in reason_rows]

    # top query texts (min 1 occurrence, from feedback_log.query_text)
    query_rows = cconn.execute(
        f"SELECT query_text, COUNT(*) AS cnt FROM feedback_log "
        f"WHERE query_text IS NOT NULL AND query_text != '' AND created_at >= ?{co_filter} "
        f"GROUP BY query_text ORDER BY cnt DESC LIMIT ?",
        params_base + [limit],
    ).fetchall()
    queries = [{"text": r["query_text"], "count": r["cnt"]} for r in query_rows]

    # entry_version_ids mentioned in feedback → look up domains via knowledge DB
    ev_rows = cconn.execute(
        f"SELECT DISTINCT entry_version_id FROM feedback_log "
        f"WHERE entry_version_id IS NOT NULL AND created_at >= ?{co_filter}",
        params_base,
    ).fetchall()
    cconn.close()

    domains: list = []
    if ev_rows and os.path.exists(KNOWLEDGE_DB):
        ev_ids = [r["entry_version_id"] for r in ev_rows]
        placeholders = ",".join("?" * len(ev_ids))
        kconn = get_knowledge_conn()
        dom_rows = kconn.execute(
            f"SELECT d.name, COUNT(DISTINCT ev.id) AS cnt "
            f"FROM entry_versions ev "
            f"JOIN entries e ON e.id = ev.entry_id "
            f"JOIN features f ON f.id = e.feature_id "
            f"JOIN domains d ON d.id = f.domain_id "
            f"WHERE ev.id IN ({placeholders}) "
            f"GROUP BY d.name ORDER BY cnt DESC",
            ev_ids,
        ).fetchall()
        kconn.close()
        domains = [{"name": r["name"], "count": r["cnt"]} for r in dom_rows]

    return {"domains": domains, "reasons": reasons, "queries": queries}


@app.get("/admin/analytics/users")
async def analytics_users(
    company_id: Optional[str] = None,
    days:       int = 30,
    limit:      int = 20,
    offset:     int = 0,
    _key: str = Depends(verify_api_key),
):
    if not os.path.exists(CHAT_DB):
        return {"total": 0, "items": []}

    since = _anl_date_threshold(days)
    cconn = get_chat_conn()

    params: list = [since]
    co_filter = ""
    if company_id:
        co_filter = " AND ch.company_id = ?"
        params.append(company_id)

    base = f"""
        FROM (
            SELECT user_id, company_id,
                   COUNT(*) AS messages,
                   MAX(timestamp) AS last_seen
            FROM chat_history
            WHERE role='user' AND timestamp >= ?{co_filter}
            GROUP BY user_id, company_id
        ) ch
        LEFT JOIN (
            SELECT user_id, company_id,
                   COUNT(*) AS feedback_count,
                   SUM(CASE WHEN rating='up' THEN 1 ELSE 0 END) AS fb_up
            FROM feedback_log
            GROUP BY user_id, company_id
        ) fb ON fb.user_id = ch.user_id AND fb.company_id = ch.company_id
        LEFT JOIN user_preferences up
               ON up.user_id = ch.user_id AND up.company_id = ch.company_id
    """

    total = cconn.execute(f"SELECT COUNT(*) {base}", params).fetchone()[0]
    rows  = cconn.execute(
        f"SELECT ch.user_id, ch.company_id, ch.messages, ch.last_seen, "
        f"COALESCE(fb.feedback_count, 0) AS feedback_count, "
        f"COALESCE(fb.fb_up, 0) AS fb_up, "
        f"COALESCE(up.language, 'auto') AS language, "
        f"COALESCE(up.response_len, 'normal') AS response_len "
        f"{base} ORDER BY ch.messages DESC LIMIT ? OFFSET ?",
        params + [limit, offset],
    ).fetchall()
    cconn.close()

    items = []
    for r in rows:
        fc = r["feedback_count"]
        positive_rate = round(r["fb_up"] / fc * 100, 1) if fc else None
        items.append({
            "user_id":       r["user_id"],
            "company_id":    r["company_id"],
            "messages":      r["messages"],
            "last_seen":     r["last_seen"],
            "feedback_count": fc,
            "positive_rate": positive_rate,
            "language":      r["language"],
            "response_len":  r["response_len"],
        })

    return {"total": total, "items": items}
