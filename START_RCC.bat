@echo off
cd /d "C:\Users\BAJAJ1\Desktop\RCC"

REM Kill any existing sync_worker processes first
wmic process where "commandline like '%%sync_worker%%'" delete >nul 2>&1

REM Start sync worker
start "" pythonw sync_worker.py

echo RCC Sync Worker started.
timeout /t 3 >nul
