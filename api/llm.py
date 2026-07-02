"""
ERP AI Assistant — LLM Client
Gemini client wrapper, system prompt builder, response parser, and data query pipeline.
"""
import json
import re
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types as genai_types

from api.config import GEMINI_API_KEY, LLM_MODEL, ROLE_MD, SKILLS_URL

# ─── Gemini Client ─────────────────────────────────────────────────────────────
_gemini_client = genai.Client(api_key=GEMINI_API_KEY)


# ─── ROLE.md ───────────────────────────────────────────────────────────────────
def load_role_md() -> str:
    try:
        return Path(ROLE_MD).read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"[WARN] ROLE.md not found at {ROLE_MD}")
        return "You are a helpful ERP assistant for Globe3 ERP by TNO Systems Pte Ltd."


ROLE_CONTENT = load_role_md()
print(f"[OK] ROLE.md loaded ({len(ROLE_CONTENT)} chars)")


# ─── System Prompt Builder ─────────────────────────────────────────────────────
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


# ─── Prompts ───────────────────────────────────────────────────────────────────
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


# ─── Response Parser ───────────────────────────────────────────────────────────
def parse_response(raw: str) -> dict:
    raw = re.sub(r'^```json\s*|^```\s*|\s*```$', '', raw.strip(), flags=re.MULTILINE)

    try:
        d = json.loads(raw)
        return {
            "intro": d.get("intro", ""),
            "steps": d.get("steps", []),
            "closing": d.get("closing", "")
        }
    except Exception:
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
        except Exception:
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


# ─── Skills / Data-Query Pipeline ──────────────────────────────────────────────
def _http_get(url: str, timeout: int = 5) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read())


def _http_post(url: str, payload: dict, timeout: int = 30) -> dict:
    data = json.dumps(payload, ensure_ascii=False).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
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


def format_tool_result_fallback(tool_results: list[dict], lang: str = "en") -> str:
    """Deterministic formatter used when the model fails after tool execution."""
    if not tool_results:
        return "Unable to retrieve ERP data for that request."

    result = tool_results[0]
    if not result.get("ok", True):
        err = result.get("error") or result.get("message") or "Unknown ERP data error"
        return f"⚠️ ERP data query failed: {err}"

    payload = result.get("result", result)
    if isinstance(payload, dict) and payload.get("ok") is False:
        return f"⚠️ ERP data query failed: {payload.get('error', 'Unknown ERP data error')}"

    columns = payload.get("columns", []) if isinstance(payload, dict) else []
    rows = payload.get("rows", []) if isinstance(payload, dict) else []
    row_count = payload.get("rowCount", len(rows)) if isinstance(payload, dict) else 0

    if row_count == 0 or not rows:
        return "No matching ERP data was found for that period.\n\nWould you like to try a different date range?"

    first = rows[0]
    if isinstance(first, dict):
        if len(rows) == 1:
            facts = [f"{key}: {value}" for key, value in first.items()]
            return "Here is the result from ERP data: " + "; ".join(facts) + ".\n\nWould you like to see more details?"

        table_cols = columns or list(first.keys())
        header = "| " + " | ".join(str(c) for c in table_cols) + " |"
        sep = "| " + " | ".join("---" for _ in table_cols) + " |"
        body = ["| " + " | ".join(str(row.get(c, "")) for c in table_cols) + " |" for row in rows[:10]]
        return "Here are the ERP results:\n\n" + "\n".join([header, sep] + body) + "\n\nWould you like to refine this further?"

    return f"ERP returned: {payload}\n\nWould you like to refine this further?"


def _format_table(headers: list[str], rows: list[list[Any]]) -> str:
    if not rows:
        return ""
    header = "| " + " | ".join(headers) + " |"
    sep = "| " + " | ".join("---" for _ in headers) + " |"
    body = ["| " + " | ".join(str(cell) for cell in row) + " |" for row in rows]
    return "\n".join([header, sep] + body)


def _fmt_num(value, digits: int = 0) -> str:
    try:
        num = float(value)
    except Exception:
        return str(value)
    if digits:
        return f"{num:,.{digits}f}"
    if abs(num - round(num)) < 1e-9:
        return f"{int(round(num)):,}"
    return f"{num:,.2f}"


def _scm_column_label(column: str, lang: str) -> str:
    labels = {
        "transaction_count": ("Transactions", "Số giao dịch"),
        "revenue_local": ("Revenue (Local)", "Doanh thu (Nội tệ)"),
        "avg_transaction_value": ("Average Transaction", "Giá trị giao dịch TB"),
        "customer_count": ("Customers", "Khách hàng"),
        "code": ("Code", "Mã"),
        "product": ("Product", "Sản phẩm"),
        "category": ("Category", "Nhóm sản phẩm"),
        "current_qty": ("Current Qty", "SL kỳ hiện tại"),
        "previous_qty": ("Previous Qty", "SL kỳ trước"),
        "current_revenue": ("Current Revenue", "Doanh thu hiện tại"),
        "growth_pct": ("Growth (%)", "Tăng trưởng (%)"),
        "qty_sold": ("Qty Sold", "SL đã bán"),
        "revenue": ("Revenue", "Doanh thu"),
        "stock_on_hand": ("Stock On Hand", "Tồn kho"),
        "reorder_level": ("Reorder Level", "Mức đặt hàng lại"),
        "supplier": ("Supplier", "Nhà cung cấp"),
        "late_deliveries": ("Late Deliveries", "Số lần giao trễ"),
        "avg_days_late": ("Avg Days Late", "Số ngày trễ TB"),
        "max_days_late": ("Max Days Late", "Trễ nhiều nhất"),
        "code_a": ("Product A Code", "Mã SP A"),
        "product_a": ("Product A", "Sản phẩm A"),
        "code_b": ("Product B Code", "Mã SP B"),
        "product_b": ("Product B", "Sản phẩm B"),
        "together_count": ("Bought Together", "Số lần mua cùng"),
        "forecast_qty": ("Forecast Qty", "SL dự báo"),
        "forecast_revenue": ("Forecast Revenue", "Doanh thu dự báo"),
        "weekly_volatility": ("Weekly Volatility", "Biến động tuần"),
        "volatility_pct": ("Volatility (%)", "Biến động (%)"),
        "last_month_actual": ("Last Month Actual", "Thực tế tháng trước"),
        "this_month_forecast": ("This Month Forecast", "Dự báo tháng này"),
        "variance": ("Variance", "Chênh lệch"),
        "invoice_no": ("Invoice No.", "Số hóa đơn"),
        "invoice_date": ("Invoice Date", "Ngày hóa đơn"),
        "customer_code": ("Customer Code", "Mã khách hàng"),
        "amount_local": ("Amount (Local)", "Số tiền (Nội tệ)"),
        "currency": ("Currency", "Tiền tệ"),
    }
    en, vi = labels.get(column, (column.replace("_", " ").title(), column.replace("_", " ").title()))
    return vi if lang == "vi" else en


def _scm_analysis_title(analysis: str, lang: str, top: int) -> str:
    titles = {
        "overview": ("SCM Performance Summary", "Tổng quan hiệu suất SCM"),
        "sales_invoices": ("Sales Invoice List", "Danh sách hóa đơn bán hàng"),
        "growth": (f"Top {top} Fastest-Growing Products", f"Top {top} sản phẩm tăng trưởng nhanh nhất"),
        "demand_surge": (f"Top {top} Products with Rising Demand", f"Top {top} sản phẩm có nhu cầu tăng mạnh"),
        "stable_growth": (f"Top {top} Products with Stable Growth", f"Top {top} sản phẩm tăng trưởng ổn định"),
        "revenue": (f"Top {top} Products by Revenue", f"Top {top} sản phẩm theo doanh thu"),
        "bestselling": (f"Top {top} Bestselling Products", f"Top {top} sản phẩm bán chạy nhất"),
        "stock_low_sales": (f"Top {top} High-Stock, Low-Sales Products", f"Top {top} sản phẩm tồn kho cao, bán chậm"),
        "low_stock_bestsellers": (f"Top {top} Bestsellers Running Low on Stock", f"Top {top} sản phẩm bán chạy sắp hết hàng"),
        "supplier_delay": (f"Top {top} Suppliers by Delivery Delays", f"Top {top} nhà cung cấp giao hàng trễ"),
        "basket": (f"Top {top} Product Pairs Bought Together", f"Top {top} cặp sản phẩm thường mua cùng"),
        "demand_forecast": (f"Top {top} Product Demand Forecast", f"Top {top} dự báo nhu cầu sản phẩm"),
        "forecast_volatility": (f"Top {top} Products by Forecast Volatility", f"Top {top} sản phẩm có dự báo biến động cao"),
        "forecast_vs_actual": ("Forecast vs Last Month Actual", "Dự báo so với thực tế tháng trước"),
    }
    en, vi = titles.get(analysis, ("SCM Analysis", "Phân tích SCM"))
    return vi if lang == "vi" else en


def _looks_like_scm_analytics(query: str) -> bool:
    q = (query or "").lower()
    return any(term in q for term in [
        "scm", "supply chain", "inventory", "stock", "sku", "product", "products",
        "supplier", "delivery delay", "delivery delays", "demand", "forecast",
        "sales growth", "revenue", "bestselling", "best selling", "top 20",
        "top products", "reorder", "running out of stock", "high inventory",
        "low sales", "performance", "summary", "overview", "trend",
    ])


def _extract_period_days(query: str, default: int = 30) -> int:
    """Extract an explicit lookback period from English or Vietnamese text."""
    q = (query or "").lower()
    patterns = [
        (r"\b(\d+)\s*(?:days?|ngày)\b", 1),
        (r"\b(\d+)\s*(?:weeks?|tuần)\b", 7),
        (r"\b(\d+)\s*(?:months?|tháng)\b", 30),
        (r"\b(\d+)\s*(?:years?|năm)\b", 365),
    ]
    for pattern, multiplier in patterns:
        match = re.search(pattern, q, re.IGNORECASE)
        if match:
            return min(max(int(match.group(1)) * multiplier, 1), 365)
    return default


def _route_scm_special_query(query: str) -> dict | None:
    q = (query or "").lower()

    days = _extract_period_days(q)
    top = 20 if "20" in q else 10
    realtime_rules = [
        (["which invoice", "which invoices", "which sales invoice", "which sales invoices", "list sales invoice", "list of sales invoice",
          "sales invoice nào", "các sales invoice", "danh sách sales invoice",
          "hóa đơn bán hàng nào", "danh sách hóa đơn bán hàng"], "sales_invoices"),
        (["purchased together", "bought together"], "basket"),
        (["forecast volatility", "volatility"], "forecast_volatility"),
        (["compare this month", "forecast demand with last month", "forecast demand with last month's actual"], "forecast_vs_actual"),
        (["high inventory but low sales"], "stock_low_sales"),
        (["supplier had the most delivery delays", "delivery delays last month"], "supplier_delay"),
        (["running out of stock"], "low_stock_bestsellers"),
        (["highest revenue"], "revenue"),
        (["stable growth"], "stable_growth"),
        (["surge in demand"], "demand_surge"),
        (["highest sales growth", "fastest sales growth"], "growth"),
        (["bestselling", "best selling"], "bestselling"),
        (["forecast", "predict", "projection", "next month", "upcoming season"], "demand_forecast"),
    ]
    for terms, analysis in realtime_rules:
        if any(term in q for term in terms):
            return {"kind": "tool", "tool": "analyze_scm_realtime", "args": {
                "analysis": analysis, "days": days, "top": 20 if analysis == "sales_invoices" else top,
                "group_by": "category" if any(term in q for term in ["group", "category"]) else "product",
            }}

    if _looks_like_scm_analytics(q):
        return {"kind": "tool", "tool": "analyze_scm_realtime", "args": {
            "analysis": "overview", "days": days, "top": top, "group_by": "product",
        }}

    overview_terms = [
        "scm overview",
        "summary of scm performance",
        "performance over the last 30 days",
        "high inventory but low sales",
        "supplier had the most delivery delays",
        "delivery delays last month",
        "bestselling products",
        "best selling products",
        "highest revenue",
        "running out of stock",
    ]
    if any(term in q for term in overview_terms):
        days = 30
        if "last 4 weeks" in q or "4 weeks" in q:
            days = 28
        elif "last 90 days" in q or "90 days" in q:
            days = 90
        top = 20 if "20" in q else 10
        return {"kind": "tool", "tool": "get_scm_overview", "args": {"days": days, "top": top}}

    trend_terms = [
        "surge in demand",
        "showing stable growth",
        "fastest sales growth",
        "highest sales growth",
        "potential products",
        "product trend",
        "top products",
        "bestselling",
        "best selling",
    ]
    forecast_terms = [
        "forecast demand",
        "demand forecast",
        "forecast market demand",
        "next month",
        "upcoming season",
        "inventory for the upcoming season",
        "product group",
        "by product group",
        "by category",
        "by sku",
        "by product",
    ]

    if any(term in q for term in trend_terms):
        if "forecast" in q and any(term in q for term in ["product group", "by category", "by sku", "by product"]):
            return {
                "kind": "tool",
                "tool": "run_scm_model",
                "args": {
                    "task": "demand_forecast",
                    "query": query,
                    "days": 30,
                    "top": 10,
                    "group_by": "category" if any(term in q for term in ["group", "category"]) else "product",
                },
            }
        return {
            "kind": "tool",
            "tool": "run_scm_model",
            "args": {
                "task": "product_trend",
                "query": query,
                "days": 90,
                "top": 20 if "20" in q else 10,
            },
        }

    if any(term in q for term in forecast_terms):
        return {
            "kind": "tool",
            "tool": "run_scm_model",
            "args": {
                "task": "demand_forecast",
                "query": query,
                "days": 30,
                "top": 10,
                "group_by": "category" if any(term in q for term in ["group", "category"]) else "product",
            },
        }

    if any(term in q for term in ["market demand", "market forecast", "market trend", "external trend", "internet trend", "social trend"]):
        return {
            "kind": "tool",
            "tool": "analyze_market_trends",
            "args": {"top": 10},
        }

    return None


def run_scm_special_query(query: str, masterfn: str, companyfn: str, lang: str = "en", history_text: str = "") -> str | None:
    route = _route_scm_special_query(query)
    if not route:
        return None

    if route["kind"] == "unsupported":
        return route["message_vi"] if lang == "vi" else route["message_en"]

    if not masterfn or not companyfn:
        return (
            "Không thể chạy câu hỏi SCM này vì thiếu `masterfn` hoặc `companyfn`."
            if lang == "vi"
            else "Cannot run this SCM question because `masterfn` or `companyfn` is missing."
        )

    tool_name = route["tool"]
    args = route["args"]
    if history_text and _extract_period_days(query, 0) == 0:
        args["days"] = _extract_period_days(history_text, args.get("days", 30))
    result = execute_skill_tool(tool_name, args, masterfn, companyfn)
    payload = result.get("result", result)
    if not result.get("ok", True):
        err = result.get("error") or payload.get("error") if isinstance(payload, dict) else None
        return (
            f"⚠️ Không chạy được SCM tool: {err or 'unknown error'}"
            if lang == "vi"
            else f"⚠️ Could not run the SCM tool: {err or 'unknown error'}"
        )

    if tool_name == "get_scm_overview":
        sales = payload.get("sales_summary", {}) if isinstance(payload, dict) else {}
        top_products = payload.get("top_products", []) if isinstance(payload, dict) else []
        reorder_items = payload.get("reorder_items", []) if isinstance(payload, dict) else []
        overstock = payload.get("overstock_or_slow_items", []) if isinstance(payload, dict) else []
        late_suppliers = payload.get("late_suppliers", []) if isinstance(payload, dict) else []

        lines = []
        if lang == "vi":
            lines += [
                f"[SCM Overview] {payload.get('period_days', 30)} ngày gần nhất",
                "",
                f"**Số giao dịch:** {_fmt_num(sales.get('transaction_count', 0))}  ",
                f"**Doanh thu local:** {_fmt_num(sales.get('revenue_local', 0), 2)}  ",
                f"**Giá trị giao dịch trung bình:** {_fmt_num(sales.get('avg_transaction_value', 0), 2)}",
            ]
        else:
            lines += [
                f"[SCM Overview] Last {payload.get('period_days', 30)} days",
                "",
                f"**Transactions:** {_fmt_num(sales.get('transaction_count', 0))}  ",
                f"**Revenue (local):** {_fmt_num(sales.get('revenue_local', 0), 2)}  ",
                f"**Avg transaction value:** {_fmt_num(sales.get('avg_transaction_value', 0), 2)}",
            ]

        if top_products:
            lines += ["", "Top products:"]
            rows = [
                [
                    r.get("product") or r.get("stkcode_code") or "",
                    r.get("category") or "",
                    _fmt_num(r.get("qty_sold", 0)),
                    _fmt_num(r.get("revenue_local", 0), 2),
                ]
                for r in top_products[:10]
            ]
            lines.append(_format_table(["Product", "Category", "Qty sold", "Revenue"], rows))

        if reorder_items:
            lines += ["", "Reorder candidates:"]
            rows = [
                [
                    r.get("product") or r.get("stkcode_code") or "",
                    _fmt_num(r.get("stock_on_hand", 0)),
                    _fmt_num(r.get("reorder_level", 0)),
                    _fmt_num(r.get("suggested_reorder_qty", 0)),
                ]
                for r in reorder_items[:10]
            ]
            lines.append(_format_table(["Product", "On hand", "Reorder level", "Suggested reorder"], rows))

        if overstock:
            lines += ["", "High stock / low sales:"]
            rows = [
                [
                    r.get("product") or r.get("stkcode_code") or "",
                    _fmt_num(r.get("stock_on_hand", 0)),
                    _fmt_num(r.get("qty_sold_period", 0)),
                ]
                for r in overstock[:10]
            ]
            lines.append(_format_table(["Product", "On hand", "Sold in period"], rows))

        if late_suppliers:
            lines += ["", "Late suppliers:"]
            rows = [
                [
                    r.get("supplier") or r.get("party_desc") or "",
                    _fmt_num(r.get("late_delivery_count", 0)),
                    _fmt_num(r.get("avg_days_late", 0), 1),
                ]
                for r in late_suppliers[:10]
            ]
            lines.append(_format_table(["Supplier", "Late deliveries", "Avg days late"], rows))

        return "\n".join(lines)

    if tool_name == "analyze_scm_realtime":
        rows = payload.get("rows", []) if isinstance(payload, dict) else []
        analysis = payload.get("analysis", "SCM") if isinstance(payload, dict) else "SCM"
        period_days = payload.get("period_days", args.get("days", 30)) if isinstance(payload, dict) else args.get("days", 30)
        total = payload.get("total") if isinstance(payload, dict) else None
        if not rows:
            return ("Không có dữ liệu SCM phù hợp trong phạm vi và thời gian đã chọn."
                    if lang == "vi" else "No matching SCM data was found for the selected scope and period.")
        columns = list(rows[0].keys())
        headers = [_scm_column_label(column, lang) for column in columns]
        body = [[_fmt_num(row.get(col), 2) if isinstance(row.get(col), float) else row.get(col, "")
                 for col in columns] for row in rows]
        title = _scm_analysis_title(analysis, lang, int(args.get("top", 10)))
        title += (f" — {period_days} ngày gần nhất"
                  if lang == "vi" else f" — Last {period_days} days")
        if total is not None:
            title += (f" — hiển thị {len(rows)} trên tổng {total}"
                      if lang == "vi" else f" — showing {len(rows)} of {total}")
        return title + "\n\n" + _format_table(headers, body)

    if tool_name == "run_scm_model":
        if not isinstance(payload, dict):
            return json.dumps(payload, ensure_ascii=False, default=str)
        task = payload.get("task")
        if payload.get("ok") is False:
            err = payload.get("error", "Unknown SCM model error")
            return f"⚠️ SCM model failed: {err}" if lang == "en" else f"⚠️ SCM model lỗi: {err}"

        if task == "demand_forecast":
            rows = payload.get("forecast", [])
            if not rows:
                note = payload.get("note")
                return note or "No demand forecast rows were returned."
            lines = [
                f"[Demand Forecast] {payload.get('horizon_days', 30)} days",
                "",
                _format_table(
                    ["Code", "Name", "Forecast qty", "Forecast revenue"],
                    [
                        [
                            r.get("code", ""),
                            r.get("name", ""),
                            _fmt_num(r.get("forecast_qty", 0)),
                            _fmt_num(r.get("forecast_revenue", 0), 2),
                        ]
                        for r in rows[:20]
                    ],
                ),
            ]
            return "\n".join(lines)

        if task == "product_trend":
            result = payload.get("result", {})
            products = result.get("top_potential_products", []) if isinstance(result, dict) else []
            if not products:
                period = result.get("analysis_period", {}) if isinstance(result, dict) else {}
                note = "No product trend rows were returned."
                if period:
                    note += f" Analysis window: {period.get('from', 'N/A')} to {period.get('to', 'N/A')}."
                return note
            lines = [
                f"[Product Trend] {result.get('analysis_period', {}).get('days_analyzed', 90)} days",
                "",
                _format_table(
                    ["Product", "Score", "Revenue", "Qty", "Customers", "Growth"],
                    [
                        [
                            r.get("stkcode_desc") or r.get("product_name") or r.get("stkcode_code") or "",
                            _fmt_num(r.get("potential_score", 0), 2),
                            _fmt_num(r.get("total_revenue", 0), 2),
                            _fmt_num(r.get("total_quantity", 0)),
                            _fmt_num(r.get("unique_customer_count", 0)),
                            f"{_fmt_num(float(r.get('growth_rate', 0)) * 100, 1)}%",
                        ]
                        for r in products[:20]
                    ],
                ),
            ]
            return "\n".join(lines)

        if task == "forecast":
            insights = payload.get("insights", {}) if isinstance(payload, dict) else {}
            daily = payload.get("daily_forecast", []) if isinstance(payload, dict) else []
            lines = [
                f"[Sales Forecast] {payload.get('model_name', 'forecast')}",
                "",
                f"- Forecast days: {len(daily)}",
                f"- Total forecasted revenue: {_fmt_num(insights.get('total_forecasted_revenue', 0), 2)}",
                f"- Avg daily sales: {_fmt_num(insights.get('forecasted_avg_daily_sales', 0), 2)}",
            ]
            return "\n".join(lines)

        return json.dumps(payload, ensure_ascii=False, default=str)

    return json.dumps(payload, ensure_ascii=False, default=str)


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
            if not getattr(resp, "candidates", None):
                return {"content": "⚠️ The AI model did not return a response. Please try again in a moment."}

            candidate = resp.candidates[0]
            content = getattr(candidate, "content", None)
            parts = getattr(content, "parts", None) if content else None
            if not parts:
                finish_reason = getattr(candidate, "finish_reason", None)
                return {
                    "content": (
                        "⚠️ The AI model returned an empty response"
                        + (f" ({finish_reason})." if finish_reason else ".")
                        + " Please try rephrasing your request."
                    )
                }

            part = parts[0]
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


# ─── Data Query System Prompt ──────────────────────────────────────────────────
DATA_QUERY_SYSTEM = (
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
      2. Call Gemini with tools → LLM picks the right tool
      3. Execute chosen tool(s) via skills server
      4. Call Gemini again with tool results → get formatted answer
    Returns markdown string ready to stream to the frontend.
    """
    tools = get_skill_tools()
    if not tools:
        return (
            "⚠️ Skills server không khả dụng. "
            "Vui lòng kiểm tra `node skills/server.js` đang chạy trên port 3001."
        )

    today = datetime.now().date().isoformat()
    messages: list[dict] = [{
        "role": "system",
        "content": DATA_QUERY_SYSTEM + f"\n\nCurrent date: {today}. Resolve relative dates such as 'this month' from this date.",
    }]
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
        return msg.get("content", "Không thể xử lý câu hỏi này.")

    # ── Round 2: Execute each tool call ──────────────────────────────────────
    messages.append(msg)
    tool_results = []

    for tc in tool_calls:
        fn = tc.get("function", {})
        tool_name = fn.get("name", "")
        args = fn.get("arguments", {})
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                args = {}

        print(f"  [data_query] -> {tool_name}({args})")
        try:
            result = execute_skill_tool(tool_name, args, masterfn, companyfn)
        except Exception as e:
            result = {"ok": False, "error": str(e)}
        tool_results.append(result)

        messages.append({
            "role": "tool",
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
    final_text = final.get("content", "Unable to format results.")
    if final_text.startswith("⚠️ The AI model returned an empty response"):
        return format_tool_result_fallback(tool_results, lang)
    return final_text
