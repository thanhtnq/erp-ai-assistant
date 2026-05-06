#!/usr/bin/env python
"""
Integration test for analyze_sales function.
This test verifies that the analyze_sales query returns results.
It uses mocking to simulate database responses to ensure consistent test results.
"""

import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os

# Add the sales-training directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'sales-training'))

# Import pandas for creating test DataFrames
import pandas as pd

from analyze_sales_bridge import run_analysis


class TestAnalyzeSalesIntegration(unittest.TestCase):
    """Test the analyze_sales function with various queries"""

    def test_top_10_best_selling_products_returns_results(self):
        """
        Test that 'Sales order top 10 best selling products' query returns results.
        This query contains 'product' and 'best selling' keywords
        → routes to product_analysis branch.
        """
        with patch('src.extractors.sales_extractor.SalesExtractor') as mock_extractor_class:
            # Create a mock instance with context manager support
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value = mock_instance
            mock_extractor_class.return_value = mock_instance

            # Create a real DataFrame with sample data
            mock_df = pd.DataFrame([
                {"product_code": "PROD001", "product_name": "Product A", "quantity_sold": 1000, "revenue": 50000},
                {"product_code": "PROD002", "product_name": "Product B", "quantity_sold": 800, "revenue": 40000},
                {"product_code": "PROD003", "product_name": "Product C", "quantity_sold": 600, "revenue": 30000},
            ])

            mock_instance.extract_product_analysis_data.return_value = mock_df

            # Run the analysis
            result = run_analysis(
                query="Sales order top 10 best selling products",
                companyfn="test_company",
                date_from="2025-01-01",
                date_to="2025-12-31"
            )

            # Verify the result has data
            self.assertIsNotNone(result, "Result should not be None")
            self.assertIsInstance(result, dict, "Result should be a dictionary")
            self.assertIn('resource', result, "Result should contain 'resource' key")
            self.assertEqual(result['resource'], 'product_analysis', "Resource should be 'product_analysis'")
            self.assertIn('total_rows', result, "Result should contain 'total_rows' key")
            self.assertEqual(result['total_rows'], 3, "Should have 3 rows")
            self.assertIn('data', result, "Result should contain 'data' key")
            self.assertEqual(len(result['data']), 3, "Data should have 3 records")
            self.assertIn('columns', result, "Result should contain 'columns' key")

    def test_bestseller_query_returns_results(self):
        """
        Test that 'bestseller' keyword returns product analysis results.
        """
        with patch('src.extractors.sales_extractor.SalesExtractor') as mock_extractor_class:
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value = mock_instance
            mock_extractor_class.return_value = mock_instance

            mock_df = pd.DataFrame([
                {"product_code": "P001", "product_name": "Wireless Mouse", "quantity_sold": 200, "revenue": 10000},
                {"product_code": "P002", "product_name": "Keyboard", "quantity_sold": 150, "revenue": 15000},
            ])

            mock_instance.extract_product_analysis_data.return_value = mock_df

            result = run_analysis(query="bestseller products", companyfn="test_company")

            self.assertIsNotNone(result)
            self.assertEqual(result['resource'], 'product_analysis')
            self.assertGreater(result['total_rows'], 0)

    def test_customer_query_returns_results(self):
        """
        Test that customer queries return results.
        'customer' matches the customer keyword check.
        """
        with patch('src.extractors.sales_extractor.SalesExtractor') as mock_extractor_class:
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value = mock_instance
            mock_extractor_class.return_value = mock_instance

            mock_df = pd.DataFrame([
                {"customer_code": "CUST001", "customer_name": "Customer A", "total_revenue": 100000},
                {"customer_code": "CUST002", "customer_name": "Customer B", "total_revenue": 80000},
            ])

            mock_instance.extract_customer_analysis_data.return_value = mock_df

            result = run_analysis(query="customer analysis", companyfn="test_company")

            self.assertIsNotNone(result)
            self.assertEqual(result['resource'], 'customer_analysis')
            self.assertEqual(result['total_rows'], 2)

    def test_revenue_query_returns_results(self):
        """
        Test that revenue queries return results.
        'revenue' matches the revenue keyword check.
        """
        with patch('src.extractors.sales_extractor.SalesExtractor') as mock_extractor_class:
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value = mock_instance
            mock_extractor_class.return_value = mock_instance

            mock_df = pd.DataFrame([
                {"year": 2025, "month": 1, "amt_local": 500000},
                {"year": 2025, "month": 2, "amt_local": 450000},
            ])

            mock_instance.extract_date_revenue_data.return_value = mock_df

            result = run_analysis(
                query="revenue report",
                companyfn="test_company",
                date_from="2025-01-01",
                date_to="2025-12-31"
            )

            self.assertIsNotNone(result)
            self.assertEqual(result['resource'], 'revenue_report_by_date')
            self.assertEqual(result['total_rows'], 2)
            self.assertIn('total_revenue', result)
            self.assertEqual(result['total_revenue'], 950000.0)

    def test_sales_trend_query_returns_results(self):
        """
        Test that sales trend queries return results.
        'monthly' + 'sales trend' matches the trend keyword check.
        """
        with patch('src.extractors.sales_extractor.SalesExtractor') as mock_extractor_class:
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value = mock_instance
            mock_extractor_class.return_value = mock_instance

            mock_df = pd.DataFrame([
                {"year": 2025, "month": 1, "total_revenue": 500000},
                {"year": 2025, "month": 2, "total_revenue": 450000},
            ])

            mock_instance.extract_sales_trend_data.return_value = mock_df

            result = run_analysis(query="monthly sales trend", companyfn="test_company")

            self.assertIsNotNone(result)
            self.assertEqual(result['resource'], 'sales_trend')
            self.assertEqual(result['total_rows'], 2)

    def test_empty_result_handling(self):
        """
        Test that empty results are handled correctly (total_rows = 0).
        """
        with patch('src.extractors.sales_extractor.SalesExtractor') as mock_extractor_class:
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value = mock_instance
            mock_extractor_class.return_value = mock_instance

            mock_df = pd.DataFrame()

            mock_instance.extract_product_analysis_data.return_value = mock_df

            result = run_analysis(query="product", companyfn="test_company")

            self.assertIsNotNone(result)
            self.assertEqual(result['total_rows'], 0)


if __name__ == '__main__':
    unittest.main()