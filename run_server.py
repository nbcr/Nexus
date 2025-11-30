#!/usr/bin/env python3
import uvicorn
from app.core.config import settings
import logging
from datetime import datetime

# Configure logging to write to server.log
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info(f"🚀 Nexus Server Starting - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Host: {settings.api_host}:{settings.api_port}")
    logger.info(f"Debug Mode: {settings.debug}")
    logger.info("=" * 80)
    
    try:
        uvicorn.run(
            "app.main:app",
            host=settings.api_host,
            port=settings.api_port,
            reload=settings.debug,
            log_level="info"
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server crashed: {e}")
        raise
    finally:
        logger.info("=" * 80)
        logger.info(f"🛑 Nexus Server Stopped - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)
