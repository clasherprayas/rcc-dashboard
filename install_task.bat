@echo off
REM Run this as Administrator to register RCC Sync Worker in Task Scheduler
REM This replaces the Startup folder shortcut with a more reliable method

echo Registering RCC Sync Worker task...
schtasks /create /tn "RCC Sync Worker" /xml "%~dp0rcc_sync_task.xml" /f
if %errorlevel%==0 (
    echo.
    echo SUCCESS: Task registered. Worker will auto-start 30 seconds after login.
    echo You can now delete the Startup folder shortcut if it still exists.
    echo.
    echo To test: schtasks /run /tn "RCC Sync Worker"
) else (
    echo.
    echo FAILED: Make sure you are running this as Administrator.
)
pause
