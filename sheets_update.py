import gspread
from google.oauth2.service_account import Credentials
import os
from dotenv import load_dotenv

def update_sheets(messages):
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]

    creds = Credentials.from_service_account_file("sheets-api-cred.json", scopes=scopes)
    client = gspread.authorize(creds)

    # Load .env file
    load_dotenv()
    sheet_id = os.getenv("SHEET_ID")

    if not sheet_id:
        raise ValueError("SHEET_ID not found in environment variables!")

    print(f"Loaded Sheet ID: {sheet_id}")

    sheet = client.open_by_key(sheet_id)
    worksheet = sheet.sheet1

    all_records = worksheet.get_all_records()
    print("Current sheet records:")
    print(all_records)
    
    # Create lookup dictionary from the already processed messages
    message_lookup = {}
    for message in messages:
        message_lookup[message['sender']] = message['date']
    
    print(f"\nProcessing {len(message_lookup)} unique phone numbers from messages")
    
    # Track updates
    updates = []
    updated_count = 0
    
    # Process each row in the spreadsheet
    for i, record in enumerate(all_records, start=2):  # start=2 because row 1 is headers
        sheet_phone = record.get('phone number', '')
        
        if sheet_phone:  # Only process rows with phone numbers
            # Clean the sheet phone number by removing spaces and dashes
            cleaned_sheet_phone = sheet_phone.replace(' ', '').replace('-', '')
            
            # Check if this phone number exists in our filtered messages
            if cleaned_sheet_phone in message_lookup:
                new_date = message_lookup[cleaned_sheet_phone]
                current_date = record.get('date', '')
                
                # Update if the date is different
                if current_date != new_date:
                    # Prepare the update (column E is typically the 5th column for date)
                    updates.append({
                        'range': f'E{i}',
                        'values': [[new_date]]
                    })
                    
                    print(f"Row {i}: Updating {cleaned_sheet_phone} date from '{current_date}' to '{new_date}'")
                    updated_count += 1
                else:
                    print(f"Row {i}: {cleaned_sheet_phone} already has current date '{current_date}'")
    
    # Perform batch update if there are changes
    if updates:
        try:
            # Use gspread's batch_update with proper value input option
            worksheet.batch_update(updates, value_input_option='USER_ENTERED')
            print(f"\n✅ Successfully updated {updated_count} rows!")
            
        except Exception as e:
            print(f"❌ Error updating spreadsheet: {e}")
            return updated_count, 0
    else:
        print("📋 No updates needed - all dates are already current")
    
    return updated_count