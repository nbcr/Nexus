"""
Create an admin user for the Nexus admin panel

Usage: python create_admin.py <username> <email> <password>
"""
import sys
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models import User
from app.core.auth import get_password_hash
from app.core.config import settings

async def create_admin_user(username: str, email: str, password: str):
    """Create a new admin user"""
    
    # Create async engine
    engine = create_async_engine(
        settings.database_url,
        echo=False
    )
    
    # Create session
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        # Check if user already exists
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.username == username)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"❌ User '{username}' already exists!")
            
            # Ask if we should promote to admin
            response = input(f"Promote existing user to admin? (y/n): ")
            if response.lower() == 'y':
                existing_user.is_admin = True
                await session.commit()
                print(f"✅ User '{username}' promoted to admin!")
            return
        
        # Create new admin user
        print(f"[DEBUG] Password: {repr(password)}")
        print(f"[DEBUG] Password byte length: {len(password.encode('utf-8'))}")
        hashed_password = get_password_hash(password)
        
        new_user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_admin=True,
            is_active=True
        )
        
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        
        print(f"✅ Admin user created successfully!")
        print(f"   Username: {new_user.username}")
        print(f"   Email: {new_user.email}")
        print(f"   Admin: {new_user.is_admin}")
        print(f"   ID: {new_user.id}")
        print()
        print(f"🔒 You can now access the admin panel at:")
        print(f"   https://nexus.comdat.ca/static/admin.html")
        print()
        print(f"⚠️  Keep your admin credentials secure!")
    
    await engine.dispose()

async def list_admins():
    """List all admin users"""
    
    engine = create_async_engine(
        settings.database_url,
        echo=False
    )
    
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.is_admin == True)
        )
        admins = result.scalars().all()
        
        if not admins:
            print("No admin users found.")
        else:
            print(f"Found {len(admins)} admin user(s):")
            print()
            for admin in admins:
                print(f"  • {admin.username} ({admin.email}) - ID: {admin.id}")
    
    await engine.dispose()

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Create admin:  python create_admin.py <username> <email> <password>")
        print("  List admins:   python create_admin.py --list")
        sys.exit(1)
    
    if sys.argv[1] == '--list':
        asyncio.run(list_admins())
    elif len(sys.argv) == 4:
        username = sys.argv[1]
        email = sys.argv[2]
        password = sys.argv[3]
        
        if len(password) < 8:
            print("❌ Password must be at least 8 characters long!")
            sys.exit(1)
        
        asyncio.run(create_admin_user(username, email, password))
    else:
        print("❌ Invalid arguments!")
        print("Usage:")
        print("  Create admin:  python create_admin.py <username> <email> <password>")
        print("  List admins:   python create_admin.py --list")
        sys.exit(1)

if __name__ == "__main__":
    main()
