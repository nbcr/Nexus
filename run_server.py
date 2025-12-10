#!/usr/bin/env python3
import sys
import os

# Force UTF-8 encoding on Windows to support emoji output
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

import uvicorn
from app.core.config import settings
import logging
from datetime import datetime

# Configure logging to write to server.log with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("server.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info(
        f">> Nexus Server Starting - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    logger.info(f"Host: {settings.api_host}:{settings.api_port}")
    logger.info(f"Debug Mode: {settings.debug}")
    logger.info("=" * 80)

    try:
        uvicorn.run(
            "app.main:app",
            host=settings.api_host,
            port=settings.api_port,
            reload=False,
            log_level="info",
            timeout_keep_alive=5,  # Close idle connections faster
            timeout_notify=10,  # Graceful shutdown timeout
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server crashed: {e}")
        raise
    finally:
        logger.info("=" * 80)
        logger.info(
            f">> Nexus Server Stopped - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        logger.info("=" * 80)
