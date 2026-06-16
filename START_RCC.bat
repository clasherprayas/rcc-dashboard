@echo off

cd /d "C:\Users\BAJAJ1\Desktop\RCC"

start "RCC" cmd /k "python -m streamlit run app.py"

timeout /t 15 >nul

start "Cloudflare" cmd /k "cloudflared tunnel run rcc"