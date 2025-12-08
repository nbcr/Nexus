# Windows Setup Guide for Nexus

This guide will help you set up the Nexus project on Windows with PostgreSQL and all required dependencies.

## Prerequisites

- Windows 10/11
- Administrator access
- Git (optional, for cloning)

## Step-by-Step Setup

### 1. Install PostgreSQL

1. Download PostgreSQL 15+ from https://www.postgresql.org/download/windows/
2. Run the installer
3. During installation:
   - Set superuser password (remember this!)
   - Default port: 5432
   - Enable pgAdmin4
4. Complete installation

**Test PostgreSQL:**
```powershell
psql -U postgres -c "SELECT version();"
```

### 2. Create Database and User

```powershell
# Run as Administrator
psql -U postgres

# In psql prompt:
CREATE USER nexus WITH PASSWORD 'nexus_password';
CREATE DATABASE nexus OWNER nexus;
GRANT ALL PRIVILEGES ON DATABASE nexus TO nexus;
\q
```

**Update .env file:**
```
DATABASE_URL=postgresql+asyncpg://nexus:nexus_password@localhost:5432/nexus
DATABASE_URL_SYNC=postgresql://nexus:nexus_password@localhost:5432/nexus
```

### 3. Install Python Requirements

```powershell
# Navigate to project directory
cd "c:\Users\Yot\Documents\GitHub Projects\Nexus\Nexus"

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 4. Initialize Database

```powershell
# Activate virtual environment (if not already)
.\venv\Scripts\Activate.ps1

# Run migrations
python -m alembic upgrade head

# (Alternative) Run initialization script
python scripts/init_db.py
```

### 5. Create .env File

Create `.env` in project root:

```
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
SECRET_KEY=your-secret-key-change-this-in-production

# Email (optional)
BREVO_API_KEY=your_api_key_here
ADMIN_EMAIL=admin@example.com
```

### 6. Start the Server

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run server
python run_server.py
```

Server will start at: http://127.0.0.1:8000

## Alternative: Use Batch Script for Automation

Use `run-windows.bat` to automate startup:

```powershell
# First run setup
.\setup-windows.bat

# Then start the server
.\run-windows.bat
```

## Troubleshooting

### PostgreSQL Connection Issues

```powershell
# Test PostgreSQL connection
psql -U nexus -d nexus -h localhost
```

### Python Virtual Environment Issues

```powershell
# Recreate virtual environment
Remove-Item venv -Recurse -Force
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### asyncpg on Windows

If asyncpg fails to install, try:

```powershell
pip install --only-binary :all: asyncpg
# or
pip install psycopg2-binary
```

### Port Already in Use

If port 8000 is already in use, change in `.env`:
```
API_PORT=8001
```

## Database Backup

```powershell
# Backup database
pg_dump -U nexus -d nexus > backup.sql

# Restore database
psql -U nexus -d nexus < backup.sql
```

## Next Steps

1. Access the application at http://127.0.0.1:8000
2. Create admin user if needed
3. Configure RSS feeds and article sources
4. Set up any additional environment variables

