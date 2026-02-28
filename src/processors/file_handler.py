"""File handler for reading and processing invoice files."""
import os
import re
import pdfplumber
import shutil
from collections import defaultdict

from src.config import settings


def read_txt(filepath: str) -> str:
    """Read text file content."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def read_pdf(filepath: str) -> str:
    """Extract text from PDF file."""
    content = ""
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                content += text + "\n"
    return content


def read_file(filepath: str) -> str:
    """Read file content, automatically detecting file type."""
    if filepath.lower().endswith(".pdf"):
        return read_pdf(filepath)
    elif filepath.lower().endswith(".txt"):
        return read_txt(filepath)
    return ""


def parse_email_headers(txt_filepath: str) -> dict:
    """Parse email metadata from text file headers."""
    metadata = {
        "sender_email": "",
        "thread_id": "",
        "received_time": "",
        "subject": ""
    }

    lines = read_txt(txt_filepath).split('\n')
    for line in lines:
        if line.startswith("Sender Email:"):
            metadata["sender_email"] = line.split(":", 1)[1].strip()
        elif line.startswith("Gmail Thread ID:"):
            metadata["thread_id"] = line.split(":", 1)[1].strip()
        elif line.startswith("Date:"):
            metadata["received_time"] = line.split(":", 1)[1].strip()
        elif line.startswith("Subject:"):
            metadata["subject"] = line.split(":", 1)[1].strip()
        elif line.startswith("-" * 10):
            break

    return metadata


def get_invoice_files(invoice_dir: str = None) -> dict:
    """Group invoice files by their base timestamp.

    Args:
        invoice_dir: Directory to scan. Defaults to settings.INVOICE_DIR.
    """
    invoice_dir = invoice_dir or settings.INVOICE_DIR

    if not os.path.exists(invoice_dir):
        return {}

    grouped = defaultdict(list)
    base_pattern = re.compile(r'(.+_\d{13})')

    for filename in os.listdir(invoice_dir):
        if filename.lower().endswith((".pdf", ".txt")):
            filepath = os.path.join(invoice_dir, filename)

            match = base_pattern.match(filename)
            if match:
                base = match.group(1)
            else:
                base = filename

            grouped[base].append(filepath)

    return grouped


def combine_content(file_paths: list) -> str:
    """Combine content from multiple files."""
    content = ""
    for fp in file_paths:
        text = read_file(fp)
        if text:
            content += f"\n--- {os.path.basename(fp)} ---\n{text}\n"
    return content


def move_processed_files(file_paths: list, target_dir: str):
    """Move processed files to an archive directory."""
    os.makedirs(target_dir, exist_ok=True)

    for fp in file_paths:
        try:
            filename = os.path.basename(fp)
            target_path = os.path.join(target_dir, filename)

            # Handle potential filename collisions
            if os.path.exists(target_path):
                base, ext = os.path.splitext(filename)
                target_path = os.path.join(target_dir, f"{base}_duplicate{ext}")

            shutil.move(fp, target_path)
        except Exception as e:
            print(f"[ERROR] Failed to move {fp}: {e}")
