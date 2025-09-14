from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
import os, base64

"""Only and only run this script if you need to download older invoices from Gmail."""
"""This script searches for emails containing the keyword "Invoice" and saves any PDF attachments or the email text itself if no PDF is found."""

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

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

def download_invoices():
    """Search Gmail for emails containing 'Invoice' and save PDF or email text."""
    service = get_service()

    # Search emails with the keyword "Invoice"
    results = service.users().messages().list(
        userId='me',
        q='Invoice OR Receipt OR Bill'   # Gmail search query: subject/body must contain "Invoice"
    ).execute()

    messages = results.get('messages', [])
    if not messages:
        print("⚠️ No emails containing 'Invoice' found.")
        return

    os.makedirs('Old invoices', exist_ok=True)

    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()

        # Get subject line for logging
        headers = msg_data['payload'].get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "(No Subject)")
        print(f"📩 Checking email: {subject}")

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
                    file_path = os.path.join('invoices', part['filename'])
                    with open(file_path, 'wb') as f:
                        f.write(data)
                    print(f"✅ Saved PDF: {file_path}")
                    pdf_found = True

        # If no PDF, save email text itself
        if not pdf_found:
            # Try to get plain text body
            body = ""
            if msg_data['payload'].get('body', {}).get('data'):
                body = base64.urlsafe_b64decode(msg_data['payload']['body']['data']).decode('utf-8')
            else:
                for part in parts:
                    if part.get('mimeType') == 'text/plain' and part['body'].get('data'):
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break

            if body:
                file_path = os.path.join('invoices', f"{msg['id']}.txt")
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(body)
                print(f"📝 Saved email text: {file_path}")

if __name__ == "__main__":
    download_invoices()
