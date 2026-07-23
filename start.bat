@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"
title IT Asset Repair System

echo ========================================
echo   IT Asset Repair System - Starting
echo ========================================
echo.

:: First stop any existing services
echo [0/5] Cleaning up old processes...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 :5173 :5174 :5175 :5176" ^| findstr "LISTENING"') do taskkill /F /PID %%a >nul 2>&1
timeout /t 2 /nobreak >nul

:: Start backend
echo [1/5] Starting Backend (Port 8000)...
start "IT-Backend" cmd /k "chcp 65001 >nul 2>&1 && cd /d %~dp0backend && title IT-Backend && echo [START] Backend Server (Port 8000) && echo Directory: %cd% && echo. && python run.py"
timeout /t 5 /nobreak >nul

:: Check backend
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo     [!] Backend not ready yet, waiting...
    timeout /t 5 /nobreak >nul
) else (
    echo     [OK] Backend is running
)

:: Start user client
echo [2/5] Starting User Client (Port 5173)...
start "IT-Client" cmd /k "chcp 65001 >nul 2>&1 && cd /d %~dp0frontend-client && title IT-Client && echo [START] User Client (Port 5173) && echo Directory: %cd% && echo. && npm run dev"
timeout /t 3 /nobreak >nul

:: Start agent client
echo [3/5] Starting Agent Client (Port 5174)...
start "IT-Agent" cmd /k "chcp 65001 >nul 2>&1 && cd /d %~dp0frontend-agent && title IT-Agent && echo [START] Agent Client (Port 5174) && echo Directory: %cd% && echo. && npm run dev"
timeout /t 3 /nobreak >nul

:: Start admin panel
echo [4/5] Starting Admin Panel (Port 5175)...
start "IT-Admin" cmd /k "chcp 65001 >nul 2>&1 && cd /d %~dp0frontend && title IT-Admin && echo [START] Admin Panel (Port 5175) && echo Directory: %cd% && echo. && npm run dev -- --port 5175"
timeout /t 3 /nobreak >nul

:: Start OPS panel
echo [5/5] Starting OPS Panel (Port 5176)...
start "IT-OPS" cmd /k "chcp 65001 >nul 2>&1 && cd /d %~dp0frontend-ops && title IT-OPS && echo [START] OPS Panel (Port 5176) && echo Directory: %cd% && echo. && npm run dev"
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo   All services started!
echo   User Service Desk: http://localhost:5173
echo   ITSM (Agent):     http://localhost:5174
echo   Admin Panel:      http://localhost:5175
echo   OPS Statistics:   http://localhost:5176
echo   API Docs:         http://localhost:8000/docs
echo ========================================
echo.
echo Press any key to open browsers...
pause >nul

start http://localhost:5173
start http://localhost:5174
start http://localhost:5176
