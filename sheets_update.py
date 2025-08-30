import gspread
from google.oauth2.service_account import Credentials
import os
from dotenv import load_dotenv
import re

def update_sheets(message_data):
    """
    Update Google Sheets with message data.
    Expects message_data to be a dict with:
    - 'practice_updates': list of dicts with 'sender', 'date', and 'datetime' for column I updates
    - 'message_updates': list of dicts with 'sender', 'date', and 'datetime' for column F updates
    Phone numbers should already be cleaned and dates formatted.
    
    Also updates:
    - Column D: last practice date (date only format)
    - Column G: message_update counter (increments when F is updated with newer data)
    - Class counters: columns J-AA (שיעור 1-18) based on class number in column B
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
    worksheet = sheet.worksheet("main")
    all_records = worksheet.get_all_records()

    
    # Create lookup dictionaries from the messages
    practice_lookup = {}
    for message in message_data['practice_updates']:
        practice_lookup[message['sender']] = {
            'date': message['date'],
            'datetime': message['datetime']
        }
    
    message_lookup = {}
    for message in message_data['message_updates']:
        message_lookup[message['sender']] = {
            'date': message['date'],
            'datetime': message['datetime']
        }
    
    print(f"\nProcessing {len(practice_lookup)} practice updates and {len(message_lookup)} message updates")
    
    # Track updates
    updates = []
    practice_updated = 0
    message_updated = 0
    class_counters_updated = 0
    
    # Debug: Print what we're looking for
    print("\n=== DEBUGGING INFO ===")
    print("Practice lookup keys (cleaned phone numbers):")
    for phone in practice_lookup.keys():
        print(f"  '{phone}'")
    
    print("\nMessage lookup keys (cleaned phone numbers):")
    for phone in message_lookup.keys():
        print(f"  '{phone}'")
    
    print(f"\nSpreadsheet phone numbers:")
    for i, record in enumerate(all_records, start=2):
        sheet_phone = record.get('phone number', '')
        if sheet_phone:
            print(f"  Row {i}: '{sheet_phone}'")
    print("======================\n")
    
    def get_class_column_from_number(class_number):
        """
        Convert class number to corresponding column letter.
        שיעור 1 = Column J (10), שיעור 2 = Column K (11), ..., שיעור 18 = Column AA (27)
        """
        if 1 <= class_number <= 18:
            column_index = 9 + class_number  # J=10, so שיעור 1 = 9+1=10
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
    
    # Process each row in the spreadsheet
    for i, record in enumerate(all_records, start=2):  # start=2 because row 1 is headers
        sheet_phone = record.get('phone number', '')
        
        if sheet_phone:  # Only process rows with phone numbers
            # Clean the sheet phone number to match our lookup format
            cleaned_sheet_phone = sheet_phone.replace(' ', '').replace('-', '').lstrip('+')
            
            print(f"Row {i}:")
            
            # Get class information from column B
            class_text = worksheet.cell(i, 2).value or ''  # Column B = 2
            class_number = extract_class_number(class_text)
            
            if class_number:
                print(f"  Class info: '{class_text}' -> Class number: {class_number}")
            
            # Check for practice updates (column I for datetime, column H for counter)
            if cleaned_sheet_phone in practice_lookup:
                new_date = practice_lookup[cleaned_sheet_phone]['date']
                new_datetime = practice_lookup[cleaned_sheet_phone]['datetime']
                
                # Get current practice datetime from column I
                current_practice_datetime = worksheet.cell(i, 9).value or ''  # Column I = 9
                
                print(f"  Found practice match! Current practice datetime: '{current_practice_datetime}' -> New: '{new_datetime}'")
                
                # Update datetime in column I if different
                if current_practice_datetime != new_datetime:
                    # Update the datetime in column I
                    updates.append({
                        'range': f'I{i}',
                        'values': [[new_datetime]]
                    })
                    
                    # Update the last practice date in column D (date only format)
                    updates.append({
                        'range': f'D{i}',
                        'values': [[new_date]]
                    })
                    
                    # Update class counter if class number is valid
                    if class_number:
                        class_column = get_class_column_from_number(class_number)
                        if class_column:
                            # Convert column letter back to number for cell access
                            if len(class_column) == 1:
                                class_col_num = ord(class_column) - ord('A') + 1
                            else:  # AA, AB, etc.
                                class_col_num = (ord(class_column[0]) - ord('A') + 1) * 26 + (ord(class_column[1]) - ord('A') + 1)
                            
                            current_class_counter_value = worksheet.cell(i, class_col_num).value or 0
                            try:
                                current_class_counter = int(current_class_counter_value) if current_class_counter_value != '' and current_class_counter_value is not None else 0
                            except (ValueError, TypeError):
                                current_class_counter = 0
                            
                            new_class_counter = current_class_counter + 1
                            
                            # Update the class counter
                            updates.append({
                                'range': f'{class_column}{i}',
                                'values': [[new_class_counter]]
                            })
                            
                            print(f"  ✅ INCREMENTING class {class_number} counter for {cleaned_sheet_phone} from {current_class_counter} to {new_class_counter} (Column {class_column})")
                            class_counters_updated += 1
                    
                    print(f"  ✅ UPDATING practice datetime for {cleaned_sheet_phone} from '{current_practice_datetime}' to '{new_datetime}' (Column I)")
                    print(f"  ✅ UPDATING last practice date for {cleaned_sheet_phone} to '{new_date}' (Column D)")
                    practice_updated += 1
                else:
                    print(f"  ➖ {cleaned_sheet_phone} already has current practice datetime '{current_practice_datetime}' (Column I)")
            
            # Check for message updates (column F for datetime, column G for counter)
            if cleaned_sheet_phone in message_lookup:
                new_date = message_lookup[cleaned_sheet_phone]['date']
                new_datetime = message_lookup[cleaned_sheet_phone]['datetime']
                
                # Get current message datetime from column F
                current_message_datetime = worksheet.cell(i, 6).value or ''  # Column F = 6
                
                print(f"  Found message match! Current message datetime: '{current_message_datetime}' -> New: '{new_datetime}'")
                
                # Update datetime in column F if different
                if current_message_datetime != new_datetime:
                    # Update the datetime in column F
                    updates.append({
                        'range': f'F{i}',
                        'values': [[new_datetime]]
                    })
                    
                    # Get current counter value from column G and increment it
                    current_message_counter_value = worksheet.cell(i, 7).value or 0  # Column G = 7
                    try:
                        current_message_counter = int(current_message_counter_value) if current_message_counter_value != '' and current_message_counter_value is not None else 0
                    except (ValueError, TypeError):
                        current_message_counter = 0
                    
                    new_message_counter = current_message_counter + 1
                    
                    # Update the counter in column G
                    updates.append({
                        'range': f'G{i}',
                        'values': [[new_message_counter]]
                    })
                    
                    print(f"  ✅ UPDATING message datetime for {cleaned_sheet_phone} from '{current_message_datetime}' to '{new_datetime}' (Column F)")
                    print(f"  ✅ INCREMENTING message counter for {cleaned_sheet_phone} from {current_message_counter} to {new_message_counter} (Column G)")
                    message_updated += 1
                else:
                    print(f"  ➖ {cleaned_sheet_phone} already has current message datetime '{current_message_datetime}' (Column F)")
            
            if cleaned_sheet_phone not in practice_lookup and cleaned_sheet_phone not in message_lookup:
                print(f"  ❌ No match found for {cleaned_sheet_phone}")
    
    # Perform batch update if there are changes
    total_updated = practice_updated + message_updated
    if updates:
        try:
            worksheet.batch_update(updates, value_input_option='USER_ENTERED')
            print(f"\n✅ Successfully updated {total_updated} rows!")
            print(f"   - Practice updates (Column D + I): {practice_updated}")
            print(f"   - Message updates (Column F + Counter G): {message_updated}")
            print(f"   - Class counters updated: {class_counters_updated}")
            print(f"   - Total batch operations: {len(updates)}")
            
        except Exception as e:
            print(f"❌ Error updating spreadsheet: {e}")
            return practice_updated, message_updated, 0
    else:
        print("📋 No updates needed - all dates are already current")
    
    return practice_updated, message_updated