"""
Request ID tracking middleware
Adds unique request IDs for debugging and log correlation
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
import logging
import time
from typing import Callable

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds unique request ID to each request.

    Features:
    - Generates UUID for each request
    - Accepts existing X-Request-ID header
    - Adds request ID to response headers
    - Logs request timing and status
    """

    async def dispatch(self, request: Request, call_next: Callable):
        """Process request with ID tracking."""

        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())

        # Store in request state for access in endpoints
        request.state.request_id = request_id

        # Log request start
        start_time = time.time()
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} - Request started"
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate request duration
            duration = time.time() - start_time

            # Log request completion
            logger.info(
                f"[{request_id}] {request.method} {request.url.path} - "
                f"Status: {response.status_code} - Duration: {duration:.3f}s"
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Log errors with request ID
            duration = time.time() - start_time
            logger.error(
                f"[{request_id}] {request.method} {request.url.path} - "
                f"Error: {str(e)} - Duration: {duration:.3f}s",
                exc_info=True
            )
            raise


def get_request_id(request: Request) -> str:
    """
    Get request ID from request state.

    Args:
        request: FastAPI request object

    Returns:
        Request ID string
    """
    return getattr(request.state, "request_id", "unknown")
