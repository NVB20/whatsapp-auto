import os
import ast
from datetime import datetime
from dotenv import load_dotenv

def message_formatter(message_data):
    # Load .env file
    load_dotenv()
    
    # Get search terms from environment variable
    search_terms_str = os.getenv("SEARCH_WORD")
    
    # Parse the string representation of the list
    try:
        if search_terms_str:
            search_terms = ast.literal_eval(search_terms_str)
        else:
            # Fallback to default search terms if env var is not set
            search_terms = ["עלה תרגול", "העליתי תרגול", "העלתי תרגול"]
    except (ValueError, SyntaxError):
        print(f"Error parsing SEARCH_WORD from .env file: {search_terms_str}")
        # Use default search terms as fallback
        search_terms = ["עלה תרגול", "העליתי תרגול", "העלתי תרגול"]
    
    print(f"Searching for terms: {search_terms}")
    
    filtered_messages = []  
    
    for message in message_data:
        sender = message['sender'].strip() 
        sender = sender.replace(' ', '').replace('-', '')
        sender = sender.lstrip('+')    
        
        text = message['text']
        timestamp = message['timestamp']
        
        # Check if the message contains any of the search terms
        contains_search_term = any(search_term in text for search_term in search_terms)
        
        if contains_search_term:
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
                # Format date as dd/mm/yy
                formatted_date = timestamp_dt.strftime("%d/%m/%y")
                
                # Add to filtered messages
                filtered_messages.append({
                    "sender": sender,
                    "date": formatted_date,
                })
    
    message_lookup = {}
    for message in filtered_messages:
        phone = message['sender']
        date = message['date']
        
        # Convert date back to datetime for comparison
        try:
            current_date = datetime.strptime(date, "%d/%m/%y")
            
            if phone not in message_lookup:
                message_lookup[phone] = {
                    'sender': phone,
                    'date': date,
                    'datetime': current_date
                }
            else:
                # Keep the more recent date
                existing_date = message_lookup[phone]['datetime']
                if current_date > existing_date:
                    message_lookup[phone] = {
                        'sender': phone,
                        'date': date,
                        'datetime': current_date
                    }
        except ValueError:
            print(f"Error parsing date for comparison: {date}")
            continue
    
    # Convert back to list format (without datetime field)
    final_filtered_messages = []
    for phone_data in message_lookup.values():
        final_filtered_messages.append({
            'sender': phone_data['sender'],
            'date': phone_data['date']
        })
    
    print(final_filtered_messages)
    print(f"\nFound {len(final_filtered_messages)} unique phone numbers with messages containing any of: {search_terms}")
    
    return final_filtered_messages