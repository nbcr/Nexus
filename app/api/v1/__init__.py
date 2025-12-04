"""
API v1 Router

This module initializes the v1 API router and includes all route modules.
Each route module is mounted with its own prefix and tags for OpenAPI documentation.

NOTE: Currently not used in main.py - routes are imported individually instead.
"""

from fastapi import APIRouter
from app.api.v1.routes import (
    auth,
    admin,
    settings,
    websocket,
    history,
)

# Create the main v1 router
api_router = APIRouter()

# Include all route modules
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"],
    responses={401: {"description": "Unauthorized"}},
)

api_router.include_router(
    admin.router,
    prefix="/admin",
    tags=["admin"],
    include_in_schema=False,  # Hide from OpenAPI docs for security
)

api_router.include_router(
    settings.router,
    prefix="/settings",
    tags=["settings"],
)

api_router.include_router(
    websocket.router,
    prefix="/ws",
    tags=["websocket"],
)

api_router.include_router(
    history.router,
    prefix="/history",
    tags=["history"],
)
