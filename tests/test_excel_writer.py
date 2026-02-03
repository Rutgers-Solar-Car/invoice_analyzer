"""Tests for src/writers/excel_writer.py"""
import pytest
import os
from unittest.mock import patch, Mock, MagicMock
from src.writers.excel_writer import (
    get_workbook, get_existing_thread_ids, format_items, write_invoice_data,
    EXCEL_FILE, EXCEL_HEADERS
)


class TestExcelConfiguration:
    def test_excel_file_path_defined(self):
        assert EXCEL_FILE is not None
        assert 'invoice' in EXCEL_FILE.lower()

    def test_excel_headers_defined(self):
        assert 'mail_thread_id' in EXCEL_HEADERS
        assert 'company_name' in EXCEL_HEADERS
        assert 'total_price' in EXCEL_HEADERS
        assert 'processed_at' in EXCEL_HEADERS


class TestGetWorkbook:
    @patch('src.writers.excel_writer.os.path.exists')
    @patch('src.writers.excel_writer.load_workbook')
    def test_get_workbook_loads_existing(self, mock_load, mock_exists):
        mock_exists.return_value = True
        mock_wb = MagicMock()
        mock_load.return_value = mock_wb

        wb, existed = get_workbook()
        assert existed is True
        mock_load.assert_called_once()

    @patch('src.writers.excel_writer.os.path.exists')
    @patch('src.writers.excel_writer.os.makedirs')
    @patch('src.writers.excel_writer.Workbook')
    def test_get_workbook_creates_new(self, mock_workbook, mock_makedirs, mock_exists):
        mock_exists.return_value = False
        mock_wb = MagicMock()
        mock_workbook.return_value = mock_wb

        wb, existed = get_workbook()
        assert existed is False
        mock_workbook.assert_called_once()
        mock_wb.save.assert_called_once()

    @patch('src.writers.excel_writer.os.path.exists')
    @patch('src.writers.excel_writer.os.makedirs')
    @patch('src.writers.excel_writer.Workbook')
    def test_get_workbook_sets_headers(self, mock_workbook, mock_makedirs, mock_exists):
        mock_exists.return_value = False
        mock_wb = MagicMock()
        mock_ws = MagicMock()
        mock_wb.active = mock_ws
        mock_workbook.return_value = mock_wb

        get_workbook()
        assert mock_ws.cell.called


class TestGetExistingThreadIds:
    @patch('src.writers.excel_writer.os.path.exists')
    def test_get_ids_no_file(self, mock_exists):
        mock_exists.return_value = False
        assert get_existing_thread_ids() == set()

    @patch('src.writers.excel_writer.get_workbook')
    @patch('src.writers.excel_writer.os.path.exists')
    def test_get_ids_from_file(self, mock_exists, mock_get_wb):
        mock_exists.return_value = True
        mock_ws = MagicMock()
        mock_ws.max_row = 4
        mock_ws.cell.side_effect = lambda r, c: Mock(value=f'thread_{r}' if r > 1 else 'header')
        mock_wb = MagicMock()
        mock_wb.active = mock_ws
        mock_get_wb.return_value = (mock_wb, True)

        result = get_existing_thread_ids()
        assert isinstance(result, set)


class TestFormatItems:
    def test_format_items_empty_list(self):
        assert format_items([]) == ""

    def test_format_items_none(self):
        assert format_items(None) == ""

    def test_format_items_single_item(self):
        items = [{'item_name': 'Widget', 'quantity': 2, 'price': 10.00}]
        result = format_items(items)
        assert 'Widget' in result
        assert 'x2' in result
        assert '$10' in result

    def test_format_items_multiple_items(self):
        items = [
            {'item_name': 'Widget A', 'quantity': 1, 'price': 5.00},
            {'item_name': 'Widget B', 'quantity': 3, 'price': 15.00}
        ]
        result = format_items(items)
        assert 'Widget A' in result
        assert 'Widget B' in result
        assert '; ' in result

    def test_format_items_missing_fields(self):
        items = [{'item_name': 'Widget'}]
        result = format_items(items)
        assert 'Widget' in result
        assert 'x1' in result
        assert '$0' in result

    def test_format_items_non_dict_ignored(self):
        items = [{'item_name': 'Valid'}, "invalid", 123]
        result = format_items(items)
        assert 'Valid' in result
        assert 'invalid' not in result


class TestWriteInvoiceData:
    @patch('src.writers.excel_writer.get_existing_thread_ids')
    def test_write_skips_duplicate(self, mock_get_ids):
        mock_get_ids.return_value = {'thread_123'}
        assert write_invoice_data({'mail_thread_id': 'thread_123', 'company_name': 'Test'}) is False

    @patch('src.writers.excel_writer.get_workbook')
    @patch('src.writers.excel_writer.get_existing_thread_ids')
    def test_write_appends_row(self, mock_get_ids, mock_get_wb):
        mock_get_ids.return_value = set()
        mock_ws = MagicMock()
        mock_ws.max_row = 1
        mock_wb = MagicMock()
        mock_wb.active = mock_ws
        mock_get_wb.return_value = (mock_wb, True)

        result = write_invoice_data({
            'mail_thread_id': 'new_thread',
            'company_name': 'Test Corp',
            'total_price': '100.00'
        })
        assert result is True
        mock_wb.save.assert_called()
        mock_wb.close.assert_called()

    @patch('src.writers.excel_writer.get_workbook')
    @patch('src.writers.excel_writer.get_existing_thread_ids')
    def test_write_includes_timestamp(self, mock_get_ids, mock_get_wb):
        mock_get_ids.return_value = set()
        mock_ws = MagicMock()
        mock_ws.max_row = 1
        mock_wb = MagicMock()
        mock_wb.active = mock_ws
        mock_get_wb.return_value = (mock_wb, True)

        result = write_invoice_data({'mail_thread_id': 'thread_1', 'company_name': 'Test'})
        assert result is True
        assert len(mock_ws.cell.call_args_list) > 0

    @patch('src.writers.excel_writer.get_existing_thread_ids')
    def test_write_handles_error(self, mock_get_ids):
        mock_get_ids.side_effect = Exception("File error")
        assert write_invoice_data({'mail_thread_id': 't1'}) is False

    @patch('src.writers.excel_writer.get_workbook')
    @patch('src.writers.excel_writer.get_existing_thread_ids')
    def test_write_formats_items_correctly(self, mock_get_ids, mock_get_wb):
        mock_get_ids.return_value = set()
        mock_ws = MagicMock()
        mock_ws.max_row = 1
        mock_wb = MagicMock()
        mock_wb.active = mock_ws
        mock_get_wb.return_value = (mock_wb, True)

        items = [{'item_name': 'Widget', 'quantity': 2, 'price': 25.00}]
        result = write_invoice_data({
            'mail_thread_id': 'thread_1',
            'company_name': 'Test',
            'items': items
        })
        assert result is True
