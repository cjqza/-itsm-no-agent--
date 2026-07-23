@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0frontend-agent"
title IT-Agent
echo.
echo [START] Agent Client (Port 5174)
echo Directory: %cd%
echo.
npm run dev
echo.
echo ========================================
echo Agent Client Exited
echo ========================================
echo Possible reasons:
echo   1. Node.js not installed (node --version)
echo   2. Dependencies not installed (npm install)
echo   3. Port 5174 already in use
echo ========================================
pause
