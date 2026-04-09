@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
title BackPocket Server
cd /d "%~dp0"
echo Starting BackPocket Server...
start /B python -m uvicorn main:app --host 127.0.0.1 --port 8000 > server.log 2>&1
echo Server started. Check dashboard at http://localhost:8000/dashboard
