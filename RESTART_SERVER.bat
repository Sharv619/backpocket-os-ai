@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
title BackPocket Server Restart

echo ========================================
echo        BACKPOCKET SERVER RESTART
echo ========================================
echo.

cd /d "%~dp0"

echo Stopping existing server processes...
taskkill /IM python.exe /F >nul 2>&1
taskkill /IM uvicorn.exe /F >nul 2>&1

echo Killing any process on port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /PID %%a /F >nul 2>&1
)

echo Waiting for port to clear...
timeout /t 2 >nul

echo Starting server...
start "BackPocket Server" cmd /k "set PYTHONIOENCODING=utf-8 && python -m uvicorn main:app --host 127.0.0.1 --port 8000"

echo Waiting for server to start...
timeout /t 3 >nul

echo Opening dashboard...
start http://localhost:8000/dashboard

echo.
echo Server restarted! Dashboard should be open.
echo.
pause
