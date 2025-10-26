from selenium_read import open_whatsapp
from render_message import message_formatter
from sheets_update import update_sheets
from sheets_last_update import last_time_updated
from download_csv_backup import download_data_to_folder

if __name__ == "__main__":
    msgs = open_whatsapp()
    msgs = message_formatter(msgs)
    update_sheets(msgs)
    last_time_updated()
    download_data_to_folder()