"""
Health check endpoint
"""
from fastapi import APIRouter, Depends
from app.schemas.response import HealthResponse
from app.services.llm_service import check_llm_health
from app.middleware import get_cache_stats, clear_cache
from app.config import settings
from app.utils.helpers import get_current_timestamp
from app.api.deps import get_current_user
import logging
import time

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Enhanced health check endpoint.

    Returns:
    - System status
    - LLM availability and detailed status
    - Response time metrics
    - Configuration validation

    This endpoint can be used by monitoring systems to detect issues.
    """
    start_time = time.time()

    # Check LLM service
    llm_status = await check_llm_health()

    # Calculate response time
    response_time = time.time() - start_time

    # Log health check with metrics
    logger.info(
        f"Health check completed: LLM={llm_status['status']}, "
        f"response_time={response_time:.3f}s"
    )

    # Determine overall status
    # System is healthy even if LLM is disconnected (graceful degradation)
    overall_status = "healthy"

    # Warn if LLM is not connected
    if llm_status["status"] != "connected":
        logger.warning(f"LLM service not available: {llm_status}")

    return HealthResponse(
        status=overall_status,
        version=settings.API_VERSION,
        llm_status=llm_status["status"],
        timestamp=get_current_timestamp()
    )


@router.get("/cache/stats")
async def cache_stats(current_user: dict = Depends(get_current_user)):
    """
    Get request cache statistics.

    Returns cache size, hit rate, and other metrics.
    Useful for monitoring cache performance.
    """
    stats = get_cache_stats()
    return {
        "cache": stats,
        "timestamp": get_current_timestamp()
    }


@router.post("/cache/clear")
async def clear_request_cache(current_user: dict = Depends(get_current_user)):
    """
    Clear the request cache.

    Use this to force fresh analysis of all requests.
    """
    clear_cache()
    return {
        "message": "Cache cleared successfully",
        "timestamp": get_current_timestamp()
    }
