#!/bin/bash
# Manually fix the .env file

echo "Checking .env file..."
echo "Current DATABASE_URL lines:"
grep -i "database" .env

echo ""
echo "Fixing all postgresql:// to postgresql+asyncpg://"

# Use a more aggressive replacement
sed -i.bak 's/postgresql:\/\//postgresql+asyncpg:\/\//g' .env

echo ""
echo "New DATABASE_URL:"
grep "DATABASE_URL" .env | head -1

echo ""
echo "Done! Now run: ./update_service.sh"
