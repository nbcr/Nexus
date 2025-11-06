# Nexus application package
import asyncio
from app.services.content_refresh import start_periodic_refresh

async def start_background_tasks():
    """Start background tasks when application starts"""
    try:
        # Start periodic content refresh in background
        asyncio.create_task(start_periodic_refresh())
        print("✅ Background tasks started")
    except Exception as e:
        print(f"❌ Failed to start background tasks: {e}")
