# Migration Guide: Old → New Structure

## Overview
The Invoice Tracker has been reorganized into a professional, modular architecture with single-responsibility modules.

---

## File Mapping

### Old Files → New Files

| Old File | New Location | Purpose |
|----------|--------------|---------|
| `Driver.py` | `main.py` | Main entry point |
| `check_gmail_connection.py` | `src/auth/gmail_auth.py` | Authentication (Gmail & Sheets) |
| `download_gmail_ALLpdfs.py` | `src/downloaders/bulk_downloader.py` | Bulk historical downloads |
| `regularCheck_gmail_pdfs.py` | `src/downloaders/monitor_downloader.py` | Real-time monitoring |
| `model_router.py` | `src/processors/invoice_processor.py` | Invoice processing orchestration |
| `file_reader.py` | `src/processors/file_handler.py` | File I/O operations |
| `llm_extractor.py` | `src/processors/llm_extractor.py` | LLM extraction (moved to src/) |
| `vendor_parser.py` | `src/processors/vendor_parser.py` | Vendor parsing (moved to src/) |
| `gsheets_writer.py` | `src/writers/sheets_writer.py` | Google Sheets writer |
| `excel_writer.py` | **DELETED** | Unused, duplicate functionality |
| N/A | `src/config/settings.py` | **NEW**: Centralized configuration |
| N/A | `src/utils/file_utils.py` | **NEW**: File utilities |
| N/A | `src/utils/date_utils.py` | **NEW**: Date utilities |

---

## Directory Structure Changes

### Old Structure
```
.
├── Driver.py
├── check_gmail_connection.py
├── download_gmail_ALLpdfs.py
├── regularCheck_gmail_pdfs.py
├── model_router.py
├── file_reader.py
├── llm_extractor.py
├── vendor_parser.py
├── gsheets_writer.py
├── excel_writer.py
├── credentials.json
├── token.json
├── processed_ids.json
├── invoices/
└── Old invoices/
```

### New Structure
```
Invoice-Tracker/
├── main.py
├── requirements.txt
├── README.md
├── MIGRATION_GUIDE.md
│
├── src/
│   ├── auth/
│   │   └── gmail_auth.py
│   ├── config/
│   │   └── settings.py
│   ├── downloaders/
│   │   ├── bulk_downloader.py
│   │   └── monitor_downloader.py
│   ├── processors/
│   │   ├── invoice_processor.py
│   │   ├── file_handler.py
│   │   ├── llm_extractor.py
│   │   └── vendor_parser.py
│   ├── writers/
│   │   └── sheets_writer.py
│   └── utils/
│       ├── file_utils.py
│       └── date_utils.py
│
├── credentials/
│   ├── credentials.json
│   └── token.json
│
└── data/
    ├── invoices/
    ├── old_invoices/
    └── processed_ids.json
```

---

## Key Improvements

### ✅ Single Responsibility Principle
Each file now has one clear purpose:
- **Auth** - Only handles authentication
- **Config** - Only manages configuration
- **Downloaders** - Only download emails
- **Processors** - Only process and extract data
- **Writers** - Only write to output destinations
- **Utils** - Only provide shared utilities

### ✅ No Code Duplication
- Authentication logic unified in `gmail_auth.py`
- File utilities extracted to `file_utils.py`
- Date utilities extracted to `date_utils.py`
- Removed duplicate Excel writer

### ✅ Centralized Configuration
All hardcoded values moved to `src/config/settings.py`:
- Google API scopes
- Spreadsheet ID
- File paths
- Check intervals
- Ollama settings
- Known vendors

### ✅ Organized Data
- Credentials → `credentials/`
- Downloaded invoices → `data/invoices/`
- Historical invoices → `data/old_invoices/`
- Tracking files → `data/`

### ✅ Professional Structure
- Proper Python package structure with `__init__.py`
- Clear module boundaries
- Easy to test
- Scalable for future features
- Standard naming conventions (main.py)

---

## Usage Changes

### Old Way
```bash
python Driver.py
```

### New Way
```bash
python main.py
```

All functionality remains the same - just better organized!

---

## Configuration Changes

### Old Way
Edit hardcoded values in each file:
- `SPREADSHEET_ID` in `gsheets_writer.py`
- `CHECK_INTERVAL` in `regularCheck_gmail_pdfs.py`
- `SCOPES` in multiple files
- etc.

### New Way
Edit one file: `src/config/settings.py`
```python
SPREADSHEET_ID = 'your-id-here'
CHECK_INTERVAL_SECONDS = 60
OLLAMA_MODEL = "gemma2:2b"
# ... all settings in one place
```

---

## Import Changes

### Old Imports (if you had custom scripts)
```python
import model_router
import file_reader
import gsheets_writer
```

### New Imports
```python
from src.processors import invoice_processor
from src.processors import file_handler
from src.writers import sheets_writer
```

---

## Benefits Summary

1. **Readability** - Clear structure, easy to navigate
2. **Maintainability** - Single responsibility, easy to modify
3. **Testability** - Each module can be tested independently
4. **Scalability** - Easy to add new features
5. **Professional** - Industry-standard project structure
6. **Documentation** - Updated README with architecture diagram

---

## Next Steps

1. Review `src/config/settings.py` and update your configuration
2. Ensure `credentials.json` is in `credentials/` folder
3. Run `python main.py` to test
4. Old files can be deleted or archived if everything works

---

## Rollback (if needed)

All old files are still in the root directory. If you need to rollback:
1. Stop using `main.py`
2. Use old `Driver.py` instead
3. Move `credentials/` files back to root
4. Move `data/` files back to root
