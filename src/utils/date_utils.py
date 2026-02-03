"""Date utility functions."""
from datetime import datetime, timedelta


def normalize_date(date_str: str) -> str:
    """Convert various date formats to YYYY-MM-DD."""
    if not date_str:
        return ""

    formats = ["%m/%d/%y", "%Y-%m-%d", "%m/%d/%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return date_str


def unix_timestamp(seconds_ago: int) -> int:
    """Calculate Unix timestamp for a time in the past."""
    return int((datetime.now() - timedelta(seconds=seconds_ago)).timestamp())
