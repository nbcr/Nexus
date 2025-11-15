#!/bin/bash
# Fix DATABASE_URL in .env file

echo "Checking .env file..."

if [ -f .env ]; then
    echo "Found .env file"
    
    # Check current DATABASE_URL
    current_url=$(grep "^DATABASE_URL=" .env | cut -d'=' -f2-)
    echo "Current DATABASE_URL: $current_url"
    
    # Fix if it's missing +asyncpg
    if [[ "$current_url" == postgresql://* ]] && [[ "$current_url" != *"+asyncpg"* ]]; then
        echo "Fixing DATABASE_URL to use asyncpg driver..."
        
        # Replace postgresql:// with postgresql+asyncpg://
        sed -i 's|^DATABASE_URL=postgresql://|DATABASE_URL=postgresql+asyncpg://|g' .env
        
        echo "✅ Fixed DATABASE_URL"
        echo "New URL:"
        grep "^DATABASE_URL=" .env
    else
        echo "DATABASE_URL already has correct driver or is not set"
    fi
else
    echo "❌ No .env file found!"
    echo "Please create a .env file with DATABASE_URL"
fi

echo ""
echo "Now restart the server with:"
echo "sudo systemctl restart nexus.service"
