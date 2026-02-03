"""Gmail authentication module."""
import os
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from src.config import settings


def get_gmail_service():
    """Authenticate and return Gmail API service."""
    creds = None

    if os.path.exists(settings.TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(settings.TOKEN_FILE, settings.SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(settings.CREDENTIALS_FILE):
                raise FileNotFoundError(f"Missing {settings.CREDENTIALS_FILE}")
            flow = InstalledAppFlow.from_client_secrets_file(settings.CREDENTIALS_FILE, settings.SCOPES)
            creds = flow.run_local_server(port=0)

        os.makedirs(os.path.dirname(settings.TOKEN_FILE), exist_ok=True)
        with open(settings.TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)
    user = service.users().getProfile(userId='me').execute()
    print(f"✅ Connected to Gmail: {user['emailAddress']}")
    return service


def get_sheets_service():
    """Authenticate and return Google Sheets API service."""
    creds = None

    if os.path.exists(settings.TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(settings.TOKEN_FILE, settings.SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(settings.CREDENTIALS_FILE):
                raise FileNotFoundError(f"Missing {settings.CREDENTIALS_FILE}")
            flow = InstalledAppFlow.from_client_secrets_file(settings.CREDENTIALS_FILE, settings.SCOPES)
            creds = flow.run_local_server(port=0)

        os.makedirs(os.path.dirname(settings.TOKEN_FILE), exist_ok=True)
        with open(settings.TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    return build('sheets', 'v4', credentials=creds)


if __name__ == "__main__":
    try:
        service = get_gmail_service()
        profile = service.users().getProfile(userId='me').execute()
        print(f"✅ Gmail connection successful: {profile['emailAddress']}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
