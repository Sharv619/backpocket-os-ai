@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
title BackPocket Diagnostics

echo ========================================
echo        BACKPOCKET DIAGNOSTICS
echo ========================================
echo.

cd /d "%~dp0"

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo [OK] Virtual environment found
    call venv\Scripts\activate.bat
) else (
    echo [WARN] No virtual environment, using system Python
)

echo.
echo Checking Python packages...
python -c "import fastapi, google, requests" 2>nul
if %errorlevel%==0 (
    echo [OK] Required packages installed
) else (
    echo [ERROR] Missing required packages
    echo Run: pip install fastapi uvicorn google-generativeai google-auth google-auth-oauthlib google-api-python-client requests python-dotenv
)

echo.
echo Testing Gemini connection...
python -c "from services.gemini import get_gemini_client; c = get_gemini_client(); print('OK' if c else 'FAIL')" 2>nul
if %errorlevel%==0 (
    echo [OK] Gemini connected
) else (
    echo [WARN] Gemini connection test failed
)

echo.
echo Checking Gmail credentials...
if exist "gmail_credentials.json" (
    echo [OK] Gmail credentials found
) else (
    echo [ERROR] gmail_credentials.json not found
)

echo.
echo Checking Sheets credentials...
if exist "credentials.json" (
    echo [OK] Sheets credentials found
) else (
    echo [ERROR] credentials.json not found
)

echo.
echo Checking database...
if exist "backpocket.db" (
    echo [OK] Database found
) else (
    echo [WARN] Database not found, will be created on first run
)

echo.
echo ========================================
echo Diagnostics complete!
echo.
pause
