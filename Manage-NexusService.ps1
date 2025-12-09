# Nexus Service Manager (PowerShell)
# This script manages the Nexus Windows service
# Run as Administrator for install/uninstall operations

param(
    [ValidateSet("install", "start", "stop", "restart", "status", "remove")]
    [string]$Command = "status"
)

$NexusRoot = "C:\Nexus"
$PythonExe = "$NexusRoot\venv\Scripts\python.exe"
$ServiceScript = "$NexusRoot\nexus_service.py"

# Check admin privileges
$IsAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")

if (-not $IsAdmin -and ($Command -in @("install", "remove"))) {
    Write-Host "ERROR: This command requires Administrator privileges" -ForegroundColor Red
    Write-Host "Please run PowerShell as Administrator" -ForegroundColor Yellow
    exit 1
}

Write-Host "=" * 80
Write-Host "Nexus Service Manager"
Write-Host "=" * 80

Set-Location $NexusRoot

switch ($Command) {
    "install" {
        Write-Host "Installing Nexus service..."
        & $PythonExe $ServiceScript install
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Service installed successfully" -ForegroundColor Green
            Write-Host "Starting service..." -ForegroundColor Cyan
            & $PythonExe $ServiceScript start
        }
    }
    
    "start" {
        Write-Host "Starting Nexus service..."
        & $PythonExe $ServiceScript start
        Start-Sleep -Seconds 2
        $Service = Get-Service -Name "NexusServer" -ErrorAction SilentlyContinue
        if ($Service.Status -eq "Running") {
            Write-Host "Service started successfully" -ForegroundColor Green
        }
    }
    
    "stop" {
        Write-Host "Stopping Nexus service..."
        & $PythonExe $ServiceScript stop
        Start-Sleep -Seconds 2
        $Service = Get-Service -Name "NexusServer" -ErrorAction SilentlyContinue
        if ($Service.Status -eq "Stopped") {
            Write-Host "Service stopped successfully" -ForegroundColor Green
        }
    }
    
    "restart" {
        Write-Host "Restarting Nexus service..."
        & $PythonExe $ServiceScript stop
        Start-Sleep -Seconds 2
        & $PythonExe $ServiceScript start
        Start-Sleep -Seconds 2
        $Service = Get-Service -Name "NexusServer" -ErrorAction SilentlyContinue
        if ($Service.Status -eq "Running") {
            Write-Host "Service restarted successfully" -ForegroundColor Green
        }
    }
    
    "status" {
        $Service = Get-Service -Name "NexusServer" -ErrorAction SilentlyContinue
        if ($null -eq $Service) {
            Write-Host "Service is NOT installed" -ForegroundColor Red
        } else {
            $StatusColor = if ($Service.Status -eq "Running") { "Green" } else { "Red" }
            Write-Host "Service Status: $($Service.Status)" -ForegroundColor $StatusColor
            Write-Host "Display Name: $($Service.DisplayName)"
            Write-Host "Startup Type: $($Service.StartType)"
        }
    }
    
    "remove" {
        Write-Host "Removing Nexus service..."
        $Service = Get-Service -Name "NexusServer" -ErrorAction SilentlyContinue
        if ($Service.Status -eq "Running") {
            Write-Host "Stopping service first..."
            & $PythonExe $ServiceScript stop
            Start-Sleep -Seconds 2
        }
        & $PythonExe $ServiceScript remove
        Write-Host "Service removed" -ForegroundColor Green
    }
}

Write-Host "=" * 80
