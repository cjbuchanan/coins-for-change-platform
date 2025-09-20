"""Campaign Management Service

Handles campaign lifecycle, configuration, and member management.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.shared.config import get_settings
from src.shared.logging import setup_logging
from src.shared.middleware import setup_middleware

# Initialize logging
setup_logging()

# Create FastAPI app
app = FastAPI(
    title="Coins for Change - Campaign Service",
    description="Campaign management and lifecycle service",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Get settings
settings = get_settings()

# Setup middleware
setup_middleware(app)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "campaigns"}


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    # TODO: Add database and external service checks
    return {"status": "ready", "service": "campaigns"}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_config=None,  # Use our custom logging
    )