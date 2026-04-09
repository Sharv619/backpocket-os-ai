@echo off
cd /d %USERPROFILE%
set HOME=%USERPROFILE%
start /b C:\Users\Cherry\cloudflared.exe --config C:\Users\Cherry\.cloudflared\config.yml tunnel run > C:\Users\Cherry\cloudflared.log 2>&1
echo Cloudflare Tunnel started for backpocket-os.backpocketsystem.io
timeout /t 3 /nobreak > nul
curl -s -o nul -w "%%{http_code}" https://backpocket-os.backpocketsystem.io/dashboard && echo SUCCESS: https://backpocket-os.backpocketsystem.io/dashboard || echo FAILED