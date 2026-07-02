"""
ERP AI Assistant — Chat Pipeline
Query rewriting, history management, preferences, and the main chat streaming logic.
"""
import json
import re
import os
import asyncio
import concurrent.futures
from datetime import datetime

from api.config import LLM_MODEL, IMAGES_DIR
from api.database import get_chat_conn, get_knowledge_conn
from api.llm import (
    _gemini_client, build_system_prompt, MAIN_PROMPT, GREETING_PROMPT,
    parse_response, run_data_query, run_scm_special_query, _lang_code,
    _looks_like_scm_analytics,
)
from api.search import (
    detect_intent, build_chart_suggestion, search_knowledge,
    format_knowledge_context, build_step_image_map,
)

# ─── Chat DB & Preferences ────────────────────────────────────────────────────

def get_user_prefs(user_id: str, company_id: str) -> dict:
    conn = get_chat_conn()
    row = conn.execute(
        "SELECT language, response_len FROM user_preferences WHERE user_id=? AND company_id=?",
        (user_id, company_id)
    ).fetchone()
    conn.close()
    return dict(row) if row else {"language": "auto", "response_len": "normal"}


def update_user_prefs(user_id: str, company_id: str, **kwargs):
    conn = get_chat_conn()
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
    t = text.lower()
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


def get_session_history(user_id: str, company_id: str, session_id: str, limit: int = 10,
                        before_id: int = None) -> tuple[list, bool]:
    conn = get_chat_conn()
    params = [user_id, company_id, session_id]
    query = """
        SELECT id, role, content, timestamp FROM chat_history
        WHERE user_id=? AND company_id=? AND session_id=?
    """
    if before_id:
        query += " AND id < ?"
        params.append(before_id)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit + 1)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    has_more = len(rows) > limit
    rows = rows[:limit]
    return list(reversed(rows)), has_more


def save_message(user_id: str, company_id: str, role: str, content: str, session_id: str = ""):
    conn = get_chat_conn()
    conn.execute("""
        INSERT INTO chat_history (user_id, company_id, role, content, timestamp, session_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, company_id, role, content, datetime.now().isoformat(), session_id))
    conn.commit()
    conn.close()


def get_sessions(user_id: str, company_id: str) -> list:
    """Get all sessions for a user, with message count and last message preview."""
    conn = get_chat_conn()
    rows = conn.execute("""
        SELECT cs.session_id, cs.title, cs.created_at, cs.updated_at,
               (SELECT COUNT(*) FROM chat_history ch WHERE ch.session_id = cs.session_id) as msg_count,
               (SELECT content FROM chat_history ch WHERE ch.session_id = cs.session_id AND ch.role='user' ORDER BY ch.id ASC LIMIT 1) as first_user_msg
        FROM chat_sessions cs
        WHERE cs.user_id=? AND cs.company_id=?
        ORDER BY cs.updated_at DESC
    """, (user_id, company_id)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_session(user_id: str, company_id: str, session_id: str, title: str = "Untitled chat"):
    """Create a new chat session."""
    now = datetime.now().isoformat()
    conn = get_chat_conn()
    conn.execute("""
        INSERT OR IGNORE INTO chat_sessions (session_id, user_id, company_id, title, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (session_id, user_id, company_id, title, now, now))
    conn.commit()
    conn.close()


def update_session_title(session_id: str, title: str):
    """Update the title of a chat session."""
    conn = get_chat_conn()
    conn.execute("""
        UPDATE chat_sessions SET title=?, updated_at=? WHERE session_id=?
    """, (title, datetime.now().isoformat(), session_id))
    conn.commit()
    conn.close()


def delete_session(session_id: str, user_id: str, company_id: str):
    """Delete a chat session and all its messages."""
    conn = get_chat_conn()
    conn.execute("DELETE FROM chat_history WHERE session_id=? AND user_id=? AND company_id=?",
                 (session_id, user_id, company_id))
    conn.execute("DELETE FROM chat_sessions WHERE session_id=? AND user_id=? AND company_id=?",
                 (session_id, user_id, company_id))
    conn.commit()
    conn.close()


def delete_recent_conversation(user_id: str, company_id: str, start_message_id: int) -> int:
    """Delete one recent conversation built from a user message and its reply rows."""
    conn = get_chat_conn()
    start = conn.execute("""
        SELECT id FROM chat_history
        WHERE id=? AND user_id=? AND company_id=? AND role='user'
    """, (start_message_id, user_id, company_id)).fetchone()
    if not start:
        conn.close()
        return 0

    next_user = conn.execute("""
        SELECT id FROM chat_history
        WHERE id>? AND user_id=? AND company_id=? AND role='user'
        ORDER BY id ASC LIMIT 1
    """, (start_message_id, user_id, company_id)).fetchone()

    if next_user:
        cur = conn.execute("""
            DELETE FROM chat_history
            WHERE user_id=? AND company_id=? AND id>=? AND id<?
        """, (user_id, company_id, start_message_id, next_user["id"]))
    else:
        cur = conn.execute("""
            DELETE FROM chat_history
            WHERE user_id=? AND company_id=? AND id>=?
        """, (user_id, company_id, start_message_id))

    deleted = cur.rowcount or 0
    conn.commit()
    conn.close()
    return deleted


def format_history(rows: list) -> str:
    if not rows:
        return "No previous conversation."
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
    if not history_text or history_text == "No previous conversation.":
        return ""

    menu_pattern = re.compile(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*>\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*>\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)')

    erp_topic_pattern = re.compile(
        r'\b(Sales\s*Order|Purchase\s*Order|Sales\s*Quotation|Purchase\s*Quotation|'
        r'Delivery\s*Order|Goods\s*Receipt|Invoice|Payment|Receipt|'
        r'Sales\s*Manager|Purchase\s*Manager|Inventory|Stock|'
        r'General\s*Ledger|Account\s*Receivable|Account\s*Payable|'
        r'Human\s*Resources|Employee|Payroll|Leave|'
        r'Project|Asset|Fleet|CRM|Customer|Vendor)\b',
        re.IGNORECASE
    )

    creating_pattern = re.compile(r'(?:Creating|Create|How\s*to|Procedure\s*for)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', re.IGNORECASE)

    lines = history_text.split('\n')
    assistant_lines = [l for l in lines if l.startswith('Assistant:')]

    for line in reversed(assistant_lines[-5:]):
        menu_match = menu_pattern.search(line)
        if menu_match:
            topic = menu_match.group(2).strip()
            print(f"  [topic] Extracted from menu path: {topic}")
            return topic

        topic_match = erp_topic_pattern.search(line)
        if topic_match:
            topic = topic_match.group(1).strip()
            print(f"  [topic] Extracted from ERP term: {topic}")
            return topic

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

    # PRIORITY 1: Explicit step number
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

    # PRIORITY 2: Jump to specific step
    jump_match = _JUMP_STEP_RE.search(user_text)
    if jump_match:
        jump_step = int(jump_match.group(2))
        result["target_step"] = jump_step
        result["navigation_type"] = "jump"
        if previous_topic:
            result["query"] = f"{previous_topic} step {jump_step}"
        print(f"  [nav] Jump to step: {jump_step} with topic: {previous_topic}")
        return result

    # PRIORITY 3: Range query
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

    # PRIORITY 4: Navigation commands
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

    # PRIORITY 5: LLM rewrite with topic context
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


# ─── Ambiguity Check ──────────────────────────────────────────────────────────

def check_ambiguity(query: str, history_text: str, intent: str, lang: str) -> dict:
    """Returns {"ambiguous": bool, "question": str | None}. Fails open on any error."""
    from api.llm import call_gemini_chat

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


# ─── SCM Training Query ───────────────────────────────────────────────────────

def is_scm_training_query(query: str) -> bool:
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


# ─── Capabilities Builder ─────────────────────────────────────────────────────

CAPABILITY_MATRIX = [
    {
        "id": "100.01",
        "requirement": "Core Finance Module Features",
        "status": "Partial",
        "coverage_en": "GL, AR, AP, and bank-reconciliation guidance exist in the assistant knowledge layer; finance-related query skills are present.",
        "gap_en": "No end-to-end budgeting, forecasting, or finance automation workflow.",
        "coverage_vi": "Có hướng dẫn GL, AR, AP và bank reconciliation; cũng có các skill truy vấn dữ liệu tài chính.",
        "gap_vi": "Chưa có luồng budgeting, forecasting hay tự động hóa nghiệp vụ tài chính.",
    },
    {
        "id": "100.02",
        "requirement": "InvoiceNow-Ready Solution Provider Accreditation",
        "status": "Not yet",
        "coverage_en": "No accreditation or IMDA listing logic is present in the repo.",
        "gap_en": "Accreditation is an external compliance state and is not verified by the assistant.",
        "coverage_vi": "Chưa có logic kiểm tra accreditation hoặc IMDA listing trong repo.",
        "gap_vi": "Đây là trạng thái tuân thủ bên ngoài, assistant chưa thể xác minh.",
    },
    {
        "id": "100.03",
        "requirement": "AI Features",
        "status": "Partial",
        "coverage_en": "The assistant itself is AI-driven and answers ERP questions.",
        "gap_en": "Product-level AI feature coverage is incomplete and not tied to a formal capability layer yet.",
        "coverage_vi": "Bản thân assistant đã là AI và đang trả lời câu hỏi ERP.",
        "gap_vi": "Các tính năng AI ở cấp sản phẩm chưa được chuẩn hóa thành capability rõ ràng.",
    },
    {
        "id": "100.04",
        "requirement": "AI Automated Invoice Processing",
        "status": "Not yet",
        "coverage_en": "No invoice OCR, auto-match, or approval-route implementation is present.",
        "gap_en": "Missing invoice capture pipeline.",
        "coverage_vi": "Chưa có OCR hóa đơn, auto-match hay routing phê duyệt.",
        "gap_vi": "Thiếu toàn bộ pipeline capture và xử lý hóa đơn.",
    },
    {
        "id": "100.05",
        "requirement": "AI Automated Journal Entry Suggestions",
        "status": "Not yet",
        "coverage_en": "No journal suggestion engine or posting recommendation workflow is present.",
        "gap_en": "Missing accounting suggestion logic.",
        "coverage_vi": "Chưa có engine gợi ý bút toán hay workflow đề xuất posting.",
        "gap_vi": "Thiếu logic đề xuất kế toán.",
    },
    {
        "id": "100.06",
        "requirement": "AI Anomaly Detection and Fraud Prevention",
        "status": "Not yet",
        "coverage_en": "No transaction anomaly or duplicate-payment detection pipeline is present.",
        "gap_en": "Missing monitoring and alerting logic.",
        "coverage_vi": "Chưa có pipeline phát hiện bất thường hoặc thanh toán trùng.",
        "gap_vi": "Thiếu giám sát và cảnh báo.",
    },
    {
        "id": "100.07",
        "requirement": "Other AI Features",
        "status": "Not yet",
        "coverage_en": "No extra AI feature registry is defined.",
        "gap_en": "Needs explicit product definition.",
        "coverage_vi": "Chưa có danh mục AI feature bổ sung.",
        "gap_vi": "Cần định nghĩa rõ thêm theo product scope.",
    },
    {
        "id": "102.01",
        "requirement": "Procurement & Purchasing Features",
        "status": "Partial",
        "coverage_en": "Purchase-order browsing and purchasing guidance exist.",
        "gap_en": "No full procurement workflow automation.",
        "coverage_vi": "Có browsing và hướng dẫn mua hàng / purchase order.",
        "gap_vi": "Chưa có tự động hóa procurement end-to-end.",
    },
    {
        "id": "102.02",
        "requirement": "Procurement & Purchasing Features Detail",
        "status": "Partial",
        "coverage_en": "PO, supplier, and confirmation data paths exist, and the assistant can guide workflows.",
        "gap_en": "Missing complete end-to-end procurement execution checks.",
        "coverage_vi": "Có data path cho PO, supplier và confirmation, cùng hướng dẫn thao tác.",
        "gap_vi": "Chưa có kiểm tra execution đầy đủ cho quy trình procurement.",
    },
    {
        "id": "102.03",
        "requirement": "Warehouse & Inventory Features",
        "status": "Partial",
        "coverage_en": "Inventory guidance and stock lookup logic exist.",
        "gap_en": "No full warehouse execution layer.",
        "coverage_vi": "Có hướng dẫn inventory và logic tra cứu tồn kho.",
        "gap_vi": "Chưa có lớp vận hành warehouse đầy đủ.",
    },
    {
        "id": "102.04",
        "requirement": "Warehouse & Inventory Features Detail",
        "status": "Partial",
        "coverage_en": "Reorder and replenishment analysis are partially covered by current skills and query helpers.",
        "gap_en": "Multi-location warehouse operations are not fully modeled.",
        "coverage_vi": "Đã cover một phần reorder và replenishment qua skills và query helpers.",
        "gap_vi": "Chưa mô hình hóa đầy đủ multi-location warehouse.",
    },
    {
        "id": "102.05",
        "requirement": "AI Features",
        "status": "Partial",
        "coverage_en": "SCM / forecasting-related code exists in the repo.",
        "gap_en": "Not yet exposed as a productized AI capability with clear coverage.",
        "coverage_vi": "Trong repo đã có code liên quan SCM / forecasting.",
        "gap_vi": "Chưa được productize thành capability rõ ràng.",
    },
    {
        "id": "102.06",
        "requirement": "AI Demand Forecasting",
        "status": "Partial",
        "coverage_en": "SCM training and forecasting code exists for scoped analysis.",
        "gap_en": "Needs clearer runtime integration and test coverage.",
        "coverage_vi": "Có code training / forecasting cho phạm vi SCM.",
        "gap_vi": "Cần tích hợp runtime rõ hơn và có test coverage.",
    },
    {
        "id": "102.07",
        "requirement": "AI Replenishment Recommendations",
        "status": "Partial",
        "coverage_en": "Inventory reorder logic is present in the query / skill layer.",
        "gap_en": "Needs stronger explanation and productized output.",
        "coverage_vi": "Có logic reorder ở lớp query / skill.",
        "gap_vi": "Cần output chuẩn hóa và dễ dùng hơn.",
    },
    {
        "id": "102.08",
        "requirement": "AI Stock Anomaly Detection",
        "status": "Not yet",
        "coverage_en": "No stock anomaly detection pipeline is present.",
        "gap_en": "Missing detection model and alerts.",
        "coverage_vi": "Chưa có pipeline phát hiện bất thường tồn kho.",
        "gap_vi": "Thiếu model và cảnh báo.",
    },
    {
        "id": "102.09",
        "requirement": "Other AI Features",
        "status": "Not yet",
        "coverage_en": "No additional AI feature backlog is defined.",
        "gap_en": "Needs product definition.",
        "coverage_vi": "Chưa có backlog AI feature bổ sung.",
        "gap_vi": "Cần định nghĩa theo product scope.",
    },
]


def _build_capability_matrix_section(lang: str) -> str:
    if lang == "vi":
        lines = [
            "",
            "## Độ phủ theo requirement",
            "",
            "| Mã | Requirement | Trạng thái | Độ phủ hiện tại | Khoảng trống |",
            "|---|---|---|---|---|",
        ]
        for item in CAPABILITY_MATRIX:
            lines.append(
                f"| {item['id']} | {item['requirement']} | {item['status']} | "
                f"{item['coverage_vi']} | {item['gap_vi']} |"
            )
        lines += [
            "",
            "## Tóm tắt nhanh",
            "",
            "- Hỗ trợ tốt nhất hiện tại: hướng dẫn ERP theo bước, sales / purchase / inventory / finance / CRM / HR / project.",
            "- Hỗ trợ một phần: procurement analysis, reorder logic, SCM forecasting, session history pagination.",
            "- Chưa có: InvoiceNow accreditation, invoice OCR, journal suggestions, anomaly detection, fraud prevention.",
        ]
    else:
        lines = [
            "",
            "## Requirement coverage",
            "",
            "| ID | Requirement | Status | Current coverage | Gap |",
            "|---|---|---|---|---|",
        ]
        for item in CAPABILITY_MATRIX:
            lines.append(
                f"| {item['id']} | {item['requirement']} | {item['status']} | "
                f"{item['coverage_en']} | {item['gap_en']} |"
            )
        lines += [
            "",
            "## Quick summary",
            "",
            "- Best covered today: step-by-step ERP guidance across sales, purchase, inventory, finance, CRM, HR, and project topics.",
            "- Partial coverage: procurement analysis, reorder logic, SCM forecasting, and session-scoped history.",
            "- Not yet covered: InvoiceNow accreditation, invoice OCR, journal suggestions, anomaly detection, and fraud prevention.",
        ]
    return "\n".join(lines)


def _build_capabilities_response(lang: str) -> str:
    """Build a dynamic list of topics the assistant can help with, from the knowledge DB."""
    try:
        conn = get_knowledge_conn()
        domains = conn.execute(
            "SELECT id, name FROM domains ORDER BY sort_order, name"
        ).fetchall()
        features = conn.execute(
            "SELECT f.id, f.name, d.name as domain FROM features f "
            "JOIN domains d ON f.domain_id = d.id ORDER BY d.sort_order, f.sort_order, f.name"
        ).fetchall()
        conn.close()
    except Exception:
        domains = []
        features = []

    if lang == "vi":
        lines = [
            "Xin chào! 👋 Tôi là trợ lý AI cho **Globe3 ERP** của TNO Systems.",
            "",
            "Tôi có thể giúp bạn với các chủ đề sau:",
            "",
        ]
    else:
        lines = [
            "Hello! 👋 I'm the AI assistant for **Globe3 ERP** by TNO Systems.",
            "",
            "I can help you with the following topics:",
            "",
        ]

    if domains:
        for d in domains:
            dname = d["name"]
            d_features = [f["name"] for f in features if f["domain"] == dname]
            if d_features:
                feat_list = ", ".join(d_features[:8])
                if len(d_features) > 8:
                    feat_list += f" +{len(d_features) - 8} more"
                lines.append(f"  📂 **{dname}**: {feat_list}")
            else:
                lines.append(f"  📂 **{dname}**")
    else:
        if lang == "vi":
            lines.append("  📂 **Bán hàng**: Sales Order, Quotation, Invoice, Delivery Order, SO Confirmation")
            lines.append("  📂 **Mua hàng**: Purchase Order, PO Confirmation, Goods Receipt, Purchase Invoice")
            lines.append("  📂 **Kho**: Inventory, Stock Item, Stock Transfer, Reorder")
            lines.append("  📂 **Tài chính**: General Ledger, Accounts Receivable, Accounts Payable")
            lines.append("  📂 **Dự án**: Project Master, Project Management")
            lines.append("  📂 **Nhân sự**: HR, Employee, Payroll, Leave")
            lines.append("  📂 **CRM**: Customer Management")
        else:
            lines.append("  📂 **Sales**: Sales Order, Quotation, Invoice, Delivery Order, SO Confirmation")
            lines.append("  📂 **Purchase**: Purchase Order, PO Confirmation, Goods Receipt, Purchase Invoice")
            lines.append("  📂 **Inventory**: Stock Item, Stock Transfer, Reorder")
            lines.append("  📂 **Finance**: General Ledger, Accounts Receivable, Accounts Payable")
            lines.append("  📂 **Project**: Project Master, Project Management")
            lines.append("  📂 **HR**: Employee, Payroll, Leave")
            lines.append("  📂 **CRM**: Customer Management")

    if lang == "vi":
        lines += [
            "",
            "💡 **Ví dụ câu hỏi bạn có thể hỏi:**",
            '  • "Cách tạo Sales Order"',
            '  • "Hướng dẫn duyệt Purchase Invoice"',
            '  • "Tồn kho hiện tại của mặt hàng A"',
            '  • "Công nợ khách hàng X"',
            '  • "Lỗi không post được Delivery Order"',
            '  • "Top 10 sản phẩm bán chạy"',
            '  • "Dự báo doanh thu tháng sau"',
            "",
            "Bạn muốn tìm hiểu về chủ đề nào? 😊",
        ]
    else:
        lines += [
            "",
            "💡 **Example questions you can ask:**",
            '  • "How to create a Sales Order"',
            '  • "Guide to approve Purchase Invoice"',
            '  • "Current stock of item A"',
            '  • "AR aging for customer X"',
            '  • "Cannot post Delivery Order error"',
            '  • "Top 10 best-selling products"',
            '  • "Revenue forecast for next month"',
            "",
            "What topic would you like to explore? 😊",
        ]

    lines.append(_build_capability_matrix_section(lang))
    return "\n".join(lines)


def _is_capability_question(text: str) -> bool:
    q = (text or "").lower()
    terms = [
        "invoicenow",
        "invoice now",
        "invoice processing",
        "invoice ocr",
        "journal entry",
        "suggest journal",
        "journal suggestions",
        "anomaly detection",
        "fraud prevention",
        "stock anomaly",
        "budgeting",
        "forecasting",
        "ai features",
        "what can you do",
        "what do you support",
        "bạn làm được gì",
        "bạn hỗ trợ gì",
        "khả năng của bạn",
        "chức năng của bạn",
    ]
    return any(term in q for term in terms)


# ─── Main Chat Stream Generator ───────────────────────────────────────────────

async def generate_chat_stream(q, history_text, prefs, system_prompt):
    """Async generator that yields SSE events for the chat/stream endpoint."""
    from tqdm import tqdm

    session_id = (q.session_id or "").strip()
    if not session_id:
        import uuid
        session_id = str(uuid.uuid4())
        q.session_id = session_id
    create_session(q.user_id, q.company_id, session_id, title=q.text[:80].strip() or "Untitled chat")

    yield f"event: status\ndata: {json.dumps({'text': 'Searching knowledge base...'})}\n\n"

    search_query = await asyncio.get_running_loop().run_in_executor(
        None, rewrite_query, q.text, history_text
    )

    topic_hint = search_query.get("topic", "")

    chart_suggestion = build_chart_suggestion(search_query.get("query") or q.text)

    # Detect intent
    intent = detect_intent(q.text)

    _rewritten_q = search_query["query"]
    if intent != "data_query" and search_query.get("is_followup") and _rewritten_q != q.text:
        intent_rewrite = detect_intent(_rewritten_q)
        if intent_rewrite == "data_query":
            intent = "data_query"
            print(f"  [intent] data_query via rewrite: '{_rewritten_q}'")

    # ── SCM analytics shortcut ───────────────────────────────────────────────
    _lc = _lang_code(q.lang)
    _masterfn = q.masterfn or q.company_code or ""
    _companyfn = q.companyfn or q.company_id or ""
    _scm_like = _looks_like_scm_analytics(q.text)
    _scm_md = await asyncio.get_running_loop().run_in_executor(
        None, run_scm_special_query, q.text, _masterfn, _companyfn, _lc, history_text
    )
    if _scm_md:
        _status = "Đang xử lý câu hỏi SCM..." if _lc == "vi" else "Processing SCM question..."
        yield f"event: status\ndata: {json.dumps({'text': _status})}\n\n"
        yield f"event: intro\ndata: {json.dumps({'text': _scm_md})}\n\n"
        save_message(q.user_id, q.company_id, "user", q.text, session_id=session_id)
        save_message(q.user_id, q.company_id, "assistant", _scm_md, session_id=session_id)
        yield f"event: total\ndata: {json.dumps({'total': 0})}\n\n"
        yield f"event: meta\ndata: {json.dumps({'sources': [], 'version_ids': []})}\n\n"
        yield f"event: done\ndata: {{}}\n\n"
        return
    if _scm_like:
        _status = "Đang xử lý câu hỏi SCM..." if _lc == "vi" else "Processing SCM question..."
        yield f"event: status\ndata: {json.dumps({'text': _status})}\n\n"
        _scm_fail = (
            "⚠️ Không thể định tuyến câu hỏi SCM này vào skill dữ liệu. Vui lòng kiểm tra session ERP hoặc cấu hình skills server."
            if _lc == "vi"
            else "⚠️ Could not route this SCM question to the data skill. Please check the ERP session or skills server configuration."
        )
        yield f"event: intro\ndata: {json.dumps({'text': _scm_fail})}\n\n"
        save_message(q.user_id, q.company_id, "user", q.text, session_id=session_id)
        save_message(q.user_id, q.company_id, "assistant", _scm_fail, session_id=session_id)
        yield f"event: total\ndata: {json.dumps({'total': 0})}\n\n"
        yield f"event: meta\ndata: {json.dumps({'sources': [], 'version_ids': []})}\n\n"
        yield f"event: done\ndata: {{}}\n\n"
        return

    # ── Data query branch ─────────────────────────────────────────────────────
    if intent == "data_query":
        _status = "Đang truy vấn dữ liệu ERP..." if _lc == "vi" else "Querying ERP data..."
        yield f"event: status\ndata: {json.dumps({'text': _status})}\n\n"
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
        parts = result_md.rsplit('\n\n', 1)
        _intro_text = parts[0].strip() if len(parts) == 2 else result_md.strip()
        _closing_text = parts[1].strip() if len(parts) == 2 else ""
        yield f"event: intro\ndata: {json.dumps({'text': _intro_text})}\n\n"
        if _closing_text:
            yield f"event: closing\ndata: {json.dumps({'text': _closing_text})}\n\n"
        _result_lc = result_md.lstrip().lower()
        if chart_suggestion and not (
            _result_lc.startswith(("no matching erp data", "there is no", "there are no"))
            or result_md.lstrip().startswith("⚠️")
        ):
            yield f"event: chart_suggestion\ndata: {json.dumps(chart_suggestion, ensure_ascii=False)}\n\n"
        save_message(q.user_id, q.company_id, "user", q.text, session_id=session_id)
        save_message(q.user_id, q.company_id, "assistant", result_md, session_id=session_id)
        yield f"event: total\ndata: {json.dumps({'total': 0})}\n\n"
        yield f"event: meta\ndata: {json.dumps({'sources': [], 'version_ids': []})}\n\n"
        yield f"event: done\ndata: {{}}\n\n"
        return

    # ── Meta-questions (capabilities / what-can-you-do) ───────────────────────
    META_QUERY_PATTERNS = [
        r"what (can|do) you (do|help|answer|tell)",
        r"list (questions|capabilities|features|topics|things)",
        r"does (the )?(solution|system|assistant) (provide|support|cover|meet|include|have|incorporate)",
        r"can (it|this|the system|the solution) (support|do|handle|cover)",
        r"is (it|this|the system|the solution) (supported|ready|available|compliant)",
        r"what (is|are) (supported|available|covered)",
        r"câu hỏi (bạn|mày) (có thể|trả lời)",
        r"bạn (có thể|biết|giúp) (làm|trả lời|gì)",
        r"bạn làm được (những )?gì",
        r"what are you (capable of|good at)",
        r"show me what you (can do|know)",
        r"what (kind|type|sort) of (questions|things)",
        r"những câu hỏi (nào|gì)",
        r"list (câu hỏi|chủ đề|domain)",
        r"bạn biết (những )?gì",
        r"bạn hỗ trợ (những )?gì",
        r"bạn giúp được gì",
        r"chức năng (của )?bạn",
        r"khả năng (của )?bạn",
        r"you can help me with",
        r"what do you know about",
    ]
    _is_meta = any(re.search(p, q.text.lower()) for p in META_QUERY_PATTERNS) or _is_capability_question(q.text)

    if _is_meta:
        _lc = _lang_code(q.lang)
        _status_text = "Đang tổng hợp danh sách chủ đề..." if _lc == "vi" else "Compiling available topics..."
        yield f"event: status\ndata: {json.dumps({'text': _status_text})}\n\n"

        capabilities = _build_capabilities_response(_lc)
        yield f"event: intro\ndata: {json.dumps({'text': capabilities})}\n\n"
        save_message(q.user_id, q.company_id, "user", q.text, session_id=session_id)
        save_message(q.user_id, q.company_id, "assistant", capabilities, session_id=session_id)
        yield f"event: total\ndata: {json.dumps({'total': 0})}\n\n"
        yield f"event: meta\ndata: {json.dumps({'sources': [], 'version_ids': []})}\n\n"
        yield f"event: done\ndata: {{}}\n\n"
        return

    # ── RAG knowledge search ──────────────────────────────────────────────────
    entries = search_knowledge(
        query=search_query["query"],
        company_code=q.company_code or q.company_id,
        topic_hint=topic_hint,
        intent=intent,
    )

    if not entries and search_query["query"] != q.text:
        print(f"  [rewrite] No results for rewritten query, retrying with original")
        entries = search_knowledge(
            query=q.text,
            company_code=q.company_code or q.company_id,
            topic_hint=topic_hint,
            intent=intent,
        )

    # ── Ambiguity check ───────────────────────────────────────────────────────
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
            save_message(q.user_id, q.company_id, "user", q.text, session_id=session_id)
            save_message(q.user_id, q.company_id, "assistant", _q_text, session_id=session_id)
            yield f"event: total\ndata: {json.dumps({'total': 0})}\n\n"
            yield f"event: meta\ndata: {json.dumps({'sources': [], 'version_ids': []})}\n\n"
            yield f"event: done\ndata: {{}}\n\n"
            return

    target_step = search_query.get("target_step")
    target_steps = search_query.get("target_steps")
    navigation_type = search_query.get("navigation_type")

    step_image_map = {}
    for e in entries:
        step_image_map.update(build_step_image_map(e))

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
        system_prompt=system_prompt,
        history=history_text,
        context=context or "No relevant content found in the knowledge base.",
        question=q.text,
        target_step=target_step if target_step else "None",
        target_steps=target_steps if target_steps else "None",
        navigation_type=navigation_type if navigation_type else "None"
    )

    yield f"event: status\ndata: {json.dumps({'text': 'Generating answer...'})}\n\n"

    loop = asyncio.get_running_loop()
    queue = asyncio.Queue()
    DONE = object()

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

    buffer = ""
    intro_sent = False
    closing_sent = False
    steps_sent = []
    sent_images = set()
    plain_lines = []

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
            step_num = int(sm.group(1))
            step_text = sm.group(2).replace('\\"', '"').replace('\\n', '\n')
            image_keyword = sm.group(3).replace('\\"', '"').strip()
            image_file = step_image_map.get(step_num)

            if step_num not in steps_sent:
                steps_sent.append(step_num)
                step_data = {
                    "step_number": step_num,
                    "text": step_text,
                    "image_keyword": image_keyword,
                    "image": image_file,
                }
                yield f"event: step\ndata: {json.dumps(step_data, ensure_ascii=False)}\n\n"
                plain_lines.append(f"Step {step_num}: {step_text}")
                if image_file:
                    plain_lines.append(f"[[IMG:{image_file}]]")

                if image_keyword and image_keyword not in sent_images:
                    sent_images.add(image_keyword)
                    img_path = f"{IMAGES_DIR}/{image_keyword}"
                    if os.path.exists(img_path):
                        import base64
                        with open(img_path, "rb") as f:
                            b64 = base64.b64encode(f.read()).decode()
                        yield f"event: image\ndata: {json.dumps({'step': step_num, 'image': b64, 'keyword': image_keyword})}\n\n"

        if not closing_sent:
            m = re.search(r'"closing"\s*:\s*"((?:[^"\\]|\\.)*)"', buffer)
            if m:
                text = m.group(1).replace('\\"', '"').replace('\\n', '\n')
                if text.strip():
                    yield f"event: closing\ndata: {json.dumps({'text': text})}\n\n"
                    plain_lines.append(text)
                closing_sent = True

    full_text = "\n".join(plain_lines)
    save_message(q.user_id, q.company_id, "user", q.text, session_id=session_id)
    save_message(q.user_id, q.company_id, "assistant", full_text, session_id=session_id)

    yield f"event: total\ndata: {json.dumps({'total': len(steps_sent)})}\n\n"
    yield f"event: meta\ndata: {json.dumps({'sources': sources, 'version_ids': ver_ids})}\n\n"
    yield f"event: done\ndata: {{}}\n\n"
    print(f"  [stream] Done — {len(steps_sent)} steps, {len(sources)} sources")
