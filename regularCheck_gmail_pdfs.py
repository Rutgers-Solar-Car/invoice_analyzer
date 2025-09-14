from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
import os
import base64
import time
from datetime import datetime, timedelta
import json

"""This script continuously monitors Gmail for new invoices/receipts and downloads them."""

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
CHECK_INTERVAL = 20  # seconds
PROCESSED_FILE = 'processed_messages.json'

def get_service():
    """Authenticate and return Gmail API service."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def load_processed_messages():
    """Load list of already processed message IDs."""
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_processed_messages(processed_ids):
    """Save list of processed message IDs."""
    with open(PROCESSED_FILE, 'w') as f:
        json.dump(list(processed_ids), f)

def get_unix_timestamp(seconds_ago):
    """Get Unix timestamp for X seconds ago."""
    past_time = datetime.now() - timedelta(seconds=seconds_ago)
    return int(past_time.timestamp())

def download_new_invoices(service, time_window_seconds=20):
    """Search Gmail for new emails containing invoice keywords within the time window."""

    # Load already processed messages
    processed_ids = load_processed_messages()

    # Calculate timestamp for the time window
    after_timestamp = get_unix_timestamp(time_window_seconds)

    # Gmail search query with time filter
    # Note: Gmail's 'after:' uses Unix timestamp
    query = f'(Invoice OR Receipt OR Bill) after:{after_timestamp}'

    try:
        results = service.users().messages().list(
            userId='me',
            q=query
        ).execute()
    except Exception as e:
        print(f"❌ Error searching emails: {e}")
        return

    messages = results.get('messages', [])

    if not messages:
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - No new invoices in the last {time_window_seconds} seconds")
        return

    # Create directory if it doesn't exist
    os.makedirs('invoices', exist_ok=True)

    new_count = 0

    for msg in messages:
        # Skip if already processed
        if msg['id'] in processed_ids:
            continue

        try:
            msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()

            # Get email metadata
            headers = msg_data['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "(No Subject)")
            sender = next((h['value'] for h in headers if h['name'] == 'From'), "(Unknown Sender)")
            date = next((h['value'] for h in headers if h['name'] == 'Date'), "(Unknown Date)")

            print(f"\n📩 New email found!")
            print(f"   Subject: {subject}")
            print(f"   From: {sender}")
            print(f"   Date: {date}")

            parts = msg_data['payload'].get('parts', [])
            pdf_found = False

            # Check for PDF attachments
            for part in parts:
                if part.get('filename') and part['filename'].endswith('.pdf'):
                    attach_id = part['body'].get('attachmentId')
                    if attach_id:
                        attachment = service.users().messages().attachments().get(
                            userId='me',
                            messageId=msg['id'],
                            id=attach_id
                        ).execute()
                        data = base64.urlsafe_b64decode(attachment['data'])

                        # Create filename with timestamp to avoid overwrites
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        safe_filename = f"{timestamp}_{part['filename']}"
                        file_path = os.path.join('invoices', safe_filename)

                        with open(file_path, 'wb') as f:
                            f.write(data)
                        print(f"   ✅ Saved PDF: {file_path}")
                        pdf_found = True

            # If no PDF, save email text
            if not pdf_found:
                body = ""
                if msg_data['payload'].get('body', {}).get('data'):
                    body = base64.urlsafe_b64decode(msg_data['payload']['body']['data']).decode('utf-8', errors='ignore')
                else:
                    for part in parts:
                        if part.get('mimeType') == 'text/plain' and part['body'].get('data'):
                            body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                            break

                if body:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    file_path = os.path.join('invoices', f"{timestamp}_{msg['id']}.txt")
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(f"Subject: {subject}\n")
                        f.write(f"From: {sender}\n")
                        f.write(f"Date: {date}\n")
                        f.write("-" * 50 + "\n")
                        f.write(body)
                    print(f"   📝 Saved email text: {file_path}")

            # Mark as processed
            processed_ids.add(msg['id'])
            new_count += 1

        except Exception as e:
            print(f"   ❌ Error processing message {msg['id']}: {e}")

    # Save processed IDs
    save_processed_messages(processed_ids)

    if new_count > 0:
        print(f"\n🎉 Processed {new_count} new invoice(s)")

def monitor_invoices():
    """Continuously monitor for new invoices."""
    print("🚀 Starting Gmail Invoice Monitor")
    print(f"⏱️  Checking every {CHECK_INTERVAL} seconds for new invoices...")
    print("-" * 50)

    service = get_service()

    try:
        while True:
            download_new_invoices(service, time_window_seconds=CHECK_INTERVAL * 2)  # Check slightly wider window to avoid missing emails
            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print("\n\n👋 Monitoring stopped by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    monitor_invoices()