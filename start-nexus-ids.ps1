#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Nexus Server with Intrusion Detection Service
.DESCRIPTION
    Starts the FastAPI server with integrated IDS monitoring for blocking malicious IPs via Cloudflare
#>

$ErrorActionPreference = "Stop"

# Get script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Nexus Server with IDS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check virtual environment
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "Virtual environment not found." -ForegroundColor Red
    Write-Host "Please run: setup-windows.ps1" -ForegroundColor Yellow
    exit 1
}

# Load environment variables from .env
if (Test-Path ".env") {
    Write-Host "Loading environment variables from .env..." -ForegroundColor Gray
    Get-Content .env | Where-Object { $_ -match '^\w+=' } | ForEach-Object {
        $key, $val = $_ -split '=', 2
        [Environment]::SetEnvironmentVariable($key, $val, 'Process')
    }
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Gray
& ".\venv\Scripts\Activate.ps1"

Write-Host ""
Write-Host "Starting FastAPI server with intrusion detection..." -ForegroundColor Green
Write-Host "API will be available at: http://localhost:8000" -ForegroundColor Gray
Write-Host "Logs:" -ForegroundColor Gray
Write-Host "  - Server: server.log" -ForegroundColor Gray
Write-Host "  - IDS: intrusion_detector.log" -ForegroundColor Gray
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Run the server
python run_server.py
