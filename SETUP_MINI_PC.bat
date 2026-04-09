@echo off
chcp 65001 >nul
echo ========================================
echo BACKPOCKET MINI-PC SELF-SUFFICIENT SETUP
echo ========================================
echo.

REM Check if Ollama is installed
where ollama >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [1/5] Installing Ollama...
    powershell -Command "irm https://ollama.com/install.ps1 | iex"
) else (
    echo [1/5] Ollama already installed
)

REM Update Ollama
echo [2/5] Updating Ollama...
ollama pull deepseek-r1:8b
ollama pull qwen3:8b

REM Install Pi (the coding agent)
echo [3/5] Installing Pi...
ollama launch pi 2>nul || echo "Pi may already be installed or needs manual setup"

REM Check Python
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

REM Install required Python packages
echo [4/5] Installing Python dependencies...
pip install fastapi uvicorn python-dotenv google-generativeai aiofiles pydantic --quiet

REM Set up folder structure
echo [5/5] Setting up folders...
if not exist "BackPocket_MVP" mkdir BackPocket_MVP
cd BackPocket_MVP

echo.
echo ========================================
echo SETUP COMPLETE!
echo ========================================
echo.
echo Next steps:
echo 1. Copy your BackPocket_MVP folder to this mini-PC
echo 2. Run LAUNCH_MINI_PC.bat to start everything
echo.
pause
