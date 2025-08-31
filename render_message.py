from datetime import datetime
from dotenv import load_dotenv
import os
import re

def clean_phone_number(phone):
    """Clean phone number by removing spaces, dashes, and leading plus signs, then normalize to Israeli format."""
    # Remove all non-digit characters
    cleaned = re.sub(r'[^\d]', '', phone.strip())
    
    # Handle different Israeli phone number formats
    if cleaned.startswith('972'):
        # Already in international format (972XXXXXXXXX)
        return cleaned
    elif cleaned.startswith('0'):
        # Israeli domestic format (0XXXXXXXXX) - remove leading 0 and add 972
        return '972' + cleaned[1:]
    elif len(cleaned) == 9:
        # 9-digit number without country code or leading 0 - add 972
        return '972' + cleaned
    elif len(cleaned) == 10 and not cleaned.startswith('972'):
        # 10-digit number starting with area code - add 972
        return '972' + cleaned
    else:
        # Return as-is if format is unclear
        return cleaned

def message_formatter(message_data):
    """
    Process message data and return categorized messages for sheet updates.
    Returns dict with 'practice_updates' (for column E) and 'message_updates' (for column H).
    For each phone number, keeps the most recent message of each type (practice/sent).
    """
    # Load .env file
    load_dotenv()
    
    # Get search terms from environment variables
    practice_terms_env = os.getenv("PRACTICE_WORDS")
    message_terms_env = os.getenv("MESSAGE_WORDS")
    
    # Parse the environment variables (assuming they're stored as JSON-like strings)
    import json
    try:
        practice_terms = json.loads(practice_terms_env) if practice_terms_env else ["עלה תרגול", "העליתי תרגול", "העלתי תרגול"]
        message_terms = json.loads(message_terms_env) if message_terms_env else ["שלחתי הודעה"]
    except (json.JSONDecodeError, TypeError):
        # Fallback to default values if parsing fails
        print("Warning: Could not parse search terms from environment variables, using defaults")
        practice_terms = ["עלה תרגול", "העליתי תרגול", "העלתי תרגול"]
        message_terms = ["שלחתי הודעה"]
    
    print(f"Searching for practice terms: {practice_terms}")
    print(f"Searching for message terms: {message_terms}")
    
    # Dictionary to store the latest message of each type for each phone number
    # Structure: {phone_number: {'practice': message_data, 'sent': message_data}}
    phone_messages = {}
    
    for message in message_data:
        sender = clean_phone_number(message['sender'])
        text = message['text']
        timestamp = message['timestamp']
        
        print(f"Processing phone: {message['sender']} -> normalized: {sender}")
        
        # Check message type
        is_practice_message = any(term in text for term in practice_terms)
        is_sent_message = any(term in text for term in message_terms)
        
        if is_practice_message or is_sent_message:
            # Convert timestamp to datetime if it's a string
            if isinstance(timestamp, str):
                try:
                    # Format: "22:06, 8/24/2025"
                    timestamp_dt = datetime.strptime(timestamp, "%H:%M, %m/%d/%Y")
                except ValueError:
                    try:
                        # Alternative format: "22:06, 24/8/2025"
                        timestamp_dt = datetime.strptime(timestamp, "%H:%M, %d/%m/%Y")
                    except ValueError:
                        print(f"Could not parse timestamp: {timestamp}")
                        continue
                        
                # Format date as dd/mm/yy and time as HH:MM
                formatted_date = timestamp_dt.strftime("%d/%m/%y")
                formatted_datetime = timestamp_dt.strftime("%H:%M, %d/%m/%y")
                
                message_info = {
                    "sender": sender,
                    "date": formatted_date,
                    "datetime": formatted_datetime,
                    "datetime_obj": timestamp_dt
                }
                
                # Initialize phone entry if it doesn't exist
                if sender not in phone_messages:
                    phone_messages[sender] = {}
                
                # Process practice messages
                if is_practice_message:
                    if 'practice' not in phone_messages[sender]:
                        phone_messages[sender]['practice'] = message_info
                    else:
                        # Keep the more recent practice message
                        existing_dt = phone_messages[sender]['practice']['datetime_obj']
                        if timestamp_dt > existing_dt:
                            phone_messages[sender]['practice'] = message_info
                
                # Process sent messages
                if is_sent_message:
                    if 'sent' not in phone_messages[sender]:
                        phone_messages[sender]['sent'] = message_info
                    else:
                        # Keep the more recent sent message
                        existing_dt = phone_messages[sender]['sent']['datetime_obj']
                        if timestamp_dt > existing_dt:
                            phone_messages[sender]['sent'] = message_info
    
    # Extract practice and message updates
    practice_updates = []
    message_updates = []
    
    for phone, messages in phone_messages.items():
        if 'practice' in messages:
            msg_data = messages['practice']
            practice_updates.append({
                'sender': msg_data['sender'],
                'date': msg_data['date'],
                'datetime': msg_data['datetime']
            })
        
        if 'sent' in messages:
            msg_data = messages['sent']
            message_updates.append({
                'sender': msg_data['sender'],
                'date': msg_data['date'],
                'datetime': msg_data['datetime']
            })
    
    print(f"\nPractice updates: {practice_updates}")
    print(f"Message updates: {message_updates}")
    print(f"\nFound {len(practice_updates)} unique phone numbers for practice updates")
    print(f"Found {len(message_updates)} unique phone numbers for message updates")
    
    return {
        'practice_updates': practice_updates,
        'message_updates': message_updates
    }