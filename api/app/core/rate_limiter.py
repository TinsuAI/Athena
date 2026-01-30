"""Rate limiting middleware using Redis."""

import json
import time
from typing import Callable

import redis.asyncio as redis
from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings
from app.schemas.base import error_response

settings = get_settings()

# Rate limit constants
RATE_LIMIT_REQUESTS = 100  # requests per window
RATE_LIMIT_WINDOW = 60  # seconds (1 minute)


class RateLimiter:
    """Redis-based rate limiter using sliding window counter.

    Tracks request counts per client IP with a 1-minute window.
    Returns 429 Too Many Requests when limit exceeded.
    """

    def __init__(self, redis_client: redis.Redis | None = None):  # type: ignore[type-arg]
        """Initialize rate limiter.

        Args:
            redis_client: Redis client for storing rate limit data
        """
        self.redis_client = redis_client
        self.requests_limit = RATE_LIMIT_REQUESTS
        self.window_seconds = RATE_LIMIT_WINDOW
        self.key_prefix = "rate_limit:"

    def _get_client_key(self, client_ip: str) -> str:
        """Generate Redis key for client IP.

        Args:
            client_ip: Client IP address

        Returns:
            Redis key for rate limiting
        """
        return f"{self.key_prefix}{client_ip}"

    async def is_allowed(self, client_ip: str) -> tuple[bool, int, int]:
        """Check if request is allowed under rate limit.

        Args:
            client_ip: Client IP address

        Returns:
            Tuple of (allowed, remaining_requests, reset_time_seconds)
        """
        if not self.redis_client:
            # No Redis, allow all requests
            return True, self.requests_limit, self.window_seconds

        key = self._get_client_key(client_ip)
        current_time = int(time.time())
        window_start = current_time - self.window_seconds

        try:
            # Use Redis pipeline for atomic operations
            async with self.redis_client.pipeline(transaction=True) as pipe:
                # Remove old entries outside the window
                await pipe.zremrangebyscore(key, 0, window_start)
                # Count current requests in window
                await pipe.zcard(key)
                # Add current request
                await pipe.zadd(key, {str(current_time): current_time})
                # Set expiry on key
                await pipe.expire(key, self.window_seconds)
                # Execute pipeline
                results = await pipe.execute()

            # Get count before adding current request
            current_count = results[1]

            if current_count >= self.requests_limit:
                # Over limit
                return False, 0, self.window_seconds

            remaining = self.requests_limit - current_count - 1
            return True, remaining, self.window_seconds

        except Exception:
            # On error, allow request (fail open)
            return True, self.requests_limit, self.window_seconds

    async def get_headers(self, client_ip: str) -> dict[str, str]:
        """Get rate limit headers for response.

        Args:
            client_ip: Client IP address

        Returns:
            Dict of rate limit headers
        """
        allowed, remaining, reset = await self.is_allowed(client_ip)

        return {
            "X-RateLimit-Limit": str(self.requests_limit),
            "X-RateLimit-Remaining": str(max(0, remaining)),
            "X-RateLimit-Reset": str(reset),
        }


def get_client_ip(request: Request) -> str:
    """Extract client IP from request.

    Handles X-Forwarded-For header for proxied requests.

    Args:
        request: FastAPI request

    Returns:
        Client IP address
    """
    # Check for forwarded IP (behind reverse proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # First IP in the list is the client
        return forwarded.split(",")[0].strip()

    # Fall back to direct connection IP
    if request.client:
        return request.client.host

    return "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting.

    Applies rate limiting to /api/search endpoint only.
    """

    def __init__(self, app, redis_pool=None):
        """Initialize middleware.

        Args:
            app: FastAPI application
            redis_pool: Redis connection pool
        """
        super().__init__(app)
        self.redis_pool = redis_pool

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """Process request with rate limiting.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response
        """
        # Only rate limit search endpoint
        if not request.url.path.startswith("/api/search"):
            return await call_next(request)

        # Create Redis client for this request
        redis_client = None
        if self.redis_pool:
            redis_client = redis.Redis(connection_pool=self.redis_pool)

        try:
            rate_limiter = RateLimiter(redis_client=redis_client)
            client_ip = get_client_ip(request)

            allowed, remaining, reset = await rate_limiter.is_allowed(client_ip)

            if not allowed:
                # Return 429 Too Many Requests
                error = error_response(
                    type_uri="https://athena.example/errors/rate-limit-exceeded",
                    title="Too Many Requests",
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Maximum {RATE_LIMIT_REQUESTS} requests per minute.",
                    instance=request.url.path,
                )

                response = Response(
                    content=json.dumps(error),
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    media_type="application/json",
                )
                response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_REQUESTS)
                response.headers["X-RateLimit-Remaining"] = "0"
                response.headers["X-RateLimit-Reset"] = str(reset)
                response.headers["Retry-After"] = str(reset)
                return response

            # Process request
            response = await call_next(request)

            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_REQUESTS)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(reset)

            return response

        finally:
            if redis_client:
                await redis_client.aclose()
