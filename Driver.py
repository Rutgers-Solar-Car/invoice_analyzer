import check_gmail_connection
import download_gmail_ALLpdfs
import regularCheck_gmail_pdfs

def main():
    print("Select an action:")
    print("1. Test Gmail Connection")
    print("2. Download Old Emails (PDFs)")
    print("3. Start Regular Invoice Monitor")
    choice = input("Enter 1, 2, or 3: ").strip()

    if choice == "1":
        check_gmail_connection.get_service()
    elif choice == "2":
        download_gmail_ALLpdfs.download_invoices()
    elif choice == "3":
        service = check_gmail_connection.get_service()
        regularCheck_gmail_pdfs.monitor_invoices_bycall(service)
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()