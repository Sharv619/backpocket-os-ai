#!/usr/bin/env python3
import os
from dotenv import load_dotenv

load_dotenv('/home/lade/Hackathons/.git/backpocket-mvp/.env', override=True)

spreadsheet_id = os.getenv("SPREADSHEET_ID")
print(f"📊 Spreadsheet ID: {spreadsheet_id}")

if spreadsheet_id and spreadsheet_id != "your_google_sheet_id_here":
    print("✓ Spreadsheet configured")

    try:
        from services.google_sheets import test_sheets_connection
        result = test_sheets_connection()
        print(f"\n✅ Connection Test: {result}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
else:
    print("✗ Spreadsheet NOT configured (placeholder)")
    print("\nTo use Google Sheets:")
    print("1. Create a Google Sheet")
    print("2. Share it with your service account")
    print("3. Add the Sheet ID to .env as SPREADSHEET_ID")
