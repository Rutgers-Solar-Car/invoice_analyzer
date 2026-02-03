"""Shared pytest fixtures for Invoice Tracker tests."""
import os
import sys
import pytest
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def temp_dir():
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp)


@pytest.fixture
def sample_invoice_data():
    return {
        "mail_thread_id": "thread_123",
        "company_name": "Test Company",
        "purchase_date": "2024-01-15",
        "mail_received_time": "Mon, 15 Jan 2024 10:30:00 -0500",
        "purchase_receiver": "John Doe",
        "total_price": "150.00",
        "other_expenses": "10.00",
        "items": [
            {"item_name": "Widget A", "quantity": 2, "price": 50.00},
            {"item_name": "Widget B", "quantity": 1, "price": 50.00}
        ]
    }


@pytest.fixture
def sample_email_text():
    return """Subject: Your Order Confirmation
From: orders@example.com
Sender Name: Example Orders
Sender Email: orders@example.com
Reply-To: support@example.com
To: user@test.com
Cc: 
Message-ID: <abc123@example.com>
Date: Mon, 15 Jan 2024 10:30:00 -0500
Gmail Thread ID: thread_abc123
--------------------------------------------------
Thank you for your order!

Order #12345
Total: $150.00
"""


@pytest.fixture
def sample_home_depot_text():
    return """
    The Home Depot
    Order #WD12345678
    
    Order Date: 01/15/2024
    
    Items:
    - 2x4 Lumber x 10 @ $5.99
    - Screws Box x 2 @ $8.99
    
    Subtotal: $77.88
    Tax: $6.23
    Total: $84.11
    """


@pytest.fixture
def sample_mcmaster_text():
    return """
    McMaster-Carr
    
    Order Date         01/15/24
    McMaster-Carr Number    1234567890
    Ordered By         John Smith  123
    
    1  91251A540  Hex Nut Pack            10  Each  5     2.50   25.00
    2  92196A830  Machine Screw           5   Each  10    1.20   12.00
    
    Shipping   5.00
    Total   42.00
    """


@pytest.fixture
def mock_gmail_message():
    return {
        'id': 'msg_123',
        'threadId': 'thread_123',
        'internalDate': '1705329000000',
        'payload': {
            'headers': [
                {'name': 'Subject', 'value': 'Invoice #12345'},
                {'name': 'From', 'value': 'orders@vendor.com'},
                {'name': 'Date', 'value': 'Mon, 15 Jan 2024 10:30:00 -0500'},
                {'name': 'Message-ID', 'value': '<msg123@vendor.com>'}
            ],
            'body': {'data': ''},
            'parts': []
        }
    }
