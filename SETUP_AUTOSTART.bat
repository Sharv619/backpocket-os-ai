@echo off
chcp 65001 >nul
echo Setting up BackPocket OS auto-start...

set "source=C:\Users\Cherry\BackPocket_MVP\autostart_backpocket.bat"
set "dest=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\BackPocket_OS.bat"

copy /Y "%source%" "%dest%"

echo.
if exist "%dest%" (
    echo SUCCESS: BackPocket OS will now auto-start on Windows login!
    echo.
) else (
    echo FAILED: Could not set up auto-start
    echo Please run this script as Administrator
)
echo.
pause
