#!/usr/bin/env python
"""
Unit Tests for Globe3 ERP AI Assistant API
Tests core functionality including intent detection, query rewriting, error handling, and HTTP utilities.
"""

import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os

# Add the parent directory to the path to import api module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import functions to test from api.py
from api import (
    detect_intent,
    rewrite_query,
    extract_topic_from_history,
    extract_last_step_from_history,
    _http_post,
    _http_get,
    parse_response,
    format_history,
    detect_pref_change,
    _is_short,
    _extract_last_user_topic,
    _lang_code,
)


class TestDetectIntent(unittest.TestCase):
    """Test the intent detection function."""
    
    def test_data_query_best_selling(self):
        """Test that 'best selling' triggers data_query intent."""
        result = detect_intent("Top 10 best selling products")
        self.assertEqual(result, "data_query")
    
    def test_data_query_revenue(self):
        """Test that revenue queries trigger data_query intent."""
        result = detect_intent("Show me total revenue this month")
        self.assertEqual(result, "data_query")
    
    def test_data_query_top_customer(self):
        """Test that top customer queries trigger data_query intent."""
        result = detect_intent("Top 10 customers by sales")
        self.assertEqual(result, "data_query")
    
    def test_procedure_intent(self):
        """Test that how-to questions trigger procedure intent."""
        result = detect_intent("How to create a sales order")
        self.assertEqual(result, "procedure")
    
    def test_error_fix_intent(self):
        """Test that error reports trigger error_fix intent."""
        result = detect_intent("Cannot save invoice, getting error")
        self.assertEqual(result, "error_fix")
    
    def test_faq_intent(self):
        """Test that explanation questions trigger faq intent."""
        result = detect_intent("What is the difference between SO and INV?")
        self.assertEqual(result, "faq")
    
    def test_reference_intent(self):
        """Test that reference queries trigger reference intent."""
        result = detect_intent("List of all status codes")
        self.assertEqual(result, "reference")
    
    def test_vietnamese_data_query(self):
        """Test Vietnamese data queries."""
        result = detect_intent("doanh thu tháng này")
        self.assertEqual(result, "data_query")
    
    def test_vietnamese_procedure(self):
        """Test Vietnamese procedure queries."""
        result = detect_intent("cách tạo hóa đơn")
        self.assertEqual(result, "procedure")


class TestRewriteQuery(unittest.TestCase):
    """Test the query rewriting function."""
    
    def test_no_history_returns_original(self):
        """Test that with no history, original query is returned."""
        result = rewrite_query("test query", "No previous conversation.")
        self.assertEqual(result["query"], "test query")
        self.assertIsNone(result["target_step"])
    
    def test_step_navigation_in_new_conversation(self):
        """Test step navigation in a new conversation."""
        result = rewrite_query("Show me step 3", "No previous conversation.")
        self.assertEqual(result["target_step"], 3)
        self.assertEqual(result["navigation_type"], "jump")
    
    @patch('api._gemini_chat_model')
    @patch('builtins.print')  # Suppress print to avoid Windows console encoding issues
    def test_short_query_is_followup(self, mock_print, mock_model):
        """Test that short queries are treated as follow-ups."""
        # Mock the model to avoid LLM calls
        mock_model.generate_content.return_value.text = "next step"
        history = "Assistant: Let me explain the sales order process.\nStep 1: Create a new order."
        result = rewrite_query("next", history)
        self.assertTrue(result["is_followup"])
    
    def test_followup_with_step(self):
        """Test follow-up with explicit step number."""
        history = "Assistant: Here is the procedure.\nStep 1: First step.\nStep 2: Second step."
        result = rewrite_query("show me step 2", history)
        self.assertEqual(result["target_step"], 2)
        self.assertEqual(result["navigation_type"], "jump")


class TestExtractTopicFromHistory(unittest.TestCase):
    """Test the topic extraction function."""
    
    def test_empty_history(self):
        """Test with empty history."""
        result = extract_topic_from_history("")
        self.assertEqual(result, "")
    
    def test_no_topic_found(self):
        """Test when no topic is found."""
        result = extract_topic_from_history("No previous conversation.")
        self.assertEqual(result, "")
    
    def test_extract_from_menu_path(self):
        """Test extracting topic from menu path."""
        history = "Assistant: ### Sales > Sales Order > Creating\nThis is the procedure."
        result = extract_topic_from_history(history)
        self.assertEqual(result, "Sales Order")
    
    def test_extract_from_erp_term(self):
        """Test extracting topic from ERP term."""
        history = "Assistant: Let me explain about Sales Order processing."
        result = extract_topic_from_history(history)
        self.assertEqual(result, "Sales Order")


class TestExtractLastStepFromHistory(unittest.TestCase):
    """Test the step extraction function."""
    
    def test_empty_history(self):
        """Test with empty history."""
        result = extract_last_step_from_history("")
        self.assertEqual(result, (None, None))
    
    def test_extract_step_marker(self):
        """Test extracting step from marker."""
        history = "Step 1: First step.[STEP:1]"
        result = extract_last_step_from_history(history)
        self.assertEqual(result[0], 1)
    
    def test_extract_step_from_text(self):
        """Test extracting step from text."""
        history = "Assistant: Now let's move to Step 3 of the process."
        result = extract_last_step_from_history(history)
        self.assertEqual(result[0], 3)
    
    def test_extract_from_numbered_list(self):
        """Test extracting from numbered list."""
        history = "1. First step\n2. Second step\n3. Third step"
        result = extract_last_step_from_history(history)
        # The function returns (last_step, max_steps) where max_steps is None 
        # because it can't reliably determine total steps from a simple numbered list
        self.assertEqual(result[0], 3)  # last_step should be 3


class TestHttpUtilities(unittest.TestCase):
    """Test HTTP utility functions."""
    
    @patch('urllib.request.urlopen')
    def test_http_get_success(self, mock_urlopen):
        """Test successful HTTP GET."""
        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.read.return_value = json.dumps({"status": "ok"}).encode()
        mock_urlopen.return_value = mock_response
        
        result = _http_get("http://test.com/api")
        self.assertEqual(result, {"status": "ok"})
    
    @patch('urllib.request.urlopen')
    def test_http_post_success(self, mock_urlopen):
        """Test successful HTTP POST."""
        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.read.return_value = json.dumps({"result": "success"}).encode()
        mock_urlopen.return_value = mock_response
        
        result = _http_post("http://test.com/api", {"query": "test"})
        self.assertEqual(result, {"result": "success"})
    
    @patch('urllib.request.urlopen')
    def test_http_post_500_error(self, mock_urlopen):
        """Test HTTP POST with 500 error - the fix we implemented."""
        from urllib.error import HTTPError
        
        # Create a mock that raises HTTPError
        def raise_http_error(*args, **kwargs):
            error = HTTPError("http://test.com", 500, "Internal Server Error", {}, None)
            error.read = lambda: json.dumps({"error": "Database connection failed"}).encode()
            raise error
        
        mock_urlopen.side_effect = raise_http_error
        
        result = _http_post("http://test.com/api", {"query": "test"})
        self.assertFalse(result.get("ok", True))
        self.assertIn("HTTP 500", result.get("error", ""))
    
    @patch('urllib.request.urlopen')
    def test_http_post_500_error_no_body(self, mock_urlopen):
        """Test HTTP POST with 500 error and no response body."""
        from urllib.error import HTTPError
        
        def raise_http_error(*args, **kwargs):
            error = HTTPError("http://test.com", 500, "Internal Server Error", {}, None)
            error.read = lambda: b""
            raise error
        
        mock_urlopen.side_effect = raise_http_error
        
        result = _http_post("http://test.com/api", {"query": "test"})
        self.assertFalse(result.get("ok", True))
        self.assertIn("HTTP 500", result.get("error", ""))


class TestParseResponse(unittest.TestCase):
    """Test the response parser function."""
    
    def test_parse_valid_json(self):
        """Test parsing valid JSON response."""
        raw = '{"intro": "Hello", "steps": [{"step_number": 1, "text": "Step 1"}], "closing": "Bye"}'
        result = parse_response(raw)
        self.assertEqual(result["intro"], "Hello")
        self.assertEqual(len(result["steps"]), 1)
        self.assertEqual(result["closing"], "Bye")
    
    def test_parse_json_with_markdown(self):
        """Test parsing JSON wrapped in markdown code blocks."""
        raw = '```json\n{"intro": "Hello", "steps": [], "closing": "Bye"}\n```'
        result = parse_response(raw)
        self.assertEqual(result["intro"], "Hello")
    
    def test_parse_partial_json(self):
        """Test parsing partial JSON from streaming response."""
        raw = 'Some text before {"intro": "Hello", "steps": [{"step_number": 1, "text": "Test"}], "closing": "Bye"} more text'
        result = parse_response(raw)
        self.assertEqual(result["intro"], "Hello")
    
    def test_parse_regex_fallback(self):
        """Test regex fallback parsing."""
        raw = '{"intro": "Hello", "steps": [{"step_number": 1, "text": "Step \\"one\\"", "image_keyword": "screenshot"}], "closing": "Bye"}'
        result = parse_response(raw)
        self.assertEqual(len(result["steps"]), 1)
        self.assertEqual(result["steps"][0]["step_number"], 1)


class TestFormatHistory(unittest.TestCase):
    """Test the history formatting function."""
    
    def test_empty_history(self):
        """Test formatting empty history."""
        result = format_history([])
        self.assertEqual(result, "No previous conversation.")
    
    def test_format_history_rows(self):
        """Test formatting history rows."""
        rows = [
            {"role": "user", "content": "Hello", "timestamp": "2024-01-01"},
            {"role": "assistant", "content": "Hi there!", "timestamp": "2024-01-01"},
        ]
        result = format_history(rows)
        self.assertIn("User: Hello", result)
        self.assertIn("Assistant: Hi there!", result)
    
    def test_truncate_long_content(self):
        """Test that long content is truncated."""
        rows = [
            {"role": "user", "content": "A" * 1000, "timestamp": "2024-01-01"},
        ]
        result = format_history(rows)
        self.assertLessEqual(len(result), 850)  # Should be truncated


class TestDetectPrefChange(unittest.TestCase):
    """Test the preference change detection function."""
    
    def test_detect_vietnamese_preference(self):
        """Test detecting Vietnamese language preference."""
        result = detect_pref_change("trả lời tiếng việt")
        self.assertEqual(result.get("language"), "vi")
    
    def test_detect_english_preference(self):
        """Test detecting English language preference."""
        result = detect_pref_change("reply in english")
        self.assertEqual(result.get("language"), "en")
    
    def test_detect_short_preference(self):
        """Test detecting short response preference."""
        result = detect_pref_change("keep it short please")
        self.assertEqual(result.get("response_len"), "short")
    
    def test_detect_detailed_preference(self):
        """Test detecting detailed response preference."""
        result = detect_pref_change("please explain more detail")
        self.assertEqual(result.get("response_len"), "detailed")
    
    def test_no_change(self):
        """Test when no preference change is detected."""
        result = detect_pref_change("tell me about sales orders")
        self.assertEqual(result, {})


class TestLangCode(unittest.TestCase):
    """Test the language code mapping function."""
    
    def test_english_mapping(self):
        """Test English language mapping."""
        self.assertEqual(_lang_code("english"), "en")
        self.assertEqual(_lang_code("en"), "en")
        self.assertEqual(_lang_code("EN"), "en")
    
    def test_vietnamese_mapping(self):
        """Test Vietnamese language mapping."""
        self.assertEqual(_lang_code("vietnamese"), "vi")
        self.assertEqual(_lang_code("viet"), "vi")
        self.assertEqual(_lang_code("vi"), "vi")
    
    def test_default_mapping(self):
        """Test default language mapping."""
        self.assertEqual(_lang_code("unknown"), "en")
        self.assertEqual(_lang_code(""), "en")
        self.assertEqual(_lang_code(None), "en")


class TestIsShort(unittest.TestCase):
    """Test the short text detection function."""
    
    def test_short_text(self):
        """Test short text detection."""
        self.assertTrue(_is_short("next"))
        self.assertTrue(_is_short("step 3"))
        self.assertTrue(_is_short("what about that"))
    
    def test_long_text(self):
        """Test long text detection."""
        self.assertFalse(_is_short("tell me about the sales order process"))
        self.assertFalse(_is_short("how do I create a new invoice"))


class TestExtractLastUserTopic(unittest.TestCase):
    """Test the user topic extraction function."""
    
    def test_empty_history(self):
        """Test with empty history."""
        result = _extract_last_user_topic("")
        self.assertEqual(result, "")
    
    def test_extract_from_user_line(self):
        """Test extracting topic from user line."""
        history = "User: Show me the top products\nAssistant: Here they are"
        result = _extract_last_user_topic(history)
        self.assertIn("top", result.lower())
        self.assertIn("product", result.lower())
    
    def test_remove_stop_words(self):
        """Test that stop words are removed."""
        history = "User: How to create a sales order"
        result = _extract_last_user_topic(history)
        self.assertNotIn("how", result.lower())
        self.assertNotIn("to", result.lower())


if __name__ == "__main__":
    unittest.main()