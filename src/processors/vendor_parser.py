"""Vendor-specific invoice parsing."""
import re

from src.config import settings
from src.utils.date_utils import normalize_date

VENDOR_PARSERS = {}


def register(key: str):
    """Decorator to register a vendor parser function."""
    def decorator(func):
        VENDOR_PARSERS[key] = func
        return func
    return decorator


@register("home_depot")
def parse_home_depot(text: str) -> dict:
    """Parse Home Depot invoice format."""
    data = {
        "organizations": ["The Home Depot"],
        "dates": [],
        "total_amount": [],
        "order_number": [],
        "customer_info": {},
        "shipping": []
    }

    m = re.search(r'Order\s*#?\s*([A-Z0-9]{8,})', text, re.I)
    if m:
        data["order_number"].append(m.group(1))

    for m in re.finditer(r'\b(\d{1,2}/\d{1,2}/\d{4})\b', text):
        if m.group(1) not in data["dates"]:
            data["dates"].append(m.group(1))

    m = re.search(r'Total[:\s]+\$?([\d,]+\.\d{2})', text, re.I)
    if m:
        data["total_amount"].append(m.group(1))

    return data


@register("mcmaster_carr")
def parse_mcmaster_carr(text: str) -> dict:
    """Parse McMaster-Carr invoice format."""
    data = {
        "organizations": ["McMaster-Carr"],
        "dates": [],
        "total_amount": [],
        "order_number": [],
        "ordered_by": "",
        "shipping": [],
        "items": []
    }

    m = re.search(r'Order Date\s+[\s\S]*?(\d{1,2}/\d{1,2}/\d{2,4})', text, re.I)
    if m:
        data["dates"].append(m.group(1))

    m = re.search(r'McMaster-Carr Number\s+[^\n]*?(\d{7,})', text, re.I)
    if m:
        data["order_number"].append(m.group(1))

    m = re.search(r'Ordered By\s+[^\n]*?([A-Za-z\s]+)\s+\d+', text, re.I)
    if m:
        data["ordered_by"] = m.group(1).strip()

    m = re.search(r'Total\s+\$?([\d,]+\.\d{2})', text, re.I)
    if m:
        data["total_amount"].append(m.group(1))

    m = re.search(r'Shipping\s+([\d,]+\.\d{2})', text, re.I)
    if m:
        data["shipping"].append(m.group(1))

    item_pattern = r'^\s*(\d+)\s+([A-Z0-9]+)\s+(.+?)\s+(\d+)\s+[A-Za-z]+\s+\d+\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})'
    for match in re.finditer(item_pattern, text, re.MULTILINE):
        item_name = f"{match.group(2)} {match.group(3).strip()}"
        quantity = int(match.group(4))
        price = float(match.group(6).replace(',', ''))
        data["items"].append({
            "item_name": item_name,
            "quantity": quantity,
            "price": price
        })

    return data


def parse(text: str, vendor_key: str = None) -> dict:
    """Parse invoice text using vendor-specific parser."""
    if vendor_key and vendor_key in VENDOR_PARSERS:
        print(f"[VENDOR PARSER] {vendor_key}")
        return VENDOR_PARSERS[vendor_key](text)
    return None


def normalize_to_schema(raw: dict) -> dict:
    """Convert raw vendor-parsed data to standard invoice schema."""
    if not raw:
        return None

    return {
        "mail_thread_id": "",
        "company_name": raw.get("organizations", [""])[0] if raw.get("organizations") else "",
        "purchase_date": normalize_date(raw.get("dates", [""])[0]) if raw.get("dates") else "",
        "mail_received_time": "",
        "purchase_receiver": raw.get("customer_info", {}).get("name", raw.get("ordered_by", "")),
        "total_price": raw.get("total_amount", [""])[0] if raw.get("total_amount") else "",
        "sum of other_expanses": ", ".join(raw.get("shipping", [])) if raw.get("shipping") else "",
        "items": raw.get("items", [])
    }
