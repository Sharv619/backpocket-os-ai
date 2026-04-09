@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
title BackPocket Twin ENGINE
echo STARTING BACKPOCKET TWIN VERSION 2.2...
echo Checking for ghost processes...
taskkill /IM python.exe /F >nul 2>&1
taskkill /IM uvicorn.exe /F >nul 2>&1

cd /d "%~dp0"
echo Loading environment...
call venv\Scripts\activate >nul 2>&1 || echo No venv found, using system python.

echo Server starting on http://localhost:8000/dashboard
python -m uvicorn main:app --host 127.0.0.1 --port 8000
pause
