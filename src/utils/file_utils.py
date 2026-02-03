"""File utility functions."""
import re
import time


def sanitize_filename(name: str) -> str:
    """Remove unsafe characters from filename."""
    name = re.sub(r'[\\/:*?"<>|\n\r\t]+', '_', name)
    name = name.strip()
    if not name:
        return 'attachment'
    return name


def safe_filename(base_name: str) -> str:
    """Generate a unique filename using current epoch time in milliseconds."""
    millis = int(time.time() * 1000)
    return f"{millis}_{base_name}"
