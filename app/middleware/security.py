"""
Security Middlewares
Additional security measures for production deployment

Includes:
1. HTTPS Enforcement - Redirect HTTP to HTTPS
2. Request Size Limit - Limit payload size to prevent DoS
3. Security Headers - Add security headers to responses
"""
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, RedirectResponse, JSONResponse
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """
    Redirect HTTP requests to HTTPS in production.

    Features:
    - Configurable enable/disable
    - Respects X-Forwarded-Proto header (for reverse proxies)
    - Excludes health check endpoint for load balancer probes
    """

    # Paths that don't require HTTPS (for health checks)
    EXEMPT_PATHS = ['/api/v1/health', '/health', '/']

    def __init__(self, app, enabled: bool = True):
        super().__init__(app)
        self.enabled = enabled
        if enabled:
            logger.info("HTTPSRedirectMiddleware enabled")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self.enabled:
            return await call_next(request)

        # Check if already HTTPS
        scheme = request.headers.get('X-Forwarded-Proto', request.url.scheme)

        if scheme == 'https':
            return await call_next(request)

        # Allow exempt paths (health checks)
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Redirect to HTTPS
        https_url = request.url.replace(scheme='https')
        logger.debug(f"Redirecting to HTTPS: {https_url}")
        return RedirectResponse(url=str(https_url), status_code=301)


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Limit request body size to prevent DoS attacks.

    Features:
    - Configurable max size
    - Returns 413 Payload Too Large if exceeded
    - Logs oversized requests
    """

    def __init__(self, app, max_size_mb: float = 10.0):
        super().__init__(app)
        self.max_size_bytes = int(max_size_mb * 1024 * 1024)
        logger.info(f"RequestSizeLimitMiddleware: max size = {max_size_mb}MB")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check Content-Length header
        content_length = request.headers.get('Content-Length')

        if content_length:
            try:
                size = int(content_length)
                if size > self.max_size_bytes:
                    logger.warning(
                        f"Request too large: {size} bytes from {request.client.host}"
                    )
                    return JSONResponse(
                        status_code=413,
                        content={
                            'error': 'payload_too_large',
                            'message': f'Request body exceeds maximum size of {self.max_size_bytes / 1024 / 1024:.1f}MB',
                            'max_size_bytes': self.max_size_bytes
                        }
                    )
            except ValueError:
                pass

        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses.

    Headers added:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Strict-Transport-Security (HSTS)
    - Content-Security-Policy
    """

    def __init__(self, app, enable_hsts: bool = True):
        super().__init__(app)
        self.enable_hsts = enable_hsts
        logger.info("SecurityHeadersMiddleware enabled")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'

        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'DENY'

        # XSS Protection (legacy, but still useful)
        response.headers['X-XSS-Protection'] = '1; mode=block'

        # HSTS - enforce HTTPS for 1 year
        if self.enable_hsts:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        # Basic CSP - adjust based on your needs
        response.headers['Content-Security-Policy'] = "default-src 'self'"

        # Referrer Policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        return response
