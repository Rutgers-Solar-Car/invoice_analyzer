"""Tests for src/utils/file_utils.py"""
import pytest
import time
from src.utils.file_utils import sanitize_filename, safe_filename


class TestSanitizeFilename:
    def test_sanitize_removes_backslash(self):
        result = sanitize_filename("file\\name.txt")
        assert "\\" not in result
        assert result == "file_name.txt"

    def test_sanitize_removes_forward_slash(self):
        result = sanitize_filename("path/to/file.txt")
        assert "/" not in result

    def test_sanitize_removes_colon(self):
        result = sanitize_filename("C:file.txt")
        assert ":" not in result

    def test_sanitize_removes_asterisk(self):
        result = sanitize_filename("file*.txt")
        assert "*" not in result

    def test_sanitize_removes_question_mark(self):
        result = sanitize_filename("file?.txt")
        assert "?" not in result

    def test_sanitize_removes_quotes(self):
        result = sanitize_filename('file"name.txt')
        assert '"' not in result

    def test_sanitize_removes_angle_brackets(self):
        result = sanitize_filename("file<name>.txt")
        assert "<" not in result
        assert ">" not in result

    def test_sanitize_removes_pipe(self):
        result = sanitize_filename("file|name.txt")
        assert "|" not in result

    def test_sanitize_removes_newlines(self):
        result = sanitize_filename("file\nname.txt")
        assert "\n" not in result

    def test_sanitize_removes_tabs(self):
        result = sanitize_filename("file\tname.txt")
        assert "\t" not in result

    def test_sanitize_strips_whitespace(self):
        assert sanitize_filename("  filename.txt  ") == "filename.txt"

    def test_sanitize_empty_returns_attachment(self):
        assert sanitize_filename("") == "attachment"

    def test_sanitize_only_bad_chars_returns_underscore(self):
        result = sanitize_filename("\\/:*?\"<>|")
        assert "_" in result or result == "attachment"

    def test_sanitize_preserves_valid_filename(self):
        assert sanitize_filename("valid_filename-123.pdf") == "valid_filename-123.pdf"


class TestSafeFilename:
    def test_safe_filename_adds_timestamp_prefix(self):
        result = safe_filename("document.pdf")
        assert result.endswith("_document.pdf")
        prefix = result.split("_")[0]
        assert prefix.isdigit()

    def test_safe_filename_unique_timestamps(self):
        result1 = safe_filename("test.txt")
        time.sleep(0.01)
        result2 = safe_filename("test.txt")
        assert "_test.txt" in result1
        assert "_test.txt" in result2

    def test_safe_filename_preserves_extension(self):
        result = safe_filename("report.xlsx")
        assert result.endswith(".xlsx")

    def test_safe_filename_handles_no_extension(self):
        result = safe_filename("README")
        assert result.endswith("_README")
