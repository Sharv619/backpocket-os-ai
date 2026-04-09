@echo off
chcp 65001 >nul
title BackPocket Mini-PC Server
echo ========================================
echo BACKPOCKET MINI-PC LAUNCHER
echo ========================================
echo.

cd /d "%~dp0"

REM Kill existing processes
echo Stopping existing servers...
taskkill /IM python.exe /F >nul 2>&1
taskkill /IM uvicorn.exe /F >nul 2>&1

echo.
echo Starting BackPocket Server...
echo Server will be available at:
echo   - Local:   http://localhost:8000/dashboard
echo   - Network: http://192.168.0.25:8000/dashboard
echo.

REM Start the server in background
start "BackPocket Server" python -m uvicorn main:app --host 0.0.0.0 --port 8000

echo Server started! Access at http://localhost:8000/dashboard
echo.

REM Optional: Start Cloudflare Tunnel for remote access
echo To enable remote access, run this command in a new terminal:
echo   cloudflared tunnel --url http://localhost:8000
echo.

pause
