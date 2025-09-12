@echo off
setlocal enabledelayedexpansion

echo [*] Khoi dong Chatbot AI...

:: Kiem tra file .env
if not exist .env (
    echo [*] Tao file .env...
    echo GOOGLE_API_KEY=your_api_key_here > .env
    echo [*] Vui long nhap API key vao file .env
    pause
    exit /b
)

:: Kiem tra thu vien
py -m pip install -r requirements.txt
if !errorlevel! neq 0 (
    echo [ERROR] Khong the cai dat thu vien. Vui long kiem tra file requirements.txt
    pause
    exit /b
)

:: Chay ung dung
echo.
echo [*] Khoi dong thanh cong!
echo [*] Nhan Ctrl+C de thoat
echo.

py -m prefect server start

pause
