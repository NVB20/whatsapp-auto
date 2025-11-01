import gspread
from google.oauth2.service_account import Credentials
import os
from dotenv import load_dotenv
import re
from datetime import datetime

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
    mainsheet = sheet.worksheet("main")

    # Fetch all data at once to avoid API rate limits
    all_data = datasheet.get_all_values()
    headers = all_data[0] if all_data else []
    all_records = all_data[1:] if len(all_data) > 1 else []

    # Fetch main sheet data for class counter updates
    main_data = mainsheet.get_all_values()
    main_headers = main_data[0] if main_data else []
    main_records = main_data[1:] if len(main_data) > 1 else []

    # Helper function to clean any tags and quotes from strings
    def clean_value(value):
        """Remove any HTML/XML tags and quotes from strings"""
        if not value:
            return value
        cleaned = str(value)
        cleaned = re.sub(r'<[^>]+>', '', cleaned)
        cleaned = cleaned.strip()
        cleaned = cleaned.strip("'\"")
        return cleaned

    # Helper function to compare dates
    def is_date_newer(new_date_str, old_date_str):
        """
        Compare two date strings and return True if new_date is newer than old_date.
        Handles various date formats.
        """
        if not old_date_str or old_date_str.strip() == '':
            # If no old date exists, consider new date as newer
            return True
        
        if not new_date_str or new_date_str.strip() == '':
            return False
        
        try:
            # Try common date formats
            date_formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d',
                '%d/%m/%Y %H:%M:%S',
                '%d/%m/%Y',
                '%m/%d/%Y %H:%M:%S',
                '%m/%d/%Y',
            ]
            
            new_date = None
            old_date = None
            
            for fmt in date_formats:
                try:
                    new_date = datetime.strptime(new_date_str.strip(), fmt)
                    break
                except ValueError:
                    continue
            
            for fmt in date_formats:
                try:
                    old_date = datetime.strptime(old_date_str.strip(), fmt)
                    break
                except ValueError:
                    continue
            
            if new_date and old_date:
                return new_date > old_date
            
            # If parsing fails, fall back to string comparison
            return new_date_str > old_date_str
            
        except Exception as e:
            print(f"  ⚠️ Date comparison error: {e}")
            # If comparison fails, don't update to be safe
            return False

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
    def get_column_index(header_name, header_list):
        """Get column index (0-based) from header name"""
        try:
            return header_list.index(header_name)
        except ValueError:
            return None
    
    def get_class_column_from_number(class_number):
        """Convert class number to corresponding column letter."""
        if 1 <= class_number <= 18:
            # Column H is index 8 (0-based), so שיעור 1 = 7 + 1 = 8
            column_index = 7 + class_number
            if column_index <= 26:
                return chr(ord('A') + column_index - 1)
            else:
                first_letter = chr(ord('A') + (column_index - 27) // 26)
                second_letter = chr(ord('A') + (column_index - 1) % 26)
                return first_letter + second_letter
        return None
    
    def extract_class_number(class_text):
        """Extract class number from text like 'שיעור 12'"""
        if not class_text:
            return None
        match = re.search(r'שיעור\s*(\d+)', str(class_text))
        if match:
            return int(match.group(1))
        return None
        
    phone_col = get_column_index('phone number', headers)
    practice_datetime_col = get_column_index('practice_updates_datetime', headers)
    practice_date_col = get_column_index('practice_updates_date', headers)
    message_datetime_col = get_column_index('message_updates_datetime', headers)
    message_date_col = get_column_index('message_updates_date', headers)
    message_counter_col = get_column_index('message_counter', headers)
    
    main_phone_col = get_column_index('phone number', main_headers)
    main_class_col = 1  # Column B
    
    updates = []
    main_updates = []
    class_counters_updated = 0
    
    # Dictionary to track which phones should update class counters
    phones_with_newer_practice = {}

    print(f"\nSpreadsheet phone numbers:")
    for i, row in enumerate(all_records, start=2):
        sheet_phone = row[phone_col] if phone_col is not None and len(row) > phone_col else ''
        if sheet_phone:
            print(f"  Row {i}: '{sheet_phone}'")
    print("======================\n")

    # Process each row in the data spreadsheet
    for i, row in enumerate(all_records, start=2):
        sheet_phone = row[phone_col] if phone_col is not None and len(row) > phone_col else ''
        
        if sheet_phone:
            cleaned_sheet_phone = sheet_phone.replace(' ', '').replace('-', '').lstrip('+')
            
            print(f"Row {i}:")

            # Check for practice updates 
            if cleaned_sheet_phone in practice_lookup:
                new_date = practice_lookup[cleaned_sheet_phone]['date']
                new_datetime = practice_lookup[cleaned_sheet_phone]['datetime']
                
                current_practice_datetime = row[practice_datetime_col] if len(row) > practice_datetime_col else ''
                current_practice_date = row[practice_date_col] if len(row) > practice_date_col else ''
                
                print(f"  Found practice match! Current: '{current_practice_datetime}' -> New: '{new_datetime}'")

                # Check if new date is newer than current date
                if is_date_newer(new_datetime, current_practice_datetime):
                    print(f"  ✅ New practice date is newer! Will update data sheet and class counter.")
                    
                    # Update datetime if different
                    if current_practice_datetime != new_datetime:
                        updates.append({
                            'range': f'D{i}',
                            'values': [[new_datetime]]
                        })
                        
                        updates.append({
                            'range': f'E{i}',
                            'values': [[new_date]]
                        })
                    
                    # Mark this phone for class counter update
                    phones_with_newer_practice[cleaned_sheet_phone] = True
                else:
                    print(f"  ⏭️ New practice date is NOT newer. Skipping update.")

            # Check for message updates 
            if cleaned_sheet_phone in message_lookup:
                new_date = message_lookup[cleaned_sheet_phone]['date']
                new_datetime = message_lookup[cleaned_sheet_phone]['datetime']
                    
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

    # Process main sheet for class counter updates
    print("\n=== Processing Class Counters ===")
    for i, row in enumerate(main_records, start=2):
        sheet_phone = row[main_phone_col] if main_phone_col is not None and len(row) > main_phone_col else ''
        
        if sheet_phone:
            cleaned_sheet_phone = sheet_phone.replace(' ', '').replace('-', '').lstrip('+')
            
            # Get class information from column B
            class_text = row[main_class_col] if len(row) > main_class_col else ''
            class_number = extract_class_number(class_text)
            
            # Check if this phone has a newer practice update AND has a valid class number
            if cleaned_sheet_phone in phones_with_newer_practice and class_number:
                class_column = get_class_column_from_number(class_number)
                if class_column:
                    # Convert column letter to index
                    if len(class_column) == 1:
                        class_col_num = ord(class_column) - ord('A') + 1
                    else:
                        class_col_num = (ord(class_column[0]) - ord('A') + 1) * 26 + (ord(class_column[1]) - ord('A') + 1)
                    
                    class_col_index = class_col_num - 1
                    current_class_counter_value = row[class_col_index] if len(row) > class_col_index else 0
                    try:
                        current_class_counter = int(current_class_counter_value) if current_class_counter_value != '' and current_class_counter_value is not None else 0
                    except (ValueError, TypeError):
                        current_class_counter = 0
                    
                    new_class_counter = current_class_counter + 1
                    
                    main_updates.append({
                        'range': f'{class_column}{i}',
                        'values': [[new_class_counter]]
                    })
                    
                    print(f"  ✅ Row {i}: Incrementing class {class_number} counter from {current_class_counter} to {new_class_counter} (Column {class_column})")
                    class_counters_updated += 1
            elif cleaned_sheet_phone in practice_lookup and class_number:
                print(f"  ⏭️ Row {i}: Skipping class {class_number} counter - practice date is not newer")

    # Execute all updates in batches
    if updates:
        print(f"\nExecuting {len(updates)} updates on 'data' sheet...")
        datasheet.batch_update(updates, value_input_option='USER_ENTERED')
        print("Data sheet updates completed successfully!")
    else:
        print("\nNo updates needed for 'data' sheet.")
    
    if main_updates:
        print(f"\nExecuting {len(main_updates)} updates on 'main' sheet...")
        mainsheet.batch_update(main_updates, value_input_option='USER_ENTERED')
        print(f"Main sheet updates completed successfully! {class_counters_updated} class counters updated.")
    else:
        print("\nNo class counter updates needed for 'main' sheet.")
    
    return class_counters_updated