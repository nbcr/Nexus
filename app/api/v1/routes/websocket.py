"""
WebSocket Routes

Real-time push notifications for:
- New content availability
- Content updates
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Set
import asyncio
import json
from datetime import datetime

router = APIRouter()

# Store active WebSocket connections
active_connections: Set[WebSocket] = set()


class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        print(
            f"✅ WebSocket connected. Total connections: {len(self.active_connections)}"
        )

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        print(
            f"❌ WebSocket disconnected. Total connections: {len(self.active_connections)}"
        )

    async def broadcast(self, message: dict):
        """Send message to all connected clients"""
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error sending to client: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific client"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending personal message: {e}")
            self.disconnect(websocket)


manager = ConnectionManager()


@router.websocket("/feed-updates")
async def websocket_feed_updates(websocket: WebSocket):
    """
    WebSocket endpoint for real-time feed updates
    Clients connect to receive notifications about:
    - New content available
    - Content refresh suggestions
    """
    import logging

    logger = logging.getLogger("uvicorn.error")
    token = None
    # Try header first (for JS clients)
    if "authorization" in websocket.headers:
        auth_header = websocket.headers["authorization"]
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:]
    # Try cookies
    if not token:
        cookie_header = websocket.headers.get("cookie", "")
        for part in cookie_header.split(";"):
            if "access_token=" in part:
                token = part.split("access_token=")[-1].strip()
    # Try query param
    if not token:
        token = websocket.query_params.get("token")
    # Debug: print received token
    logger.info(f"WebSocket received token: {token}")
    # Validate token
    from app.core.auth import verify_token, jwt, SECRET_KEY, ALGORITHM

    payload = None
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except Exception as e:
            logger.error(f"WebSocket token decode error: {e}")
    logger.info(f"WebSocket decoded payload: {payload}")
    username = payload.get("sub") if payload else None
    if not username:
        # Accept anonymous connection, track by visitor_id
        cookie_header = websocket.headers.get("cookie", "")
        visitor_id = None
        for part in cookie_header.split(";"):
            if "visitor_id=" in part:
                visitor_id = part.split("visitor_id=")[-1].strip()
        logger.info(f"WebSocket accepted for anonymous visitor_id: {visitor_id}")
        await manager.connect(websocket)
        try:
            await websocket.send_json(
                {
                    "type": "connected",
                    "message": f"Connected to Nexus feed updates as anonymous visitor {visitor_id}",
                    "timestamp": datetime.now().isoformat(),
                }
            )
            while True:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
        except WebSocketDisconnect:
            manager.disconnect(websocket)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            manager.disconnect(websocket)
        return
    logger.info(f"WebSocket accepted for user: {username}")
    await manager.connect(websocket)
    try:
        # Send initial connection confirmation
        await websocket.send_json(
            {
                "type": "connected",
                "message": f"Connected to Nexus feed updates as {username}",
                "timestamp": datetime.now().isoformat(),
            }
        )
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            # Handle ping/pong for keepalive
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


async def notify_new_content(count: int = 1, category: str = None):
    """
    Notify all connected clients about new content

    Args:
        count: Number of new content items
        category: Optional category filter
    """
    message = {
        "type": "new_content",
        "count": count,
        "category": category,
        "timestamp": datetime.now().isoformat(),
    }
    await manager.broadcast(message)
    print(f"📢 Broadcasted new content notification: {count} items")


# Export manager for use in other modules
__all__ = ["router", "manager", "notify_new_content"]
