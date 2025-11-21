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
        print(f"✅ WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        print(f"❌ WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
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
    await manager.connect(websocket)
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to Nexus feed updates",
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            
            # Handle ping/pong for keepalive
            if data == "ping":
                await websocket.send_json({"type": "pong"})
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
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
        "timestamp": datetime.now().isoformat()
    }
    await manager.broadcast(message)
    print(f"📢 Broadcasted new content notification: {count} items")

# Export manager for use in other modules
__all__ = ['router', 'manager', 'notify_new_content']
