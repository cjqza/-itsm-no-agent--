@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"
echo Restarting services...
call stop.bat
timeout /t 2 /nobreak >nul
call start.bat
