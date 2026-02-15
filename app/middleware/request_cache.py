"""
Request Caching Middleware
Caches repeated identical requests to improve performance

Features:
1. Hash-based request identification
2. Configurable TTL (time-to-live)
3. Automatic cache cleanup
4. Cache headers in response
"""
import hashlib
import json
import time
from typing import Dict, Any, Optional, Callable
from collections import OrderedDict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
import logging

logger = logging.getLogger(__name__)


class RequestCache:
    """
    Simple in-memory cache with TTL and max size.

    Uses OrderedDict for LRU-like eviction when max size is reached.
    """

    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.hits = 0
        self.misses = 0

    def _generate_key(self, method: str, path: str, body: bytes) -> str:
        """Generate cache key from request details"""
        content = f"{method}:{path}:{body.decode('utf-8', errors='ignore')}"
        return hashlib.sha256(content.encode()).hexdigest()[:32]

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached response if exists and not expired"""
        if key not in self.cache:
            self.misses += 1
            return None

        entry = self.cache[key]
        if time.time() > entry['expires_at']:
            # Expired, remove it
            del self.cache[key]
            self.misses += 1
            return None

        # Move to end (most recently used)
        self.cache.move_to_end(key)
        self.hits += 1
        return entry['response']

    def set(self, key: str, response: Dict[str, Any]) -> None:
        """Store response in cache"""
        # Evict oldest if at max size
        while len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)

        self.cache[key] = {
            'response': response,
            'expires_at': time.time() + self.ttl_seconds,
            'cached_at': time.time()
        }

    def clear(self) -> None:
        """Clear all cached entries"""
        self.cache.clear()
        logger.info("Request cache cleared")

    def cleanup_expired(self) -> int:
        """Remove expired entries, return count removed"""
        now = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if now > entry['expires_at']
        ]
        for key in expired_keys:
            del self.cache[key]
        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'ttl_seconds': self.ttl_seconds,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate_percent': round(hit_rate, 2)
        }


# Global cache instance
request_cache = RequestCache()


class RequestCacheMiddleware(BaseHTTPMiddleware):
    """
    Middleware to cache POST request responses.

    Only caches:
    - POST requests to /forecast/review
    - Successful responses (200)

    Does not cache:
    - GET requests (typically unique)
    - Error responses
    - Requests with no-cache header
    """

    # Paths to cache
    CACHEABLE_PATHS = [
        '/api/v1/forecast/review'
    ]

    def __init__(self, app, ttl_seconds: int = 300, max_size: int = 100):
        super().__init__(app)
        request_cache.ttl_seconds = ttl_seconds
        request_cache.max_size = max_size
        logger.info(f"RequestCacheMiddleware initialized: TTL={ttl_seconds}s, max_size={max_size}")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only cache specific paths
        if request.url.path not in self.CACHEABLE_PATHS:
            return await call_next(request)

        # Only cache POST requests
        if request.method != 'POST':
            return await call_next(request)

        # Check for no-cache header
        if request.headers.get('Cache-Control') == 'no-cache':
            response = await call_next(request)
            response.headers['X-Cache'] = 'BYPASS'
            return response

        # Read body for cache key generation
        body = await request.body()
        cache_key = request_cache._generate_key(
            request.method,
            request.url.path,
            body
        )

        # Check cache
        cached = request_cache.get(cache_key)
        if cached:
            logger.debug(f"Cache HIT for {request.url.path}")
            response = JSONResponse(
                content=cached['content'],
                status_code=cached['status_code']
            )
            response.headers['X-Cache'] = 'HIT'
            response.headers['X-Cache-Key'] = cache_key[:8]
            return response

        # Cache miss - process request
        logger.debug(f"Cache MISS for {request.url.path}")

        # We need to recreate the request since body was consumed
        # Store body in request state for the endpoint to use
        request.state.body = body

        response = await call_next(request)

        # Only cache successful responses
        if response.status_code == 200:
            # Read response body
            response_body = b''
            async for chunk in response.body_iterator:
                response_body += chunk

            try:
                content = json.loads(response_body)
                request_cache.set(cache_key, {
                    'content': content,
                    'status_code': response.status_code
                })

                # Return new response with body
                new_response = JSONResponse(
                    content=content,
                    status_code=response.status_code
                )
                new_response.headers['X-Cache'] = 'MISS'
                new_response.headers['X-Cache-Key'] = cache_key[:8]
                return new_response
            except json.JSONDecodeError:
                # Not JSON, return original response
                return Response(
                    content=response_body,
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )

        return response


def get_cache_stats() -> Dict[str, Any]:
    """Get current cache statistics"""
    return request_cache.get_stats()


def clear_cache() -> None:
    """Clear the request cache"""
    request_cache.clear()
