from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.user_routes import router as user_router
from app.api.routes.item_routes import router as item_router
from app.api.routes.auth import router as auth_router
from app.core.config import settings
from app.db.session import engine, Base

# Lifespan context manager for startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create database tables
    async with engine.begin() as conn:
        # In production, use Alembic for migrations instead
        if settings.environment == "development":
            await conn.run_sync(Base.metadata.create_all)
    
    print("Application startup complete")
    yield
    # Shutdown: Cleanup resources
    print("Application shutdown complete")

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="FastAPI application with layered architecture",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    debug=settings.debug
)

# Setup CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(user_router, prefix="/api/users", tags=["users"])
app.include_router(item_router, prefix="/api/items", tags=["items"])

@app.get("/", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "message": "API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True) 