"""JSON CLI used by the Globe3 skills server to run trained SCM models."""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path
from typing import Any

import pandas as pd

from scm_training.config import analysis_dir, models_dir, processed_dir


if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def _json_default(value: Any):
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    return str(value)


def _json_safe(value: Any):
    if isinstance(value, dict):
        return {str(_json_safe(k)): _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if isinstance(value, tuple):
        return [_json_safe(v) for v in value]
    if hasattr(value, "item"):
        return value.item()
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _print(payload: dict):
    print(json.dumps(_json_safe(payload), ensure_ascii=False, default=_json_default))


def _load_parquet(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing processed dataset: {path}")
    return pd.read_parquet(path)


def _load_product_analysis_fallback(masterfn: str, companyfn: str, days: int = 90) -> pd.DataFrame:
    """Load product analysis data from live ERP tables when processed parquet is missing."""
    from scm_training.extractors.sales_extractor import SalesExtractor

    with SalesExtractor(masterfn=masterfn, companyfn=companyfn) as extractor:
        min_date, max_date = extractor.get_available_date_range(companyfn=companyfn)

        try:
            end_date = pd.to_datetime(max_date, errors="coerce")
        except Exception:
            end_date = pd.NaT
        if pd.isna(end_date):
            end_date = pd.Timestamp.today()

        start_date = end_date - pd.Timedelta(days=max(int(days), 1))
        df = extractor.extract_product_analysis_data(
            companyfn=companyfn,
            date_from=start_date.strftime("%Y-%m-%d"),
            date_to=end_date.strftime("%Y-%m-%d"),
        )
        if not df.empty:
            return df

        # Broaden the window to the full available history before giving up.
        try:
            full_start = pd.to_datetime(min_date, errors="coerce")
        except Exception:
            full_start = pd.NaT
        if pd.isna(full_start):
            full_start = end_date - pd.Timedelta(days=max(int(days) * 3, 180))

        return extractor.extract_product_analysis_data(
            companyfn=companyfn,
            date_from=full_start.strftime("%Y-%m-%d"),
            date_to=end_date.strftime("%Y-%m-%d"),
        )


def _require_model(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Missing trained model: {path}")


def run_forecast(args) -> dict:
    from scm_training.trainers.sales_forecaster import SalesForecaster

    p_dir = processed_dir(args.masterfn, args.companyfn)
    m_dir = models_dir(args.masterfn, args.companyfn)
    _require_model(m_dir / "sales_forecaster.pkl")

    historical = _load_parquet(p_dir / "sales_trend.parquet")
    forecaster = SalesForecaster(model_dir=str(m_dir))
    prepared = forecaster.prepare_forecast_data(historical)
    forecast_df = forecaster.forecast(prepared, forecast_days=args.days)
    insights = forecaster.get_forecast_insights(prepared, forecast_df)

    daily = forecast_df[["transaction_date", "forecasted_revenue"]].copy()
    daily["transaction_date"] = daily["transaction_date"].dt.strftime("%Y-%m-%d")

    return {
        "ok": True,
        "task": "forecast",
        "trained_model_used": True,
        "model_name": "sales_forecaster",
        "scope": {"masterfn": args.masterfn, "companyfn": args.companyfn},
        "insights": insights,
        "daily_forecast": daily.head(min(args.days, 31)).to_dict("records"),
    }


def run_churn(args) -> dict:
    from scm_training.trainers.churn_predictor import ChurnPredictor

    p_dir = processed_dir(args.masterfn, args.companyfn)
    m_dir = models_dir(args.masterfn, args.companyfn)
    _require_model(m_dir / "churn_predictor.pkl")

    retention = _load_parquet(p_dir / "customer_retention.parquet")
    predictor = ChurnPredictor(model_dir=str(m_dir))
    prepared = predictor.prepare_churn_data(retention)
    predicted = predictor.predict(prepared)
    insights = predictor.get_churn_insights(predicted)

    display_cols = [
        c for c in [
            "customer_id",
            "customer_name",
            "party_code",
            "party_desc",
            "days_since_last_purchase",
            "total_purchases",
            "total_spent",
            "churn_prediction",
            "churn_risk",
        ]
        if c in predicted.columns
    ]
    high_risk = predicted[predicted.get("churn_risk").astype(str) == "High"] if "churn_risk" in predicted.columns else predicted.head(0)

    return {
        "ok": True,
        "task": "churn",
        "trained_model_used": True,
        "model_name": "churn_predictor",
        "scope": {"masterfn": args.masterfn, "companyfn": args.companyfn},
        "insights": insights,
        "high_risk_customers": high_risk[display_cols].head(args.top).to_dict("records"),
    }


def run_demand_forecast(args) -> dict:
    p_dir = processed_dir(args.masterfn, args.companyfn)
    product = None
    parquet_path = p_dir / "product_analysis.parquet"
    try:
        product = _load_parquet(parquet_path)
    except FileNotFoundError:
        product = _load_product_analysis_fallback(args.masterfn, args.companyfn, days=max(int(args.days or 30), 90))

    if product is None or product.empty:
        product = _load_product_analysis_fallback(args.masterfn, args.companyfn, days=max(int(args.days or 30), 90))

    if product.empty:
        return {
            "ok": True,
            "task": "demand_forecast",
            "trained_model_used": False,
            "model_name": "moving_average_product_demand",
            "scope": {"masterfn": args.masterfn, "companyfn": args.companyfn},
            "group_by": args.group_by,
            "horizon_days": max(int(args.days or 30), 1),
            "history_days_used": 0,
            "note": "No product analysis data was available for this scope.",
            "forecast": [],
        }

    horizon_days = max(int(args.days or 30), 1)
    top = max(int(args.top or 10), 1)
    group_col = "category_name" if args.group_by == "category" else "product_name"
    code_col = "category_code" if args.group_by == "category" else "product_code"
    if group_col not in product.columns:
        raise ValueError(f"Dataset does not contain {group_col}")

    df = product.copy()
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    df = df.dropna(subset=["transaction_date"])
    if df.empty:
        raise ValueError("No valid transaction_date rows were available for demand forecast")

    qty_col = "quantity_sold" if "quantity_sold" in df.columns else None
    revenue_col = "revenue" if "revenue" in df.columns else None
    if not qty_col and not revenue_col:
        raise ValueError("Dataset does not contain quantity_sold or revenue")

    last_date = df["transaction_date"].max()
    start_date = last_date - pd.Timedelta(days=90)
    recent = df[df["transaction_date"] >= start_date].copy()
    if recent.empty:
        recent = df.copy()

    observed_days = max((recent["transaction_date"].max() - recent["transaction_date"].min()).days + 1, 1)
    agg_map = {}
    if qty_col:
        agg_map[qty_col] = "sum"
    if revenue_col:
        agg_map[revenue_col] = "sum"
    grouped = recent.groupby([code_col, group_col], dropna=False).agg(agg_map).reset_index()

    if qty_col:
        grouped["forecast_qty"] = grouped[qty_col] / observed_days * horizon_days
    else:
        grouped["forecast_qty"] = None
    if revenue_col:
        grouped["forecast_revenue"] = grouped[revenue_col] / observed_days * horizon_days
    else:
        grouped["forecast_revenue"] = None

    sort_col = "forecast_qty" if qty_col else "forecast_revenue"
    grouped = grouped.sort_values(sort_col, ascending=False).head(top)
    rows = []
    for _, row in grouped.iterrows():
        rows.append({
            "code": row.get(code_col),
            "name": row.get(group_col),
            "forecast_qty": None if pd.isna(row.get("forecast_qty")) else float(row.get("forecast_qty")),
            "forecast_revenue": None if pd.isna(row.get("forecast_revenue")) else float(row.get("forecast_revenue")),
        })

    return {
        "ok": True,
        "task": "demand_forecast",
        "trained_model_used": False,
        "model_name": "moving_average_product_demand",
        "scope": {"masterfn": args.masterfn, "companyfn": args.companyfn},
        "group_by": args.group_by,
        "horizon_days": horizon_days,
        "history_days_used": observed_days,
        "note": "This uses trained/extracted SCM product artifacts with a moving-average demand forecast. A persisted per-product .pkl model has not been trained yet.",
        "forecast": rows,
    }


def run_product_trend(args) -> dict:
    from scm_training.analysis.product_trend_analyzer import ProductTrendAnalyzer
    from scm_training.extractors.sales_extractor import SalesExtractor

    scoped_analysis_dir = analysis_dir(args.masterfn, args.companyfn)
    scoped_analysis_dir.mkdir(parents=True, exist_ok=True)

    with SalesExtractor(masterfn=args.masterfn, companyfn=args.companyfn) as extractor:
        analyzer = ProductTrendAnalyzer(extractor)
        result = analyzer.analyze_product_trends(
            companyfn=args.companyfn,
            days_history=args.days,
            top_n=args.top,
        )

    return {
        "ok": True,
        "task": "product_trend",
        "trained_model_used": False,
        "model_name": "product_trend_analyzer",
        "scope": {"masterfn": args.masterfn, "companyfn": args.companyfn},
        "note": "This analyzer uses live sales history scoring, not a persisted .pkl model.",
        "result": result,
    }


def infer_task(query: str) -> str:
    q = (query or "").lower()
    if any(k in q for k in ["churn", "retention", "rời bỏ", "mất khách", "khách hàng có nguy cơ"]):
        return "churn"
    if any(k in q for k in ["nhu cầu", "demand", "theo từng nhóm", "category forecast", "product forecast"]):
        return "demand_forecast"
    if any(k in q for k in ["trend", "xu hướng", "triển vọng", "tiềm năng", "potential"]):
        return "product_trend"
    return "forecast"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run trained SCM model tools")
    parser.add_argument("--task", choices=["auto", "forecast", "churn", "product_trend", "demand_forecast"], default="auto")
    parser.add_argument("--query", default="")
    parser.add_argument("--masterfn", required=True)
    parser.add_argument("--companyfn", required=True)
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--group-by", choices=["product", "category"], default="category")
    args = parser.parse_args()

    try:
        task = infer_task(args.query) if args.task == "auto" else args.task
        if task == "forecast":
            payload = run_forecast(args)
        elif task == "churn":
            payload = run_churn(args)
        elif task == "demand_forecast":
            payload = run_demand_forecast(args)
        elif task == "product_trend":
            payload = run_product_trend(args)
        else:
            raise ValueError(f"Unsupported task: {task}")
        _print(payload)
        return 0
    except Exception as exc:
        _print({
            "ok": False,
            "error": str(exc),
            "trace": traceback.format_exc(limit=5),
            "scope": {"masterfn": args.masterfn, "companyfn": args.companyfn},
        })
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
