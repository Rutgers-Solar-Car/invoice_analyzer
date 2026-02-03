"""Tests for src/processors/vendor_parser.py"""
import pytest
from src.processors.vendor_parser import (
    parse, 
    normalize_to_schema, 
    parse_home_depot, 
    parse_mcmaster_carr,
    VENDOR_PARSERS
)


class TestVendorParserRegistry:
    def test_home_depot_registered(self):
        assert 'home_depot' in VENDOR_PARSERS

    def test_mcmaster_carr_registered(self):
        assert 'mcmaster_carr' in VENDOR_PARSERS


class TestHomeDepotParser:
    def test_parse_home_depot_order_number(self, sample_home_depot_text):
        result = parse_home_depot(sample_home_depot_text)
        assert 'order_number' in result
        assert len(result['order_number']) > 0
        assert 'WD12345678' in result['order_number']

    def test_parse_home_depot_organization(self, sample_home_depot_text):
        result = parse_home_depot(sample_home_depot_text)
        assert 'organizations' in result
        assert 'The Home Depot' in result['organizations']

    def test_parse_home_depot_dates(self, sample_home_depot_text):
        result = parse_home_depot(sample_home_depot_text)
        assert 'dates' in result
        assert len(result['dates']) > 0

    def test_parse_home_depot_total(self, sample_home_depot_text):
        result = parse_home_depot(sample_home_depot_text)
        assert 'total_amount' in result
        assert len(result['total_amount']) > 0
        assert result['total_amount'][0] in ['77.88', '84.11']

    def test_parse_home_depot_no_order_number(self):
        result = parse_home_depot("Random text without order")
        assert result['order_number'] == []


class TestMcMasterCarrParser:
    def test_parse_mcmaster_order_number(self, sample_mcmaster_text):
        result = parse_mcmaster_carr(sample_mcmaster_text)
        assert 'order_number' in result
        assert len(result['order_number']) > 0

    def test_parse_mcmaster_organization(self, sample_mcmaster_text):
        result = parse_mcmaster_carr(sample_mcmaster_text)
        assert 'organizations' in result
        assert 'McMaster-Carr' in result['organizations']

    def test_parse_mcmaster_ordered_by(self, sample_mcmaster_text):
        result = parse_mcmaster_carr(sample_mcmaster_text)
        assert 'ordered_by' in result

    def test_parse_mcmaster_shipping(self, sample_mcmaster_text):
        result = parse_mcmaster_carr(sample_mcmaster_text)
        assert 'shipping' in result

    def test_parse_mcmaster_total(self, sample_mcmaster_text):
        result = parse_mcmaster_carr(sample_mcmaster_text)
        assert 'total_amount' in result

    def test_parse_mcmaster_items(self, sample_mcmaster_text):
        result = parse_mcmaster_carr(sample_mcmaster_text)
        assert 'items' in result


class TestParseFunction:
    def test_parse_with_home_depot_vendor(self, sample_home_depot_text):
        result = parse(sample_home_depot_text, 'home_depot')
        assert result is not None
        assert 'The Home Depot' in result['organizations']

    def test_parse_with_mcmaster_vendor(self, sample_mcmaster_text):
        result = parse(sample_mcmaster_text, 'mcmaster_carr')
        assert result is not None
        assert 'McMaster-Carr' in result['organizations']

    def test_parse_with_unknown_vendor(self):
        result = parse("Some text", 'unknown_vendor')
        assert result is None

    def test_parse_with_none_vendor(self):
        result = parse("Some text", None)
        assert result is None


class TestNormalizeToSchema:
    def test_normalize_empty_returns_none(self):
        assert normalize_to_schema(None) is None

    def test_normalize_empty_dict_returns_dict(self):
        result = normalize_to_schema({})
        assert result is None or isinstance(result, dict)

    def test_normalize_extracts_company_name(self):
        raw = {'organizations': ['Test Corp']}
        result = normalize_to_schema(raw)
        assert result['company_name'] == 'Test Corp'

    def test_normalize_extracts_first_date(self):
        raw = {'dates': ['01/15/24', '01/16/24']}
        result = normalize_to_schema(raw)
        assert result['purchase_date'] == '2024-01-15'

    def test_normalize_extracts_total_price(self):
        raw = {'total_amount': ['150.00']}
        result = normalize_to_schema(raw)
        assert result['total_price'] == '150.00'

    def test_normalize_extracts_shipping_as_other_expenses(self):
        raw = {'shipping': ['10.00', '5.00']}
        result = normalize_to_schema(raw)
        assert '10.00' in result['sum of other_expanses']
        assert '5.00' in result['sum of other_expanses']

    def test_normalize_preserves_items(self):
        items = [{'item_name': 'Widget', 'quantity': 2, 'price': 10.00}]
        raw = {'items': items}
        result = normalize_to_schema(raw)
        assert result['items'] == items

    def test_normalize_handles_missing_fields(self):
        raw = {'organizations': ['Test']}
        result = normalize_to_schema(raw)
        assert result['mail_thread_id'] == ''
        assert result['mail_received_time'] == ''
        assert result['items'] == []
