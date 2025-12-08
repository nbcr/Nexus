@echo off
REM Windows Server Startup Script for Nexus Project

setlocal enabledelayedexpansion

echo.
echo ========================================
echo  Nexus Server Startup
echo ========================================
echo.

REM Check virtual environment
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found
    echo Please run setup-windows.bat first
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if .env exists
if not exist ".env" (
    echo [WARNING] .env file not found
    echo Please create .env file with required settings
    pause
    exit /b 1
)

REM Start server
echo [1/1] Starting Nexus server...
echo.
python run_server.py

pause
