import time
import logging
import os
from dotenv import load_dotenv

from selenium_read import open_whatsapp
from render_message import message_formatter
from sheets_update import update_sheets
from sheets_last_update import last_time_updated
from download_csv_backup import download_data_to_folder
from time_log import timed, table_log, setup_handler, no_messages


# === Configuration ===
load_dotenv()
CSV_DOWNLOAD = os.getenv("CSV_DOWNLOAD")

# Initialize logging before any log message
setup_handler()


if __name__ == "__main__":
    total_start = time.time()
    logging.info("\n" + "=" * 70)
    logging.info("🚀 Script started.")

    runtimes = {}

    elapsed, msgs = timed("open_whatsapp", open_whatsapp)
    runtimes["open_whatsapp"] = elapsed

if len(msgs) == 0:
    no_messages(elapsed)
    
else:
    elapsed, msgs = timed("message_formatter", message_formatter, msgs)
    runtimes["message_formatter"] = elapsed

    elapsed, _ = timed("update_sheets", update_sheets, msgs)
    runtimes["update_sheets"] = elapsed

    elapsed, _ = timed("last_time_updated", last_time_updated)
    runtimes["last_time_updated"] = elapsed

    elapsed, _ = timed("download_data_to_folder", download_data_to_folder)
    runtimes["download_data_to_folder"] = elapsed

    total_elapsed = time.time() - total_start

    table_log(runtimes, total_elapsed)
