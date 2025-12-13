@echo off
REM Platform-agnostic Nexus Server Launcher for Windows
REM This script handles dependency installation and server startup

setlocal enabledelayedexpansion

cd /d "%~dp0"

echo [STARTUP] Nexus Server Launcher for Windows
echo [STARTUP] Python: %PYTHON%
echo.

REM Run the startup wrapper
python start_server.py
exit /b %errorlevel%
