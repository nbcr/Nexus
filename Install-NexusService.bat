@echo off
REM Install Nexus Service as Administrator
REM This script must be run as Administrator

echo Checking for Administrator privileges...
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: This script must be run as Administrator
    echo Please right-click and select "Run as Administrator"
    pause
    exit /b 1
)

echo.
echo ========================================
echo Nexus Service Installer
echo ========================================
echo.

cd /d C:\Nexus

echo Step 1: Removing existing service (if any)...
C:\Nexus\venv\Scripts\python.exe nexus_service.py remove 2>nul
timeout /t 2 /nobreak

echo Step 2: Installing new service...
C:\Nexus\venv\Scripts\python.exe nexus_service.py install

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo SUCCESS: Service installed!
    echo ========================================
    echo.
    echo Service name: NexusServer
    echo Display name: Nexus AI News Platform
    echo.
    echo You can now:
    echo - Start the service: net start NexusServer
    echo - Stop the service: net stop NexusServer
    echo - View in Services.msc
    echo.
    pause
) else (
    echo.
    echo ERROR: Service installation failed
    pause
    exit /b 1
)
