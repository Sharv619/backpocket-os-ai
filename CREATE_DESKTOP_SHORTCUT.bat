@echo off
chcp 65001 >nul

echo ========================================
echo    BackPocket Desktop Shortcut Creator
echo ========================================
echo.

' Create a proper Windows shortcut using PowerShell
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%USERPROFILE%\Desktop\BackPocket Twin.lnk'); $s.TargetPath = '%~dp0Launch_BackPocket.vbs'; $s.WorkingDirectory = '%~dp0'; $s.Description = 'Launch BackPocket OS Twin'; $s.Save()"

if exist "%USERPROFILE%\Desktop\BackPocket Twin.lnk" (
    echo.
    echo SUCCESS! Desktop shortcut created!
    echo Double-click 'BackPocket Twin' on your desktop to start.
) else (
    echo.
    echo Note: Shortcut creation requires permissions.
    echo You can manually create a shortcut to Launch_BackPocket.vbs
)

echo.
pause