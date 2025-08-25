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


if __name__ == "__main__":
    message_data = [
        {'sender': '+972 55-885-7955 ', 'timestamp': '00:07, 8/24/2025', 'text': '@+972 52-645-0147 @נתנאל דוידוב האקדמיה למסחר העליתי תרגול בתקווה שהאחרון @+972 52-645-0147 @+972 52-645-0147 +972 52-645-0147 @נתנאל דוידוב האקדמיה למסחר @נתנאל דוידוב האקדמיה למסחר נתנאל דוידוב האקדמיה למסחר'},
        {'sender': '+972 52-252-3201 ', 'timestamp': '10:57, 8/24/2025', 'text': '@נתנאל דוידוב האקדמיה למסחר שלחתי הודעה @נתנאל דוידוב האקדמיה למסחר @נתנאל דוידוב האקדמיה למסחר נתנאל דוידוב האקדמיה למסחר'},
        {'sender': '+972 54-660-3802 ', 'timestamp': '13:25, 8/24/2025', 'text': '@נתנאל דוידוב האקדמיה למסחר עלה תרגול @נתנאל דוידוב האקדמיה למסחר @נתנאל דוידוב האקדמיה למסחר נתנאל דוידוב האקדמיה למסחר'},
        {'sender': '+972 53-431-9663 ', 'timestamp': '16:35, 8/24/2025', 'text': 'שבוע טוב לכולם שלחתי הודעה בפרטי @נתנאל דוידוב האקדמיה למסחר @נתנאל דוידוב האקדמיה למסחר @נתנאל דוידוב האקדמיה למסחר נתנאל דוידוב האקדמיה למסחר'},
        {'sender': '+972 54-776-5677 ', 'timestamp': '22:06, 8/24/2025', 'text': 'עלה תרגול @+972 52-645-0147 @+972 52-645-0147 @+972 52-645-0147 +972 52-645-0147'},   
        {'sender': '+972 55-885-7955 ', 'timestamp': '22:47, 8/24/2025', 'text': '@+972 52-645-0147 עלה תרגול @+972 52-645-0147 @+972 52-645-0147 +972 52-645-0147'},     
        {'sender': '+972 53-284-8492 ', 'timestamp': '11:07, 8/25/2025', 'text': '@+972 52-645-0147 עלה תרגול @+972 52-645-0147 @+972 52-645-0147 +972 52-645-0147'},    
        {'sender': '+972 58-550-0993 ', 'timestamp': '13:10, 8/25/2025', 'text': 'שלחתי הודעה @נתנאל דוידוב האקדמיה למסחר @נתנאל דוידוב האקדמיה למסחר @נתנאל דוידוב האקדמיה למסחר חר @נתנאל דוידוב האקדמיה למסחר נתנאל דוידוב האקדמיה למסחר'},
        {'sender': '+972 50-370-0952 ', 'timestamp': '15:53, 8/25/2025', 'text': 'שלחתי הודעה @נתנאל דוידוב האקדמיה למסחר @נתנאל דוידוב האקדמיה למסחר @נתנאל דוידוב האקדמיה למסחר נתנאל דוידוב האקדמיה למסחר'}
    ]

    message_formatter(message_data)