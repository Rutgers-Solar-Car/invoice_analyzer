"""Invoice Tracker - Main Entry Point"""
import time
from datetime import datetime, time as dt_time, timedelta

from src.auth.gmail_auth import get_gmail_service
from src.downloaders import bulk_downloader, monitor_downloader
from src.processors import invoice_processor
from src.writers import sheets_writer
from src.config import settings


def backfill():
    """Download historical invoices and process them."""
    print("\n" + "=" * 60)
    print("STEP 1: Downloading historical invoices")
    print("=" * 60)

    sheets_writer.init_sheet()
    bulk_downloader.download_invoices()

    existing = sheets_writer.get_existing_thread_ids()
    print(f"[INFO] {len(existing)} existing entries in Google Sheets")

    count = 0
    for r in invoice_processor.process_all(existing):
        if sheets_writer.write_invoice_data(r):
            count += 1
            tid = r.get("mail_thread_id", "")
            if tid:
                existing.add(tid)

    print(f"\n[OK] Backfill complete: {count} new invoices")
    return count


def monitor():
    """Start 24/7 monitoring for new invoice emails."""
    print("\n" + "=" * 60)
    print("STEP 2: Starting 24/7 monitor")
    print(f"Checking every {settings.CHECK_INTERVAL_SECONDS}s - Ctrl+C to stop")
    print("=" * 60)

    service = get_gmail_service()
    processed = monitor_downloader.load_processed_ids()
    excel_ids = sheets_writer.get_existing_thread_ids()

    try:
        while True:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n[{ts}] Checking...")

            messages = monitor_downloader.search_new_messages(
                service, settings.CHECK_INTERVAL_SECONDS * 2
            )

            if messages:
                new = monitor_downloader.process_messages(service, messages, processed)
                monitor_downloader.save_processed_ids(processed)

                if new > 0:
                    print(f"[NEW] {new} email(s)")
                    for r in invoice_processor.process_all(excel_ids):
                        if sheets_writer.write_invoice_data(r):
                            tid = r.get("mail_thread_id", "")
                            if tid:
                                excel_ids.add(tid)
            else:
                print("No new invoices")

            time.sleep(settings.CHECK_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\n[STOP] Monitor stopped")


def scheduled_check_with_llm():
    """Check for new emails at midnight and 7 AM daily."""
    print("\n" + "=" * 60)
    print("SCHEDULED LLM MONITOR")
    print("Running at 12:00 AM and 7:00 AM daily - Ctrl+C to stop")
    print("=" * 60)

    service = get_gmail_service()
    processed = monitor_downloader.load_processed_ids()
    excel_ids = sheets_writer.get_existing_thread_ids()

    scheduled_times = [dt_time(0, 0), dt_time(7, 0)]

    # --- Initial catch-up: process any invoices received since the last check ---
    print("\n[INIT] Checking for unprocessed invoices since last run...")
    messages = monitor_downloader.search_new_messages(service, 7 * 24 * 3600)  # look back 7 days

    if messages:
        new = monitor_downloader.process_messages(service, messages, processed)
        monitor_downloader.save_processed_ids(processed)

        if new > 0:
            print(f"[INIT] {new} new email(s) found - Processing with LLM...")
            added_count = 0
            for r in invoice_processor.process_all(excel_ids):
                if sheets_writer.write_invoice_data(r):
                    added_count += 1
                    tid = r.get("mail_thread_id", "")
                    if tid:
                        excel_ids.add(tid)
            print(f"[INIT] Catch-up complete: {added_count} invoices processed and added to sheet")
        else:
            print("[INIT] No unprocessed invoices found")
    else:
        print("[INIT] No new invoices found")

    print("\n[INFO] Initial catch-up done. Now waiting for scheduled times (12 AM & 7 AM)...")

    try:
        while True:
            now = datetime.now()
            current_time = now.time()

            should_run = False
            for scheduled_time in scheduled_times:
                time_diff = abs((current_time.hour * 60 + current_time.minute) -
                                (scheduled_time.hour * 60 + scheduled_time.minute))
                if time_diff < 1:
                    should_run = True
                    break

            if should_run:
                ts = now.strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n[{ts}] Scheduled check starting...")

                messages = monitor_downloader.search_new_messages(service, 24 * 3600)

                if messages:
                    new = monitor_downloader.process_messages(service, messages, processed)
                    monitor_downloader.save_processed_ids(processed)

                    if new > 0:
                        print(f"[NEW] {new} email(s) - Processing with LLM...")
                        added_count = 0
                        for r in invoice_processor.process_all(excel_ids):
                            if sheets_writer.write_invoice_data(r):
                                added_count += 1
                                tid = r.get("mail_thread_id", "")
                                if tid:
                                    excel_ids.add(tid)
                        print(f"[OK] {added_count} invoices processed and added to sheet")
                    else:
                        print("Emails downloaded but already processed")
                else:
                    print("No new invoices found")

                time.sleep(120)
            else:
                next_run = None
                for scheduled_time in scheduled_times:
                    next_datetime = datetime.combine(now.date(), scheduled_time)
                    if next_datetime <= now:
                        next_datetime += timedelta(days=1)
                    if next_run is None or next_datetime < next_run:
                        next_run = next_datetime

                print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] Waiting... Next check: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
                time.sleep(60)

    except KeyboardInterrupt:
        print("\n[STOP] Scheduled monitor stopped")


def main():
    """Main application entry point."""
    sheets_writer.init_sheet()
    print("""
============================================================
           INVOICE TRACKER (Google Sheets Edition)
============================================================
  1. Test Gmail Connection
  2. Download Old Emails
  3. Start Invoice Monitor (download only)
  4. Process Existing Invoices
  5. FULL AUTO (24/7) [*]
  6. Scheduled Check (12 AM & 7 AM) with LLM
============================================================
    """)

    choice = input("Choice (1-6): ").strip()

    if choice == "1":
        get_gmail_service()
    elif choice == "2":
        bulk_downloader.download_invoices()
    elif choice == "3":
        service = get_gmail_service()
        monitor_downloader.monitor_invoices(service)
    elif choice == "4":
        existing = sheets_writer.get_existing_thread_ids()
        count = 0
        for r in invoice_processor.process_all(existing):
            if sheets_writer.write_invoice_data(r):
                count += 1
                tid = r.get("mail_thread_id", "")
                if tid:
                    existing.add(tid)
        print(f"\n[OK] {count} invoices added")
    elif choice == "5":
        backfill()
        monitor()
    elif choice == "6":
        scheduled_check_with_llm()
    else:
        print("[ERROR] Invalid choice")


if __name__ == "__main__":
    main()
