@echo off
REM Nexus Service Installer - Run as Administrator
REM This script installs/starts/stops the Nexus service

setlocal enabledelayedexpansion

cd /d C:\Nexus

if "%1"=="" (
    echo Usage: nexus_service.bat [install^|start^|stop^|restart^|remove]
    echo.
    echo Examples:
    echo   nexus_service.bat install  - Install service
    echo   nexus_service.bat start    - Start service
    echo   nexus_service.bat stop     - Stop service
    echo   nexus_service.bat restart  - Restart service
    echo   nexus_service.bat remove   - Remove service
    exit /b 1
)

REM Check for admin privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: This script must be run as Administrator
    pause
    exit /b 1
)

REM Run the service command
C:\Nexus\venv\Scripts\python.exe nexus_service.py %1

if %errorlevel% equ 0 (
    echo.
    echo Service command completed successfully
) else (
    echo.
    echo ERROR: Service command failed
    pause
)

exit /b %errorlevel%
