@echo off
REM Windows Setup Script for Nexus Project
REM Run this script to install all dependencies and set up the database

setlocal enabledelayedexpansion

echo.
echo ========================================
echo  Nexus Windows Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/5] Python found: 
python --version

REM Check if PostgreSQL is installed
psql --version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] PostgreSQL not found in PATH
    echo Please install PostgreSQL from https://www.postgresql.org/download/windows/
    echo After installation, add PostgreSQL bin directory to PATH
    pause
    exit /b 1
)

echo [2/5] PostgreSQL found: 
psql --version

REM Create virtual environment
if not exist "venv" (
    echo [3/5] Creating Python virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
) else (
    echo [3/5] Virtual environment already exists
)

REM Activate virtual environment
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

REM Install requirements
echo [4/5] Installing Python dependencies...
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo [5/5] Creating .env file...
    (
        echo # Environment
        echo ENVIRONMENT=development
        echo DEBUG=true
        echo.
        echo # API
        echo API_HOST=127.0.0.1
        echo API_PORT=8000
        echo.
        echo # Frontend
        echo FRONTEND_URL=http://localhost:8000
        echo.
        echo # Database
        echo DATABASE_URL=postgresql+asyncpg://nexus:nexus_password@localhost:5432/nexus
        echo DATABASE_URL_SYNC=postgresql://nexus:nexus_password@localhost:5432/nexus
        echo.
        echo # Security
        echo SECRET_KEY=dev-secret-key-change-in-production
        echo.
        echo # Email (optional^)
        echo BREVO_API_KEY=
        echo ADMIN_EMAIL=admin@example.com
    ) > .env
    echo .env file created. Please edit it with your settings.
) else (
    echo [5/5] .env file already exists
)

echo.
echo ========================================
echo  Setup Complete!
echo ========================================
echo.
echo Next steps:
echo.
echo 1. Create PostgreSQL database and user:
echo    - Run: setup-db-windows.bat
echo    OR manually run in psql:
echo    CREATE USER nexus WITH PASSWORD 'nexus_password';
echo    CREATE DATABASE nexus OWNER nexus;
echo    GRANT ALL PRIVILEGES ON DATABASE nexus TO nexus;
echo.
echo 2. Initialize database schema:
echo    python -m alembic upgrade head
echo.
echo 3. Start the server:
echo    python run_server.py
echo.
echo Server will run at: http://127.0.0.1:8000
echo.
pause
