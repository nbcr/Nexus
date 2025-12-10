"""
Intrusion Detection Service - runs in background thread
Monitors server logs and blocks malicious IPs via Cloudflare
"""

import os
import sys
import threading
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class IntrusionDetectionService:
    """Service to manage intrusion detection in background"""
    
    def __init__(self):
        self.detector = None
        self.thread = None
        self.running = False
        
    def start(self):
        """Start the intrusion detection service"""
        try:
            if self.running:
                logger.warning("[IDS] Service already running")
                return
            
            # Import here to avoid issues if intrusion_detector.py not available
            try:
                from intrusion_detector import IntrusionDetector
            except ImportError:
                logger.error("[IDS] intrusion_detector module not found. Skipping IDS startup.")
                return
            
            # Determine log file path - try multiple common locations
            log_paths = [
                'C:\\Nexus\\logs\\access.log',  # Primary - Nexus project logs
                'C:\\nginx\\logs\\access.log',  # Nginx
                'C:\\logs\\access.log',  # Custom logs
                '/home/nexus/nexus/logs/access.log',  # Linux (if applicable)
                os.path.expandvars('%SYSTEMROOT%\\System32\\LogFiles\\W3SVC1\\access.log'),  # IIS
            ]
            
            log_path = None
            for path in log_paths:
                if os.path.exists(path):
                    log_path = path
                    break
            
            if not log_path:
                logger.warning(f"[IDS] No access log found at common locations. Checked: {log_paths}")
                logger.warning("[IDS] Please configure log_path in intrusion_service.py")
                return
            
            logger.info(f"[IDS] Using access log: {log_path}")
            
            # Initialize detector
            config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config_ids.json')
            self.detector = IntrusionDetector(log_path=log_path, config_path=config_path)
            
            # Start monitoring in background thread
            self.running = True
            self.thread = threading.Thread(
                target=self._monitor_loop,
                daemon=True,
                name="IntrusionDetector"
            )
            self.thread.start()
            
            logger.info("[IDS] Intrusion Detection Service started successfully")
            
        except Exception as e:
            logger.error(f"[IDS] Failed to start service: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _monitor_loop(self):
        """Run the monitoring loop (called in background thread)"""
        try:
            # Setup logging for this thread
            import logging.handlers
            
            # Add a file handler for this thread's logger
            log_handler = logging.handlers.RotatingFileHandler(
                'intrusion_detector.log',
                maxBytes=10485760,  # 10MB
                backupCount=5
            )
            log_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            log_handler.setFormatter(formatter)
            
            thread_logger = logging.getLogger('intrusion_detector')
            thread_logger.addHandler(log_handler)
            
            self.detector.monitor_logs()
        except Exception as e:
            logger.error(f"[IDS] Monitor loop error: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def stop(self):
        """Stop the intrusion detection service"""
        try:
            if not self.running:
                logger.warning("[IDS] Service not running")
                return
            
            self.running = False
            
            # The monitor loop will exit on KeyboardInterrupt
            # Give it a moment to clean up
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=5)
            
            logger.info("[IDS] Intrusion Detection Service stopped")
            
        except Exception as e:
            logger.error(f"[IDS] Error stopping service: {e}")

# Global instance
ids_service = IntrusionDetectionService()
