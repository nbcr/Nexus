@echo off
REM Windows Database Setup Script for Nexus Project
REM This script creates the PostgreSQL database and user

setlocal enabledelayedexpansion

echo.
echo ========================================
echo  Nexus Database Setup
echo ========================================
echo.

REM Check if PostgreSQL is installed
psql --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] PostgreSQL not found
    echo Please install PostgreSQL from https://www.postgresql.org/download/windows/
    echo And add its bin directory to your system PATH
    pause
    exit /b 1
)

echo [1/3] PostgreSQL found
psql --version

REM Create database user and database
echo [2/3] Creating database user and database...
echo Please enter PostgreSQL superuser password:

psql -U postgres -c "CREATE USER nexus WITH PASSWORD 'nexus_password';" 2>nul
if errorlevel 1 (
    echo [WARNING] User 'nexus' may already exist
)

psql -U postgres -c "CREATE DATABASE nexus OWNER nexus;" 2>nul
if errorlevel 1 (
    echo [WARNING] Database 'nexus' may already exist
)

psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE nexus TO nexus;" 2>nul

REM Run migrations
echo [3/3] Running database migrations...
call venv\Scripts\activate.bat
python -m alembic upgrade head

echo.
echo ========================================
echo  Database Setup Complete!
echo ========================================
echo.
echo You can now start the server with:
echo   python run_server.py
echo.
pause
