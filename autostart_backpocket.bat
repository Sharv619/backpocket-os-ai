@echo off
REM BackPocket OS Auto-Start (Hidden)
REM Place in: %APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup

cd /d "%~dp0"
set PYTHONIOENCODING=utf-8

REM Run server hidden (no console window)
start /b pythonw -m uvicorn main:app --host 127.0.0.1 --port 8000 --log-level warning
