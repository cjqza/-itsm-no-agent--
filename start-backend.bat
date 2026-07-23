@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0backend"
title IT-Backend
echo.
echo [START] Backend Server (Port 8000)
echo Directory: %cd%
echo.
python run.py
echo.
echo ========================================
echo Backend Server Exited
echo ========================================
echo Possible reasons:
echo   1. Python not installed (python --version)
echo   2. Dependencies not installed (pip install -r requirements.txt)
echo   3. Port 8000 already in use
echo ========================================
pause
