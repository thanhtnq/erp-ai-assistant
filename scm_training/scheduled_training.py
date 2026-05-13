"""Scheduled SCM training jobs.

This is intentionally separate from schedule/scheduler.py for now. It can be
run with:
    python -m scm_training.main scheduled
"""

import logging
import time
from datetime import datetime, timedelta

import schedule

from scm_training.config import LOG_DIR, ensure_dirs, processed_dir
from scm_training.extractors.sales_extractor import SalesExtractor
from scm_training.trainers.churn_predictor import ChurnPredictor
from scm_training.trainers.sales_forecaster import SalesForecaster
from scm_training.transformers.data_transformer import DataTransformer

ensure_dirs()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "scheduled_training.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def run_daily_training(companyfn: str = None, masterfn: str = None):
    if not masterfn:
        raise ValueError("masterfn is required for scheduled SCM training")
    logger.info("Starting daily SCM training")
    scoped_processed_dir = processed_dir(masterfn, companyfn)
    scoped_processed_dir.mkdir(parents=True, exist_ok=True)
    extractor = SalesExtractor(companyfn=companyfn, masterfn=masterfn)
    transformer = DataTransformer()

    try:
        date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        date_to = datetime.now().strftime("%Y-%m-%d")

        df_main = extractor.extract_sales_main(date_from=date_from, date_to=date_to)
        df_data = extractor.extract_sales_data(date_from=date_from, date_to=date_to)
        df_revenue = extractor.extract_date_revenue_data(date_from=date_from, date_to=date_to)

        transformer.save_transformed_data(
            transformer.clean_sales_main(df_main),
            str(scoped_processed_dir / "sales_main_latest.parquet"),
        )
        transformer.save_transformed_data(
            transformer.clean_sales_data(df_data),
            str(scoped_processed_dir / "sales_data_latest.parquet"),
        )
        transformer.save_transformed_data(
            transformer.transform_date_revenue(df_revenue),
            str(scoped_processed_dir / "revenue_report_by_date.parquet"),
        )

        if len(df_main) > 100:
            df_retention = transformer.transform_customer_retention(
                extractor.extract_customer_retention_data()
            )
            df_retention_prep = ChurnPredictor().prepare_churn_data(df_retention)
            if len(df_retention_prep) > 50:
                ChurnPredictor().train(df_retention_prep)

            df_trend = transformer.transform_sales_trend(
                extractor.extract_sales_trend_data(date_from=date_from, date_to=date_to)
            )
            df_trend_prep = SalesForecaster().prepare_forecast_data(df_trend)
            if len(df_trend_prep) > 30:
                SalesForecaster().train(df_trend_prep)

        logger.info("Daily SCM training completed")
    except Exception as exc:
        logger.error("Daily SCM training failed: %s", exc)
    finally:
        extractor.close()


def run_weekly_training(companyfn: str = None, masterfn: str = None):
    if not masterfn:
        raise ValueError("masterfn is required for scheduled SCM training")
    logger.info("Starting weekly SCM training")
    scoped_processed_dir = processed_dir(masterfn, companyfn)
    scoped_processed_dir.mkdir(parents=True, exist_ok=True)
    extractor = SalesExtractor(companyfn=companyfn, masterfn=masterfn)
    transformer = DataTransformer()

    try:
        date_from, date_to = extractor.get_available_date_range()

        datasets = {
            "customer_analysis": transformer.transform_customer_analysis(
                extractor.extract_customer_analysis_data(date_from=date_from, date_to=date_to)
            ),
            "product_analysis": transformer.transform_product_analysis(
                extractor.extract_product_analysis_data(date_from=date_from, date_to=date_to)
            ),
            "sales_trend": transformer.transform_sales_trend(
                extractor.extract_sales_trend_data(date_from=date_from, date_to=date_to)
            ),
            "customer_retention": transformer.transform_customer_retention(
                extractor.extract_customer_retention_data(lookback_days=None)
            ),
            "revenue_report_by_date": transformer.transform_date_revenue(
                extractor.extract_date_revenue_data(date_from=date_from, date_to=date_to)
            ),
        }

        for name, df in datasets.items():
            transformer.save_transformed_data(df, str(scoped_processed_dir / f"{name}.parquet"))

        df_retention_prep = ChurnPredictor().prepare_churn_data(datasets["customer_retention"])
        ChurnPredictor().train(df_retention_prep, hyperparameter_tuning=True)

        df_trend_prep = SalesForecaster().prepare_forecast_data(datasets["sales_trend"])
        SalesForecaster().train(df_trend_prep)

        logger.info("Weekly SCM training completed")
    except Exception as exc:
        logger.error("Weekly SCM training failed: %s", exc)
    finally:
        extractor.close()


def main(masterfn: str = None, companyfn: str = None):
    if not masterfn:
        raise ValueError("masterfn is required for scheduled SCM training")
    logger.info("Starting scheduled SCM training service")
    schedule.every().day.at("02:00").do(run_daily_training, companyfn=companyfn, masterfn=masterfn)
    schedule.every().sunday.at("03:00").do(run_weekly_training, companyfn=companyfn, masterfn=masterfn)

    run_daily_training(companyfn=companyfn, masterfn=masterfn)

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
