"""Bulk email downloader for historical invoices."""
import os
import base64

from src.auth.gmail_auth import get_gmail_service
from src.config import settings
from src.utils.file_utils import safe_filename


def download_invoices():
    """Search Gmail for historical emails and save PDF attachments or email text."""
    service = get_gmail_service()

    results = service.users().messages().list(
        userId='me',
        q=settings.GMAIL_SEARCH_QUERY
    ).execute()

    messages = results.get('messages', [])
    if not messages:
        print("No emails containing invoice keywords found.")
        return

    os.makedirs(settings.INVOICE_DIR, exist_ok=True)

    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()

        headers = msg_data['payload'].get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "(No Subject)")
        print(f"Checking email: {subject}")

        parts = msg_data['payload'].get('parts', [])
        pdf_found = False

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
                    filename = safe_filename(part['filename'])
                    file_path = os.path.join(settings.INVOICE_DIR, filename)
                    with open(file_path, 'wb') as f:
                        f.write(data)
                    print(f"  Saved PDF: {file_path}")
                    pdf_found = True

        if not pdf_found:
            body = ""
            if msg_data['payload'].get('body', {}).get('data'):
                body = base64.urlsafe_b64decode(
                    msg_data['payload']['body']['data']
                ).decode('utf-8', errors='ignore')
            else:
                for part in parts:
                    if part.get('mimeType') == 'text/plain' and part['body'].get('data'):
                        body = base64.urlsafe_b64decode(
                            part['body']['data']
                        ).decode('utf-8', errors='ignore')
                        break

            if body:
                filename = safe_filename(f"{msg['id']}.txt")
                file_path = os.path.join(settings.INVOICE_DIR, filename)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(body)
                print(f"   Saved email text: {file_path}")


if __name__ == "__main__":
    download_invoices()
