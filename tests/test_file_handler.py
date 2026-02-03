"""Tests for src/processors/file_handler.py"""
import pytest
import os
from unittest.mock import patch, Mock, MagicMock
from src.processors.file_handler import (
    read_txt, read_pdf, read_file, parse_email_headers, get_invoice_files, combine_content
)


class TestReadTxt:
    def test_read_txt_returns_content(self, temp_dir):
        filepath = os.path.join(temp_dir, "test.txt")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("Hello World")
        assert read_txt(filepath) == "Hello World"

    def test_read_txt_utf8_encoding(self, temp_dir):
        filepath = os.path.join(temp_dir, "test.txt")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("Unicode: café ñ 日本語")
        result = read_txt(filepath)
        assert "café" in result
        assert "日本語" in result

    def test_read_txt_multiline(self, temp_dir):
        filepath = os.path.join(temp_dir, "test.txt")
        content = "Line 1\nLine 2\nLine 3"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        assert read_txt(filepath) == content


class TestReadPdf:
    @patch('src.processors.file_handler.pdfplumber.open')
    def test_read_pdf_extracts_text(self, mock_pdf_open):
        mock_page = Mock()
        mock_page.extract_text.return_value = "PDF content here"
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        mock_pdf_open.return_value = mock_pdf

        assert "PDF content here" in read_pdf("fake.pdf")

    @patch('src.processors.file_handler.pdfplumber.open')
    def test_read_pdf_multiple_pages(self, mock_pdf_open):
        mock_page1, mock_page2 = Mock(), Mock()
        mock_page1.extract_text.return_value = "Page 1"
        mock_page2.extract_text.return_value = "Page 2"
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        mock_pdf_open.return_value = mock_pdf

        result = read_pdf("fake.pdf")
        assert "Page 1" in result
        assert "Page 2" in result

    @patch('src.processors.file_handler.pdfplumber.open')
    def test_read_pdf_empty_page(self, mock_pdf_open):
        mock_page = Mock()
        mock_page.extract_text.return_value = None
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        mock_pdf_open.return_value = mock_pdf

        assert read_pdf("fake.pdf") == ""


class TestReadFile:
    def test_read_file_txt(self, temp_dir):
        filepath = os.path.join(temp_dir, "test.txt")
        with open(filepath, 'w') as f:
            f.write("Text content")
        assert read_file(filepath) == "Text content"

    @patch('src.processors.file_handler.read_pdf')
    def test_read_file_pdf(self, mock_read_pdf, temp_dir):
        mock_read_pdf.return_value = "PDF content"
        filepath = os.path.join(temp_dir, "test.pdf")
        read_file(filepath)
        mock_read_pdf.assert_called_once()

    def test_read_file_unknown_extension(self, temp_dir):
        filepath = os.path.join(temp_dir, "test.xyz")
        assert read_file(filepath) == ""

    def test_read_file_case_insensitive(self, temp_dir):
        filepath = os.path.join(temp_dir, "test.TXT")
        with open(filepath, 'w') as f:
            f.write("Content")
        assert read_file(filepath) == "Content"


class TestParseEmailHeaders:
    def test_parse_email_headers_extracts_sender(self, temp_dir, sample_email_text):
        filepath = os.path.join(temp_dir, "email.txt")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(sample_email_text)
        result = parse_email_headers(filepath)
        assert result['sender_email'] == 'orders@example.com'

    def test_parse_email_headers_extracts_thread_id(self, temp_dir, sample_email_text):
        filepath = os.path.join(temp_dir, "email.txt")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(sample_email_text)
        result = parse_email_headers(filepath)
        assert result['thread_id'] == 'thread_abc123'

    def test_parse_email_headers_extracts_date(self, temp_dir, sample_email_text):
        filepath = os.path.join(temp_dir, "email.txt")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(sample_email_text)
        result = parse_email_headers(filepath)
        assert 'Mon, 15 Jan 2024' in result['received_time']

    def test_parse_email_headers_extracts_subject(self, temp_dir, sample_email_text):
        filepath = os.path.join(temp_dir, "email.txt")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(sample_email_text)
        result = parse_email_headers(filepath)
        assert result['subject'] == 'Your Order Confirmation'

    def test_parse_email_headers_missing_fields(self, temp_dir):
        filepath = os.path.join(temp_dir, "email.txt")
        with open(filepath, 'w') as f:
            f.write("Just body text, no headers")
        result = parse_email_headers(filepath)
        assert result['sender_email'] == ''
        assert result['thread_id'] == ''


class TestGetInvoiceFiles:
    @patch('src.processors.file_handler.settings')
    def test_get_invoice_files_groups_by_timestamp(self, mock_settings, temp_dir):
        mock_settings.INVOICE_DIR = temp_dir
        base = "msgid_1705329000000"
        open(os.path.join(temp_dir, f"{base}.txt"), 'w').close()
        open(os.path.join(temp_dir, f"{base}_invoice.pdf"), 'w').close()

        result = get_invoice_files()
        assert len(result) == 1
        assert len(list(result.values())[0]) == 2

    @patch('src.processors.file_handler.settings')
    def test_get_invoice_files_ignores_non_invoice_files(self, mock_settings, temp_dir):
        mock_settings.INVOICE_DIR = temp_dir
        open(os.path.join(temp_dir, "readme.md"), 'w').close()
        open(os.path.join(temp_dir, "config.json"), 'w').close()
        open(os.path.join(temp_dir, "invoice_1705329000000.txt"), 'w').close()

        result = get_invoice_files()
        all_files = []
        for files in result.values():
            all_files.extend(files)
        assert all(f.endswith(('.txt', '.pdf')) for f in all_files)

    @patch('src.processors.file_handler.settings')
    def test_get_invoice_files_nonexistent_dir(self, mock_settings):
        mock_settings.INVOICE_DIR = "/nonexistent/path"
        assert get_invoice_files() == {}


class TestCombineContent:
    def test_combine_content_multiple_files(self, temp_dir):
        file1 = os.path.join(temp_dir, "file1.txt")
        file2 = os.path.join(temp_dir, "file2.txt")
        with open(file1, 'w') as f:
            f.write("Content 1")
        with open(file2, 'w') as f:
            f.write("Content 2")

        result = combine_content([file1, file2])
        assert "Content 1" in result
        assert "Content 2" in result

    def test_combine_content_adds_separators(self, temp_dir):
        file1 = os.path.join(temp_dir, "test.txt")
        with open(file1, 'w') as f:
            f.write("Content")
        result = combine_content([file1])
        assert "---" in result

    def test_combine_content_empty_list(self):
        assert combine_content([]) == ""
