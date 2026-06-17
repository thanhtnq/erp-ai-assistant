"""
ERP AI Assistant — LLM Client
Gemini client wrapper, system prompt builder, response parser, and data query pipeline.
"""
import json
import re
import urllib.request
from datetime import datetime
from pathlib import Path

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
