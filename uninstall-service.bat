@echo off
REM Uninstall Nexus service without reboot
REM Requires Administrator privileges

echo Removing Nexus service...

REM Force delete the service immediately
sc.exe delete Nexus

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] Nexus service removed immediately
    echo No reboot required
) else (
    echo.
    echo [ERROR] Failed to remove service
    echo Make sure you're running as Administrator
    exit /b 1
)
