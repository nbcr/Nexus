import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from sqlalchemy import select # pyright: ignore[reportMissingImports]

from app.database import AsyncSessionLocal
from app.services.trending_service import trending_service


class ContentRefreshService:
    def __init__(self):
        self.last_refresh = None
        
    async def should_refresh_content(self, db: AsyncSession) -> bool:
        """Check if we should refresh content (every 4 hours for trends)"""
        from app.models import ContentItem
        
        if not self.last_refresh:
            # Check the latest trending content in database
            result = await db.execute(
                select(ContentItem)
                .order_by(ContentItem.created_at.desc())
                .limit(1)
            )
            latest_content = result.scalar_one_or_none()
            
            if not latest_content:
                return True  # No content yet
                
            self.last_refresh = latest_content.created_at
        
        # Refresh if last refresh was more than 4 hours ago
        refresh_time = datetime.utcnow() - timedelta(hours=4)
        return self.last_refresh < refresh_time
    
    async def refresh_content_if_needed(self):
        """Refresh trending content if it's stale"""
        async with AsyncSessionLocal() as db:
            if await self.should_refresh_content(db):
                print("🔄 Refreshing trending content from Google Trends...")
                await trending_service.save_trends_to_database(db)
                self.last_refresh = datetime.utcnow()
                print("✅ Trending content refresh completed!")
            else:
                print("⏭️  Content is still fresh, skipping refresh")


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
