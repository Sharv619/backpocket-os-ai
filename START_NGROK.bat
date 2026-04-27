@echo off
setlocal
echo ---------------------------------------------------
echo   BACKPOCKET OS: NGROK DEPLOYMENT
echo ---------------------------------------------------
echo.

:: Check if ngrok is in path
where ngrok >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] ngrok is not installed or not in your PATH.
    echo Please download it from: https://ngrok.com/download
    echo.
    pause
    exit /b 1
)

echo [1/2] Starting ngrok tunnel on port 8000...
echo.
echo IMPORTANT: Once started, look for the "Forwarding" URL 
echo (e.g., https://abcd-123.ngrok-free.dev)
echo.
echo Your Flutter Web UI will be available at:
echo [URL]/app/
echo.
echo Press Ctrl+C to stop the tunnel.
echo.

ngrok http 8000

endlocal
