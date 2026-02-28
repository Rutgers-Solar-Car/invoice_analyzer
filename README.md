#  Invoice Tracker – Rutgers Solar Car

A professional Python application that automatically monitors Gmail for invoices, extracts data using LLM and vendor-specific parsers, and writes to Google Sheets.

##  Features

*  Gmail API + OAuth 2.0 authentication
*  Automatic invoice email detection (Invoice, Receipt, Bill keywords)
*  PDF attachment and email text extraction
*  Dual extraction engines:
  * Vendor-specific regex parsers (Home Depot, McMaster-Carr)
  * LLM-based extraction via Ollama for unknown vendors
*  Google Sheets integration for data storage
*  24/7 monitoring with configurable check intervals
*  Scheduled processing (midnight & 7 AM)

---

##  Requirements

* Python **3.10+**
* Gmail account (Rutgers Gmail supported)
* Google Cloud project with Gmail API and Sheets API enabled
* Ollama (for LLM extraction)

---

##  Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Google Cloud credentials:**
   * Download `credentials.json` from Google Cloud Console
   * Place in `credentials/` folder

3. **Configure settings:**
   * Edit `src/config/settings.py`
   * Set your `SPREADSHEET_ID`

4. **Run the application:**
   ```bash
   python main.py
   ```

---

##  Project Structure

```
Invoice-Tracker/
├── main.py                    # Main entry point
├── requirements.txt           # Python dependencies
├── README.md                  # Documentation
│
├── src/
│   ├── auth/
│   │   └── gmail_auth.py      # Gmail & Sheets authentication
│   ├── config/
│   │   └── settings.py        # Centralized configuration
│   ├── downloaders/
│   │   ├── bulk_downloader.py     # Historical email downloader
│   │   └── monitor_downloader.py  # Real-time email monitor
│   ├── processors/
│   │   ├── invoice_processor.py   # Orchestrates parsing
│   │   ├── file_handler.py        # PDF/TXT file operations
│   │   ├── llm_extractor.py       # LLM-based extraction
│   │   └── vendor_parser.py       # Vendor-specific parsers
│   ├── writers/
│   │   └── sheets_writer.py       # Google Sheets writer
│   └── utils/
│       ├── file_utils.py          # File utilities
│       └── date_utils.py          # Date utilities
│
├── credentials/
│   ├── credentials.json       # OAuth credentials (you provide)
│   └── token.json            # Auth token (auto-generated)
│
└── data/
    ├── invoices/             # Current invoices
    ├── old_invoices/         # Historical invoices
    └── processed_ids.json    # Tracking file
```

---

##  Google Cloud Setup

### 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project → name it `invoice-tracker`

### 2. Enable APIs

1. Enable **Gmail API**
2. Enable **Google Sheets API**

### 3. OAuth Consent Screen

1. **APIs & Services** → **OAuth consent screen**
2. User Type: **External**
3. App name: `Invoice Tracker`
4. Add your email as developer contact

### 4. Create Credentials

1. **APIs & Services** → **Credentials**
2. **Create Credentials** → **OAuth Client ID**
3. Application type: **Desktop App**
4. Download JSON → rename to `credentials.json`
5. Place in `credentials/` folder

---

##  Configuration

Edit `src/config/settings.py`:

```python
# Your Google Sheets ID (from the URL)
SPREADSHEET_ID = 'your-spreadsheet-id-here'

# Check interval (seconds)
CHECK_INTERVAL_SECONDS = 60

# Ollama configuration
OLLAMA_MODEL = "gemma2:2b"
OLLAMA_URL = "http://localhost:11434/api/chat"
```

---

## Usage

Run the main application:

```bash
python main.py
```

### Menu Options

1. **Test Gmail Connection** - Verify authentication
2. **Download Old Emails** - Bulk download historical invoices
3. **Start Invoice Monitor** - Download-only mode (no processing)
4. **Process Existing Invoices** - Process downloaded invoices
5. **FULL AUTO (24/7)** - Complete automation (backfill + monitor)
6. **Scheduled Check** - Run at midnight & 7 AM daily

---

##  Testing

1. Send yourself a test email with subject containing "Invoice"
2. Attach a PDF or include invoice details in email body
3. Run option **3** (Monitor) or **5** (Full Auto)
4. Check your Google Sheet for extracted data

---

##  Architecture

### Single Responsibility Design

Each module has one clear purpose:

* **`auth/`** - Authentication only
* **`config/`** - Configuration management
* **`downloaders/`** - Email downloading
* **`processors/`** - Data extraction and processing
* **`writers/`** - Data output to Google Sheets
* **`utils/`** - Shared utilities

### Processing Flow

```
Gmail → Downloader → File Handler → Invoice Processor
                                           ↓
                              Vendor Parser or LLM Extractor
                                           ↓
                                    Sheets Writer
```

---

##  Development

### Adding a New Vendor Parser

Edit `src/processors/vendor_parser.py`:

```python
@register("new_vendor")
def parse_new_vendor(text: str) -> dict:
    # Your parsing logic
    return {
        "organizations": ["Vendor Name"],
        "dates": [...],
        "total_amount": [...],
        ...
    }
```

Update `src/config/settings.py`:

```python
KNOWN_VENDORS = {
    "vendor.com": "new_vendor",
    ...
}
```

---

##  Notes

* **Credentials:** Never commit `credentials.json` or `token.json`
* **Data Files:** Stored in `data/` for easy management
* **Logs:** All operations print status messages for debugging
* **Duplicate Prevention:** Uses Gmail thread IDs to avoid duplicates

---

##  Troubleshooting

**Authentication errors:**
* Delete `credentials/token.json` and re-authenticate

**No emails found:**
* Check `src/config/settings.py` → `GMAIL_SEARCH_QUERY`
* Verify email keywords match your inbox

**LLM extraction fails:**
* Ensure Ollama is running: `ollama serve`
* Check model is installed: `ollama list`

**Google Sheets errors:**
* Verify `SPREADSHEET_ID` is correct
* Ensure Sheets API is enabled
* Check sheet permissions

---

## 📝 License

Internal use for Rutgers Solar Car team.
