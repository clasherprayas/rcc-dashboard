"""
RCC Data Sync Worker
Runs every 30 seconds. Compares HDFC source file timestamp with OneDrive copy.
If source is newer, copies to local + OneDrive.
No dependency on app.py or Streamlit.
"""

import shutil
import time
import os
import threading
import subprocess
from datetime import datetime
from pathlib import Path

# ─── PATHS ───
# Auto-detect current month's folder
BASE_TW_PATH = Path(r"\\Hdfc1\d\HDFC\ALLOCATION FILE\TW FILES")

def get_source_file():
    """Auto-detect the latest month's TW ALLOCATION file."""
    import calendar
    from datetime import datetime
    
    now = datetime.now()
    
    # Try current month first, then previous month
    for months_back in range(0, 3):
        d = now.month - months_back
        y = now.year
        if d <= 0:
            d += 12
            y -= 1
        month_name = calendar.month_name[d].upper()
        yr = str(y)[2:]  # "26" from 2026
        
        folder_name = f"{month_name} {yr}"
        file_name = f"TW ALLOCATION {month_name} {yr}.xlsx"
        full_path = BASE_TW_PATH / folder_name / file_name
        
        try:
            if full_path.exists():
                return full_path
        except OSError:
            continue
    
    # Fallback — return current month path even if not found yet
    month_name = calendar.month_name[now.month].upper()
    yr = str(now.year)[2:]
    folder_name = f"{month_name} {yr}"
    file_name = f"TW ALLOCATION {month_name} {yr}.xlsx"
    return BASE_TW_PATH / folder_name / file_name

SOURCE_FILE = get_source_file()
LOCAL_COPY = Path(r"C:\Users\BAJAJ1\Desktop\RCC\RCC_DATA.xlsx")
ONEDRIVE_COPY = Path(r"C:\Users\BAJAJ1\OneDrive\RCC\RCC_DATA.xlsx")
LOG_FILE = Path(r"C:\Users\BAJAJ1\Desktop\RCC\sync_log.txt")

POLL_INTERVAL = 30  # seconds
NETWORK_TIMEOUT = 10  # seconds max for network file check


def log(level, msg):
    """Append timestamped log entry + print to console."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{ts}] {level} | {msg}"
    print(entry, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry + "\n")
    except Exception:
        pass


RCC_DIR = str(LOCAL_COPY.parent)

def _git_push():
    """Auto git push RCC_DATA.xlsx to GitHub → triggers Render redeploy."""
    try:
        subprocess.run(
            ["git", "add", "RCC_DATA.xlsx"],
            cwd=RCC_DIR, capture_output=True, timeout=10
        )
        subprocess.run(
            ["git", "commit", "-m", "Auto sync: data updated"],
            cwd=RCC_DIR, capture_output=True, timeout=10
        )
        result = subprocess.run(
            ["git", "push"],
            cwd=RCC_DIR, capture_output=True, timeout=30
        )
        if result.returncode == 0:
            log("SUCCESS", "Git push done → Render will redeploy")
        else:
            log("WARN", f"Git push failed: {result.stderr.decode()[:100]}")
    except Exception as e:
        log("ERROR", f"Git push error: {e}")


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


def check_source_exists_with_timeout(timeout=NETWORK_TIMEOUT):
    """Check if source file exists with a timeout (network can hang)."""
    result = [None]

    def check():
        try:
            result[0] = SOURCE_FILE.exists()
        except OSError:
            result[0] = False

    t = threading.Thread(target=check, daemon=True)
    t.start()
    t.join(timeout=timeout)

    if t.is_alive():
        # Thread still running = network hung
        return None  # timeout
    return result[0]


def sync():
    """Check source vs destination timestamps and sync if needed."""
    global SOURCE_FILE
    SOURCE_FILE = get_source_file()  # Re-detect each cycle (handles month change)
    log("INFO", f"Cycle start | Source: {SOURCE_FILE.name}")

    # Check source reachable with timeout
    source_exists = check_source_exists_with_timeout()

    if source_exists is None:
        log("WARN", f"Source check TIMEOUT ({NETWORK_TIMEOUT}s). Network hung.")
        return
    if not source_exists:
        log("WARN", "Source not reachable")
        return

    try:
        source_mtime = get_mtime(SOURCE_FILE)
        onedrive_mtime = get_mtime(ONEDRIVE_COPY)

        log("INFO", f"Comparing | Src: {fmt_time(source_mtime)} | OD: {fmt_time(onedrive_mtime)} | Newer: {source_mtime > onedrive_mtime}")

        # Compare: sync only if source is newer than OneDrive copy
        if source_mtime > onedrive_mtime:
            # Copy to local
            shutil.copy2(SOURCE_FILE, LOCAL_COPY)
            # Copy to OneDrive
            if ONEDRIVE_COPY.parent.exists():
                shutil.copy2(SOURCE_FILE, ONEDRIVE_COPY)
            else:
                log("ERROR", f"OneDrive folder missing: {ONEDRIVE_COPY.parent}")
                return
            log("SUCCESS", f"Synced | Source: {fmt_time(source_mtime)}")
            
            # Auto git push to Render
            _git_push()
        else:
            log("INFO", "No changes detected")
    except PermissionError:
        log("ERROR", "File locked (Excel open?). Retry next cycle.")
    except OSError as e:
        log("ERROR", f"Copy failed: {e}")


def wait_for_network(max_wait=120, check_interval=5):
    """Wait for network path to become available after boot."""
    log("INFO", f"Waiting for network path (max {max_wait}s)...")
    waited = 0
    while waited < max_wait:
        try:
            if SOURCE_FILE.parent.exists():
                log("INFO", f"Network path available after {waited}s")
                return True
        except OSError:
            pass
        time.sleep(check_interval)
        waited += check_interval
    log("WARN", f"Network path NOT available after {max_wait}s. Starting anyway.")
    return False


def main():
    """Main loop: poll every 30 seconds."""
    log("INFO", f"Sync worker started | PID: {os.getpid()}")

    # Wait for network/OneDrive to be ready (critical after reboot)
    wait_for_network()

    cycle = 0
    while True:
        cycle += 1
        try:
            sync()
        except Exception as e:
            log("ERROR", f"Unexpected in cycle {cycle}: {e}")
        log("INFO", f"Sleeping {POLL_INTERVAL}s (cycle {cycle} done)")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
