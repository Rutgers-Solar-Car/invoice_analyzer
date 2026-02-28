"""Invoice processing orchestrator."""
import os

from src.config import settings
from src.processors import file_handler, vendor_parser, llm_extractor


def detect_vendor(sender_email: str) -> str:
    """Detect vendor from sender email address."""
    if not sender_email:
        return None

    sender = sender_email.lower()
    for domain, vendor in settings.KNOWN_VENDORS.items():
        if domain in sender:
            return vendor
    return None


def route(sender_email: str, content: str) -> dict:
    """Route invoice content to appropriate parser."""
    vendor = detect_vendor(sender_email)

    if vendor:
        print(f"[MODEL A] {vendor}")
        raw = vendor_parser.parse(content, vendor)
        return vendor_parser.normalize_to_schema(raw)
    else:
        print(f"[MODEL B] LLM")
        return llm_extractor.extract(content)


def process_group(file_paths: list) -> dict:
    """Process a group of files belonging to the same invoice."""
    txt_file = next((f for f in file_paths if f.lower().endswith(".txt")), None)
    content = file_handler.combine_content(file_paths)

    if not content.strip():
        print("[WARN] No content")
        return None

    if txt_file:
        metadata = file_handler.parse_email_headers(txt_file)
        sender_email = metadata["sender_email"]
        thread_id = metadata["thread_id"]
        received_time = metadata["received_time"]
    else:
        print("[WARN] No email context, using content-based detection")
        sender_email = ""
        thread_id = ""
        received_time = ""

        for fp in file_paths:
            fname = os.path.basename(fp).lower()
            if "mcmaster" in fname:
                sender_email = "order@mcmaster.com"
            elif "homedepot" in fname or "home depot" in fname:
                sender_email = "orders@homedepot.com"

    result = route(sender_email, content)

    if result:
        result["mail_thread_id"] = thread_id or result.get("mail_thread_id", "")
        result["mail_received_time"] = received_time or result.get("mail_received_time", "")
        if not result.get("company_name") and sender_email and "@" in sender_email:
            result["company_name"] = sender_email.split("@")[1].split(".")[0].title()

    return result


def process_all(skip_ids: set = None, invoice_dir: str = None):
    """Process all invoice files in a directory.

    Yields results one at a time so callers can save each invoice
    immediately before the next one is processed.

    Args:
        skip_ids: Thread IDs to skip.
        invoice_dir: Directory containing invoice files. Defaults to settings.INVOICE_DIR.
    """
    skip_ids = skip_ids or set()
    grouped = file_handler.get_invoice_files(invoice_dir=invoice_dir)

    for base, paths in grouped.items():
        print(f"\nProcessing: {base}")
        result = process_group(paths)

        if result:
            tid = result.get("mail_thread_id", "")
            if tid and tid in skip_ids:
                print(f"[SKIP] Already processed: {tid}")
                continue
            print(f"[OK] {result.get('company_name', 'Unknown')} - ${result.get('total_price', 'N/A')}")
            yield result
