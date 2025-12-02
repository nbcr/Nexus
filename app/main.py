from fastapi import FastAPI, Request  # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore
from fastapi.staticfiles import StaticFiles  # type: ignore
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse, RedirectResponse
import os

from app.api.routes import topics, content, users, session, trending
from app.api.v1.routes import (
    admin,
    settings as v1_settings,
    websocket,
    history,
    auth as v1_auth,
)
from app.core.config import settings
from app.services.scheduler_service import scheduler_service

# Configure Jinja2 templates
templates = Jinja2Templates(directory="app/templates")

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-Powered Content Personalization Engine",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Serve /login and /register as static files
from fastapi.responses import FileResponse


@app.get("/login", include_in_schema=False)
async def login_page():
    from fastapi import Request
    from fastapi.responses import RedirectResponse, FileResponse
    from app.core.auth import verify_token

    async def _login_page(request: Request):
        # Check if user has a valid token by trying to verify it
        token = request.cookies.get("access_token")
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ", 1)[1]

        # Only redirect if token exists AND is valid
        if token:
            username = verify_token(token)
            if username:
                # Token is valid, redirect to home
                return RedirectResponse(url="/")
            # Token is invalid/expired, clear it and show login page
            response = FileResponse("app/static/login.html")
            response.delete_cookie("access_token", path="/")
            return response
        # No token, show login page
        return FileResponse("app/static/login.html")

    return await _login_page


@app.get("/register", include_in_schema=False)
async def register_page():
    return FileResponse("app/static/register.html")


from fastapi import FastAPI  # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore
from fastapi.staticfiles import StaticFiles  # type: ignore
import os

from app.api.routes import topics, content, users, auth, session, trending
from app.api.v1.routes import admin, settings as v1_settings, websocket, history
from app.core.config import settings
from app.services.scheduler_service import scheduler_service

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-Powered Content Personalization Engine",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Start background scheduler on app startup"""
    import logging
    from datetime import datetime

    logger = logging.getLogger("uvicorn")
    logger.info("=" * 80)
    logger.info(
        f"🚀 Nexus API Started - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    logger.info(f"Version: {settings.VERSION}")
    logger.info(f"Environment: {'Development' if settings.debug else 'Production'}")
    logger.info("=" * 80)
    scheduler_service.start()


@app.on_event("shutdown")
async def shutdown_event():
    """Stop background scheduler on app shutdown"""
    import logging
    from datetime import datetime

    logger = logging.getLogger("uvicorn")
    logger.info("=" * 80)
    logger.info(
        f"🛑 Nexus API Shutting Down - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    logger.info("=" * 80)
    scheduler_service.stop()


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(
    v1_auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["authentication"]
)
app.include_router(
    session.router, prefix=f"{settings.API_V1_STR}/session", tags=["session"]
)
app.include_router(
    trending.router, prefix=f"{settings.API_V1_STR}/trending", tags=["trending"]
)
app.include_router(
    topics.router, prefix=f"{settings.API_V1_STR}/topics", tags=["topics"]
)
app.include_router(
    content.router, prefix=f"{settings.API_V1_STR}/content", tags=["content"]
)
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])

# Include admin and settings routes from v1
app.include_router(
    admin.router,
    prefix=f"{settings.API_V1_STR}/admin",
    tags=["admin"],
    include_in_schema=False,
)
app.include_router(
    v1_settings.router, prefix=f"{settings.API_V1_STR}/settings", tags=["settings"]
)

# Include WebSocket routes
app.include_router(
    websocket.router, prefix=f"{settings.API_V1_STR}/ws", tags=["websocket"]
)


# Include history routes
app.include_router(
    history.router, prefix=f"{settings.API_V1_STR}/history", tags=["history"]
)


# Page routes - using Jinja2 templates
@app.get("/", include_in_schema=False)
async def root(request: Request):
    """Serve the main feed page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/login", include_in_schema=False)
async def login_page(request: Request):
    """Serve login page, redirect if already logged in"""
    from app.core.auth import verify_token

    # Check if user has a valid token
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]

    # Only redirect if token exists AND is valid
    if token:
        username = verify_token(token)
        if username:
            # Token is valid, redirect to home
            return RedirectResponse(url="/")
        # Token is invalid/expired, clear it and show login page
        response = templates.TemplateResponse("login.html", {"request": request})
        response.delete_cookie("access_token", path="/")
        return response

    # No token, show login page
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register", include_in_schema=False)
async def register_page(request: Request):
    """Serve registration page"""
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/settings", include_in_schema=False)
async def settings_page(request: Request):
    """Serve settings page"""
    return templates.TemplateResponse("settings.html", {"request": request})


# Legacy routes for backwards compatibility
@app.get("/app", include_in_schema=False)
async def serve_frontend(request: Request):
    """Legacy route - redirect to /"""
    return RedirectResponse(url="/")


@app.get("/history", include_in_schema=False)
async def history_page_legacy(request: Request):
    """Legacy route - redirect to /settings"""
    return RedirectResponse(url="/settings")


# Utility routes
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "nexus-api"}


@app.get("/robots.txt")
async def robots():
    """Serve robots.txt"""
    return FileResponse("app/static/robots.txt", media_type="text/plain")


@app.get("/ads.txt")
async def ads_txt():
    """Serve ads.txt"""
    return FileResponse("app/static/ads.txt", media_type="text/plain")


# Admin panel (still uses static HTML)
@app.get("/admin.html", include_in_schema=False)
async def serve_admin():
    """Serve admin panel"""
    return FileResponse("app/static/admin.html")


# Direct link to content by slug
@app.get("/story/{slug}")
async def view_story(slug: str):
    from fastapi.responses import RedirectResponse  # type: ignore

    # Redirect to main feed with hash to the content
    return RedirectResponse(url=f"/?story={slug}")


if __name__ == "__main__":
    import uvicorn  # type: ignore

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="info",
    )
