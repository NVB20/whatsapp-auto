import time
import logging
from logging.handlers import RotatingFileHandler
import os
from dotenv import load_dotenv

from selenium_read import open_whatsapp
from render_message import message_formatter
from sheets_update import update_sheets
from sheets_last_update import last_time_updated
from download_csv_backup import download_data_to_folder


# === Configuration ===
load_dotenv()
CSV_DOWNLOAD = os.getenv("CSV_DOWNLOAD")
LOG_FILE = os.path.join(CSV_DOWNLOAD, "runtime.log")
os.makedirs(CSV_DOWNLOAD, exist_ok=True)

# === Setup Logging (UTF-8 safe) ===
handler = RotatingFileHandler(LOG_FILE, maxBytes=500_000, backupCount=3, encoding="utf-8")

# Use UTF-8 console output to avoid UnicodeEncodeError on Windows
console = logging.StreamHandler()
console.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
console.stream = open(os.sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[handler, console]
)


def timed(label, func, *args, **kwargs):
    """Run a function, log its runtime, and return the result."""
    start = time.time()
    logging.info(f"▶️ Starting {label}...")
    try:
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        logging.info(f"✅ {label} completed in {elapsed:.2f}s")
        return elapsed, result
    except Exception as e:
        elapsed = time.time() - start
        logging.error(f"❌ {label} failed after {elapsed:.2f}s: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    total_start = time.time()
    logging.info("🚀 Script started.")

    runtimes = {}

    elapsed, msgs = timed("open_whatsapp", open_whatsapp)
    runtimes["open_whatsapp"] = elapsed

    elapsed, msgs = timed("message_formatter", message_formatter, msgs)
    runtimes["message_formatter"] = elapsed

    elapsed, _ = timed("update_sheets", update_sheets, msgs)
    runtimes["update_sheets"] = elapsed

    elapsed, _ = timed("last_time_updated", last_time_updated)
    runtimes["last_time_updated"] = elapsed

    elapsed, _ = timed("download_data_to_folder", download_data_to_folder)
    runtimes["download_data_to_folder"] = elapsed

    total_elapsed = time.time() - total_start

    # === Summary Table ===
    logging.info("\n" + "=" * 50)
    logging.info("🏁 SUMMARY OF TASK RUNTIMES")
    for name, t in runtimes.items():
        logging.info(f" - {name:<25} {t:>6.2f}s")
    logging.info("-" * 50)
    logging.info(f"TOTAL RUNTIME: {total_elapsed:.2f}s")
    logging.info("=" * 50)
    logging.info(f"🗂️ Log file saved to: {LOG_FILE}")
