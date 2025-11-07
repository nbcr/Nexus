"""
API v1 Router

This module initializes the v1 API router and includes all route modules.
Each route module is mounted with its own prefix and tags for OpenAPI documentation.
"""
from fastapi import APIRouter
from app.api.v1.routes import auth, content, session, topics, trending, users

# Create the main v1 router
api_router = APIRouter()

# Include all route modules
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"],
    responses={401: {"description": "Unauthorized"}}
)

api_router.include_router(
    content.router,
    prefix="/content",
    tags=["content"],
    responses={404: {"description": "Content not found"}}
)

api_router.include_router(
    session.router,
    prefix="/session",
    tags=["session"],
    responses={401: {"description": "Unauthorized"}}
)

api_router.include_router(
    topics.router,
    prefix="/topics",
    tags=["topics"],
    responses={404: {"description": "Topic not found"}}
)

api_router.include_router(
    trending.router,
    prefix="/trending",
    tags=["trending"]
)

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["users"],
    responses={401: {"description": "Unauthorized"}, 404: {"description": "User not found"}}
)