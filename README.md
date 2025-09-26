# 📩 Gmail Invoice Manager – Rutgers Solar Car

A Python app that connects to Gmail and automatically:

* 📥 Watches for **invoice/receipt/billing emails**
* 📄 Downloads **PDF attachments** (if present)
* 📝 Saves email text if no PDF is attached
* ⏱️ Checks Gmail at regular intervals (default: **10 seconds for testing**)
* 💾 Stores files in an `invoices/` folder

---

## 🚀 Features

* Gmail API + OAuth 2.0 authentication
* **Case-insensitive keyword detection**
* Supported keywords:

  ```
  invoice, receipt, bill, billing, payment, statement,
  order confirmation, purchase, transaction, remittance,
  sales order, quote, estimate, delivery note, packing slip,
  charge, fee, account summary, subscription, renewal,
  tax invoice, amount due, proof of payment, customer statement
  ```
* Scripts included for:

  * ✅ Gmail connection test
  * 📥 Bulk PDF download
  * 🔄 Regular invoice polling

---

## 📦 Requirements

* 🐍 Python **3.10+**
* 📧 Gmail account (Rutgers Gmail supported)
* ☁️ Google Cloud project with Gmail API enabled
* 💻 IntelliJ IDEA / VS Code / any Python IDE

---

## 🔑 Google Cloud Setup (One-Time)

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. **Create a new project** → name it `invoice-watcher`.
3. **Enable Gmail API**:

   * Menu → **APIs & Services → Enable APIs and Services**
   * Search “Gmail API” → Enable
4. **OAuth Consent Screen**:

   * Menu → **APIs & Services → OAuth consent screen**
   * User Type: **External**
   * App name: `Invoice Watcher`
   * Developer contact: your Gmail
   * Save
5. **Create OAuth Credentials**:

   * Menu → **APIs & Services → Credentials**
   * Create Credentials → OAuth Client ID
   * Application type: **Desktop App**
   * Download JSON → rename it to **`credentials.json`**
   * Place `credentials.json` in your project folder

---

## 🛠 Local Setup

1. Clone this repo or download the project folder.

2. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate      # Mac/Linux
   venv\Scripts\activate         # Windows
   ```

3. Install dependencies:

   ```bash
   pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
   ```

(Optional PDF parsing libraries):

```bash
pip install pdfplumber pytesseract pdf2image openpyxl pandas
```

---

## 🔑 First Authentication

1. Run the Gmail connection test:

   ```bash
   python check_gmail_connection.py
   ```

2. A browser will open → log in with Gmail → click **Allow**.

3. A `token.json` file will be created in your project folder.

   * Stores your login so you don’t need to reauthenticate.

---

## ▶ Usage

### 🔍 1. Test Gmail Connection

```bash
python check_gmail_connection.py
```

---

### 📥 2. Download All PDFs

```bash
python download_gmail_ALLpdfs.py
```

---

### 🔄 3. Regular Invoice Checking

```bash
python regularCheck_gmail_pdfs.py
```

* Runs every **10 seconds** by default
* Downloads PDFs or saves text for invoice-related emails
* Prints **“No invoice receipt.”** if nothing is found

---

## 🧪 Testing

1. Send yourself an email with subject:

   ```
   Invoice Test – Rutgers Solar Car
   ```

   Attach a PDF.
2. Run:

   ```bash
   python regularCheck_gmail_pdfs.py
   ```
3. Within 10 seconds:

   * ✅ PDF saved in `invoices/`
   * 📝 If no PDF → `.txt` file with email text

---

## ⚙️ Automation (Optional)

* **Windows**: Use Task Scheduler → run `regularCheck_gmail_pdfs.py` at login
* **Mac/Linux**: Use `cron` or `systemd` to keep it running

---

## 📂 Repository Structure

```
.
├── README.md                  # Project documentation
├── check_gmail_connection.py  # Test Gmail API connection
├── download_gmail_ALLpdfs.py  # Bulk PDF downloader
├── regularCheck_gmail_pdfs.py # Poll Gmail for new invoices
├── last_check_ms.txt          # Tracks last poll time
├── processed_messages.json    # Stores processed message IDs
├── credentials.json           # OAuth credentials (you add this)
├── token.json                 # Saved Gmail session (auto-created)
└── invoices/                  # Downloaded PDFs and text files
```

---

## 📌 Notes

* 🔑 `credentials.json` = your Google Cloud keys
* 🔐 `token.json` = your saved Gmail login session
* ⏱ Default interval = **10 seconds** (for testing) → change in code for production (`600` for 10 minutes)

Do you want me to also add a **Quick Start section at the very top** (just 5 steps) for advanced users who don’t need the long explanation?
