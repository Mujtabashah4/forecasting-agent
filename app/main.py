"""
FastAPI Main Application
Forecasting Agent API Server
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1.router import api_router
from app.utils.logger import setup_logger
from app.middleware import (
    RateLimitMiddleware,
    RequestIDMiddleware,
    RequestCacheMiddleware,
    RequestSizeLimitMiddleware,
    SecurityHeadersMiddleware
)
import logging

# Setup logger
logger = setup_logger()

# Create FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="""
    AI-Powered Forecasting Agent for Project Cost Analysis

    ## Features
    * Analyzes project forecasts, actuals, and purchase orders
    * Detects variances and threshold breaches
    * Generates forecast scenarios with explanations
    * Provides human-in-the-loop recommendations
    * Integrates with Capexplan via API

    ## Authentication
    Use POST /api/v1/auth/token to get an access token.
    Include token in Authorization header: `Bearer {token}`

    ## Security
    * Token-based authentication
    * IP address whitelisting
    * Rate limiting
    * Audit logging
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add request ID tracking middleware (first, so all logs include request ID)
app.add_middleware(RequestIDMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware (security)
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=60,  # 60 requests per minute per IP
    burst_requests=10  # Max 10 requests in 10 seconds
)

# Add request size limit middleware (DoS protection)
app.add_middleware(
    RequestSizeLimitMiddleware,
    max_size_mb=10.0  # 10MB max request size
)

# Add security headers middleware
app.add_middleware(
    SecurityHeadersMiddleware,
    enable_hsts=not settings.DEBUG  # Only enable HSTS in production
)

# Add request caching middleware (performance)
app.add_middleware(
    RequestCacheMiddleware,
    ttl_seconds=300,  # 5 minute cache TTL
    max_size=100  # Max 100 cached responses
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
async def startup_event():
    """Log startup information"""
    logger.info("=" * 60)
    logger.info(f"Starting {settings.API_TITLE} v{settings.API_VERSION}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"LLM Model: {settings.OLLAMA_MODEL}")
    logger.info(f"LLM Host: {settings.OLLAMA_HOST}")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown"""
    logger.info("Shutting down Forecasting Agent API")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Forecasting Agent API",
        "version": settings.API_VERSION,
        "docs": "/docs",
        "health": f"{settings.API_V1_PREFIX}/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
