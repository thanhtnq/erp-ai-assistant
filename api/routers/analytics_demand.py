"""
ERP AI Assistant — Demand Planning Router
Endpoints: /analytics/demand-plan, /analytics/demand/results, /analytics/demand/forecasts
Queries real ERP data from PostgreSQL for demand forecasting and replenishment recommendations.
"""
import json
import traceback
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query

from api.auth import verify_api_key
from api.config import GEMINI_API_KEY
from api.database import get_chat_conn
from api.llm import call_gemini_chat
from api.models import DemandForecastRequest
from api.services.erp_db import (
    query_sales_history,
    query_current_stock,
    query_sku_master,
    query_on_order_stock,
    query_committed_stock,
)

router = APIRouter()


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def _num(value, default=0.0):
    """Convert DB numeric values (including Decimal) to plain JSON-safe floats."""
    if value is None:
        return default
    return float(value)


def _latest_demand_context(masterfn: str, companyfn: str) -> dict:
    conn = get_chat_conn()
    init_demand_tables(conn)
    forecast = conn.execute("""
        SELECT * FROM demand_forecasts
        WHERE masterfn=? AND companyfn=?
        ORDER BY created_at DESC LIMIT 1
    """, (masterfn, companyfn)).fetchone()
    if not forecast:
        conn.close()
        return {"latest_forecast": None, "sample_rows": []}

    rows = conn.execute("""
        SELECT sku, location, forecast_qty, on_hand_qty, committed_qty, on_order_qty,
               safety_stock, recommended_qty, action, confidence, details_json
        FROM demand_sku_forecasts
        WHERE forecast_id=?
        ORDER BY
          CASE action WHEN 'reorder' THEN 0 WHEN 'review' THEN 1 ELSE 2 END,
          recommended_qty DESC
        LIMIT 8
    """, (forecast["id"],)).fetchall()
    conn.close()

    sample_rows = []
    for row in rows:
        item = dict(row)
        try:
            item["details"] = json.loads(item.pop("details_json") or "{}")
        except Exception:
            item["details"] = {}
        sample_rows.append(item)
    return {"latest_forecast": dict(forecast), "sample_rows": sample_rows}


def _demand_chat_fallback(message: str, context: dict) -> str:
    msg = (message or "").lower()
    latest = context.get("latest_forecast")
    if any(k in msg for k in ("hello", "helo", "hi", "xin chào", "chao")):
        return (
            "Chào bạn. Tôi là Demand Planning assistant. Bạn có thể hỏi tôi dự báo nhu cầu, "
            "SKU nào cần reorder, vì sao một dòng cần review, hoặc cần dữ liệu gì để forecast chạy được."
        )
    if "reorder" in msg or "cần mua" in msg or "bo sung" in msg:
        return (
            "Reorder là các SKU/location có khả năng cần bổ sung hàng dựa trên forecast, tồn kho, "
            "safety stock, hàng đang mua và hàng đã committed. Nếu đã có forecast, hãy hỏi 'show reorder rows'."
        )
    if "safety" in msg or "an toàn" in msg:
        return (
            "Safety stock là lượng tồn kho đệm để giảm rủi ro hết hàng. Module tính dựa trên demand, "
            "service factor, lead time và độ ổn định lịch sử bán."
        )
    no_data_terms = (
        "không",
        "khong",
        "khong co",
        "khong ra",
        "no data",
        "0 row",
        "zero row",
        "missing data",
        "empty",
    )
    if any(term in msg for term in no_data_terms):
        return (
            "Nếu forecast không có rows, thường là do scope quá hẹp, SKU master/stock/sales history không có dữ liệu "
            "trong company hiện tại, hoặc analytics API đang đọc sai scope. Hãy thử SKU=all, Location=all, Horizon=180 days."
        )
    if latest:
        return (
            f"Forecast gần nhất #{latest.get('id')} có {latest.get('total_skus', 0)} SKU rows, "
            f"{latest.get('need_reorder', 0)} reorder, {latest.get('need_review', 0)} review, "
            f"{latest.get('sufficient', 0)} OK. Bạn có thể hỏi 'show reorder rows' hoặc 'copy summary'."
        )
    return (
        "Tôi có thể hỗ trợ trong phạm vi Demand Planning: forecast nhu cầu SKU, kiểm tra reorder risk, "
        "giải thích missing data, safety stock, reorder point, và tạo summary cho buyer. Hãy thử: forecast all SKU for 90 days."
    )


def init_demand_tables(conn):
    """Create demand planning tables if they don't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS demand_forecasts (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            masterfn       TEXT NOT NULL,
            companyfn      TEXT NOT NULL,
            horizon_days   INTEGER NOT NULL DEFAULT 90,
            sku_filter     TEXT NOT NULL DEFAULT 'all',
            location_filter TEXT NOT NULL DEFAULT 'all',
            total_skus     INTEGER NOT NULL DEFAULT 0,
            need_reorder   INTEGER NOT NULL DEFAULT 0,
            need_review    INTEGER NOT NULL DEFAULT 0,
            sufficient     INTEGER NOT NULL DEFAULT 0,
            status         TEXT NOT NULL DEFAULT 'completed',
            created_at     TEXT NOT NULL,
            completed_at   TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS demand_sku_forecasts (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            forecast_id     INTEGER NOT NULL,
            masterfn        TEXT NOT NULL,
            companyfn       TEXT NOT NULL,
            sku             TEXT NOT NULL,
            location        TEXT NOT NULL,
            forecast_qty    REAL NOT NULL DEFAULT 0,
            on_hand_qty     REAL NOT NULL DEFAULT 0,
            committed_qty   REAL NOT NULL DEFAULT 0,
            on_order_qty    REAL NOT NULL DEFAULT 0,
            safety_stock    REAL NOT NULL DEFAULT 0,
            reorder_point   REAL NOT NULL DEFAULT 0,
            recommended_qty REAL NOT NULL DEFAULT 0,
            action          TEXT NOT NULL DEFAULT 'ok',
            confidence      REAL NOT NULL DEFAULT 0.8,
            details_json    TEXT NOT NULL DEFAULT '{}',
            created_at      TEXT NOT NULL,
            FOREIGN KEY (forecast_id) REFERENCES demand_forecasts(id)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_demand_sku_scope
        ON demand_sku_forecasts(masterfn, companyfn, sku, location)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_demand_forecasts_scope
        ON demand_forecasts(masterfn, companyfn, created_at)
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ai_module_chat_messages (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            module     TEXT NOT NULL,
            user_id    TEXT NOT NULL DEFAULT '',
            masterfn   TEXT NOT NULL,
            companyfn  TEXT NOT NULL,
            role       TEXT NOT NULL,
            content    TEXT NOT NULL,
            meta_json  TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_ai_module_chat_scope
        ON ai_module_chat_messages(module, user_id, masterfn, companyfn, created_at)
    """)
    conn.commit()


# ─── Generate forecast from real ERP data ─────────────────────────────────
def _generate_real_forecast(masterfn: str, companyfn: str, forecast_id: int,
                            horizon_days: int = 90,
                            sku_filter: str = "all",
                            location_filter: str = "all",
                            service_factor: float = 0.95) -> tuple:
    """
    Generate demand forecast using real ERP sales history and stock data.
    Uses simple moving average + trend projection for forecasting.
    Now includes on-order (PO), committed (SO), and service factor.
    Returns (results, partial_errors) tuple.
    """
    results = []
    partial_errors = []

    def _safe_query(query_fn, query_name, *args, **kwargs):
        """Run a query safely, capturing errors as partial errors."""
        try:
            return query_fn(*args, **kwargs)
        except Exception as e:
            partial_errors.append({
                "source": query_name,
                "error_type": type(e).__name__,
                "message": str(e)[:200],
                "detail": traceback.format_exc()[:500],
            })
            return []

    # Get real sales history
    sales_data = _safe_query(
        query_sales_history, "query_sales_history",
        masterfn, companyfn,
        sku_filter=sku_filter,
        location_filter=location_filter,
        days=horizon_days,
    )

    # Get real current stock
    stock_data = _safe_query(
        query_current_stock, "query_current_stock",
        masterfn, companyfn,
        sku_filter=sku_filter,
        location_filter=location_filter,
    )

    # Get on-order (PO not yet received) and committed (SO not yet delivered)
    on_order_data = _safe_query(
        query_on_order_stock, "query_on_order_stock",
        masterfn, companyfn,
        sku_filter=sku_filter,
        location_filter=location_filter,
    )
    committed_data = _safe_query(
        query_committed_stock, "query_committed_stock",
        masterfn, companyfn,
        sku_filter=sku_filter,
        location_filter=location_filter,
    )

    # Build stock lookup: sku -> stock info
    stock_map = {}
    for s in stock_data:
        key = s["sku"]
        stock_map[key] = s

    # Build sales lookup: (sku, location) -> sales info
    sales_map = {}
    for s in sales_data:
        key = (s["sku"], s["location"])
        sales_map[key] = s

    # Build on-order lookup: (sku, location) -> qty
    on_order_map = {}
    for s in on_order_data:
        key = (s["sku"], s["location"])
        on_order_map[key] = _num(s["on_order_qty"])

    # Build committed lookup: (sku, location) -> qty
    committed_map = {}
    for s in committed_data:
        key = (s["sku"], s["location"])
        committed_map[key] = _num(s["committed_qty"])

    # Get all unique SKUs from sales data
    skus_in_sales = set((s["sku"], s["location"]) for s in sales_data)
    skus_in_stock = set(s["sku"] for s in stock_data)

    # Also get SKU master for SKUs that have stock but no sales
    all_skus = set()
    for sku, loc in skus_in_sales:
        all_skus.add((sku, loc))
    for sku in skus_in_stock:
        if (sku, location_filter) not in all_skus and location_filter != "all":
            all_skus.add((sku, location_filter))
        elif sku not in [x[0] for x in all_skus]:
            all_skus.add((sku, "default"))

    for sku, loc in all_skus:
        if sku_filter != "all" and sku != sku_filter:
            continue
        if location_filter != "all" and loc != location_filter:
            continue

        # Get sales data for this SKU/location
        sale_info = sales_map.get((sku, loc), None)
        stock_info = stock_map.get(sku, None)

        # Calculate forecast from historical sales
        sale_qty = _num(sale_info["total_qty"]) if sale_info else 0
        order_count = int(_num(sale_info["order_count"], 0)) if sale_info else 0

        if sale_info and sale_qty > 0:
            daily_rate = sale_qty / max(horizon_days, 1)
            forecast_qty = daily_rate * horizon_days
            confidence = min(0.95, 0.5 + (order_count / 50))
        else:
            # No sales history — use conservative estimate
            forecast_qty = 0
            confidence = 0.3

        # Current stock levels
        on_hand = _num(stock_info["on_hand_qty"]) if stock_info else 0
        stock_value = _num(stock_info["stock_value"]) if stock_info else 0

        # On-order (PO) and committed (SO) quantities
        on_order_qty = on_order_map.get((sku, loc), 0)
        committed_qty = committed_map.get((sku, loc), 0)

        # Safety stock using service factor (Z-score approximation)
        # service_factor 0.95 -> Z=1.645, 0.99 -> Z=2.326, 0.90 -> Z=1.282
        z_scores = {0.99: 2.326, 0.95: 1.645, 0.90: 1.282, 0.85: 1.036, 0.80: 0.842}
        z = z_scores.get(round(service_factor, 2), 1.645)
        # Estimate std dev as 30% of daily rate * sqrt(lead_time_days)
        # Assume lead time = 14 days (configurable later)
        lead_time_days = 14
        daily_rate = sale_qty / max(horizon_days, 1) if sale_qty > 0 else 0
        std_dev_daily = daily_rate * 0.3  # 30% coefficient of variation
        safety_stock = round(z * std_dev_daily * (lead_time_days ** 0.5))
        reorder_point = round(daily_rate * lead_time_days + safety_stock)

        # Available = on_hand + on_order - committed
        available = on_hand + on_order_qty - committed_qty

        # Determine action
        if available < reorder_point:
            action = "reorder"
            recommended = max(0, round(reorder_point * 1.5 - available))
        elif available < reorder_point * 1.3:
            action = "review"
            recommended = max(0, round(reorder_point - available))
        else:
            action = "ok"
            recommended = 0

        # Round to integers
        forecast_qty = round(forecast_qty)
        on_hand = round(on_hand)

        # Build missing inputs list
        missing_inputs = []
        if not sale_info:
            missing_inputs.append("sales_history")
        if not stock_info:
            missing_inputs.append("stock_data")
        if not on_order_data:
            missing_inputs.append("on_order_data")
        if not committed_data:
            missing_inputs.append("committed_data")

        results.append({
            "forecast_id": forecast_id,
            "masterfn": masterfn,
            "companyfn": companyfn,
            "sku": sku,
            "location": loc,
            "forecast_qty": forecast_qty,
            "on_hand_qty": on_hand,
            "committed_qty": round(committed_qty),
            "on_order_qty": round(on_order_qty),
            "safety_stock": safety_stock,
            "reorder_point": reorder_point,
            "recommended_qty": recommended,
            "action": action,
            "confidence": round(confidence, 2),
            "details_json": json.dumps({
                "source": "erp_postgresql",
                "data_type": "live",
                "sales_history_days": horizon_days,
                "historical_orders": order_count,
                "last_order_date": str(sale_info["last_order_date"]) if sale_info and sale_info["last_order_date"] else None,
                "stock_value": stock_value,
                "model": "simple_moving_average_with_safety_stock",
                "service_factor": service_factor,
                "lead_time_days": lead_time_days,
                "z_score": round(z, 3),
                "daily_rate": round(daily_rate, 2),
                "missing_inputs": missing_inputs,
            }),
            "created_at": now_iso(),
        })

    return results, partial_errors


# ─── Endpoints ─────────────────────────────────────────────────────────────

@router.post("/analytics/demand-plan")
async def generate_forecast(
    body: DemandForecastRequest,
    _key: str = Depends(verify_api_key),
):
    """
    Generate a demand forecast with replenishment recommendations.

    Required scope: masterfn, companyfn
    Returns forecast by SKU/location with on-hand, safety stock, reorder point,
    recommended quantity, and action. Discloses assumptions and missing inputs.
    """
    if not body.masterfn or not body.companyfn:
        raise HTTPException(400, "masterfn and companyfn are required")

    conn = get_chat_conn()
    init_demand_tables(conn)

    now = now_iso()

    # Create forecast record
    cur = conn.execute("""
        INSERT INTO demand_forecasts
            (masterfn, companyfn, horizon_days, sku_filter, location_filter,
             total_skus, need_reorder, need_review, sufficient,
             status, created_at, completed_at)
        VALUES (?, ?, ?, ?, ?, 0, 0, 0, 0, 'running', ?, NULL)
    """, (body.masterfn, body.companyfn, body.horizon_days or 90,
          body.sku_filter or "all", body.location_filter or "all", now))
    forecast_id = cur.lastrowid

    # Generate forecast from real ERP data
    skus, partial_errors = _generate_real_forecast(
        body.masterfn, body.companyfn, forecast_id,
        horizon_days=body.horizon_days or 90,
        sku_filter=body.sku_filter or "all",
        location_filter=body.location_filter or "all",
        service_factor=body.service_factor or 0.95,
    )

    # Insert SKU forecasts
    for s in skus:
        conn.execute("""
            INSERT INTO demand_sku_forecasts
                (forecast_id, masterfn, companyfn, sku, location,
                 forecast_qty, on_hand_qty, committed_qty, on_order_qty,
                 safety_stock, reorder_point, recommended_qty, action,
                 confidence, details_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (s["forecast_id"], s["masterfn"], s["companyfn"], s["sku"],
              s["location"], s["forecast_qty"], s["on_hand_qty"],
              s["committed_qty"], s["on_order_qty"], s["safety_stock"],
              s["reorder_point"], s["recommended_qty"], s["action"],
              s["confidence"], s["details_json"], s["created_at"]))

    # Update summary
    need_reorder = sum(1 for s in skus if s["action"] == "reorder")
    need_review = sum(1 for s in skus if s["action"] == "review")
    sufficient = sum(1 for s in skus if s["action"] == "ok")

    conn.execute("""
        UPDATE demand_forecasts SET
            total_skus = ?, need_reorder = ?, need_review = ?,
            sufficient = ?, status = 'completed', completed_at = ?
        WHERE id = ?
    """, (len(skus), need_reorder, need_review, sufficient, now, forecast_id))
    conn.commit()
    conn.close()

    response = {
        "forecast_id": forecast_id,
        "status": "completed",
        "horizon_days": body.horizon_days or 90,
        "summary": {
            "total_skus": len(skus),
            "need_reorder": need_reorder,
            "need_review": need_review,
            "sufficient": sufficient,
        },
        "items": skus,
        "assumptions": {
            "model": "simple_moving_average",
            "safety_stock_pct": 30,
            "reorder_point_multiplier": 1.5,
            "horizon_days": body.horizon_days or 90,
            "missing_inputs_disclosed": True,
        },
        "disclaimer": (
            "Forecast is an estimate based on historical sales data. "
            "Actual demand may vary. Review recommendations before placing orders."
        ),
    }

    # Include partial errors if any upstream tool failed
    if partial_errors:
        response["partial_errors"] = partial_errors

    return response



@router.get("/analytics/demand/results")
async def get_demand_results(
    masterfn: str = Query(...),
    companyfn: str = Query(...),
    forecast_id: int = Query(None),
    sku: str = Query("all"),
    location: str = Query("all"),
    action: str = Query("all"),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    _key: str = Depends(verify_api_key),
):
    """Get demand forecast results with optional filters."""
    conn = get_chat_conn()
    init_demand_tables(conn)

    # Get latest forecast if forecast_id not specified
    if not forecast_id:
        row = conn.execute("""
            SELECT id FROM demand_forecasts
            WHERE masterfn=? AND companyfn=?
            ORDER BY created_at DESC LIMIT 1
        """, (masterfn, companyfn)).fetchone()
        if not row:
            conn.close()
            return {"total": 0, "items": [], "summary": None}
        forecast_id = row["id"]

    # Get forecast summary
    forecast = conn.execute("""
        SELECT * FROM demand_forecasts WHERE id=? AND masterfn=? AND companyfn=?
    """, (forecast_id, masterfn, companyfn)).fetchone()
    if not forecast:
        conn.close()
        raise HTTPException(404, "Forecast not found")

    # Build query for SKU forecasts
    where = ["forecast_id=?", "masterfn=?", "companyfn=?"]
    params = [forecast_id, masterfn, companyfn]
    if sku != "all":
        where.append("sku=?")
        params.append(sku)
    if location != "all":
        where.append("location=?")
        params.append(location)
    if action != "all":
        where.append("action=?")
        params.append(action)

    w = " AND ".join(where)
    total = conn.execute(f"SELECT COUNT(*) FROM demand_sku_forecasts WHERE {w}", params).fetchone()[0]
    rows = conn.execute(
        f"SELECT * FROM demand_sku_forecasts WHERE {w} ORDER BY recommended_qty DESC, sku ASC LIMIT ? OFFSET ?",
        params + [limit, offset]
    ).fetchall()
    conn.close()

    items = []
    for row in rows:
        item = dict(row)
        item["details"] = json.loads(item.pop("details_json") or "{}")
        items.append(item)

    return {
        "total": total,
        "items": items,
        "summary": {
            "forecast_id": forecast["id"],
            "horizon_days": forecast["horizon_days"],
            "sku_filter": forecast["sku_filter"],
            "location_filter": forecast["location_filter"],
            "total_skus": forecast["total_skus"],
            "need_reorder": forecast["need_reorder"],
            "need_review": forecast["need_review"],
            "sufficient": forecast["sufficient"],
            "created_at": forecast["created_at"],
            "completed_at": forecast["completed_at"],
        },
    }


@router.get("/analytics/demand/forecasts")
async def list_forecasts(
    masterfn: str = Query(...),
    companyfn: str = Query(...),
    limit: int = Query(10, le=50),
    _key: str = Depends(verify_api_key),
):
    """List recent demand forecasts."""
    conn = get_chat_conn()
    init_demand_tables(conn)
    rows = conn.execute("""
        SELECT * FROM demand_forecasts
        WHERE masterfn=? AND companyfn=?
        ORDER BY created_at DESC LIMIT ?
    """, (masterfn, companyfn, limit)).fetchall()
    conn.close()
    return {"forecasts": [dict(r) for r in rows]}


@router.get("/analytics/demand/chat-history")
async def get_demand_chat_history(
    masterfn: str = Query(...),
    companyfn: str = Query(...),
    user_id: str = Query(""),
    limit: int = Query(50, le=200),
    _key: str = Depends(verify_api_key),
):
    """Return persisted Demand Planning chat messages for the current ERP scope."""
    conn = get_chat_conn()
    init_demand_tables(conn)
    rows = conn.execute("""
        SELECT id, role, content, meta_json, created_at
        FROM ai_module_chat_messages
        WHERE module='demand' AND user_id=? AND masterfn=? AND companyfn=?
        ORDER BY id DESC
        LIMIT ?
    """, (user_id, masterfn, companyfn, limit)).fetchall()
    conn.close()

    items = []
    for row in reversed(rows):
        item = dict(row)
        item["meta"] = json.loads(item.pop("meta_json") or "{}")
        items.append(item)
    return {"items": items}


@router.post("/analytics/demand/chat-history")
async def save_demand_chat_message(
    body: dict,
    _key: str = Depends(verify_api_key),
):
    """Persist one Demand Planning chat message in the server chat DB."""
    masterfn = body.get("masterfn") or ""
    companyfn = body.get("companyfn") or ""
    role = body.get("role") or ""
    content = body.get("content") or ""
    if not masterfn or not companyfn:
        raise HTTPException(400, "masterfn and companyfn are required")
    if role not in {"user", "ai", "system"}:
        raise HTTPException(400, "role must be user, ai, or system")
    if not content:
        raise HTTPException(400, "content is required")

    conn = get_chat_conn()
    init_demand_tables(conn)
    cur = conn.execute("""
        INSERT INTO ai_module_chat_messages
            (module, user_id, masterfn, companyfn, role, content, meta_json, created_at)
        VALUES ('demand', ?, ?, ?, ?, ?, ?, ?)
    """, (
        body.get("user_id") or "",
        masterfn,
        companyfn,
        role,
        content[:4000],
        json.dumps(body.get("meta") or {}, ensure_ascii=False),
        now_iso(),
    ))
    conn.commit()
    message_id = cur.lastrowid
    conn.close()
    return {"id": message_id, "status": "saved"}


@router.post("/analytics/demand/chat-answer")
async def demand_chat_answer(
    body: dict,
    _key: str = Depends(verify_api_key),
):
    """Answer a Demand Planning chat question using latest forecast context."""
    masterfn = body.get("masterfn") or ""
    companyfn = body.get("companyfn") or ""
    message = (body.get("message") or "").strip()
    if not masterfn or not companyfn:
        raise HTTPException(400, "masterfn and companyfn are required")
    if not message:
        raise HTTPException(400, "message is required")

    context = _latest_demand_context(masterfn, companyfn)
    fallback = _demand_chat_fallback(message, context)

    if not GEMINI_API_KEY:
        return {"answer": fallback, "source": "fallback", "context": context}

    system = (
        "You are the Demand Planning assistant inside Globe3 ERP. "
        "Answer only within demand planning, replenishment, SKU forecast, stock, reorder, "
        "sales history, safety stock, lead time, and buyer workflow. "
        "Use the provided ERP context. If there is no data, explain what is missing and what to try next. "
        "Do not invent rows, quantities, vendors, documents, or forecasts. "
        "Keep answers concise and practical. Reply in the same language as the user when possible."
    )
    context_text = json.dumps(context, ensure_ascii=False, default=str)[:6000]
    try:
        msg = call_gemini_chat([
            {"role": "system", "content": system},
            {"role": "user", "content": f"ERP demand context:\n{context_text}\n\nUser question:\n{message}"},
        ], timeout=25, retries=0)
        answer = (msg.get("content") or "").strip()
        if not answer:
            answer = fallback
        return {"answer": answer, "source": "gemini", "context": context}
    except Exception as exc:
        return {
            "answer": fallback,
            "source": "fallback",
            "warning": str(exc)[:160],
            "context": context,
        }


@router.delete("/analytics/demand/chat-history")
async def clear_demand_chat_history(
    masterfn: str = Query(...),
    companyfn: str = Query(...),
    user_id: str = Query(""),
    _key: str = Depends(verify_api_key),
):
    """Clear persisted Demand Planning chat messages for the current ERP scope."""
    conn = get_chat_conn()
    init_demand_tables(conn)
    conn.execute("""
        DELETE FROM ai_module_chat_messages
        WHERE module='demand' AND user_id=? AND masterfn=? AND companyfn=?
    """, (user_id, masterfn, companyfn))
    conn.commit()
    conn.close()
    return {"status": "deleted"}
