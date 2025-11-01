import gspread
from google.oauth2.service_account import Credentials
import os
from dotenv import load_dotenv
import re

def update_sheets_data(message_data):
    """
    Update Google Sheets with message data.
    Expects message_data to be a dict with:
    - 'practice_updates': list of dicts with 'sender', 'date', 'datetime', and 'class_number'
    - 'message_updates': list of dicts with 'sender', 'date', and 'datetime'
    Phone numbers should already be cleaned and dates formatted.
    
    Updates in 'data' sheet:
    - Column B: message_updates_datetime
    - Column C: message_updates_date
    - Column D: practice_updates_datetime
    - Column E: practice_updates_date
    - Column F: message counter (increments when B is updated)
    
    Updates in 'main' sheet:
    - Columns H-Y: שיעור 1-18 counters (increments when practice update matches class in column B)
    """
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
    data_all = datasheet.get_all_values()
    data_headers = data_all[0] if data_all else []
    data_records = data_all[1:] if len(data_all) > 1 else []
    
    main_all = mainsheet.get_all_values()
    main_headers = main_all[0] if main_all else []
    main_records = main_all[1:] if len(main_all) > 1 else []

    # Create lookup dictionaries from the messages
    practice_lookup = {}
    for message in message_data['practice_updates']:
        practice_lookup[message['sender']] = {
            'date': message['date'],
            'datetime': message['datetime'],
            'class_number': message.get('class_number')  # Store class number
        }
    
    message_lookup = {}
    for message in message_data['message_updates']:
        message_lookup[message['sender']] = {
            'date': message['date'],
            'datetime': message['datetime']
        }
    
    print(f"\nProcessing {len(practice_lookup)} practice updates and {len(message_lookup)} message updates")
    
    # Track updates
    data_updates = []
    main_updates = []
    practice_updated = 0
    message_updated = 0
    class_counters_updated = 0
    
    # Debug: Print what we're looking for
    print("\n=== DEBUGGING INFO ===")
    print("Practice lookup keys (cleaned phone numbers):")
    for phone, data in practice_lookup.items():
        class_num = data.get('class_number', 'N/A')
        print(f"  '{phone}' - Class: {class_num}")
    
    print("\nMessage lookup keys (cleaned phone numbers):")
    for phone in message_lookup.keys():
        print(f"  '{phone}'")
    
    # Helper function to get column index from header name
    def get_column_index(header_name, headers_list):
        """Get column index (0-based) from header name"""
        try:
            return headers_list.index(header_name)
        except ValueError:
            return None
    
    # Get column indices for data sheet
    data_phone_col = get_column_index('phone number', data_headers)
    message_datetime_col = 1  # Column B
    message_date_col = 2  # Column C
    practice_datetime_col = 3  # Column D
    practice_date_col = 4  # Column E
    message_counter_col = 5  # Column F
    
    # Get column indices for main sheet
    main_phone_col = get_column_index('phone number', main_headers)
    main_class_col = 1  # Column B
    
    print(f"\nData sheet phone numbers:")
    for i, row in enumerate(data_records, start=2):
        sheet_phone = row[data_phone_col] if data_phone_col is not None and len(row) > data_phone_col else ''
        if sheet_phone:
            print(f"  Row {i}: '{sheet_phone}'")
    
    print(f"\nMain sheet phone numbers:")
    for i, row in enumerate(main_records, start=2):
        sheet_phone = row[main_phone_col] if main_phone_col is not None and len(row) > main_phone_col else ''
        if sheet_phone:
            print(f"  Row {i}: '{sheet_phone}'")
    print("======================\n")
    
    def get_class_column_from_number(class_number):
        """
        Convert class number to corresponding column letter.
        שיעור 1 = Column H (8), שיעור 2 = Column I (9), ..., שיעור 18 = Column Y (25)
        """
        if 1 <= class_number <= 18:
            column_index = 7 + class_number  # H=8, so שיעור 1 = 7+1=8
            if column_index <= 26:
                return chr(ord('A') + column_index - 1)  # A=1, B=2, ..., Z=26
            else:
                # For columns beyond Z (AA, AB, etc.)
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
    
    # Dictionary to track which phones should update class counters and their class numbers
    phones_with_practice_updates = {}
    
    # Process each row in the DATA spreadsheet
    print("=== Processing DATA sheet ===")
    for i, row in enumerate(data_records, start=2):  # start=2 because row 1 is headers
        sheet_phone = row[data_phone_col] if data_phone_col is not None and len(row) > data_phone_col else ''
        
        if sheet_phone:  # Only process rows with phone numbers
            # Clean the sheet phone number to match our lookup format
            cleaned_sheet_phone = sheet_phone.replace(' ', '').replace('-', '').lstrip('+')
            
            print(f"Row {i}:")
            
            # Check for practice updates (column D for datetime, column E for date)
            if cleaned_sheet_phone in practice_lookup:
                new_date = practice_lookup[cleaned_sheet_phone]['date']
                new_datetime = practice_lookup[cleaned_sheet_phone]['datetime']
                practice_class_number = practice_lookup[cleaned_sheet_phone].get('class_number')
                
                # Get current practice datetime from column D (index 3)
                current_practice_datetime = row[practice_datetime_col] if len(row) > practice_datetime_col else ''
                
                print(f"  Found practice match! Current practice datetime: '{current_practice_datetime}' -> New: '{new_datetime}'")
                if practice_class_number:
                    print(f"  Practice is for class: {practice_class_number}")
                
                # Update datetime in column D if different
                if current_practice_datetime != new_datetime:
                    # Update the datetime in column D
                    data_updates.append({
                        'range': f'D{i}',
                        'values': [[new_datetime]]
                    })
                    
                    # Update the last practice date in column E (date only format)
                    data_updates.append({
                        'range': f'E{i}',
                        'values': [[new_date]]
                    })
                    
                    # Mark this phone for class counter update with specific class number
                    if practice_class_number:
                        phones_with_practice_updates[cleaned_sheet_phone] = practice_class_number
                    
                    print(f"  ✅ UPDATING practice datetime for {cleaned_sheet_phone} from '{current_practice_datetime}' to '{new_datetime}' (Column D)")
                    print(f"  ✅ UPDATING last practice date for {cleaned_sheet_phone} to '{new_date}' (Column E)")
                    practice_updated += 1
                else:
                    print(f"  ➖ {cleaned_sheet_phone} already has current practice datetime '{current_practice_datetime}' (Column D)")
            
            # Check for message updates (column B for datetime, column C for date, column F for counter)
            if cleaned_sheet_phone in message_lookup:
                new_date = message_lookup[cleaned_sheet_phone]['date']
                new_datetime = message_lookup[cleaned_sheet_phone]['datetime']
                
                # Get current message datetime from column B (index 1)
                current_message_datetime = row[message_datetime_col] if len(row) > message_datetime_col else ''
                
                print(f"  Found message match! Current message datetime: '{current_message_datetime}' -> New: '{new_datetime}'")
                
                # Update datetime in column B if different
                if current_message_datetime != new_datetime:
                    # Update the datetime in column B
                    data_updates.append({
                        'range': f'B{i}',
                        'values': [[new_datetime]]
                    })
                    
                    # Update the date in column C
                    data_updates.append({
                        'range': f'C{i}',
                        'values': [[new_date]]
                    })
                    
                    # Get current counter value from column F (index 5) and increment it
                    current_message_counter_value = row[message_counter_col] if len(row) > message_counter_col else 0
                    try:
                        current_message_counter = int(current_message_counter_value) if current_message_counter_value != '' and current_message_counter_value is not None else 0
                    except (ValueError, TypeError):
                        current_message_counter = 0
                    
                    new_message_counter = current_message_counter + 1
                    
                    # Update the counter in column F
                    data_updates.append({
                        'range': f'F{i}',
                        'values': [[new_message_counter]]
                    })
                    
                    print(f"  ✅ UPDATING message datetime for {cleaned_sheet_phone} from '{current_message_datetime}' to '{new_datetime}' (Column B)")
                    print(f"  ✅ UPDATING message date for {cleaned_sheet_phone} to '{new_date}' (Column C)")
                    print(f"  ✅ INCREMENTING message counter for {cleaned_sheet_phone} from {current_message_counter} to {new_message_counter} (Column F)")
                    message_updated += 1
                else:
                    print(f"  ➖ {cleaned_sheet_phone} already has current message datetime '{current_message_datetime}' (Column B)")
            
            if cleaned_sheet_phone not in practice_lookup and cleaned_sheet_phone not in message_lookup:
                print(f"  ❌ No match found for {cleaned_sheet_phone}")
    
    # Process each row in the MAIN spreadsheet for class counters
    print("\n=== Processing MAIN sheet (Class Counters) ===")
    for i, row in enumerate(main_records, start=2):
        sheet_phone = row[main_phone_col] if main_phone_col is not None and len(row) > main_phone_col else ''
        
        if sheet_phone:
            # Clean the sheet phone number to match our lookup format
            cleaned_sheet_phone = sheet_phone.replace(' ', '').replace('-', '').lstrip('+')
            
            # Get class information from column B (index 1)
            class_text = row[main_class_col] if len(row) > main_class_col else ''
            class_number = extract_class_number(class_text)
            
            if class_number:
                print(f"Row {i}: Class info: '{class_text}' -> Class number: {class_number}")
            
            # Check if this phone has a practice update AND the class numbers match
            if cleaned_sheet_phone in phones_with_practice_updates and class_number:
                practice_class_number = phones_with_practice_updates[cleaned_sheet_phone]
                
                # Only update if the class numbers match
                if practice_class_number == class_number:
                    class_column = get_class_column_from_number(class_number)
                    if class_column:
                        # Convert column letter back to number for cell access
                        if len(class_column) == 1:
                            class_col_num = ord(class_column) - ord('A') + 1
                        else:  # AA, AB, etc.
                            class_col_num = (ord(class_column[0]) - ord('A') + 1) * 26 + (ord(class_column[1]) - ord('A') + 1)
                        
                        # Get current class counter value from row data
                        class_col_index = class_col_num - 1  # Convert to 0-based index
                        current_class_counter_value = row[class_col_index] if len(row) > class_col_index else 0
                        try:
                            current_class_counter = int(current_class_counter_value) if current_class_counter_value != '' and current_class_counter_value is not None else 0
                        except (ValueError, TypeError):
                            current_class_counter = 0
                        
                        new_class_counter = current_class_counter + 1
                        
                        # Update the class counter
                        main_updates.append({
                            'range': f'{class_column}{i}',
                            'values': [[new_class_counter]]
                        })
                        
                        print(f"  ✅ INCREMENTING class {class_number} counter for {cleaned_sheet_phone} from {current_class_counter} to {new_class_counter} (Column {class_column})")
                        class_counters_updated += 1
                else:
                    print(f"  ➖ Row {i}: Skipping class {class_number} counter - practice was for class {practice_class_number}, not {class_number}")
    
    # Perform batch updates if there are changes
    if data_updates:
        try:
            datasheet.batch_update(data_updates, value_input_option='USER_ENTERED')
            print(f"\n✅ Successfully updated DATA sheet!")
            print(f"   - Practice updates (Column D + E): {practice_updated}")
            print(f"   - Message updates (Column B + C + Counter F): {message_updated}")
            print(f"   - Total batch operations: {len(data_updates)}")
        except Exception as e:
            print(f"❌ Error updating data sheet: {e}")
    else:
        print("\n📋 No updates needed for DATA sheet - all dates are already current")
    
    if main_updates:
        try:
            mainsheet.batch_update(main_updates, value_input_option='USER_ENTERED')
            print(f"\n✅ Successfully updated MAIN sheet!")
            print(f"   - Class counters updated: {class_counters_updated}")
            print(f"   - Total batch operations: {len(main_updates)}")
        except Exception as e:
            print(f"❌ Error updating main sheet: {e}")
    else:
        print("\n📋 No updates needed for MAIN sheet - no class counters to update")
    
    return practice_updated, message_updated, class_counters_updated