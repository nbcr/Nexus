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

from app.services.content_refresh import content_refresh
from app.database import AsyncSessionLocal


class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
    
    async def refresh_content_job(self):
        """Job to refresh content from RSS feeds and notify clients"""
        try:
            print(f"⏰ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running scheduled content refresh...")
            count = await content_refresh.refresh_content_if_needed()
            
            if count > 0:
                print(f"✅ Scheduled refresh completed - {count} new items added")
            else:
                print("ℹ️  No new content to add")
                
        except Exception as e:
            print(f"❌ Error in scheduled content refresh: {e}")
    
    def start(self):
        """Start the scheduler"""
        if self.is_running:
            print("⚠️  Scheduler already running")
            return
        
        # Schedule content refresh every 15 minutes
        self.scheduler.add_job(
            self.refresh_content_job,
            trigger=IntervalTrigger(minutes=15),
            id='content_refresh',
            name='Refresh RSS feed content',
            replace_existing=True
        )
        
        # Run immediately on startup
        self.scheduler.add_job(
            self.refresh_content_job,
            trigger='date',
            run_date=datetime.now(),
            id='initial_content_refresh',
            name='Initial content refresh on startup'
        )
        
        self.scheduler.start()
        self.is_running = True
        print("✅ Background scheduler started - content will refresh every 15 minutes")
    
    def stop(self):
        """Stop the scheduler"""
        if not self.is_running:
            return
        
        self.scheduler.shutdown()
        self.is_running = False
        print("🛑 Background scheduler stopped")


# Global scheduler instance
scheduler_service = SchedulerService()
