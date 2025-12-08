# Windows Database Setup Script for Nexus Project (PowerShell)
# Run: .\setup-db-windows.ps1

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

function Write-Success {
    param([string]$Text)
    Write-Host "[OK] $Text" -ForegroundColor Green
}

Write-Header "Nexus Database Setup"

# Check PostgreSQL
Write-Step 1 3 "Checking PostgreSQL installation..."
try {
    $psqlVersion = psql --version 2>&1
    Write-Success "PostgreSQL found: $psqlVersion"
}
catch {
    Write-Host "[ERROR] PostgreSQL not found in PATH" -ForegroundColor Red
    Write-Host "Install from: https://www.postgresql.org/download/windows/" -ForegroundColor Yellow
    Write-Host "And add bin directory to your system PATH" -ForegroundColor Yellow
    exit 1
}

# Create database user and database
Write-Step 2 3 "Creating PostgreSQL user and database..."

Write-Host "Note: This script uses default password 'nexus_password'" -ForegroundColor Cyan
Write-Host "You will be prompted for PostgreSQL superuser password" -ForegroundColor Cyan
Write-Host ""

try {
    # Create user
    Write-Host "Creating user 'nexus'..." -ForegroundColor Gray
    psql -U postgres -c "CREATE USER nexus WITH PASSWORD 'nexus_password';" 2>&1 | ForEach-Object {
        if ($_ -notmatch "already exists") {
            Write-Host $_
        }
    }
    
    # Create database
    Write-Host "Creating database 'nexus'..." -ForegroundColor Gray
    psql -U postgres -c "CREATE DATABASE nexus OWNER nexus;" 2>&1 | ForEach-Object {
        if ($_ -notmatch "already exists") {
            Write-Host $_
        }
    }
    
    # Grant privileges
    Write-Host "Granting privileges..." -ForegroundColor Gray
    psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE nexus TO nexus;" 2>&1 | Out-Null
    
    Write-Success "Database setup completed"
}
catch {
    Write-Host "[WARNING] Database setup had issues - it may already exist" -ForegroundColor Yellow
}

# Run migrations
Write-Step 3 3 "Running database migrations..."

# Activate virtual environment
if (Test-Path ".\venv\Scripts\Activate.ps1") {
    & ".\venv\Scripts\Activate.ps1"
}
else {
    Write-Host "[WARNING] Virtual environment not found" -ForegroundColor Yellow
    Write-Host "Run setup-windows.ps1 first" -ForegroundColor Yellow
    exit 1
}

try {
    python -m alembic upgrade head
    Write-Success "Database migrations completed"
}
catch {
    Write-Host "[WARNING] Migrations may have issues" -ForegroundColor Yellow
    Write-Host "Try running manually: python -m alembic upgrade head" -ForegroundColor Gray
}

Write-Header "Database Setup Complete!"
Write-Host "You can now start the server with:" -ForegroundColor Cyan
Write-Host "  python run_server.py" -ForegroundColor Gray
Write-Host ""
