"""
Nexus API Package

This package contains all API routes and endpoints for the Nexus application.
Routes are organized by version (v1, v2, etc.) to maintain backward compatibility
when making breaking changes.

Current versions:
- v1: Initial API version

Usage:
    from app.api.v1 import api_router
    app.include_router(api_router, prefix="/api/v1")
"""

from app.api.v1 import api_router

__all__ = ["api_router"]