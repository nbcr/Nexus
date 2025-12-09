@echo off
setlocal enabledelayedexpansion

REM Run as administrator check
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo This script must be run as Administrator!
    pause
    exit /b 1
)

echo Installing Nexus services...

REM Install PostgreSQL (already running as service - just verify)
echo Checking PostgreSQL service...
sc query postgresql-x64-18 >nul 2>&1
if %errorLevel% equ 0 (
    echo PostgreSQL service found
) else (
    echo PostgreSQL service not found - install via EnterpriseDB
)

REM Install FastAPI as service using NSSM
echo Installing NSSM...
choco install nssm -y

REM Install FastAPI Nexus service
echo Installing FastAPI Nexus service...

REM Install Nexus FastAPI service
nssm install NexusAPI "C:\Nexus\venv\Scripts\python.exe" "C:\Nexus\run_server.py"
nssm set NexusAPI AppDirectory "C:\Nexus"
nssm set NexusAPI AppStdout "C:\Nexus\logs\nexus_service.log"
nssm set NexusAPI AppStderr "C:\Nexus\logs\nexus_service_error.log"
nssm set NexusAPI Start SERVICE_AUTO_START

REM Install Nginx service
echo Installing Nginx service...
nssm install NexusNginx "C:\ProgramData\chocolatey\lib\nginx\tools\nginx-1.29.3\nginx.exe" "-c C:\Nexus\nginx\local.conf"
nssm set NexusNginx AppDirectory "C:\Nexus"
nssm set NexusNginx AppStdout "C:\Nexus\logs\nginx_service.log"
nssm set NexusNginx AppStderr "C:\Nexus\logs\nginx_service_error.log"
nssm set NexusNginx Start SERVICE_AUTO_START

REM Start services
echo Starting services...
net start NexusAPI
net start NexusNginx

echo Done! All services installed and started.
echo Check Services (services.msc) to verify.
pause
