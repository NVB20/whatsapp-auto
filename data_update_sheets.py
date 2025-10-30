import gspread
from google.oauth2.service_account import Credentials
import os
from dotenv import load_dotenv
import re

def update_sheets_data(message_data):
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
    datasheet = sheet.worksheet("data")

    # Fetch all data at once to avoid API rate limits
    all_data = datasheet.get_all_values()
    headers = all_data[0] if all_data else []
    all_records = all_data[1:] if len(all_data) > 1 else []

    # Helper function to clean any tags and quotes from strings
    def clean_value(value):
        """Remove any HTML/XML tags and quotes from strings"""
        if not value:
            return value
        # Convert to string
        cleaned = str(value)
        # Remove any tags like <tag>content</tag> or <tag>
        cleaned = re.sub(r'<[^>]+>', '', cleaned)
        # Strip whitespace
        cleaned = cleaned.strip()
        # Remove leading/trailing quotes (single or double)
        cleaned = cleaned.strip("'\"")
        return cleaned

    # Create lookup dictionaries from the messages with cleaned values
    practice_lookup = {}
    for message in message_data['practice_updates']:
        practice_lookup[message['sender']] = {
            'date': clean_value(message['date']),
            'datetime': clean_value(message['datetime'])
        }
    
    message_lookup = {}
    for message in message_data['message_updates']:
        message_lookup[message['sender']] = {
            'date': clean_value(message['date']),
            'datetime': clean_value(message['datetime'])
        }
    
    print(f"\nProcessing {len(practice_lookup)} practice updates and {len(message_lookup)} message updates")
    
    # Helper function to get column index from header name
    def get_column_index(header_name):
        """Get column index (0-based) from header name"""
        try:
            return headers.index(header_name)
        except ValueError:
            return None
        
    phone_col = get_column_index('phone number')
    practice_datetime_col = get_column_index('practice_updates_datetime')
    practice_date_col = get_column_index('practice_updates_date')
    message_datetime_col = get_column_index('message_updates_datetime')
    message_date_col = get_column_index('message_updates_date')
    message_counter_col = get_column_index('message_counter')
    updates = []

    print(f"\nSpreadsheet phone numbers:")
    for i, row in enumerate(all_records, start=2):
        # Get phone number from the identified column
        sheet_phone = row[phone_col] if phone_col is not None and len(row) > phone_col else ''
        if sheet_phone:
            print(f"  Row {i}: '{sheet_phone}'")
    print("======================\n")

    # Process each row in the spreadsheet
    for i, row in enumerate(all_records, start=2):  # start=2 because row 1 is headers
        # Safely get phone number
        sheet_phone = row[phone_col] if phone_col is not None and len(row) > phone_col else ''
        
        if sheet_phone:  # Only process rows with phone numbers
            # Clean the sheet phone number to match our lookup format
            cleaned_sheet_phone = sheet_phone.replace(' ', '').replace('-', '').lstrip('+')
            
            print(f"Row {i}:")

            # Check for practice updates 
            if cleaned_sheet_phone in practice_lookup:
                new_date = practice_lookup[cleaned_sheet_phone]['date']
                new_datetime = practice_lookup[cleaned_sheet_phone]['datetime']
                
                # Get current practice datetime
                current_practice_datetime = row[practice_datetime_col] if len(row) > practice_datetime_col else ''
                
                print(f"  Found practice match! Current practice datetime: '{current_practice_datetime}' -> New: '{new_datetime}'")

                # Update datetime if different
                if current_practice_datetime != new_datetime:
                    # Update the datetime in column D
                    updates.append({
                        'range': f'D{i}',
                        'values': [[new_datetime]]
                    })
                    
                    # Update the last practice date in column E (date only format)
                    updates.append({
                        'range': f'E{i}',
                        'values': [[new_date]]
                    })    

            # Check for message updates 
            if cleaned_sheet_phone in message_lookup:
                new_date = message_lookup[cleaned_sheet_phone]['date']
                new_datetime = message_lookup[cleaned_sheet_phone]['datetime']
                    
                # Get current message datetime 
                current_message_datetime = row[message_datetime_col] if len(row) > message_datetime_col else ''
                    
                print(f"  Found message match! Current message datetime: '{current_message_datetime}' -> New: '{new_datetime}'")

                current_message_counter_value = row[message_counter_col] if len(row) > message_counter_col else 0
                try:
                    current_message_counter = int(current_message_counter_value) if current_message_counter_value != '' and current_message_counter_value is not None else 0
                except (ValueError, TypeError):
                    current_message_counter = 0
                        
                new_message_counter = current_message_counter + 1

                if current_message_datetime != new_datetime:
                    updates.append({
                        'range': f'B{i}',
                        'values': [[new_datetime]]
                    })
                    updates.append({
                        'range': f'C{i}',
                        'values': [[new_date]]
                    })
                    updates.append({
                        'range': f'F{i}',
                        'values': [[new_message_counter]]
                    })

    # Execute all updates in a batch
    if updates:
        print(f"\nExecuting {len(updates)} updates...")
        datasheet.batch_update(updates, value_input_option='USER_ENTERED')
        print("Updates completed successfully!")
    else:
        print("\nNo updates needed.")