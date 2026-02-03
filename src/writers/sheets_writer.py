"""Google Sheets writer for invoice data."""
from datetime import datetime

from src.auth.gmail_auth import get_sheets_service
from src.config import settings


def init_sheet() -> bool:
    """Initialize Google Sheets with headers."""
    if settings.SPREADSHEET_ID == 'YOUR_SPREADSHEET_ID_HERE':
        print("[ERROR] Please set SPREADSHEET_ID in src/config/settings.py")
        return False

    try:
        service = get_sheets_service()
        sheet = service.spreadsheets()

        body = {'values': [settings.SHEET_HEADERS]}
        sheet.values().update(
            spreadsheetId=settings.SPREADSHEET_ID,
            range=f'{settings.SHEET_NAME}!A1:K1',
            valueInputOption='RAW',
            body=body
        ).execute()

        print("[OK] Headers updated")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to initialize sheet: {e}")
        return False


def get_existing_thread_ids() -> set:
    """Retrieve all existing thread IDs from the spreadsheet."""
    if settings.SPREADSHEET_ID == 'YOUR_SPREADSHEET_ID_HERE':
        return set()

    try:
        service = get_sheets_service()
        result = service.spreadsheets().values().get(
            spreadsheetId=settings.SPREADSHEET_ID,
            range=f'{settings.SHEET_NAME}!A:A'
        ).execute()

        values = result.get('values', [])
        return {str(row[0]) for row in values[1:] if row}
    except Exception as e:
        print(f"[WARN] Could not fetch existing thread IDs: {e}")
        return set()


def write_invoice_data(data: dict) -> bool:
    """Write invoice data to Google Sheets."""
    if settings.SPREADSHEET_ID == 'YOUR_SPREADSHEET_ID_HERE':
        print("[ERROR] SPREADSHEET_ID not set")
        return False

    try:
        tid = str(data.get("mail_thread_id", ""))
        existing = get_existing_thread_ids()

        if tid and tid in existing:
            print(f"[SKIP] Duplicate: {tid}")
            return False

        items = data.get("items", [])
        item_names = ", ".join([str(i.get('item_name', '')) for i in items if isinstance(i, dict)])
        item_quantities = ", ".join([str(i.get('quantity', '')) for i in items if isinstance(i, dict)])
        item_prices = ", ".join([str(i.get('price', '')) for i in items if isinstance(i, dict)])

        values = [[
            data.get("mail_thread_id", ""),
            data.get("company_name", ""),
            data.get("purchase_date", ""),
            data.get("mail_received_time", ""),
            data.get("purchase_receiver", ""),
            data.get("total_price", ""),
            item_names,
            item_quantities,
            item_prices,
            data.get("sum of other_expanses", data.get("other_expenses", "")),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ]]

        service = get_sheets_service()
        body = {'values': values}
        service.spreadsheets().values().append(
            spreadsheetId=settings.SPREADSHEET_ID,
            range=settings.RANGE_NAME,
            valueInputOption='RAW',
            body=body
        ).execute()

        print(f"[OK] Saved to Google Sheets: {data.get('company_name', '?')}")
        return True

    except Exception as e:
        print(f"[ERROR] GSheets: {e}")
        return False
