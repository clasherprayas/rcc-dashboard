"""
RCC Data Sync Worker
Runs every 30 seconds. Compares HDFC source file timestamp with OneDrive copy.
If source is newer, copies to local + OneDrive.
No dependency on app.py or Streamlit.
"""

import shutil
import time
from datetime import datetime
from pathlib import Path

# ─── PATHS ───
SOURCE_FILE = Path(r"\\Hdfc1\d\HDFC\ALLOCATION FILE\TW FILES\JUNE 26\TW ALLOCATION JUNE 26.xlsx")
LOCAL_COPY = Path(r"C:\Users\BAJAJ1\Desktop\RCC\RCC_DATA.xlsx")
ONEDRIVE_COPY = Path(r"C:\Users\BAJAJ1\OneDrive\RCC\RCC_DATA.xlsx")
LOG_FILE = Path(r"C:\Users\BAJAJ1\Desktop\RCC\sync_log.txt")

POLL_INTERVAL = 30  # seconds


def log(level, msg):
    """Append timestamped log entry."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{ts}] {level} | {msg}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry)


def get_mtime(path):
    """Get file modification time. Returns 0 if file doesn't exist."""
    try:
        if path.exists():
            return path.stat().st_mtime
    except OSError:
        pass
    return 0


def fmt_time(mtime):
    """Format mtime to readable string."""
    if mtime == 0:
        return "N/A"
    return datetime.fromtimestamp(mtime).strftime("%d.%m.%Y %H:%M:%S")


def sync():
    """Check source vs destination timestamps and sync if needed."""
    # Check source reachable
    try:
        if not SOURCE_FILE.exists():
            log("WARN", "Source not reachable")
            return
    except OSError as e:
        log("ERROR", f"Source check failed: {e}")
        return

    source_mtime = get_mtime(SOURCE_FILE)
    onedrive_mtime = get_mtime(ONEDRIVE_COPY)

    log("INFO", f"Checking | Src: {fmt_time(source_mtime)} | OD: {fmt_time(onedrive_mtime)}")

    # Compare: sync only if source is newer than OneDrive copy
    if source_mtime > onedrive_mtime:
        try:
            # Copy to local
            shutil.copy2(SOURCE_FILE, LOCAL_COPY)
            # Copy to OneDrive
            if ONEDRIVE_COPY.parent.exists():
                shutil.copy2(SOURCE_FILE, ONEDRIVE_COPY)
            else:
                log("ERROR", f"OneDrive folder missing: {ONEDRIVE_COPY.parent}")
                return

            log("SUCCESS", f"Synced | Source mtime: {fmt_time(source_mtime)}")
        except PermissionError:
            log("ERROR", "File locked (Excel open?). Will retry next cycle.")
        except OSError as e:
            log("ERROR", f"Copy failed: {e}")
    else:
        log("INFO", "No changes detected")


def main():
    """Main loop: poll every 30 seconds."""
    import os
    log("INFO", f"Sync worker started | PID: {os.getpid()}")
    while True:
        try:
            sync()
        except Exception as e:
            log("ERROR", f"Unexpected: {e}")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
