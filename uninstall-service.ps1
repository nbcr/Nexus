#!/usr/bin/env powershell
# Uninstall Nexus service without reboot
# Requires Administrator privileges

param(
    [switch]$Force
)

$serviceName = "Nexus"

# Check admin privileges
$IsAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")

if (-not $IsAdmin) {
    Write-Host "ERROR: This command requires Administrator privileges" -ForegroundColor Red
    Write-Host "Please run PowerShell as Administrator" -ForegroundColor Yellow
    exit 1
}

Write-Host "Removing Nexus service..." -ForegroundColor Cyan

# Try to stop the service first
$service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
if ($service) {
    if ($service.Status -eq "Running") {
        Write-Host "Stopping service..." -ForegroundColor Yellow
        try {
            Stop-Service -Name $serviceName -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 1
        }
        catch {
            Write-Host "Service stop failed or already stopped" -ForegroundColor Gray
        }
    }
}

# Force delete using sc.exe (works immediately without reboot)
$output = sc.exe delete $serviceName 2>&1
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0 -or $output -match "marked for deletion") {
    Write-Host "`n✓ SUCCESS: Nexus service removed" -ForegroundColor Green
    Write-Host "No reboot required - service is gone" -ForegroundColor Green
    Write-Host "`nTo reinstall the service later, run:" -ForegroundColor Cyan
    Write-Host "`  `"C:\Program Files\Python312\python.exe`" C:\Nexus\nexus_service.py install" -ForegroundColor Gray
}
else {
    Write-Host "`n✗ ERROR: Failed to remove service" -ForegroundColor Red
    Write-Host "Output: $output" -ForegroundColor Red
    exit 1
}
