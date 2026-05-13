"""CLI for SCM sales training and analytics.

Run from project root:
    python -m scm_training.main extract --masterfn <masterfn> [--companyfn <companyfn>]
    python -m scm_training.main train --masterfn <masterfn> [--companyfn <companyfn>]
    python -m scm_training.main query --masterfn <masterfn> [--companyfn <companyfn>] -q "Top customers"
"""

import argparse
import json
import logging
import sys
from datetime import datetime

import pandas as pd

from scm_training.config import (
    analysis_dir,
    ensure_dirs,
    ensure_scope_dirs,
    models_dir,
    processed_dir,
)

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def _extractor_args(args) -> dict:
    return {
        "companyfn": getattr(args, "companyfn", None),
        "masterfn": getattr(args, "masterfn", None),
    }


def _require_masterfn(args) -> str:
    masterfn = (getattr(args, "masterfn", None) or "").strip()
    if not masterfn:
        raise ValueError("masterfn is required. Pass the value from cookmfnunique / ChatRequest.masterfn.")
    return masterfn


def _scope_paths(args) -> tuple:
    masterfn = _require_masterfn(args)
    companyfn = getattr(args, "companyfn", None)
    ensure_scope_dirs(masterfn, companyfn)
    return (
        processed_dir(masterfn, companyfn),
        models_dir(masterfn, companyfn),
        analysis_dir(masterfn, companyfn),
    )


def run_extraction(args):
    from scm_training.extractors.sales_extractor import SalesExtractor
    from scm_training.transformers.data_transformer import DataTransformer
    from scm_training.extractors.purchase_extractor import PurchaseExtractor
    from scm_training.extractors.stock_extractor import StockExtractor
    from scm_training.transformers.purchase_transformer import PurchaseTransformer
    from scm_training.transformers.stock_transformer import StockTransformer

    logger.info("Starting SCM training data extraction")

    scoped_processed_dir, _, _ = _scope_paths(args)
    extractor = SalesExtractor(**_extractor_args(args))
    pur_extractor = PurchaseExtractor(**_extractor_args(args))
    stk_extractor = StockExtractor(**_extractor_args(args))
    transformer = DataTransformer()
    pur_transformer = PurchaseTransformer()
    stk_transformer = StockTransformer()

    if not args.date_from or not args.date_to:
        min_date, max_date = extractor.get_available_date_range()
        date_from = args.date_from or min_date
        date_to = args.date_to or max_date
        logger.info("Auto detected date range: %s to %s", date_from, date_to)
    else:
        date_from = args.date_from
        date_to = args.date_to
        logger.info("Using date range: %s to %s", date_from, date_to)

    df_main = extractor.extract_sales_main(date_from=date_from, date_to=date_to)
    df_data = extractor.extract_sales_data(date_from=date_from, date_to=date_to)
    df_customer = extractor.extract_customer_analysis_data(date_from=date_from, date_to=date_to)
    df_product = extractor.extract_product_analysis_data(date_from=date_from, date_to=date_to)
    df_trend = extractor.extract_sales_trend_data(date_from=date_from, date_to=date_to)
    df_retention = extractor.extract_customer_retention_data(lookback_days=None)
    df_revenue = extractor.extract_date_revenue_data(date_from=date_from, date_to=date_to)

    # Purchase extraction
    df_pur_main = pur_extractor.extract_purchase_main(date_from=date_from, date_to=date_to)
    df_pur_data = pur_extractor.extract_purchase_data(date_from=date_from, date_to=date_to)
    df_vendor = pur_extractor.extract_vendor_analysis_data(date_from=date_from, date_to=date_to)
    df_pur_trend = pur_extractor.extract_purchase_trend_data(date_from=date_from, date_to=date_to)

    # Stock extraction
    df_stock_main = stk_extractor.extract_stock_main(date_from=date_from, date_to=date_to)

    datasets = {
        "sales_main": transformer.clean_sales_main(df_main),
        "sales_data": transformer.clean_sales_data(df_data),
        "customer_analysis": transformer.transform_customer_analysis(df_customer),
        "sales_trend": transformer.transform_sales_trend(df_trend),
        "customer_retention": transformer.transform_customer_retention(df_retention),
        "purchase_main": pur_transformer.transform_purchase_main(df_pur_main),
        "purchase_data": pur_transformer.transform_purchase_data(df_pur_data),
        "vendor_analysis": pur_transformer.transform_vendor_analysis(df_vendor),
        "purchase_trend": pur_transformer.transform_purchase_trend(df_pur_trend),
        "stock_main": stk_transformer.transform_stock_main(df_stock_main),
    }

    try:
        datasets["product_analysis"] = transformer.transform_product_analysis(df_product)
    except Exception as exc:
        logger.error("Product dataset transform failed: %s", exc)

    try:
        datasets["revenue_report_by_date"] = transformer.transform_date_revenue(df_revenue)
    except Exception as exc:
        logger.error("Revenue dataset transform failed: %s", exc)

    for name, df in datasets.items():
        if df is not None:
            transformer.save_transformed_data(df, str(scoped_processed_dir / f"{name}.parquet"))

    extractor.close()
    logger.info("Extraction completed: %s main rows, %s detail rows", len(df_main), len(df_data))


def run_training(args):
    from scm_training.extractors.sales_extractor import SalesExtractor
    from scm_training.trainers.churn_predictor import ChurnPredictor
    from scm_training.trainers.sales_forecaster import SalesForecaster
    from scm_training.transformers.data_transformer import DataTransformer

    logger.info("Starting SCM model training")

    scoped_processed_dir, scoped_models_dir, _ = _scope_paths(args)
    extractor = SalesExtractor(**_extractor_args(args))
    transformer = DataTransformer()

    def _load_or_extract_dataset(name: str, extract_fn, transform_fn):
        path = scoped_processed_dir / f"{name}.parquet"
        if path.exists():
            logger.info("Using processed dataset: %s", path)
            return pd.read_parquet(path)
        logger.info("Processed dataset missing, extracting: %s", name)
        df = transform_fn(extract_fn())
        transformer.save_transformed_data(df, str(path))
        return df

    if args.model in ["churn", "all"]:
        df_retention_clean = _load_or_extract_dataset(
            "customer_retention",
            extractor.extract_customer_retention_data,
            transformer.transform_customer_retention,
        )
        churn_predictor = ChurnPredictor(model_dir=str(scoped_models_dir))
        df_retention_prep = churn_predictor.prepare_churn_data(df_retention_clean)
        result = churn_predictor.train(df_retention_prep)
        logger.info("Churn model F1: %.4f", result["metrics"]["f1_score"])

    if args.model in ["forecast", "all"]:
        df_trend_clean = _load_or_extract_dataset(
            "sales_trend",
            extractor.extract_sales_trend_data,
            transformer.transform_sales_trend,
        )
        forecaster = SalesForecaster(model_dir=str(scoped_models_dir))
        df_trend_prep = forecaster.prepare_forecast_data(df_trend_clean)
        result = forecaster.train(df_trend_prep)
        logger.info("Forecast model R2: %.4f", result["metrics"]["r2"])

    extractor.close()
    logger.info("Training completed")


def _discover_scopes(limit: int = None) -> list[dict]:
    from sqlalchemy import text

    from scm_training.extractors.database_extractor import DatabaseExtractor

    db = DatabaseExtractor()
    try:
        sql = """
            SELECT masterfn, companyfn, COUNT(*) AS row_count
            FROM scm_sal_main
            WHERE tag_deleted_yn = 'n'
              AND tag_void_yn = 'n'
              AND masterfn IS NOT NULL
              AND masterfn <> ''
              AND companyfn IS NOT NULL
              AND companyfn <> ''
            GROUP BY masterfn, companyfn
            ORDER BY masterfn, companyfn
        """
        if limit:
            sql += " LIMIT :limit"
            df = pd.read_sql(text(sql), db.engine, params={"limit": limit})
        else:
            df = pd.read_sql(text(sql), db.engine)
        return df.to_dict("records")
    finally:
        db.close()


def run_train_database(args):
    scopes = _discover_scopes(limit=args.limit)
    scopes = [s for s in scopes if int(s.get("row_count") or 0) >= args.min_rows]
    if not scopes:
        raise ValueError("No masterfn/companyfn scopes with enough rows found in scm_sal_main")

    logger.info("Discovered %s SCM scope(s) to train", len(scopes))
    for idx, scope in enumerate(scopes, 1):
        masterfn = scope["masterfn"]
        companyfn = scope["companyfn"]
        logger.info(
            "[%s/%s] Training scope masterfn=%s companyfn=%s (%s source rows)",
            idx, len(scopes), masterfn, companyfn, scope.get("row_count"),
        )

        scoped_args = argparse.Namespace(
            masterfn=masterfn,
            companyfn=companyfn,
            date_from=args.date_from,
            date_to=args.date_to,
            model=args.model,
        )
        run_extraction(scoped_args)
        run_training(scoped_args)


def run_query(args):
    from scm_training.query.ai_query_interface import AIQueryInterface

    _require_masterfn(args)
    interface = AIQueryInterface(masterfn=args.masterfn, companyfn=args.companyfn)

    if args.interactive:
        print("\n=== SCM Training Query Interface ===")
        print("Type 'quit' to exit.\n")
        while True:
            try:
                query = input("Question: ").strip()
                if query.lower() in ["quit", "exit", "q"]:
                    break
                if query:
                    print(interface.format_response(interface.process_query(query)))
                    print()
            except KeyboardInterrupt:
                break
    else:
        query = args.query or "Sales overview"
        print(interface.format_response(interface.process_query(query)))


def run_trend_analysis(args):
    from scm_training.analysis.product_trend_analyzer import ProductTrendAnalyzer
    from scm_training.extractors.sales_extractor import SalesExtractor

    _, _, scoped_analysis_dir = _scope_paths(args)
    with SalesExtractor(**_extractor_args(args)) as extractor:
        analyzer = ProductTrendAnalyzer(extractor)
        result = analyzer.analyze_product_trends(
            companyfn=args.companyfn,
            days_history=args.days,
            top_n=args.top,
        )

    if result.get("status") == "success":
        output_file = scoped_analysis_dir / f"product_trends_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_file.write_text(
            json.dumps(result, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        logger.info("Product trend analysis saved: %s", output_file)

    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return result


def run_scheduled(_args):
    from scm_training.scheduled_training import main as scheduled_main

    scheduled_main(masterfn=_args.masterfn, companyfn=_args.companyfn)


def main():
    ensure_dirs()

    parser = argparse.ArgumentParser(description="SCM sales training and analytics")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    extract_parser = subparsers.add_parser("extract", help="Extract and transform SCM sales data")
    extract_parser.add_argument("--date-from", help="Start date (YYYY-MM-DD)")
    extract_parser.add_argument("--date-to", help="End date (YYYY-MM-DD)")
    extract_parser.add_argument("--masterfn", required=True, help="Master/client scope")
    extract_parser.add_argument("--companyfn", "-c", help="Company/entity scope")

    train_parser = subparsers.add_parser("train", help="Train SCM ML models")
    train_parser.add_argument("--model", choices=["churn", "forecast", "all"], default="all")
    train_parser.add_argument("--masterfn", required=True, help="Master/client scope")
    train_parser.add_argument("--companyfn", "-c", help="Company/entity scope")

    train_db_parser = subparsers.add_parser("train-db", help="Extract and train every masterfn/companyfn scope in the current PG database")
    train_db_parser.add_argument("--model", choices=["churn", "forecast", "all"], default="all")
    train_db_parser.add_argument("--date-from", help="Start date (YYYY-MM-DD)")
    train_db_parser.add_argument("--date-to", help="End date (YYYY-MM-DD)")
    train_db_parser.add_argument("--limit", type=int, help="Limit number of discovered scopes")
    train_db_parser.add_argument("--min-rows", type=int, default=5, help="Minimum scm_sal_main rows required per scope")

    query_parser = subparsers.add_parser("query", help="Query processed SCM training datasets")
    query_parser.add_argument("--query", "-q", help="Query string")
    query_parser.add_argument("--masterfn", required=True, help="Master/client scope")
    query_parser.add_argument("--companyfn", "-c", help="Company/entity scope")
    query_parser.add_argument("--interactive", "-i", action="store_true")

    trend_parser = subparsers.add_parser("trend", help="Analyze top potential products")
    trend_parser.add_argument("--days", "-d", type=int, default=90)
    trend_parser.add_argument("--top", "-t", type=int, default=10)
    trend_parser.add_argument("--masterfn", required=True, help="Master/client scope")
    trend_parser.add_argument("--companyfn", "-c", help="Company/entity scope")

    scheduled_parser = subparsers.add_parser("scheduled", help="Run scheduled SCM training service")
    scheduled_parser.add_argument("--masterfn", required=True, help="Master/client scope")
    scheduled_parser.add_argument("--companyfn", "-c", help="Company/entity scope")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == "extract":
            run_extraction(args)
        elif args.command == "train":
            run_training(args)
        elif args.command == "train-db":
            run_train_database(args)
        elif args.command == "query":
            run_query(args)
        elif args.command == "trend":
            run_trend_analysis(args)
        elif args.command == "scheduled":
            run_scheduled(args)
    except Exception as exc:
        logger.error("Error: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
