"""LLM-based invoice data extraction."""
import json
import requests

from src.config import settings


def _strip_schema_placeholders(value):
    """Normalize LLM output by stripping schema placeholder strings."""
    if isinstance(value, dict):
        return {k: _strip_schema_placeholders(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_strip_schema_placeholders(v) for v in value]
    if isinstance(value, str):
        placeholder = value.strip().lower()
        if placeholder in ("string", "integer", "float", "yyyy-mm-dd"):
            return ""
    return value


def build_prompt(email_body: str, attachment_texts: list = None) -> str:
    """Build a structured prompt with email body and attachment texts."""
    parts = [
        "Extract invoice data from the following email and its attachments.",
        f"Return ONLY valid JSON matching this schema:\n{json.dumps(settings.INVOICE_SCHEMA, indent=2)}",
        "",
    ]

    parts.append("=== EMAIL BODY ===")
    parts.append(email_body.strip() if email_body else "[No email body]")

    if attachment_texts:
        for i, text in enumerate(attachment_texts, 1):
            parts.append(f"\n=== ATTACHMENT {i} ===")
            parts.append(text.strip() if text else "[Empty attachment]")

    return "\n".join(parts)


def extract(email_body: str, attachment_texts: list = None) -> dict:
    """Extract invoice data from structured email content using LLM."""
    if not email_body and not attachment_texts:
        return None

    prompt = build_prompt(email_body, attachment_texts)

    payload = {
        "model": settings.OLLAMA_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "format": "json",
        "stream": False,
        "options": {"temperature": 0.1}
    }

    print("[LLM] Sending to Ollama...")

    try:
        r = requests.post(settings.OLLAMA_URL, json=payload, timeout=settings.OLLAMA_TIMEOUT)
        r.raise_for_status()
        raw = json.loads(r.json()['message']['content'])
        return _strip_schema_placeholders(raw)
    except Exception as e:
        print(f"[LLM] Error: {e}")
        return None
