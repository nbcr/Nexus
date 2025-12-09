@echo off
REM Clean up corrupted NexusServer service and reinstall fresh
REM This script MUST be run as Administrator

echo Checking for Administrator privileges...
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: This script must be run as Administrator
    echo.
    echo To run as Administrator:
    echo 1. Right-click Command Prompt or PowerShell
    echo 2. Select "Run as Administrator"
    echo 3. Navigate to C:\Nexus
    echo 4. Run: cleanup_service.bat
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Nexus Service Cleanup & Reinstall
echo ========================================
echo.

cd /d C:\Nexus

echo Step 1: Stopping service (if running)...
net stop NexusServer 2>nul
timeout /t 2 /nobreak

echo Step 2: Removing service registry entries...
sc delete NexusServer >nul 2>&1

echo Step 3: Waiting for cleanup...
timeout /t 3 /nobreak

echo Step 4: Verifying service is gone...
sc query NexusServer >nul 2>&1
if %errorlevel% equ 0 (
    echo WARNING: Service still exists, attempting force delete...
    wmic service where name="NexusServer" delete >nul 2>&1
    timeout /t 2 /nobreak
)

echo Step 5: Installing fresh service...
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
    echo Next steps:
    echo 1. Start the service: net start NexusServer
    echo 2. Or right-click Services.msc and find "Nexus AI News Platform"
    echo 3. Check logs: C:\Nexus\logs\service.log
    echo.
    pause
) else (
    echo.
    echo ERROR: Service installation failed
    echo Please check the error above and try again
    pause
    exit /b 1
)
