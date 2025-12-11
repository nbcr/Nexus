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
from app.services.reboot_manager import reboot_manager

router = APIRouter()

# Store active WebSocket connections
active_connections: Set[WebSocket] = set()


class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        reboot_manager.register_connection()
        print(
            f"✅ WebSocket connected. Total connections: {len(self.active_connections)}"
        )

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        reboot_manager.unregister_connection()
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


def _extract_token_from_websocket(websocket: WebSocket) -> str | None:
    """Extract JWT token from WebSocket headers, cookies, or query params."""
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
    return token


def _extract_visitor_id_from_cookies(websocket: WebSocket) -> str | None:
    """Extract visitor_id from WebSocket cookies."""
    cookie_header = websocket.headers.get("cookie", "")
    visitor_id = None
    for part in cookie_header.split(";"):
        if "visitor_id=" in part:
            visitor_id = part.split("visitor_id=")[-1].strip()
    return visitor_id


def _decode_jwt_token(token: str, logger) -> dict | None:
    """Decode and validate JWT token, return payload or None."""
    from app.core.auth import jwt, SECRET_KEY, ALGORITHM

    payload = None
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except Exception as e:
            safe_error = str(e).replace("\n", "").replace("\r", "")
            logger.error(f"WebSocket token decode error: {safe_error}")
    return payload


async def _handle_websocket_connection(websocket: WebSocket, identifier: str):
    """Handle WebSocket keepalive loop and message processing."""
    try:
        await websocket.send_json(
            {
                "type": "connected",
                "message": f"Connected to Nexus feed updates as {identifier}",
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
        import logging

        logger = logging.getLogger("uvicorn.error")
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@router.websocket("/feed-updates")
async def websocket_feed_updates(websocket: WebSocket):
    """WebSocket endpoint for real-time feed updates."""
    import logging

    logger = logging.getLogger("uvicorn.error")

    # Extract and validate token
    token = _extract_token_from_websocket(websocket)
    safe_token = str(token).replace("\n", "").replace("\r", "") if token else None
    logger.info(f"WebSocket received token: {safe_token}")

    # Decode token to get user identity
    payload = _decode_jwt_token(token, logger)
    safe_payload = str(payload).replace("\n", "").replace("\r", "") if payload else None
    logger.info(f"WebSocket decoded payload: {safe_payload}")

    username = payload.get("sub") if payload else None

    # Handle anonymous connection
    if not username:
        visitor_id = _extract_visitor_id_from_cookies(websocket)
        safe_visitor_id = (
            str(visitor_id).replace("\n", "").replace("\r", "") if visitor_id else None
        )
        logger.info(f"WebSocket accepted for anonymous visitor_id: {safe_visitor_id}")
        await manager.connect(websocket)
        await _handle_websocket_connection(websocket, f"anonymous visitor {visitor_id}")
        return

    # Handle authenticated connection
    safe_username = username.replace("\n", "").replace("\r", "")
    logger.info(f"WebSocket accepted for user: {safe_username}")
    await manager.connect(websocket)
    await _handle_websocket_connection(websocket, username)


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
