"""Tests for src/processors/invoice_processor.py"""
import pytest
from unittest.mock import patch, Mock
from src.processors.invoice_processor import detect_vendor, route, process_group, process_all


class TestDetectVendor:
    def test_detect_vendor_homedepot_com(self):
        assert detect_vendor("orders@homedepot.com") == "home_depot"

    def test_detect_vendor_homedepot_subdomain(self):
        assert detect_vendor("noreply@orders.homedepot.com") == "home_depot"

    def test_detect_vendor_mcmaster(self):
        assert detect_vendor("order@mcmaster.com") == "mcmaster_carr"

    def test_detect_vendor_mcmaster_hyphen(self):
        assert detect_vendor("sales@mcmaster-carr.com") == "mcmaster_carr"

    def test_detect_vendor_unknown(self):
        assert detect_vendor("orders@amazon.com") is None

    def test_detect_vendor_empty_string(self):
        assert detect_vendor("") is None

    def test_detect_vendor_none(self):
        assert detect_vendor(None) is None

    def test_detect_vendor_case_insensitive(self):
        assert detect_vendor("ORDERS@HOMEDEPOT.COM") == "home_depot"


class TestRoute:
    @patch('src.processors.invoice_processor.vendor_parser')
    def test_route_to_vendor_parser(self, mock_vendor):
        mock_vendor.parse.return_value = {'organizations': ['Test']}
        mock_vendor.normalize_to_schema.return_value = {'company_name': 'Test'}

        route("orders@homedepot.com", "Invoice content")
        mock_vendor.parse.assert_called_once()
        mock_vendor.normalize_to_schema.assert_called_once()

    @patch('src.processors.invoice_processor.llm_extractor')
    def test_route_to_llm_for_unknown(self, mock_llm):
        mock_llm.extract.return_value = {'company_name': 'Unknown Corp'}
        route("orders@random.com", "Invoice content")
        mock_llm.extract.assert_called_once()

    @patch('src.processors.invoice_processor.llm_extractor')
    def test_route_to_llm_for_empty_sender(self, mock_llm):
        mock_llm.extract.return_value = {}
        route("", "Invoice content")
        mock_llm.extract.assert_called_once()


class TestProcessGroup:
    @patch('src.processors.invoice_processor.file_handler')
    @patch('src.processors.invoice_processor.route')
    def test_process_group_with_txt_file(self, mock_route, mock_file_handler):
        mock_file_handler.combine_content.return_value = "Invoice content"
        mock_file_handler.parse_email_headers.return_value = {
            'sender_email': 'orders@vendor.com',
            'thread_id': 'thread_123',
            'received_time': '2024-01-15',
            'subject': 'Invoice'
        }
        mock_route.return_value = {'company_name': 'Vendor'}

        result = process_group(['/path/to/email.txt', '/path/to/invoice.pdf'])
        assert result is not None
        assert result['mail_thread_id'] == 'thread_123'

    @patch('src.processors.invoice_processor.file_handler')
    @patch('src.processors.invoice_processor.route')
    def test_process_group_empty_content(self, mock_route, mock_file_handler):
        mock_file_handler.combine_content.return_value = "   "
        assert process_group(['/path/to/empty.txt']) is None

    @patch('src.processors.invoice_processor.file_handler')
    @patch('src.processors.invoice_processor.route')
    def test_process_group_fallback_vendor_detection(self, mock_route, mock_file_handler):
        mock_file_handler.combine_content.return_value = "Invoice content"
        mock_route.return_value = {'company_name': 'McMaster'}
        process_group(['/path/to/mcmaster_invoice.pdf'])
        mock_route.assert_called()


class TestProcessAll:
    @patch('src.processors.invoice_processor.file_handler')
    @patch('src.processors.invoice_processor.process_group')
    def test_process_all_returns_list(self, mock_process_group, mock_file_handler):
        mock_file_handler.get_invoice_files.return_value = {
            'base1': ['/path/file1.txt'],
            'base2': ['/path/file2.txt']
        }
        mock_process_group.side_effect = [
            {'mail_thread_id': 't1', 'company_name': 'A'},
            {'mail_thread_id': 't2', 'company_name': 'B'}
        ]
        assert len(process_all()) == 2

    @patch('src.processors.invoice_processor.file_handler')
    @patch('src.processors.invoice_processor.process_group')
    def test_process_all_skips_existing_ids(self, mock_process_group, mock_file_handler):
        mock_file_handler.get_invoice_files.return_value = {
            'base1': ['/path/file1.txt'],
            'base2': ['/path/file2.txt']
        }
        mock_process_group.side_effect = [
            {'mail_thread_id': 't1', 'company_name': 'A'},
            {'mail_thread_id': 't2', 'company_name': 'B'}
        ]
        result = process_all(skip_ids={'t1'})
        assert len(result) == 1
        assert result[0]['mail_thread_id'] == 't2'

    @patch('src.processors.invoice_processor.file_handler')
    @patch('src.processors.invoice_processor.process_group')
    def test_process_all_filters_none_results(self, mock_process_group, mock_file_handler):
        mock_file_handler.get_invoice_files.return_value = {
            'base1': ['/path/file1.txt'],
            'base2': ['/path/file2.txt']
        }
        mock_process_group.side_effect = [
            {'mail_thread_id': 't1', 'company_name': 'A'},
            None
        ]
        assert len(process_all()) == 1

    @patch('src.processors.invoice_processor.file_handler')
    def test_process_all_empty_directory(self, mock_file_handler):
        mock_file_handler.get_invoice_files.return_value = {}
        assert process_all() == []
