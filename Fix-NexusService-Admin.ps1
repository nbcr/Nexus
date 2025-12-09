#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Force remove and reinstall the Nexus service
    
.DESCRIPTION
    This script must be run as Administrator to properly remove and reinstall 
    the corrupted NexusServer service that's marked for deletion.
    
.EXAMPLE
    Right-click PowerShell → "Run as Administrator"
    cd C:\Nexus
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
    .\Fix-NexusService-Admin.ps1
#>

Write-Host "========================================" -ForegroundColor Green
Write-Host "Nexus Service - Force Reinstall (ADMIN)" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Check admin
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] 'Administrator')) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

Write-Host "[1/5] Stopping service..." -ForegroundColor Cyan
Stop-Service -Name "NexusServer" -Force -ErrorAction SilentlyContinue | Out-Null
Start-Sleep -Seconds 1

Write-Host "[2/5] Force-deleting service via WMI..." -ForegroundColor Cyan
try {
    Get-CimInstance -ClassName Win32_Service -Filter "Name='NexusServer'" | Remove-CimInstance -Force -ErrorAction Stop
    Write-Host "   Service deleted via WMI" -ForegroundColor Green
} catch {
    Write-Host "   WMI delete failed, trying SC..." -ForegroundColor Yellow
    & sc.exe delete NexusServer 2>&1 | Out-Null
}
Start-Sleep -Seconds 2

Write-Host "[3/5] Deleting registry entries..." -ForegroundColor Cyan
try {
    Remove-Item -Path "HKLM:\SYSTEM\CurrentControlSet\Services\NexusServer" -Force -Recurse -ErrorAction SilentlyContinue
    Write-Host "   Registry cleaned" -ForegroundColor Green
} catch {
    Write-Host "   Registry cleanup skipped" -ForegroundColor Yellow
}

Write-Host "[4/5] Verifying service is gone..." -ForegroundColor Cyan
try {
    $service = Get-Service -Name "NexusServer" -ErrorAction Stop
    Write-Host "   WARNING: Service still exists" -ForegroundColor Yellow
    Write-Host "   Forcing final deletion..." -ForegroundColor Yellow
    & cmd.exe /c "sc.exe config NexusServer binPath= `"`"C:\Nexus\venv\Scripts\pythonw.exe`" `"C:\Nexus\nexus_service.py`"`"" 2>&1 | Out-Null
    & cmd.exe /c "sc.exe delete NexusServer" 2>&1 | Out-Null
    Start-Sleep -Seconds 2
} catch {
    Write-Host "   Service successfully removed" -ForegroundColor Green
}

Write-Host "[5/5] Installing fresh service..." -ForegroundColor Cyan
cd C:\Nexus
& C:\Nexus\venv\Scripts\python.exe nexus_service.py install 2>&1 | Select-String "Service installed|error" -CaseSensitive

Start-Sleep -Seconds 1

try {
    $service = Get-Service -Name "NexusServer" -ErrorAction Stop
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "SUCCESS: Service installed!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Set to auto-start: Set-Service -Name NexusServer -StartupType Automatic"
    Write-Host "  2. Start service: Start-Service -Name NexusServer"
    Write-Host "  3. Check status: Get-Service -Name NexusServer"
    Write-Host "  4. View logs: Get-Content C:\Nexus\logs\service.log -Tail 50"
    Write-Host ""
} catch {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "ERROR: Service installation failed!" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Try running: C:\Nexus\venv\Scripts\python.exe nexus_service.py install" -ForegroundColor Yellow
    Write-Host ""
}
