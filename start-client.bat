@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0frontend-client"
title IT-Client
echo.
echo [START] User Client (Port 5173)
echo Directory: %cd%
echo.
npm run dev
echo.
echo ========================================
echo User Client Exited
echo ========================================
echo Possible reasons:
echo   1. Node.js not installed (node --version)
echo   2. Dependencies not installed (npm install)
echo   3. Port 5173 already in use
echo ========================================
pause
