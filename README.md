# WhatsApp Assignment Tracker

An automated system that monitors WhatsApp group messages for student assignment submissions and tracks them in Google Sheets with visual status indicators.

## Overview

This project uses Selenium WebDriver to monitor a WhatsApp Web group chat for student assignment submissions. When a student sends a message indicating they've submitted their assignment, the system automatically updates a Google Sheets document with the submission date and applies color-coded status indicators.

## Features

- **Real-time WhatsApp Monitoring**: Continuously tracks messages in a specified WhatsApp group
- **Assignment Detection**: Filters messages to identify assignment submissions
- **Google Sheets Integration**: Automatically updates spreadsheet with submission dates
- **Visual Status System**: 
  - 🟢 Green: Recent submission (within 1 week)
  - 🔴 Red: Overdue submission (more than 1 week old)
- **Date Tracking**: Records exact submission timestamps

## Prerequisites

- Python 3.7 or higher
- Chrome/Chromium browser
- Google account with Sheets API access
- WhatsApp account with access to the target group

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/whatsapp-assignment-tracker.git
cd whatsapp-assignment-tracker
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```
### Basic Usage
```bash
python main.py
```

## How It Works

1. **Message Monitoring**: Selenium WebDriver connects to WhatsApp Web and  read the specified group chat messages
2. **Message Filtering**: Each new message is analyzed for submission keywords 
3. **Student Identification**: The system identifies which student sent the submission message based on his phone number
4. **Sheet Updates**: Google Sheets API updates the corresponding row with:
   - Current date/time
   - Green background color for the status cell
5. **Status Checking**: Periodically reviews all submissions and marks entries red if older than one week


## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request



## Disclaimer

This tool is for educational and administrative purposes only. Ensure you have proper permissions to monitor WhatsApp groups and comply with your institution's privacy policies.

