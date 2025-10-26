import os
import csv
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

def download_data_to_folder():
    # === LOAD ENVIRONMENT VARIABLES ===
    load_dotenv()

    SERVICE_ACCOUNT_FILE = os.getenv("KEY_PATH")
    SPREADSHEET_ID = os.getenv("SHEET_ID")
    BASE_FOLDER = os.getenv("CSV_DOWNLOAD", "downloads")

    # === AUTHENTICATION ===
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
    gc = gspread.authorize(creds)

    # === CONNECT TO SPREADSHEET ===
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)

    # === CREATE TIMESTAMPED SUBFOLDER ===
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_folder = os.path.join(BASE_FOLDER, timestamp)
    os.makedirs(output_folder, exist_ok=True)

    print(f"📁 Saving CSV files to: {output_folder}")

    # === DOWNLOAD EACH TAB ===
    for worksheet in spreadsheet.worksheets():
        name = worksheet.title
        rows = worksheet.get_all_values()

        # Clean up name for valid filename
        safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else "_" for c in name)
        file_path = os.path.join(output_folder, f"{safe_name}.csv")

        # Write to CSV
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

        print(f"✅ Saved {file_path}")

    print(f"🎉 All sheets downloaded successfully to '{output_folder}'")
