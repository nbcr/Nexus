"""
Background Scheduler Service

Handles periodic tasks:
- RSS feed updates every 15 minutes
- Content refresh notifications
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import asyncio
import logging

from app.services.content_refresh import content_refresh
from app.db import AsyncSessionLocal

# Setup logger
logger = logging.getLogger(__name__)


class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False

    async def refresh_content_job(self):
        """Job to refresh content from RSS feeds and notify clients"""
        try:
            logger.info(
                f"⏰ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running scheduled content refresh..."
            )
            count = await content_refresh.refresh_content_if_needed()

            if count > 0:
                logger.info(f"✅ Scheduled refresh completed - {count} new items added")
            else:
                logger.info("ℹ️  No new content to add")

        except Exception as e:
            logger.error(f"❌ Error in scheduled content refresh: {e}")

    def start(self):
        """Start the scheduler"""
        if self.is_running:
            logger.warning("⚠️  Scheduler already running")
            return

        # Schedule content refresh every 15 minutes (cross-platform with APScheduler)
        self.scheduler.add_job(
            self.refresh_content_job,
            trigger=IntervalTrigger(minutes=15),
            id='content_refresh',
            name='Content Refresh Job',
            replace_existing=True
        )
        
        self.scheduler.start()
        self.is_running = True
        logger.info(
            "✅ Background scheduler started (content refresh scheduled every 15 minutes)"
        )

    def stop(self):
        """Stop the scheduler"""
        if not self.is_running:
            return

        self.scheduler.shutdown()
        self.is_running = False
        logger.info("🛑 Background scheduler stopped")


# Global scheduler instance
scheduler_service = SchedulerService()
