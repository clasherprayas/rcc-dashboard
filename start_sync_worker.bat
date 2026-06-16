@echo off
REM Wait 30 seconds for network drives and OneDrive to be ready after login
timeout /t 30 /nobreak >nul

REM Start sync_worker.py in background using pythonw (no console window)
start "" "C:\Users\BAJAJ1\AppData\Local\Python\pythoncore-3.14-64\pythonw.exe" "C:\Users\BAJAJ1\Desktop\RCC\sync_worker.py"
