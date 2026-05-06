#!/usr/bin/env python
"""
Test the specific query "Top 10 best selling products" to verify the HTTP 500 error fix.
This test simulates the exact scenario from the bug report.
"""

import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api import detect_intent, run_data_query


class TestBestSellingQuery(unittest.TestCase):
    """Test the exact query that was failing: 'Top 10 best selling products'"""
    
    def test_intent_detection_for_best_selling(self):
        """Verify that 'Top 10 best selling products' is correctly detected as data_query."""
        query = "Top 10 best selling products"
        intent = detect_intent(query)
        self.assertEqual(intent, "data_query", 
                        "Query should be detected as data_query intent")
    
    def test_intent_detection_for_best_selling_erp_docs(self):
        """Verify that 'Top 10 best selling products ERP documentation' is detected as data_query."""
        query = "Top 10 best selling products ERP documentation"
        intent = detect_intent(query)
        self.assertEqual(intent, "data_query",
                        "Query should be detected as data_query intent")
    
    @patch('api.get_skill_tools')
    @patch('api.call_gemini_chat')
    @patch('api.execute_skill_tool')
    def test_run_data_query_best_selling_success(self, mock_execute, mock_gemini, mock_tools):
        """Test that the query executes successfully without HTTP 500 error."""
        # Mock tools to be available
        mock_tools.return_value = [{"name": "analyze_sales", "description": "...", "parameters": {}}]
        
        # Mock the skill tool to return valid data
        mock_execute.return_value = {
            "ok": True,
            "result": {
                "resource": "product_analysis",
                "total_rows": 10,
                "columns": ["product_code", "product_name", "quantity_sold", "revenue"],
                "data": [
                    {"product_code": "PROD001", "product_name": "Product A", "quantity_sold": 1000, "revenue": 50000},
                    {"product_code": "PROD002", "product_name": "Product B", "quantity_sold": 800, "revenue": 40000},
                ]
            }
        }
        
        # Mock Gemini to return a formatted response
        mock_gemini.return_value = {"content": "Here are the top selling products..."}
        
        query = "Top 10 best selling products"
        history_text = ""
        masterfn = "test_master"
        companyfn = "test_company"
        
        # This should NOT raise an exception
        result = run_data_query(query, history_text, masterfn, companyfn, "en")
        
        # Verify the result is a string (formatted response)
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)
    
    @patch('api.get_skill_tools')
    @patch('api.call_gemini_chat')
    @patch('api.execute_skill_tool')
    def test_run_data_query_handles_http_500_error(self, mock_execute, mock_gemini, mock_tools):
        """Test that HTTP 500 errors are handled gracefully."""
        # Mock tools to be available
        mock_tools.return_value = [{"name": "analyze_sales", "description": "...", "parameters": {}}]
        
        # Simulate HTTP 500 error from skills server
        mock_execute.return_value = {
            "ok": False,
            "error": "HTTP 500: Internal Server Error"
        }
        
        # Mock Gemini to return an error message
        mock_gemini.return_value = {
            "content": "Xin lỗi, hiện không có dữ liệu bán hàng trong hệ thống Globe3 ERP của bạn..."
        }
        
        query = "Top 10 best selling products"
        history_text = ""
        masterfn = "test_master"
        companyfn = "test_company"
        
        # This should NOT raise an exception, but return an error message
        result = run_data_query(query, history_text, masterfn, companyfn, "en")
        
        # Verify the result is a string (error message)
        self.assertIsInstance(result, str)
    
    @patch('api.get_skill_tools')
    @patch('api.call_gemini_chat')
    @patch('api.execute_skill_tool')
    def test_run_data_query_handles_empty_result(self, mock_execute, mock_gemini, mock_tools):
        """Test that empty results are handled gracefully."""
        # Mock tools to be available
        mock_tools.return_value = [{"name": "analyze_sales", "description": "...", "parameters": {}}]
        
        # Simulate empty result (0 rows)
        mock_execute.return_value = {
            "ok": True,
            "result": {
                "resource": "product_analysis",
                "total_rows": 0,
                "columns": [],
                "data": []
            }
        }
        
        # Mock Gemini to return a message
        mock_gemini.return_value = {"content": "Xin lỗi, không có dữ liệu bán hàng."}
        
        query = "Top 10 best selling products"
        history_text = ""
        masterfn = "test_master"
        companyfn = "test_company"
        
        # This should return a user-friendly message about no data
        result = run_data_query(query, history_text, masterfn, companyfn, "vi")
        
        # Should return message about no data
        self.assertIsInstance(result, str)
        # Check for Vietnamese "no data" message
        self.assertTrue(
            "không có dữ liệu" in result.lower() or "no data" in result.lower() or "no records" in result.lower(),
            f"Expected 'no data' message, got: {result[:100]}"
        )


if __name__ == "__main__":
    unittest.main()