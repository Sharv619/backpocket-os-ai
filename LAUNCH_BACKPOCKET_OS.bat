@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
title BackPocket OS
echo.
echo  ==========================================
echo          BACKPOCKET OS LAUNCHER
echo     Your Digital Twin is starting...
echo  ==========================================
echo.

cd /d "%~dp0"

REM Kill any existing Python processes on port 8000 (be more thorough)
echo Cleaning up old processes...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo Killing process %%a on port 8000
    taskkill /PID %%a /F >nul 2>&1
)
REM Also kill any uvicorn/python processes that might be holding the port
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM python3.exe >nul 2>&1
timeout /t 2 >nul

REM Start the server in a new window
echo Starting server...
start "BackPocket OS Server" cmd /k "set PYTHONIOENCODING=utf-8 && python -m uvicorn main:app --host 127.0.0.1 --port 8000"

REM Wait for server to start
echo Waiting for server...
timeout /t 5 >nul

REM Open the dashboard
echo Opening dashboard...
start http://localhost:8000/dashboard

echo.
echo Dashboard should be open in your browser!
echo.
echo Press any key to exit this window (server will keep running)...
pause >nul
