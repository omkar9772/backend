"""
Naad Bailgada - Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Naad Bailgada API",
    description="Digital platform for managing traditional bullock cart racing (Bailgada Sharyat)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    from app.services.firebase_service import firebase_service
    import os

    try:
        # Initialize Firebase Admin SDK with Firebase-specific credentials
        # Use secret path in production (Cloud Run), local file in development
        firebase_key_path = "/secrets/firebase-key.json" if os.path.exists("/secrets/firebase-key.json") else "firebase-key.json"

        firebase_service.initialize(firebase_key_path)
        logger.info(f"✅ Firebase Admin SDK initialized at startup (using {firebase_key_path})")
    except Exception as e:
        logger.warning(f"⚠️ Firebase initialization warning (may already be initialized): {e}")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "naad-bailgada-api",
            "version": "1.0.0"
        }
    )

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": "Welcome to Naad Bailgada API",
        "docs": "/docs",
        "health": "/health",
        "version": "1.0.0"
    }

# Include API v1 router
from app.api.v1.router import api_router as api_v1_router
app.include_router(api_v1_router, prefix="/api/v1")

# Mount static files for uploads
from app.core.config import settings
uploads_dir = settings.BASE_DIR / "uploads"
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
