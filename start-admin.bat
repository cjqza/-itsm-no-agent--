@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0frontend"
title IT-Admin
echo.
echo [START] Admin Panel (Port 5175)
echo Directory: %cd%
echo.
npm run dev -- --port 5175
echo.
echo ========================================
echo Admin Panel Exited
echo ========================================
echo Possible reasons:
echo   1. Node.js not installed (node --version)
echo   2. Dependencies not installed (npm install)
echo   3. Port 5175 already in use
echo ========================================
pause
