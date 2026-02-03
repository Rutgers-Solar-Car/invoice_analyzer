"""Tests for src/writers/sheets_writer.py"""
import pytest
from unittest.mock import patch, Mock, MagicMock
from src.writers.sheets_writer import init_sheet, get_existing_thread_ids, write_invoice_data


class TestInitSheet:
    @patch('src.writers.sheets_writer.settings')
    def test_init_sheet_no_spreadsheet_id(self, mock_settings):
        mock_settings.SPREADSHEET_ID = 'YOUR_SPREADSHEET_ID_HERE'
        assert init_sheet() is False

    @patch('src.writers.sheets_writer.get_sheets_service')
    @patch('src.writers.sheets_writer.settings')
    def test_init_sheet_updates_headers(self, mock_settings, mock_get_service):
        mock_settings.SPREADSHEET_ID = 'valid_id'
        mock_settings.SHEET_NAME = 'Sheet1'
        mock_settings.SHEET_HEADERS = ['col1', 'col2']
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        assert init_sheet() is True
        mock_service.spreadsheets().values().update.assert_called()

    @patch('src.writers.sheets_writer.get_sheets_service')
    @patch('src.writers.sheets_writer.settings')
    def test_init_sheet_handles_error(self, mock_settings, mock_get_service):
        mock_settings.SPREADSHEET_ID = 'valid_id'
        mock_get_service.side_effect = Exception("API Error")
        assert init_sheet() is False


class TestGetExistingThreadIds:
    @patch('src.writers.sheets_writer.settings')
    def test_get_ids_no_spreadsheet_id(self, mock_settings):
        mock_settings.SPREADSHEET_ID = 'YOUR_SPREADSHEET_ID_HERE'
        assert get_existing_thread_ids() == set()

    @patch('src.writers.sheets_writer.get_sheets_service')
    @patch('src.writers.sheets_writer.settings')
    def test_get_ids_returns_set(self, mock_settings, mock_get_service):
        mock_settings.SPREADSHEET_ID = 'valid_id'
        mock_settings.SHEET_NAME = 'Sheet1'
        mock_service = MagicMock()
        mock_service.spreadsheets().values().get().execute.return_value = {
            'values': [['mail_thread_id'], ['thread1'], ['thread2'], ['thread3']]
        }
        mock_get_service.return_value = mock_service

        result = get_existing_thread_ids()
        assert isinstance(result, set)
        assert 'thread1' in result
        assert 'thread2' in result
        assert 'mail_thread_id' not in result

    @patch('src.writers.sheets_writer.get_sheets_service')
    @patch('src.writers.sheets_writer.settings')
    def test_get_ids_empty_sheet(self, mock_settings, mock_get_service):
        mock_settings.SPREADSHEET_ID = 'valid_id'
        mock_settings.SHEET_NAME = 'Sheet1'
        mock_service = MagicMock()
        mock_service.spreadsheets().values().get().execute.return_value = {
            'values': [['mail_thread_id']]
        }
        mock_get_service.return_value = mock_service
        assert get_existing_thread_ids() == set()

    @patch('src.writers.sheets_writer.get_sheets_service')
    @patch('src.writers.sheets_writer.settings')
    def test_get_ids_handles_error(self, mock_settings, mock_get_service):
        mock_settings.SPREADSHEET_ID = 'valid_id'
        mock_get_service.side_effect = Exception("API Error")
        assert get_existing_thread_ids() == set()


class TestWriteInvoiceData:
    @patch('src.writers.sheets_writer.settings')
    def test_write_no_spreadsheet_id(self, mock_settings):
        mock_settings.SPREADSHEET_ID = 'YOUR_SPREADSHEET_ID_HERE'
        assert write_invoice_data({'company_name': 'Test'}) is False

    @patch('src.writers.sheets_writer.get_existing_thread_ids')
    @patch('src.writers.sheets_writer.settings')
    def test_write_skips_duplicate(self, mock_settings, mock_get_ids):
        mock_settings.SPREADSHEET_ID = 'valid_id'
        mock_get_ids.return_value = {'thread_123'}
        assert write_invoice_data({'mail_thread_id': 'thread_123', 'company_name': 'Test'}) is False

    @patch('src.writers.sheets_writer.get_sheets_service')
    @patch('src.writers.sheets_writer.get_existing_thread_ids')
    @patch('src.writers.sheets_writer.settings')
    def test_write_appends_new_row(self, mock_settings, mock_get_ids, mock_get_service):
        mock_settings.SPREADSHEET_ID = 'valid_id'
        mock_settings.RANGE_NAME = 'Sheet1!A:L'
        mock_get_ids.return_value = set()
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        result = write_invoice_data({
            'mail_thread_id': 'new_thread',
            'company_name': 'Test Corp',
            'total_price': '100.00',
            'items': []
        })
        assert result is True
        mock_service.spreadsheets().values().append.assert_called()

    @patch('src.writers.sheets_writer.get_sheets_service')
    @patch('src.writers.sheets_writer.get_existing_thread_ids')
    @patch('src.writers.sheets_writer.settings')
    def test_write_formats_items(self, mock_settings, mock_get_ids, mock_get_service):
        mock_settings.SPREADSHEET_ID = 'valid_id'
        mock_settings.RANGE_NAME = 'Sheet1!A:L'
        mock_get_ids.return_value = set()
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        items = [
            {'item_name': 'Widget A', 'quantity': 2, 'price': 10.00},
            {'item_name': 'Widget B', 'quantity': 1, 'price': 20.00}
        ]
        result = write_invoice_data({'mail_thread_id': 'thread_1', 'company_name': 'Test', 'items': items})
        assert result is True

    @patch('src.writers.sheets_writer.get_sheets_service')
    @patch('src.writers.sheets_writer.get_existing_thread_ids')
    @patch('src.writers.sheets_writer.settings')
    def test_write_handles_error(self, mock_settings, mock_get_ids, mock_get_service):
        mock_settings.SPREADSHEET_ID = 'valid_id'
        mock_get_ids.return_value = set()
        mock_get_service.side_effect = Exception("API Error")
        assert write_invoice_data({'mail_thread_id': 't1'}) is False
