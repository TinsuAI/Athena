"""Redis connection and utilities."""

from collections.abc import AsyncGenerator

import redis.asyncio as redis

from app.core.config import get_settings

settings = get_settings()

# Create Redis connection pool with timeout configuration
redis_pool = redis.ConnectionPool.from_url(
    settings.redis_url,
    decode_responses=True,
    max_connections=20,
    socket_timeout=5.0,  # 5 second timeout for operations
    socket_connect_timeout=2.0,  # 2 second timeout for connection
)


async def get_redis() -> AsyncGenerator[redis.Redis, None]:  # type: ignore[type-arg]
    """Dependency that provides a Redis client."""
    client = redis.Redis(connection_pool=redis_pool)
    try:
        yield client
    finally:
        await client.aclose()


async def check_redis_connection() -> bool:
    """Check if Redis is available."""
    try:
        client = redis.Redis(connection_pool=redis_pool)
        await client.ping()
        await client.aclose()
        return True
    except Exception:
        return False
