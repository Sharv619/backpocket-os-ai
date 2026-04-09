@echo off
chcp 65001 >nul
title BackPocket Logs

echo ========================================
echo        BACKPOCKET SERVER LOGS
echo ========================================
echo Press Ctrl+C to exit log viewer
echo.

cd /d "%~dp0"

REM Try to find log file or show console output
if exist "logs\backpocket.log" (
    type logs\backpocket.log
) else (
    echo No log file found. Showing live console output...
    echo.
    echo Starting server in live log mode...
    python -m uvicorn main:app --host 127.0.0.1 --port 8000
)
