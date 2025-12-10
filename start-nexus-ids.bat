@echo off
REM Nexus Server with Intrusion Detection
REM This script starts the FastAPI server with integrated IDS monitoring

setlocal enabledelayedexpansion

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Virtual environment not found. Please run setup-windows.bat first.
    pause
    exit /b 1
)

REM Load environment variables from .env
for /f "tokens=*" %%i in ('type .env ^| find /v "^#" ^| find "="') do (
    for /f "tokens=1* delims==" %%a in ("%%i") do (
        set "%%a=%%b"
    )
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Start the server
echo.
echo ========================================
echo   Nexus Server with IDS
echo ========================================
echo.
echo Starting FastAPI server with intrusion detection...
echo API will be available at: http://localhost:8000
echo Logs: server.log and intrusion_detector.log
echo.
echo Press Ctrl+C to stop the server
echo.

python run_server.py

pause
