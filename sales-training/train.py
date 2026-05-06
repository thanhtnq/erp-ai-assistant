#!/usr/bin/env python
"""
Sales Training Script - Extract data and train ML models.
Run this FIRST before using the analyze_sales feature.

Usage:
    cd d:\Web\erp-ai-assistant
    python sales-training/train.py              # Train all models
    python sales-training/train.py --churn       # Train only churn prediction
    python sales-training/train.py --forecast    # Train only sales forecast
    python sales-training/train.py --extract     # Extract data only, no training
"""

import sys, os, logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('sales_train')

# Fix paths
SALES_DIR = os.path.dirname(os.path.abspath(__file__))       # d:\...\sales-training
PROJECT_ROOT = os.path.dirname(SALES_DIR)                     # d:\...\erp-ai-assistant
os.chdir(PROJECT_ROOT)
sys.path.insert(0, SALES_DIR)
sys.path.insert(0, PROJECT_ROOT)

CONFIG_PATH = os.path.join(SALES_DIR, 'config', 'database.json')
DATA_DIR    = os.path.join(SALES_DIR, 'data', 'processed')
MODEL_DIR   = os.path.join(SALES_DIR, 'data', 'models')
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

logger.info(f"Config: {CONFIG_PATH}")
logger.info(f"Data:   {DATA_DIR}")
logger.info(f"Models: {MODEL_DIR}")


def run_extraction():
    """Extract data from PostgreSQL and save as parquet files."""
    from src.extractors.sales_extractor import SalesExtractor
    from src.transformers.data_transformer import DataTransformer

    logger.info("=" * 60)
    logger.info("BAT DAU EXTRACT DU LIEU TU POSTGRESQL")
    logger.info("=" * 60)

    extractor = SalesExtractor(config_path=CONFIG_PATH)
    transformer = DataTransformer()

    min_date, max_date = extractor.get_available_date_range()
    logger.info(f"Khoang thoi gian: {min_date} -> {max_date}")

    df_main = extractor.extract_sales_main(date_from=min_date, date_to=max_date)
    df_data = extractor.extract_sales_data(date_from=min_date, date_to=max_date)
    df_customer = extractor.extract_customer_analysis_data(date_from=min_date, date_to=max_date)
    df_product  = extractor.extract_product_analysis_data(date_from=min_date, date_to=max_date)
    df_trend    = extractor.extract_sales_trend_data(date_from=min_date, date_to=max_date)
    df_retention = extractor.extract_customer_retention_data()
    df_revenue  = extractor.extract_date_revenue_data(date_from=min_date, date_to=max_date)

    logger.info("Dang xu ly va luu du lieu...")
    transformer.save_transformed_data(
        transformer.clean_sales_main(df_main),
        os.path.join(DATA_DIR, 'sales_main.parquet')
    )
    transformer.save_transformed_data(
        transformer.clean_sales_data(df_data),
        os.path.join(DATA_DIR, 'sales_data.parquet')
    )

    for name, df in [
        ('customer_analysis', df_customer),
        ('product_analysis', df_product),
        ('sales_trend', df_trend),
        ('customer_retention', df_retention),
        ('revenue_report_by_date', df_revenue)
    ]:
        if df is not None and len(df) > 0:
            transformer.save_transformed_data(df, os.path.join(DATA_DIR, f'{name}.parquet'))
            logger.info(f"  OK {name}: {len(df)} records")

    extractor.close()
    logger.info(f"OK EXTRACT: {len(df_main)} don hang, {len(df_data)} dong chi tiet")
    return True


def run_churn_training():
    from src.extractors.sales_extractor import SalesExtractor
    from src.transformers.data_transformer import DataTransformer
    from src.trainers.churn_predictor import ChurnPredictor

    logger.info("-" * 40)
    logger.info("TRAIN: Churn Prediction")
    logger.info("-" * 40)

    extractor = SalesExtractor(config_path=CONFIG_PATH)
    transformer = DataTransformer()
    df_retention = extractor.extract_customer_retention_data()
    df_clean = transformer.transform_customer_retention(df_retention)
    predictor = ChurnPredictor(model_dir=MODEL_DIR)
    df_prep = predictor.prepare_churn_data(df_clean)
    result = predictor.train(df_prep)
    logger.info(f"F1={result['metrics']['f1_score']:.4f} Acc={result['metrics']['accuracy']:.4f}")
    logger.info(f"Churn rate: {result['churn_rate']*100:.1f}%")
    extractor.close()
    return result


def run_forecast_training():
    from src.extractors.sales_extractor import SalesExtractor
    from src.transformers.data_transformer import DataTransformer
    from src.trainers.sales_forecaster import SalesForecaster

    logger.info("-" * 40)
    logger.info("TRAIN: Sales Forecast")
    logger.info("-" * 40)

    extractor = SalesExtractor(config_path=CONFIG_PATH)
    transformer = DataTransformer()
    df_trend = extractor.extract_sales_trend_data()
    df_clean = transformer.transform_sales_trend(df_trend)
    forecaster = SalesForecaster(model_dir=MODEL_DIR)
    df_prep = forecaster.prepare_forecast_data(df_clean)
    result = forecaster.train(df_prep)
    logger.info(f"R2={result['metrics']['r2']:.4f} RMSE={result['metrics']['rmse']:.2f}")
    extractor.close()
    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Train Sales ML Models')
    parser.add_argument('--churn', action='store_true', help='Train only churn model')
    parser.add_argument('--forecast', action='store_true', help='Train only forecast model')
    parser.add_argument('--extract', action='store_true', help='Extract data only')
    args = parser.parse_args()

    run_extraction()
    if args.extract:
        logger.info("OK Hoan tat extract.")
        return

    train_churn = args.churn or not args.forecast
    train_forecast = args.forecast or not args.churn
    if train_churn:
        run_churn_training()
    if train_forecast:
        run_forecast_training()

    logger.info("=" * 60)
    logger.info("OK HOAN TAT! Model da san sang.")
    logger.info("Xem files trong: %s", MODEL_DIR)
    logger.info("=" * 60)


if __name__ == '__main__':
    main()