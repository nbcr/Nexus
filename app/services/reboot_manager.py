"""
Graceful Reboot Manager

Monitors a reboot request file and initiates graceful shutdown when requested.
Respects active users and content refresh operations.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Reboot request file location
if sys.platform == "win32":
    REBOOT_FILE = Path(os.path.join(os.path.expanduser("~"), ".nexus_reboot_request"))
else:
    REBOOT_FILE = Path("/tmp/nexus_reboot_request")

logger = logging.getLogger(__name__)


class RebootManager:
    def __init__(self):
        self.is_running = False
        self.reboot_requested = False
        self.active_connections = 0
        self.content_refresh_in_progress = False

    async def check_reboot_request(self):
        """Check if reboot has been requested"""
        if REBOOT_FILE.exists():
            try:
                content = REBOOT_FILE.read_text(encoding="utf-8").strip().lower()
                if content == "reboot":
                    return True
            except Exception as e:
                logger.error(f"[ERROR] Failed to read reboot request file: {e}")
        return False

    async def clear_reboot_request(self):
        """Clear the reboot request file"""
        try:
            if REBOOT_FILE.exists():
                REBOOT_FILE.unlink()
                logger.info("[OK] Reboot request cleared")
        except Exception as e:
            logger.error(f"[ERROR] Failed to clear reboot request: {e}")

    async def wait_for_safe_reboot(self, timeout_seconds: int = 300):
        """
        Wait for safe conditions to reboot (max 5 minutes)
        - No active user connections
        - No content refresh in progress
        """
        start_time = datetime.now()
        max_wait = timedelta(seconds=timeout_seconds)
        check_interval = 5  # Check every 5 seconds

        logger.info(
            f"[REBOOT] Waiting for safe conditions to reboot (max {timeout_seconds}s)..."
        )

        while (datetime.now() - start_time) < max_wait:
            # Check if content refresh is in progress
            from app.services.content_refresh import content_refresh
            from app.db import AsyncSessionLocal

            try:
                async with AsyncSessionLocal() as db:
                    is_refreshing = not await content_refresh.should_refresh_content(db)
            except Exception:
                is_refreshing = False

            if self.active_connections == 0 and not is_refreshing:
                logger.info("[REBOOT] Safe conditions met - proceeding with reboot")
                return True

            if self.active_connections > 0:
                logger.info(
                    f"[REBOOT] Waiting for {self.active_connections} active connection(s) to close..."
                )
            if is_refreshing:
                logger.info("[REBOOT] Waiting for content refresh to complete...")

            await asyncio.sleep(check_interval)

        logger.warning(
            f"[REBOOT] Timeout reached after {timeout_seconds}s, forcing reboot"
        )
        return True

    async def monitor_reboot_requests(self):
        """Monitor for reboot requests every minute"""
        while self.is_running:
            try:
                if await self.check_reboot_request():
                    if not self.reboot_requested:
                        self.reboot_requested = True
                        logger.warning("[REBOOT] Reboot requested - initiating graceful shutdown...")
                        
                        # Wait for safe conditions
                        await self.wait_for_safe_reboot()
                        
                        # Clear the request file
                        await self.clear_reboot_request()
                        
                        # Trigger shutdown
                        logger.info("[REBOOT] Triggering application shutdown...")
                        import signal
                        import sys
                        
                        if sys.platform == "win32":
                            # Windows: Use SystemExit
                            raise SystemExit(0)
                        else:
                            # Unix: Use SIGTERM
                            os.kill(os.getpid(), signal.SIGTERM)

            except SystemExit:
                raise
            except Exception as e:
                logger.error(f"[ERROR] Error in reboot monitor: {e}")

            # Check every 60 seconds
            await asyncio.sleep(60)

    def start(self):
        """Start the reboot monitor"""
        if self.is_running:
            logger.warning("[WARN] Reboot manager already running")
            return

        self.is_running = True
        logger.info("[OK] Reboot manager started (monitoring for reboot requests)")

    def stop(self):
        """Stop the reboot monitor"""
        if not self.is_running:
            return

        self.is_running = False
        logger.info("[STOP] Reboot manager stopped")

    def register_connection(self):
        """Register an active user connection"""
        self.active_connections += 1

    def unregister_connection(self):
        """Unregister a user connection"""
        self.active_connections = max(0, self.active_connections - 1)


# Global instance
reboot_manager = RebootManager()
