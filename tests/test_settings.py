"""Tests for src/config/settings.py"""
import pytest
from src.config import settings


class TestSettingsConfiguration:
    def test_settings_has_scopes(self):
        assert hasattr(settings, 'SCOPES')
        assert isinstance(settings.SCOPES, list)
        assert len(settings.SCOPES) > 0

    def test_scopes_contains_gmail_readonly(self):
        assert 'https://www.googleapis.com/auth/gmail.readonly' in settings.SCOPES

    def test_scopes_contains_spreadsheets(self):
        assert 'https://www.googleapis.com/auth/spreadsheets' in settings.SCOPES

    def test_settings_has_spreadsheet_id(self):
        assert hasattr(settings, 'SPREADSHEET_ID')
        assert isinstance(settings.SPREADSHEET_ID, str)

    def test_settings_has_sheet_name(self):
        assert hasattr(settings, 'SHEET_NAME')
        assert settings.SHEET_NAME == 'Sheet1'

    def test_settings_has_sheet_headers(self):
        assert hasattr(settings, 'SHEET_HEADERS')
        assert isinstance(settings.SHEET_HEADERS, list)
        assert 'mail_thread_id' in settings.SHEET_HEADERS
        assert 'company_name' in settings.SHEET_HEADERS
        assert 'total_price' in settings.SHEET_HEADERS

    def test_settings_has_credentials_file(self):
        assert hasattr(settings, 'CREDENTIALS_FILE')
        assert 'credentials' in settings.CREDENTIALS_FILE.lower()

    def test_settings_has_token_file(self):
        assert hasattr(settings, 'TOKEN_FILE')
        assert 'token' in settings.TOKEN_FILE.lower()

    def test_settings_has_invoice_dir(self):
        assert hasattr(settings, 'INVOICE_DIR')
        assert 'invoice' in settings.INVOICE_DIR.lower()

    def test_settings_has_gmail_search_query(self):
        assert hasattr(settings, 'GMAIL_SEARCH_QUERY')
        assert 'Invoice' in settings.GMAIL_SEARCH_QUERY

    def test_settings_has_check_interval(self):
        assert hasattr(settings, 'CHECK_INTERVAL_SECONDS')
        assert isinstance(settings.CHECK_INTERVAL_SECONDS, int)
        assert settings.CHECK_INTERVAL_SECONDS > 0


class TestKnownVendors:
    def test_known_vendors_exists(self):
        assert hasattr(settings, 'KNOWN_VENDORS')
        assert isinstance(settings.KNOWN_VENDORS, dict)

    def test_known_vendors_has_home_depot(self):
        vendors = settings.KNOWN_VENDORS
        home_depot_found = any('homedepot' in k.lower() for k in vendors.keys())
        assert home_depot_found

    def test_known_vendors_has_mcmaster(self):
        vendors = settings.KNOWN_VENDORS
        mcmaster_found = any('mcmaster' in k.lower() for k in vendors.keys())
        assert mcmaster_found


class TestOllamaConfiguration:
    def test_ollama_model_defined(self):
        assert hasattr(settings, 'OLLAMA_MODEL')
        assert isinstance(settings.OLLAMA_MODEL, str)

    def test_ollama_url_defined(self):
        assert hasattr(settings, 'OLLAMA_URL')
        assert settings.OLLAMA_URL.startswith('http')

    def test_ollama_timeout_defined(self):
        assert hasattr(settings, 'OLLAMA_TIMEOUT')
        assert isinstance(settings.OLLAMA_TIMEOUT, int)
        assert settings.OLLAMA_TIMEOUT > 0


class TestInvoiceSchema:
    def test_invoice_schema_exists(self):
        assert hasattr(settings, 'INVOICE_SCHEMA')
        assert isinstance(settings.INVOICE_SCHEMA, dict)

    def test_invoice_schema_has_required_fields(self):
        schema = settings.INVOICE_SCHEMA
        assert 'mail_thread_id' in schema
        assert 'company_name' in schema
        assert 'total_price' in schema
        assert 'items' in schema
