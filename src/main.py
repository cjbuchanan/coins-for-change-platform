"""
Main FastAPI application with database infrastructure.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.config import get_settings
from shared.health import router as health_router
from shared.database import close_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting Coins for Change application...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Coins for Change application...")
    await close_database()
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Coins for Change Platform",
    description="A collaborative ideation and prioritization system",
    version="1.0.0",
    debug=settings.debug,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include health check routes
app.include_router(health_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Coins for Change Platform",
        "version": "1.0.0",
        "environment": settings.environment
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )