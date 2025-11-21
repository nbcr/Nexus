from fastapi import FastAPI # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from fastapi.staticfiles import StaticFiles # type: ignore
import os

from app.api.routes import topics, content, users, auth, session, trending
from app.core.config import settings

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-Powered Content Personalization Engine",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

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
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["authentication"])
app.include_router(session.router, prefix=f"{settings.API_V1_STR}/session", tags=["session"])
app.include_router(trending.router, prefix=f"{settings.API_V1_STR}/trending", tags=["trending"])
app.include_router(topics.router, prefix=f"{settings.API_V1_STR}/topics", tags=["topics"])
app.include_router(content.router, prefix=f"{settings.API_V1_STR}/content", tags=["content"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])

@app.get("/")
async def root():
    return {"message": "Welcome to Nexus API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "nexus-api"}

@app.get("/robots.txt")
async def robots():
    from fastapi.responses import FileResponse # type: ignore
    return FileResponse("app/static/robots.txt", media_type="text/plain")

# Serve the frontend
@app.get("/app")
async def serve_frontend():
    from fastapi.responses import FileResponse # type: ignore
    return FileResponse("app/static/index.html")

if __name__ == "__main__":
    import uvicorn # type: ignore
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="info"
    )
