@echo off
REM Nexus Service - Final Fix (Restart Required)
REM This script handles the "marked for deletion" state that requires a restart

echo ========================================
echo Nexus Service - Final Fix
echo ========================================
echo.
echo The service is stuck in "marked for deletion" state.
echo This requires a Windows restart to fully clear.
echo.
echo Options:
echo.
echo 1. Restart NOW and auto-install service
echo 2. Restart LATER (manual restart required)
echo 3. Cancel
echo.

set /p choice="Enter your choice (1-3): "

if "%choice%"=="1" (
    echo.
    echo Installing service before restart...
    C:\Nexus\venv\Scripts\python.exe nexus_service.py install 2>nul
    timeout /t 2
    
    echo.
    echo Scheduling restart in 10 seconds...
    timeout /t 10
    
    shutdown /r /t 0 /c "Nexus service cleanup and reinstall"
    
) else if "%choice%"=="2" (
    echo.
    echo Skipping restart.
    echo.
    echo To complete the fix manually:
    echo 1. Restart Windows
    echo 2. Run: Fix-NexusService-Admin.bat
    echo 3. Or run: net start NexusServer
    echo.
    pause
    
) else if "%choice%"=="3" (
    echo Cancelled.
    pause
    exit /b 1
    
) else (
    echo Invalid choice.
    pause
    exit /b 1
)
