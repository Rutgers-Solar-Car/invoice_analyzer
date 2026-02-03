"""Tests for src/processors/llm_extractor.py"""
import pytest
from unittest.mock import patch, Mock
from src.processors.llm_extractor import extract


class TestLLMExtractor:
    def test_extract_empty_text_returns_none(self):
        assert extract("") is None

    def test_extract_none_text_returns_none(self):
        assert extract(None) is None

    @patch('src.processors.llm_extractor.requests.post')
    def test_extract_calls_ollama_api(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {
            'message': {'content': '{"company_name": "Test Corp", "total_price": "100.00"}'}
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = extract("Invoice from Test Corp, Total: $100.00")
        assert mock_post.called

    @patch('src.processors.llm_extractor.requests.post')
    def test_extract_returns_parsed_json(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {
            'message': {'content': '{"company_name": "Test Corp", "total_price": "150.00"}'}
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = extract("Invoice text here")
        assert result is not None
        assert result['company_name'] == 'Test Corp'
        assert result['total_price'] == '150.00'

    @patch('src.processors.llm_extractor.requests.post')
    def test_extract_handles_api_error(self, mock_post):
        mock_post.side_effect = Exception("Connection refused")
        assert extract("Some invoice text") is None

    @patch('src.processors.llm_extractor.requests.post')
    def test_extract_handles_invalid_json_response(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {'message': {'content': 'Not valid JSON'}}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        assert extract("Invoice text") is None

    @patch('src.processors.llm_extractor.requests.post')
    def test_extract_sends_schema_in_prompt(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {'message': {'content': '{}'}}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        extract("Invoice text")

        call_args = mock_post.call_args
        payload = call_args.kwargs.get('json') or call_args[1].get('json')
        prompt = payload['messages'][0]['content']
        assert 'company_name' in prompt
        assert 'total_price' in prompt

    @patch('src.processors.llm_extractor.requests.post')
    def test_extract_uses_json_format(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {'message': {'content': '{}'}}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        extract("Invoice text")

        call_args = mock_post.call_args
        payload = call_args.kwargs.get('json') or call_args[1].get('json')
        assert payload.get('format') == 'json'
