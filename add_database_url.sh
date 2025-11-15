#!/bin/bash
# Add DATABASE_URL to .env file

echo "Adding DATABASE_URL to .env..."

# Prompt for database password
echo "Please enter your PostgreSQL password for user 'nexus_user':"
read -s DB_PASSWORD

# Append to .env
cat >> .env << EOF

# Database Configuration
DATABASE_URL=postgresql+asyncpg://nexus_user:${DB_PASSWORD}@localhost:5432/nexus
DATABASE_URL_SYNC=postgresql://nexus_user:${DB_PASSWORD}@localhost:5432/nexus
EOF

echo ""
echo "✅ Added DATABASE_URL to .env"
echo ""
echo "Now run: ./update_service.sh"
