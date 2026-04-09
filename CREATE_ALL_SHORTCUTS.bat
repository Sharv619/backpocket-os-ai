@echo off
chcp 65001 >nul

echo ========================================
echo    BackPocket Desktop Shortcut Creator
echo ========================================
echo.

echo Creating shortcuts for:
echo   - BackPocket Twin (dashboard)
echo   - BackPocket AI (OpenCode)
echo.

REM Create Twin shortcut
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%USERPROFILE%\Desktop\BackPocket Twin.lnk'); $s.TargetPath = '%~dp0Launch_BackPocket.vbs'; $s.WorkingDirectory = '%~dp0'; $s.Description = 'Open BackPocket Dashboard'; $s.Save()"

REM Create OpenCode shortcut
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%USERPROFILE%\Desktop\BackPocket AI.lnk'); $s.TargetPath = '%~dp0LAUNCH_OPENCODE.bat'; $s.WorkingDirectory = '%~dp0'; $s.Description = 'Open BackPocket AI Assistant'; $s.Save()"

if exist "%USERPROFILE%\Desktop\BackPocket Twin.lnk" (
    echo.
    echo SUCCESS! Two shortcuts created on your desktop:
    echo   [1] BackPocket Twin - Opens the dashboard (for clients)
    echo   [2] BackPocket AI - Opens AI assistant
    echo.
    echo Double-click either to start!
) else (
    echo.
    echo Note: Could not create shortcuts automatically.
    echo You can manually drag the .bat/.vbs files to your desktop.
)

echo.
pause