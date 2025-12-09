@echo off
REM Clean up corrupted NexusServer service and reinstall
REM Must run as Administrator

echo Checking for Administrator privileges...
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: This script must be run as Administrator
    pause
    exit /b 1
)

setlocal enabledelayedexpansion

echo.
echo ========================================
echo Nexus Service Cleanup and Reinstall
echo ========================================
echo.

cd /d C:\Nexus

echo Step 1: Stopping service...
net stop NexusServer 2>nul
timeout /t 1 /nobreak

echo Step 2: Removing corrupted service registry entries...
for /f "tokens=*" %%A in ('sc query NexusServer ^| find /i "NexusServer"') do (
    echo Found service, attempting removal...
)

REM Delete via registry for corrupted services
reg delete "HKLM\SYSTEM\CurrentControlSet\Services\NexusServer" /f 2>nul

echo Step 3: Waiting for registry update...
timeout /t 2 /nobreak

echo Step 4: Installing fresh service...
C:\Nexus\venv\Scripts\python.exe nexus_service.py install

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo SUCCESS: Service reinstalled!
    echo ========================================
    echo.
    echo You can now start the service:
    echo   net start NexusServer
    echo.
) else (
    echo.
    echo ERROR: Service installation failed
    echo.
)

pause
