' BackPocket OS One-Click Launcher
' Creates a silent background process - no terminal window

Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = WshShell.CurrentDirectory

' Run the batch file silently (0 = hide window, True = wait for completion)
' We'll just start it and let it run in background
CreateObject("WScript.Shell").Run """LAUNCH_BACKPOCKET_OS.bat""", 0, False

' Wait a moment for server to start
WScript.Sleep 4000

' Open the dashboard in default browser
CreateObject("WScript.Shell").Run "http://localhost:8000/dashboard", 1, False