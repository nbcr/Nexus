# Windows Server Startup Script for Nexus Project (PowerShell)
# Run: .\run-windows.ps1

$ErrorActionPreference = "Stop"

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  $Text" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Error {
    param([string]$Text)
    Write-Host "[ERROR] $Text" -ForegroundColor Red
}

function Write-Success {
    param([string]$Text)
    Write-Host "[OK] $Text" -ForegroundColor Green
}

Write-Header "Nexus Server Startup"

# Check virtual environment
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Error "Virtual environment not found"
    Write-Host "Please run setup-windows.ps1 first" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check .env file
if (-not (Test-Path ".env")) {
    Write-Host "[WARNING] .env file not found" -ForegroundColor Yellow
    Write-Host "Please create .env file with required settings" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"
Write-Success "Virtual environment activated"

# Start server
Write-Host ""
Write-Host "Starting Nexus server..." -ForegroundColor Yellow
Write-Host "Server will run at: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host ""

python run_server.py
