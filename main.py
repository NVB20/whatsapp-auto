from selenium_read import open_whatsapp
from render_message import message_formatter
from sheets_update import update_sheets

if __name__ == "__main__":
    msgs = open_whatsapp()
    msgs = message_formatter(msgs)
    update_sheets(msgs)