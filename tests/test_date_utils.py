"""Tests for src/utils/date_utils.py"""
import pytest
from datetime import datetime, timedelta
from src.utils.date_utils import normalize_date, unix_timestamp


class TestNormalizeDate:
    def test_normalize_date_mm_dd_yy(self):
        assert normalize_date("01/15/24") == "2024-01-15"

    def test_normalize_date_yyyy_mm_dd(self):
        assert normalize_date("2024-01-15") == "2024-01-15"

    def test_normalize_date_mm_dd_yyyy(self):
        assert normalize_date("01/15/2024") == "2024-01-15"

    def test_normalize_date_empty_string(self):
        assert normalize_date("") == ""

    def test_normalize_date_none(self):
        assert normalize_date(None) == ""

    def test_normalize_date_invalid_format(self):
        assert normalize_date("January 15, 2024") == "January 15, 2024"

    def test_normalize_date_partial_date(self):
        assert normalize_date("01/15") == "01/15"


class TestUnixTimestamp:
    def test_unix_timestamp_zero_seconds(self):
        result = unix_timestamp(0)
        expected = int(datetime.now().timestamp())
        assert abs(result - expected) <= 2

    def test_unix_timestamp_60_seconds(self):
        result = unix_timestamp(60)
        expected = int((datetime.now() - timedelta(seconds=60)).timestamp())
        assert abs(result - expected) <= 2

    def test_unix_timestamp_returns_int(self):
        assert isinstance(unix_timestamp(100), int)

    def test_unix_timestamp_past_is_smaller(self):
        past = unix_timestamp(3600)
        current = unix_timestamp(0)
        assert past < current
