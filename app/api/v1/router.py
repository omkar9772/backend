"""
Main API v1 router - includes all endpoint routers
"""
from fastapi import APIRouter

from app.api.v1 import admin_auth, auth, owners, bulls, races, race_results, dashboard, public, search, upload, marketplace, user_bulls

# Create main API v1 router
api_router = APIRouter()

# Include all sub-routers
api_router.include_router(admin_auth.router)
api_router.include_router(auth.router)
api_router.include_router(owners.router)
api_router.include_router(bulls.router)
api_router.include_router(races.router)
api_router.include_router(race_results.router)
api_router.include_router(dashboard.router)
api_router.include_router(public.router)
api_router.include_router(search.router)
api_router.include_router(upload.router)
api_router.include_router(marketplace.router)
api_router.include_router(user_bulls.router)
