#!/bin/bash
# Nexus Phase 2: Database Setup Guide

echo "=== Nexus Phase 2: Database Setup ==="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. PostgreSQL Installation
echo -e "${YELLOW}Step 1: Installing PostgreSQL...${NC}"
sudo apt update
sudo apt install -y postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
echo -e "${GREEN}✓ PostgreSQL installed${NC}"
echo ""

# 2. Database Creation
echo -e "${YELLOW}Step 2: Creating database and user...${NC}"
echo "Please enter a secure password for the database user:"
read -s DB_PASSWORD

sudo -u postgres psql << EOF
CREATE DATABASE nexus;
CREATE USER nexus_user WITH PASSWORD '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON DATABASE nexus TO nexus_user;
\c nexus
GRANT ALL ON SCHEMA public TO nexus_user;
EOF

echo -e "${GREEN}✓ Database created${NC}"
echo ""

# 3. Update .env file
echo -e "${YELLOW}Step 3: Configuring environment...${NC}"
cd /home/nexus/nexus

cat >> .env << EOF

# Phase 2: Database Configuration
DATABASE_URL=postgresql+asyncpg://nexus_user:${DB_PASSWORD}@localhost/nexus
DATABASE_URL_SYNC=postgresql://nexus_user:${DB_PASSWORD}@localhost/nexus
EOF

echo -e "${GREEN}✓ Environment configured${NC}"
echo ""

# 4. Install Python dependencies
echo -e "${YELLOW}Step 4: Installing Python packages...${NC}"
source venv/bin/activate

pip install sqlalchemy==2.0.23 asyncpg==0.29.0 alembic==1.13.0 python-dateutil==2.8.2

echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# 5. Initialize database tables
echo -e "${YELLOW}Step 5: Creating database tables...${NC}"
python scripts/init_db.py

echo -e "${GREEN}✓ Tables created${NC}"
echo ""

# 6. Test database connection
echo -e "${YELLOW}Step 6: Testing database connection...${NC}"
python << PYEOF
import asyncio
from app.database import engine
from sqlalchemy import text

async def test_connection():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        print("✓ Database connection successful!")
        
asyncio.run(test_connection())
PYEOF

echo ""
echo -e "${GREEN}=== Phase 2 Setup Complete ===${NC}"
echo ""
echo "Next steps:"
echo "1. Restart Nexus API: sudo systemctl restart nexus"
echo "2. Test new endpoints: curl http://localhost:8000/api/v1/topics"
echo "3. Check logs: tail -f /home/nexus/nexus/logs/error.log"
echo ""
echo "Useful commands:"
echo "  - Connect to DB: psql -U nexus_user -d nexus"
echo "  - List tables: psql -U nexus_user -d nexus -c '\dt'"
echo "  - View users: psql -U nexus_user -d nexus -c 'SELECT * FROM users;'"
