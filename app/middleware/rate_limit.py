"""
Rate Limiting Middleware for FastAPI
Protects API from abuse and DoS attacks
"""
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from datetime import datetime, timedelta
import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using sliding window algorithm.

    Tracks requests per IP address and enforces configurable limits.
    """

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        burst_requests: int = 10
    ):
        """
        Initialize rate limiter.

        Args:
            app: FastAPI application
            requests_per_minute: Max requests allowed per minute
            burst_requests: Max requests allowed in a 10-second burst
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_requests = burst_requests

        # Storage: {ip: [(timestamp, count), ...]}
        self.request_history: Dict[str, list] = defaultdict(list)

        # Cleanup tracker
        self.last_cleanup = datetime.now()

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request, handling proxies."""
        # Check X-Forwarded-For header (if behind proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Take first IP in the chain
            return forwarded.split(",")[0].strip()

        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # Fall back to direct client IP
        return request.client.host if request.client else "unknown"

    def _cleanup_old_entries(self):
        """Remove entries older than 1 minute to prevent memory growth."""
        now = datetime.now()

        # Only cleanup every 5 minutes
        if now - self.last_cleanup < timedelta(minutes=5):
            return

        cutoff = now - timedelta(minutes=1)

        # Clean up old entries for each IP
        for ip in list(self.request_history.keys()):
            self.request_history[ip] = [
                (ts, count) for ts, count in self.request_history[ip]
                if ts > cutoff
            ]

            # Remove IP if no recent requests
            if not self.request_history[ip]:
                del self.request_history[ip]

        self.last_cleanup = now
        logger.debug(f"Rate limit cleanup: {len(self.request_history)} IPs tracked")

    def _check_rate_limit(self, ip: str) -> Tuple[bool, str]:
        """
        Check if request should be allowed.

        Returns:
            (allowed: bool, reason: str)
        """
        now = datetime.now()

        # Get request history for this IP
        history = self.request_history[ip]

        # Check burst limit (last 10 seconds)
        burst_cutoff = now - timedelta(seconds=10)
        recent_burst = sum(
            count for ts, count in history
            if ts > burst_cutoff
        )

        if recent_burst >= self.burst_requests:
            return False, f"Burst limit exceeded ({self.burst_requests} req/10s)"

        # Check per-minute limit
        minute_cutoff = now - timedelta(minutes=1)
        recent_minute = sum(
            count for ts, count in history
            if ts > minute_cutoff
        )

        if recent_minute >= self.requests_per_minute:
            return False, f"Rate limit exceeded ({self.requests_per_minute} req/min)"

        return True, ""

    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""

        # Skip rate limiting for health check endpoint
        if request.url.path.endswith("/health"):
            return await call_next(request)

        # Get client IP
        client_ip = self._get_client_ip(request)

        # Periodic cleanup
        self._cleanup_old_entries()

        # Check rate limit
        allowed, reason = self._check_rate_limit(client_ip)

        if not allowed:
            logger.warning(
                f"Rate limit exceeded for {client_ip}: {reason} "
                f"(path: {request.url.path})"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "rate_limit_exceeded",
                    "message": reason,
                    "retry_after": 60  # seconds
                }
            )

        # Record this request
        now = datetime.now()
        self.request_history[client_ip].append((now, 1))

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        minute_cutoff = now - timedelta(minutes=1)
        current_count = sum(
            count for ts, count in self.request_history[client_ip]
            if ts > minute_cutoff
        )

        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, self.requests_per_minute - current_count)
        )
        response.headers["X-RateLimit-Reset"] = str(60)  # seconds

        return response
