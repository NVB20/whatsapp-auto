import logging
import time
from logging.handlers import RotatingFileHandler
import os
from dotenv import load_dotenv


def setup_handler():
    load_dotenv()
    CSV_DOWNLOAD = os.getenv("CSV_DOWNLOAD")
    LOG_FILE = os.path.join(CSV_DOWNLOAD, "runtime.log")
    os.makedirs(CSV_DOWNLOAD, exist_ok=True)

    # === Setup Logging (UTF-8 safe + append mode) ===
    handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8",
        delay=True
    )
    handler.mode = "a"

    # Console logging with UTF-8 (for emojis)
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    try:
        console.stream = open(os.sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
    except Exception:
        pass

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[handler, console]
    )

    logging.info(f"🗂️ Log file initialized at: {LOG_FILE}")


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


def table_log(runtimes, total_elapsed):
    # === Summary Table ===
    logging.info("\n" + "-" * 50)
    logging.info("🏁 SUMMARY OF TASK RUNTIMES")
    for name, t in runtimes.items():
        logging.info(f" - {name:<25} {t:>6.2f}s")
    logging.info("-" * 50)
    logging.info(f"TOTAL RUNTIME: {total_elapsed:.2f}s")
    logging.info("-" * 50)
    logging.info("=" * 70 + "\n")

def no_messages(total_elapsed):
    logging.info("\n" + "-" * 50)
    logging.info("the selenium didnt succeed to read any messages")
    logging.info(f"TOTAL RUNTIME: {total_elapsed:.2f}s")
    logging.info("-" * 50)
    logging.info("=" * 70 + "\n")


