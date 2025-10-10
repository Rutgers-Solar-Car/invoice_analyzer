import os
import base64
import time
import json
from datetime import datetime, timedelta

import check_gmail_connection

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
CHECK_INTERVAL = 20  # seconds
PROCESSED_FILE = 'processed_ids.json'
SAVE_DIR = 'invoices'

def load_processed_ids():
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, 'r') as f:
            try:
                return set(json.load(f))
            except json.JSONDecodeError:
                return set()
    return set()

def save_processed_ids(ids):
    with open(PROCESSED_FILE, 'w') as f:
        json.dump(list(ids), f, indent=2)

# Setting the time based on the current time might cause issues.
# We might want to consider using millis format.
def unix_timestamp(seconds_ago):
    return int((datetime.now() - timedelta(seconds=seconds_ago)).timestamp())

def safe_filename(base_name):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{timestamp}_{base_name}"

def search_new_messages(service, window_seconds=30):
    after_ts = unix_timestamp(window_seconds)

    # This filter needs to be adjusted.
    # Add one more filter to only get emails with different IDs to exclude already processed emails.
    query = f'(Invoice OR Receipt OR Bill) after:{after_ts}'
    print(f"Searching: {query}")

    result = service.users().messages().list(userId='me', q=query).execute()
    return result.get('messages', [])

def save_pdf_attachment(service, msg_id, part, save_dir):
    attach_id = part['body'].get('attachmentId')
    if not attach_id:
        return False

    attachment = service.users().messages().attachments().get(
        userId='me', messageId=msg_id, id=attach_id
    ).execute()

    if 'data' not in attachment:
        return False

    data = base64.urlsafe_b64decode(attachment['data'])
    filename = safe_filename(part.get('filename', 'file.pdf'))
    filepath = os.path.join(save_dir, filename)

    with open(filepath, 'wb') as f:
        f.write(data)

    print(f"PDF saved: {filepath}")
    return True

def save_email_text(msg_data, msg_id, subject, sender, date, save_dir):
    body = ""
    payload = msg_data['payload']

    if payload.get('body', {}).get('data'):
        body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
    else:
        for part in payload.get('parts', []):
            if part.get('mimeType') == 'text/plain' and part['body'].get('data'):
                body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                break

    if not body:
        print(" No readable text found")
        return

    filename = safe_filename(f"{msg_id}.txt")
    filepath = os.path.join(save_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"Subject: {subject}\nFrom: {sender}\nDate: {date}\n")
        f.write("-" * 50 + "\n")
        f.write(body)

    print(f" Text saved: {filepath}")

def process_messages(service, messages, processed_ids):
    os.makedirs(SAVE_DIR, exist_ok=True)
    new_count = 0

    for msg in messages:
        msg_id = msg['id']
        if msg_id in processed_ids:
            print(f"⏭   Skipping already processed {msg_id}")
            continue

        msg_data = service.users().messages().get(userId='me', id=msg_id).execute()
        headers = msg_data['payload'].get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "(No Subject)")
        sender = next((h['value'] for h in headers if h['name'] == 'From'), "(Unknown Sender)")
        date = next((h['value'] for h in headers if h['name'] == 'Date'), "(Unknown Date)")

        print(f"\n    New email: {subject} | From: {sender}")

        parts = msg_data['payload'].get('parts', [])
        pdf_saved = any(
            save_pdf_attachment(service, msg_id, part, SAVE_DIR)
            for part in parts
            if part.get('filename', '').lower().endswith('.pdf')
        )

        save_email_text(msg_data, msg_id, subject, sender, date, SAVE_DIR)

        # if not pdf_saved:
        #     save_email_text(msg_data, msg_id, subject, sender, date, SAVE_DIR)

        processed_ids.add(msg_id)
        new_count += 1

    return new_count

def monitor_invoices():
    print("Gmail Invoice Monitor started")
    print(f"Checking every {CHECK_INTERVAL}s")

    processed_ids = load_processed_ids()

    try:
        while True:
            messages = search_new_messages(service, CHECK_INTERVAL * 2)
            if messages:
                new_count = process_messages(service, messages, processed_ids)
                save_processed_ids(processed_ids)
                if new_count:
                    print(f"{new_count} new invoice(s) processed")
            else:
                print(f"No new invoices")

            print(f"Sleeping {CHECK_INTERVAL}s...\n")
            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print("\nStopped by user")

def monitor_invoices_bycall(service):
    print("Gmail Invoice Monitor started")
    print(f"Checking every {CHECK_INTERVAL}s")

    processed_ids = load_processed_ids()

    try:
        while True:
            messages = search_new_messages(service, CHECK_INTERVAL * 2)
            if messages:
                new_count = process_messages(service, messages, processed_ids)
                save_processed_ids(processed_ids)
                if new_count:
                    print(f"{new_count} new invoice(s) processed")
            else:
                print(f"No new invoices")

            print(f"Sleeping {CHECK_INTERVAL}s...\n")
            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print("\nStopped by user")

if __name__ == "__main__":
    service = check_gmail_connection.get_service()
    monitor_invoices()
