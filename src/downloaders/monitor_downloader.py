"""Real-time invoice email monitor."""
import os
import base64
import time
import json
import mimetypes
from email.utils import parseaddr, getaddresses

from src.auth.gmail_auth import get_gmail_service
from src.config import settings
from src.utils.file_utils import sanitize_filename
from src.utils.date_utils import unix_timestamp


def load_processed_ids() -> set:
    """Load set of already processed message IDs."""
    if os.path.exists(settings.PROCESSED_IDS_FILE):
        with open(settings.PROCESSED_IDS_FILE, 'r') as f:
            try:
                return set(json.load(f))
            except json.JSONDecodeError:
                return set()
    return set()


def save_processed_ids(ids: set):
    """Save set of processed message IDs."""
    os.makedirs(os.path.dirname(settings.PROCESSED_IDS_FILE), exist_ok=True)
    with open(settings.PROCESSED_IDS_FILE, 'w', encoding='utf-8') as f:
        f.write(json.dumps(list(ids), indent=2))


def search_new_messages(service, window_seconds: int = 30) -> list:
    """Search for new invoice emails within a time window."""
    after_ts = unix_timestamp(window_seconds)
    query = f'({settings.GMAIL_SEARCH_QUERY}) after:{after_ts}'
    print(f"Searching: {query}")

    result = service.users().messages().list(userId='me', q=query).execute()
    return result.get('messages', [])


def _save_bytes_to_file(data_bytes: bytes, filepath: str):
    with open(filepath, 'wb') as f:
        f.write(data_bytes)
    print(f"Saved: {filepath}")


def save_attachment(service, msg_id: str, part: dict, save_dir: str,
                    basename: str, attach_index: int = None) -> bool:
    """Save email attachment to file."""
    filename = part.get('filename') or ''
    mimeType = part.get('mimeType', '')

    attach_id = part.get('body', {}).get('attachmentId')
    data_b64 = None

    if attach_id:
        try:
            attachment = service.users().messages().attachments().get(
                userId='me', messageId=msg_id, id=attach_id
            ).execute()
            data_b64 = attachment.get('data')
        except Exception as e:
            print(f"Failed to fetch attachment {attach_id} for {msg_id}: {e}")
            return False
    else:
        data_b64 = part.get('body', {}).get('data')

    if not data_b64:
        return False

    try:
        data = base64.urlsafe_b64decode(data_b64)
    except Exception:
        try:
            data = base64.b64decode(data_b64)
        except Exception as e:
            print(f"Failed to decode attachment data for {msg_id}: {e}")
            return False

    if filename:
        filename_clean = sanitize_filename(filename)
        out_name = f"{basename}_{filename_clean}"
    else:
        ext = mimetypes.guess_extension(mimeType) or ''
        idx = f"_{attach_index}" if attach_index is not None else ''
        out_name = f"{basename}_attachment{idx}{ext}"

    filepath = os.path.join(save_dir, out_name)

    if not os.path.splitext(filepath)[1] and mimeType:
        ext = mimetypes.guess_extension(mimeType) or ''
        if ext:
            filepath = filepath + ext

    _save_bytes_to_file(data, filepath)
    return True


def save_email_text(msg_data: dict, msg_id: str, basename: str,
                    subject: str, sender: str, date: str, save_dir: str,
                    user_email: str = None):
    """Save email text with headers to file."""
    payload = msg_data.get('payload', {})
    body = ''

    headers_list = msg_data.get('payload', {}).get('headers', [])
    headers_map = {h.get('name', '').lower(): h.get('value', '') for h in headers_list}

    if payload.get('body', {}).get('data'):
        try:
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
        except Exception:
            body = ''
    else:
        for part in payload.get('parts', []):
            if part.get('mimeType') == 'text/plain' and part.get('body', {}).get('data'):
                try:
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                except Exception:
                    body = ''
                break

    from_raw = headers_map.get('from', sender)
    sender_name, sender_email = parseaddr(from_raw)

    to_raw = headers_map.get('to', '')
    cc_raw = headers_map.get('cc', '')
    to_list = [f"{name} <{addr}>" if name else addr for name, addr in getaddresses([to_raw])]
    cc_list = [f"{name} <{addr}>" if name else addr for name, addr in getaddresses([cc_raw])]

    thread_id = msg_data.get('threadId', msg_id)

    header_fields = [
        ("Subject", subject),
        ("From", from_raw),
        ("Sender Name", sender_name),
        ("Sender Email", sender_email),
        ("Reply-To", headers_map.get('reply-to', '')),
        ("To", "; ".join(to_list) if to_list else ''),
        ("Cc", "; ".join(cc_list) if cc_list else ''),
        ("Message-ID", headers_map.get('message-id', '')),
        ("Date", headers_map.get('date', date)),
        ("Gmail Thread ID", thread_id),
    ]

    filename = f"{basename}.txt"
    filepath = os.path.join(save_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        for k, v in header_fields:
            f.write(f"{k}: {v}\n")
        f.write("-" * 50 + "\n")
        if body:
            f.write(body)
        else:
            f.write("[No readable body found]\n")

    print(f"Email text saved: {filepath}")


def _iter_parts(parts: list):
    for part in parts or []:
        yield part
        if part.get('parts'):
            for sub in _iter_parts(part.get('parts')):
                yield sub


def process_messages(service, messages: list, processed_ids: set) -> int:
    """Process and download new messages."""
    os.makedirs(settings.INVOICE_DIR, exist_ok=True)
    new_count = 0

    try:
        profile = service.users().getProfile(userId='me').execute()
        user_email = profile.get('emailAddress')
    except Exception:
        user_email = None

    for msg in messages:
        msg_id = msg['id']

        msg_data = service.users().messages().get(userId='me', id=msg_id, format='full').execute()

        headers = msg_data.get('payload', {}).get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "(No Subject)")
        sender = next((h['value'] for h in headers if h['name'] == 'From'), "(Unknown Sender)")
        date = next((h['value'] for h in headers if h['name'] == 'Date'), "(Unknown Date)")
        message_id_header = next((h['value'] for h in headers if h['name'].lower() == 'message-id'), None)

        unique_id = message_id_header if message_id_header else msg_id

        if unique_id in processed_ids:
            print(f"⏭   Skipping already processed {unique_id}")
            continue

        internal_date_ms = msg_data.get('internalDate') or str(int(time.time() * 1000))

        safe_unique_id = sanitize_filename(unique_id.strip('<>'))
        basename = f"{safe_unique_id}_{internal_date_ms}"

        print(f"\n    New email: {subject} | From: {sender} | basename: {basename}")

        save_email_text(msg_data, msg_id, basename, subject, sender, date, settings.INVOICE_DIR, user_email)

        parts = msg_data.get('payload', {}).get('parts', [])
        attach_count = 0
        for i, part in enumerate(_iter_parts(parts)):
            filename = part.get('filename', '')
            mime_type = part.get('mimeType', '')
            has_attach_id = bool(part.get('body', {}).get('attachmentId'))
            has_inline_data = bool(part.get('body', {}).get('data'))

            if mime_type in ('text/plain', 'text/html'):
                continue

            if filename or has_attach_id or has_inline_data:
                saved = save_attachment(service, msg_id, part, settings.INVOICE_DIR, basename, attach_index=attach_count)
                if saved:
                    attach_count += 1

        processed_ids.add(unique_id)
        new_count += 1

    return new_count


def monitor_invoices(service, check_interval: int = None):
    """Continuously monitor Gmail for new invoice emails."""
    check_interval = check_interval or settings.MONITOR_CHECK_INTERVAL
    print("Gmail Invoice Monitor started")
    print(f"Checking every {check_interval}s")

    processed_ids = load_processed_ids()

    try:
        while True:
            messages = search_new_messages(service, check_interval * 2)
            if messages:
                new_count = process_messages(service, messages, processed_ids)
                save_processed_ids(processed_ids)
                if new_count:
                    print(f"{new_count} new invoice(s) processed")
            else:
                print(f"No new invoices")

            print(f"Sleeping {check_interval}s...\n")
            time.sleep(check_interval)

    except KeyboardInterrupt:
        print("\nStopped by user")


if __name__ == "__main__":
    service = get_gmail_service()
    monitor_invoices(service)
