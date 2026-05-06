#!/usr/bin/env python
"""
Sales Analysis Bridge - Called by skills/globe3-sales-training via subprocess.
Receives a JSON analysis request via stdin, runs PostgreSQL queries,
returns results as JSON via stdout.

Usage (CLI):
  echo '{"query":"top 10 customers by revenue","companyfn":"xxx","date_from":"2025-01-01","date_to":"2025-12-31"}' | python analyze_sales_bridge.py

Usage (Python import):
  from analyze_sales_bridge import run_analysis
  result = run_analysis(query="...", companyfn="...", date_from="...", date_to="...")
"""

import sys, json, os, logging
from datetime import datetime

logging.basicConfig(level=logging.WARNING, format='%(levelname)s %(message)s')
logger = logging.getLogger('sales_bridge')

# Add sales-training to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def run_analysis(query: str, companyfn: str = None, date_from: str = None, date_to: str = None) -> dict:
    """
    Run a sales analysis query against the PostgreSQL database.
    Query types:
      - customer_overview  : total customers, revenue, avg per customer
      - top_customers      : top N customers by revenue
      - repeat_rate        : repeat purchase rate
      - customer_segments  : segment distribution
      - product_overview   : total products, revenue, quantity
      - top_products       : bestsellers
      - category_sales     : sales by category
      - brand_sales        : sales by brand
      - trend_monthly      : monthly sales trend
      - trend_quarterly    : quarterly sales trend
      - trend_daily        : sales by day-of-week
      - revenue_by_date    : revenue for specific month/year
      - product_trends     : top 10 potential products (trend analysis)
    """
    q = query.lower()
    results = {}

    # Import on-demand so the module doesn't fail if deps missing
    from src.extractors.sales_extractor import SalesExtractor
    from src.analysis.product_trend_analyzer import ProductTrendAnalyzer

    with SalesExtractor(companyfn=companyfn) as extractor:

        # ── Product Trends (potential products) ────────────────────────────
        if any(kw in q for kw in ['triển vọng', 'xu hướng', 'tiềm năng', 'trend', 'potential', 'top 10 product']):
            analyzer = ProductTrendAnalyzer(extractor)
            trend = analyzer.analyze_product_trends(
                companyfn=companyfn, days_history=90, top_n=10
            )
            results = trend

        # ── Revenue by Date ────────────────────────────────────────────────
        elif any(kw in q for kw in ['revenue', 'doanh thu', 'doanh số']):
            df = extractor.extract_date_revenue_data(
                companyfn=companyfn, date_from=date_from, date_to=date_to
            )
            if hasattr(df, '__len__') and len(df) > 0:
                results = {
                    'resource': 'revenue_report_by_date',
                    'total_rows': len(df),
                    'total_revenue': float(df.get('amt_local', df.iloc[:, 0]).sum()),
                    'data': json.loads(df.to_json(orient='records', date_format='iso', default_handler=str))
                }
            else:
                results = {'resource': 'revenue_report_by_date', 'total_rows': 0, 'total_revenue': 0}

        # ── Customer / Churn ───────────────────────────────────────────────
        elif any(kw in q for kw in ['customer', 'khách hàng', 'churn']):
            if any(kw in q for kw in ['churn', 'retention', 'rời bỏ', 'giữ chân']):
                df = extractor.extract_customer_retention_data(companyfn=companyfn)
            else:
                df = extractor.extract_customer_analysis_data(
                    companyfn=companyfn, date_from=date_from, date_to=date_to
                )
            if hasattr(df, '__len__') and len(df) > 0:
                results = {
                    'resource': 'customer_analysis',
                    'total_rows': len(df),
                    'columns': list(df.columns),
                    'data': json.loads(df.head(100).to_json(orient='records', date_format='iso', default_handler=str))
                }
            else:
                results = {'resource': 'customer_analysis', 'total_rows': 0}

        # ── Product ────────────────────────────────────────────────────────
        elif any(kw in q for kw in ['product', 'sản phẩm', 'bestseller', 'bán chạy']):
            df = extractor.extract_product_analysis_data(
                companyfn=companyfn, date_from=date_from, date_to=date_to
            )
            if hasattr(df, '__len__') and len(df) > 0:
                results = {
                    'resource': 'product_analysis',
                    'total_rows': len(df),
                    'columns': list(df.columns),
                    'data': json.loads(df.head(100).to_json(orient='records', date_format='iso', default_handler=str))
                }
            else:
                results = {'resource': 'product_analysis', 'total_rows': 0}

        # ── Sales Trend ────────────────────────────────────────────────────
        elif any(kw in q for kw in ['trend', 'xu hướng', 'monthly', 'tháng', 'sales trend']):
            df = extractor.extract_sales_trend_data(
                companyfn=companyfn, date_from=date_from, date_to=date_to
            )
            if hasattr(df, '__len__') and len(df) > 0:
                results = {
                    'resource': 'sales_trend',
                    'total_rows': len(df),
                    'columns': list(df.columns),
                    'data': json.loads(df.head(100).to_json(orient='records', date_format='iso', default_handler=str))
                }
            else:
                results = {'resource': 'sales_trend', 'total_rows': 0}

        # ── General / overview ─────────────────────────────────────────────
        else:
            df = extractor.extract_sales_with_details(
                companyfn=companyfn, date_from=date_from, date_to=date_to
            )
            if hasattr(df, '__len__') and len(df) > 0:
                results = {
                    'resource': 'sales_overview',
                    'total_rows': len(df),
                    'columns': list(df.columns),
                    'data': json.loads(df.head(50).to_json(orient='records', date_format='iso', default_handler=str))
                }
            else:
                results = {'resource': 'sales_overview', 'total_rows': 0}

    return results


if __name__ == '__main__':
    try:
        raw = sys.stdin.read().strip()
        if not raw:
            print(json.dumps({'ok': False, 'error': 'No input received'}))
            sys.exit(1)
        args = json.loads(raw)
        result = run_analysis(
            query=args.get('query', ''),
            companyfn=args.get('companyfn'),
            date_from=args.get('date_from'),
            date_to=args.get('date_to'),
        )
        print(json.dumps({'ok': True, 'result': result}, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({'ok': False, 'error': str(e)}, ensure_ascii=False))
        sys.exit(1)