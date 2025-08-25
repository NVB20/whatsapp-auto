from datetime import datetime

def message_formatter(message_data):
    filtered_messages = []  
    search_text = "עלה תרגול"
    
    for message in message_data:
        sender = message['sender'].strip()  # Remove extra spaces
        sender = message['sender'].replace(' ', '').replace('-', '')
        sender = sender.lstrip('+')         # Remove leading "+" if exists
        
        text = message['text']
        timestamp = message['timestamp']
        
        # Check if the message contains the search text
        if search_text in text:
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

    print(filtered_messages)
    print(f"\nFound {len(filtered_messages)} messages containing '{search_text}'")
    
    return filtered_messages

