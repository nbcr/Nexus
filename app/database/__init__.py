from .database import get_db
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Load environment variables from .env file
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("Warning: DATABASE_URL environment variable not set")
    # Set a default for testing
    DATABASE_URL = "postgresql+asyncpg://nexus_user:password@localhost:5432/nexus"

print(f"Using DATABASE_URL: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL}")

# Create engine and session
engine = create_async_engine(DATABASE_URL, echo=True)
Base = declarative_base()

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)
