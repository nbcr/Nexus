#!/bin/bash
# Fix DATABASE_URL in .env to use asyncpg driver

echo "Fixing DATABASE_URL in .env file..."

if [[ ! -f .env ]]; then
    echo "ERROR: No .env file found!" >&2
    exit 1
fi

# Backup .env
cp .env .env.backup
echo "✅ Backed up .env to .env.backup"

# Replace postgresql:// with postgresql+asyncpg:// (handles spaces and comments)
sed -i 's|postgresql://|postgresql+asyncpg://|g' .env

echo "✅ Fixed DATABASE_URL"
echo ""
echo "New DATABASE_URL:"
grep "^DATABASE_URL=" .env | sed 's/:[^:]*@/:***@/g'  # Hide password

echo ""
echo "Now run ./update_service.sh to update the systemd service"
