#!/bin/bash
# Check database connection and run migration

echo "Checking for database configuration..."

# Check if .env file exists
if [ -f .env ]; then
    echo "Found .env file, loading configuration..."
    source .env
fi

# If DATABASE_URL is not set, try common defaults
if [ -z "$DATABASE_URL" ]; then
    echo ""
    echo "DATABASE_URL not found in environment."
    echo "Please enter your PostgreSQL password for user 'nexus_user':"
    read -s DB_PASSWORD
    export DATABASE_URL="postgresql+asyncpg://nexus_user:${DB_PASSWORD}@localhost/nexus"
fi

echo ""
echo "Using database connection..."
echo "Running migration..."
python migrate_db.py
