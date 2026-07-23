@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"
echo.
echo ========================================
echo   Stopping all services...
echo ========================================
echo.

echo [1/5] Killing processes on port 8000 (Backend)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 " ^| findstr "LISTENING"') do (
    echo     Killing PID %%a
    taskkill /F /PID %%a >nul 2>&1
)

echo [2/5] Killing processes on port 5173 (Client)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173 " ^| findstr "LISTENING"') do (
    echo     Killing PID %%a
    taskkill /F /PID %%a >nul 2>&1
)

echo [3/5] Killing processes on port 5174 (Agent)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5174 " ^| findstr "LISTENING"') do (
    echo     Killing PID %%a
    taskkill /F /PID %%a >nul 2>&1
)

echo [4/5] Killing processes on port 5175 (Admin)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5175 " ^| findstr "LISTENING"') do (
    echo     Killing PID %%a
    taskkill /F /PID %%a >nul 2>&1
)

echo [5/5] Killing processes on port 5176 (OPS)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5176 " ^| findstr "LISTENING"') do (
    echo     Killing PID %%a
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo Cleaning up remaining dev processes...
for /f "tokens=2" %%a in ('wmic process where "CommandLine like '%%run.py%%' and Name='python.exe'" get ProcessId 2^>nul ^| findstr /r "[0-9]"') do (
    echo     Killing python run.py PID %%a
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=2" %%a in ('wmic process where "CommandLine like '%%vite%%' and Name='node.exe'" get ProcessId 2^>nul ^| findstr /r "[0-9]"') do (
    echo     Killing vite node PID %%a
    taskkill /F /PID %%a >nul 2>&1
)

timeout /t 1 /nobreak >nul

echo.
echo ========================================
echo   Verify ports are free:
echo ========================================
set "PORTS_FREE=1"
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 :5173 :5174 :5175 :5176" ^| findstr "LISTENING"') do (
    set "PORTS_FREE=0"
    echo   WARNING: Port still in use, PID %%a
)
if "%PORTS_FREE%"=="1" (
    echo   All ports are free!
)

echo.
echo ========================================
echo   All services stopped.
echo ========================================
pause
