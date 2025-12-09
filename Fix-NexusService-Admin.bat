@echo off
REM Self-elevate to administrator if not already elevated
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting Administrator privileges...
    powershell -Command "Start-Process 'cmd.exe' -ArgumentList '/c cd C:\Nexus && Fix-NexusService-Admin.bat' -Verb RunAs"
    exit /b
)

REM Now running as administrator
echo ========================================
echo Nexus Service - Force Reinstall (ADMIN)
echo ========================================
echo.

cd /d C:\Nexus

echo [1/5] Stopping service...
taskkill /F /IM python.exe 2>nul
net stop NexusServer 2>nul
timeout /t 1 /nobreak

echo [2/5] Force-deleting service...
sc delete NexusServer 2>nul
wmic service where name="NexusServer" delete 2>nul
timeout /t 2 /nobreak

echo [3/5] Deleting registry entries...
reg delete "HKLM\SYSTEM\CurrentControlSet\Services\NexusServer" /f 2>nul
timeout /t 1 /nobreak

echo [4/5] Verifying service is gone...
sc query NexusServer >nul 2>&1
if %errorlevel% equ 0 (
    echo   WARNING: Service still exists
    sc delete NexusServer /f 2>nul
    timeout /t 2 /nobreak
) else (
    echo   Service successfully removed
)

echo [5/5] Installing fresh service...
C:\Nexus\venv\Scripts\python.exe nexus_service.py install

timeout /t 2 /nobreak

sc query NexusServer >nul 2>&1
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
    echo   1. Set to auto-start: sc config NexusServer start=auto
    echo   2. Start service: net start NexusServer
    echo   3. Check status: sc query NexusServer
    echo.
) else (
    echo.
    echo ========================================
    echo ERROR: Service installation failed!
    echo ========================================
    echo.
    echo Try running manually:
    echo   C:\Nexus\venv\Scripts\python.exe nexus_service.py install
    echo.
)

pause
