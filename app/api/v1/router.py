"""
API v1 Router
Combines all v1 endpoints
"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, health, forecast, scenarios, batch

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(health.router, tags=["health"])
api_router.include_router(forecast.router, tags=["forecast"])
api_router.include_router(scenarios.router, prefix="/scenarios", tags=["scenarios"])
api_router.include_router(batch.router, prefix="/batch", tags=["batch"])
