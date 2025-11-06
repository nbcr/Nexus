from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.api.routes import topics, content, users, auth, session, trending
from app.core.config import settings

# Create FastAPI application
app = FastAPI(
    title="Nexus API",
    description="AI-Powered Content Personalization Engine",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8000",
        "http://localhost:8000", 
        "https://api.test.comdat.ca",
        "https://test.comdat.ca"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(session.router, prefix="/api/v1/session", tags=["session"])
app.include_router(trending.router, prefix="/api/v1/trending", tags=["trending"])
app.include_router(topics.router, prefix="/api/v1/topics", tags=["topics"])
app.include_router(content.router, prefix="/api/v1/content", tags=["content"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])

@app.get("/")
async def root():
    return {"message": "Welcome to Nexus API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "nexus-api"}

# Serve the frontend
@app.get("/app")
async def serve_frontend():
    from fastapi.responses import FileResponse
    return FileResponse("app/static/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="info"
    )
