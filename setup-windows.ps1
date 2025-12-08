# Windows Setup Script for Nexus Project (PowerShell)
# Run: .\setup-windows.ps1

param(
    [switch]$SkipVenv = $false,
    [switch]$SkipDeps = $false,
    [switch]$SkipDb = $false
)

$ErrorActionPreference = "Stop"

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  $Text" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Step {
    param(
        [int]$Step,
        [int]$Total,
        [string]$Text
    )
    Write-Host "[$Step/$Total] $Text" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Text)
    Write-Host "[ERROR] $Text" -ForegroundColor Red
}

function Write-Success {
    param([string]$Text)
    Write-Host "[OK] $Text" -ForegroundColor Green
}

Write-Header "Nexus Windows Setup (PowerShell)"

# Check Python
Write-Step 1 4 "Checking Python installation..."
try {
    $pythonVersion = python --version 2>&1
    Write-Success "Python found: $pythonVersion"
}
catch {
    Write-Error "Python is not installed or not in PATH"
    Write-Host "Install from: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Check PostgreSQL
Write-Step 2 4 "Checking PostgreSQL installation..."
try {
    $psqlVersion = psql --version 2>&1
    Write-Success "PostgreSQL found: $psqlVersion"
}
catch {
    Write-Host "[WARNING] PostgreSQL not found in PATH" -ForegroundColor Yellow
    Write-Host "Install from: https://www.postgresql.org/download/windows/" -ForegroundColor Yellow
}

# Create virtual environment
if (-not $SkipVenv) {
    Write-Step 3 4 "Setting up Python virtual environment..."
    
    if (Test-Path "venv") {
        Write-Host "Virtual environment already exists" -ForegroundColor Gray
    }
    else {
        python -m venv venv
        Write-Success "Virtual environment created"
    }
    
    # Activate virtual environment
    & ".\venv\Scripts\Activate.ps1"
    Write-Success "Virtual environment activated"
}

# Install dependencies
if (-not $SkipDeps) {
    Write-Step 4 4 "Installing Python dependencies..."
    
    pip install --upgrade pip setuptools wheel | Out-Null
    pip install -r requirements.txt
    Write-Success "Dependencies installed"
}

# Create .env file
if (-not (Test-Path ".env")) {
    Write-Host ""
    Write-Host "Creating .env file..." -ForegroundColor Yellow
    
    $envContent = @"
# Environment
ENVIRONMENT=development
DEBUG=true

# API
API_HOST=127.0.0.1
API_PORT=8000

# Frontend
FRONTEND_URL=http://localhost:8000

# Database
DATABASE_URL=postgresql+asyncpg://nexus:nexus_password@localhost:5432/nexus
DATABASE_URL_SYNC=postgresql://nexus:nexus_password@localhost:5432/nexus

# Security
SECRET_KEY=dev-secret-key-change-in-production

# Email (optional)
BREVO_API_KEY=
ADMIN_EMAIL=admin@example.com
"@
    
    Set-Content -Path ".env" -Value $envContent
    Write-Success ".env file created"
}

Write-Header "Setup Complete!"
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Set up PostgreSQL database:" -ForegroundColor White
Write-Host "   .\setup-db-windows.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Initialize database schema:" -ForegroundColor White
Write-Host "   .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "   python -m alembic upgrade head" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Start the server:" -ForegroundColor White
Write-Host "   python run_server.py" -ForegroundColor Gray
Write-Host ""
Write-Host "Server will run at: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host ""
