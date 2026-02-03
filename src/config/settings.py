"""Centralized configuration."""

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/spreadsheets'
]

SPREADSHEET_ID = '12oQ5MtzZ2GBQX9pk6aJ-U9TDYPXmARoOZ0rT1XxNhfs'
SHEET_NAME = 'Sheet1'
RANGE_NAME = f'{SHEET_NAME}!A:L'

SHEET_HEADERS = [
    "mail_thread_id", "company_name", "purchase_date", "mail_received_time",
    "purchase_receiver", "total_price", "item_names", "item_quantities",
    "item_prices", "other_expenses", "processed_at"
]

CREDENTIALS_FILE = 'credentials/credentials.json'
TOKEN_FILE = 'credentials/token.json'
INVOICE_DIR = 'data/invoices'
OLD_INVOICE_DIR = 'data/old_invoices'
PROCESSED_IDS_FILE = 'data/processed_ids.json'

GMAIL_SEARCH_QUERY = 'Invoice OR Receipt OR Bill'
CHECK_INTERVAL_SECONDS = 60
MONITOR_CHECK_INTERVAL = 20

OLLAMA_MODEL = "gemma2:2b"
OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_TIMEOUT = 300

KNOWN_VENDORS = {
    "homedepot.com": "home_depot",
    "homedepot": "home_depot",
    "mcmaster.com": "mcmaster_carr",
    "mcmaster-carr.com": "mcmaster_carr",
}

INVOICE_SCHEMA = {
    "mail_thread_id": "string",
    "company_name": "string",
    "purchase_date": "YYYY-MM-DD",
    "mail_received_time": "string",
    "purchase_receiver": "string",
    "total_price": "float",
    "sum of other_expanses": "float",
    "items": [{"item_name": "string", "quantity": "integer", "price": "float"}]
}
