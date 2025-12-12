import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession  # type: ignore
from sqlalchemy import select  # pyright: ignore[reportMissingImports]

from app.db import AsyncSessionLocal
from app.services.trending import trending_service

# Lock file to prevent concurrent refreshes (Windows-safe)
if sys.platform == "win32":
    LOCK_FILE = Path(
        os.path.join(os.path.expanduser("~"), ".nexus_content_refresh.lock")
    )
else:
    LOCK_FILE = Path("/tmp/nexus_content_refresh.lock")


class ContentRefreshService:
    LOCK_MESSAGE = ">> Content refresh already running (locked by another process)"
    
    def __init__(self):
        self.last_refresh = None

    async def should_refresh_content(self, db: AsyncSession) -> bool:
        """Check if we should refresh content (every 15 minutes for trends)"""
        from app.models import ContentItem

        # Always check if 15+ minutes have passed since last refresh
        now = datetime.now(timezone.utc)
        if self.last_refresh and (now - self.last_refresh) < timedelta(minutes=15):
            return False  # Not enough time has passed

        # If we have no last_refresh, check the database
        if not self.last_refresh:
            result = await db.execute(
                select(ContentItem).order_by(ContentItem.created_at.desc()).limit(1)
            )
            latest_content = result.scalar_one_or_none()

            if not latest_content:
                return True  # No content yet

            self.last_refresh = latest_content.created_at
            # Check again if we should refresh
            return (now - self.last_refresh) >= timedelta(minutes=15)

        return True

    def _acquire_lock(self):
        """Acquire platform-specific lock. Returns (success, lock_fd)"""
        platform = sys.platform
        if platform == "win32":
            if LOCK_FILE.exists():
                return False, None
            try:
                LOCK_FILE.touch()
                return True, None
            except Exception:
                return False, None
        else:
            try:
                import fcntl
                lock_fd = open(LOCK_FILE, "w")  # noqa: SIM115,ASYNC230
                fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)  # type: ignore
                return True, lock_fd
            except (IOError, ImportError):
                return False, None

    def _release_lock(self, lock_fd):
        """Release platform-specific lock"""
        if sys.platform == "win32":
            try:
                LOCK_FILE.unlink()
            except Exception:
                pass
        else:
            try:
                import fcntl
                if lock_fd:
                    fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)  # type: ignore
                    lock_fd.close()
            except Exception:
                pass

    async def refresh_content_if_needed(self):
        """Refresh trending content if it's stale"""
        lock_acquired, lock_fd = self._acquire_lock()
        if not lock_acquired:
            print(self.LOCK_MESSAGE)
            return 0

        try:
            async with AsyncSessionLocal() as db:
                if await self.should_refresh_content(db):
                    print(">> Refreshing trending content from Google Trends...")
                    _, new_content_count = await trending_service.save_trends_to_database(db)
                    self.last_refresh = datetime.now(timezone.utc)
                    print(f">> Trending content refresh completed! Added {new_content_count} new items")
                    return new_content_count
                else:
                    print(">> Content is still fresh, skipping refresh")
                    return 0
        finally:
            self._release_lock(lock_fd)


# Global instance
content_refresh = ContentRefreshService()


async def start_periodic_refresh():
    """Start periodic content refresh"""
    while True:
        try:
            await content_refresh.refresh_content_if_needed()
        except Exception as e:
            print(f">> Error in periodic refresh: {e}")

        # Wait 1 hour between checks
        await asyncio.sleep(3600)
