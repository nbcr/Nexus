import asyncio
import fcntl
from datetime import datetime, timedelta, timezone
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession  # type: ignore
from sqlalchemy import select  # pyright: ignore[reportMissingImports]

from app.db import AsyncSessionLocal
from app.services.trending import trending_service

# Lock file to prevent concurrent refreshes
LOCK_FILE = Path("/tmp/nexus_content_refresh.lock")


class ContentRefreshService:
    def __init__(self):
        self.last_refresh = None

    async def should_refresh_content(self, db: AsyncSession) -> bool:
        """Check if we should refresh content (every 15 minutes for trends)"""
        from app.models import ContentItem

        if not self.last_refresh:
            # Check the latest trending content in database
            result = await db.execute(
                select(ContentItem).order_by(ContentItem.created_at.desc()).limit(1)
            )
            latest_content = result.scalar_one_or_none()

            if not latest_content:
                return True  # No content yet

            self.last_refresh = latest_content.created_at

        # Refresh if last refresh was more than 15 minutes ago
        refresh_time = datetime.now(timezone.utc) - timedelta(minutes=15)
        return self.last_refresh < refresh_time

    async def refresh_content_if_needed(self):
        """Refresh trending content if it's stale"""
        # Try to acquire lock (non-blocking)
        try:
            lock_fd = open(LOCK_FILE, "w")
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            print("⏭️  Content refresh already running (locked by another process)")
            return 0

        try:
            async with AsyncSessionLocal() as db:
                if await self.should_refresh_content(db):
                    print("🔄 Refreshing trending content from Google Trends...")
                    topics = await trending_service.save_trends_to_database(db)
                    count = len(topics)  # Get count from list of topics
                    self.last_refresh = datetime.now(timezone.utc)
                    print(
                        f"✅ Trending content refresh completed! Added {count} new items"
                    )

                    # Notify connected clients about new content
                    try:
                        from app.api.v1.routes.websocket import notify_new_content

                        await notify_new_content(count=count)
                    except Exception as e:
                        print(f"⚠️  Failed to notify clients about new content: {e}")

                    return count
                else:
                    print("⏭️  Content is still fresh, skipping refresh")
                    return 0
        finally:
            # Release lock
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
            lock_fd.close()


# Global instance
content_refresh = ContentRefreshService()


async def start_periodic_refresh():
    """Start periodic content refresh"""
    while True:
        try:
            await content_refresh.refresh_content_if_needed()
        except Exception as e:
            print(f"❌ Error in periodic refresh: {e}")

        # Wait 1 hour between checks
        await asyncio.sleep(3600)
