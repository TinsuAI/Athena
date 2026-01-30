"""Search result caching service."""

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any

import redis.asyncio as redis

# Cache TTL constants
SEARCH_CACHE_TTL = 300  # 5 minutes for search results


@dataclass
class CachedSearchResult:
    """Cached search result data."""

    hs_code: str
    description_vn: str
    description_en: str
    duty_rate: float
    vat_rate: float
    unit: str | None
    confidence: int
    is_exact_match: bool


class SearchCacheService:
    """Service for caching search results.

    Features:
    - Caches search results for 5 minutes (TTL)
    - Uses MD5 hash of query for cache keys
    - Supports cache invalidation on data version change
    """

    def __init__(self, redis_client: redis.Redis | None = None):  # type: ignore[type-arg]
        """Initialize cache service.

        Args:
            redis_client: Redis client. If None, caching is disabled.
        """
        self.redis_client = redis_client
        self.cache_prefix = "search:"
        self.data_version_key = "data_version"

    def _get_cache_key(self, query: str) -> str:
        """Generate cache key for search query.

        Args:
            query: The search query

        Returns:
            Cache key with prefix
        """
        normalized = query.strip().lower()
        query_hash = hashlib.md5(normalized.encode("utf-8")).hexdigest()
        return f"{self.cache_prefix}{query_hash}"

    async def get(self, query: str) -> list[CachedSearchResult] | None:
        """Get cached search results.

        Args:
            query: The search query

        Returns:
            List of cached results or None if not found
        """
        if not self.redis_client:
            return None

        cache_key = self._get_cache_key(query)
        cached = await self.redis_client.get(cache_key)

        if not cached:
            return None

        try:
            data = json.loads(cached)
            return [CachedSearchResult(**item) for item in data]
        except (json.JSONDecodeError, TypeError, KeyError):
            # Invalid cache data, treat as cache miss
            return None

    async def set(
        self,
        query: str,
        results: list[CachedSearchResult],
        ttl: int = SEARCH_CACHE_TTL,
    ) -> None:
        """Cache search results.

        Args:
            query: The search query
            results: List of results to cache
            ttl: Time to live in seconds (default 5 minutes)
        """
        if not self.redis_client:
            return

        cache_key = self._get_cache_key(query)
        data = json.dumps([asdict(r) for r in results])

        await self.redis_client.setex(cache_key, ttl, data)

    async def invalidate_all(self) -> int:
        """Invalidate all search cache entries.

        Called when data version changes.

        Returns:
            Number of keys deleted
        """
        if not self.redis_client:
            return 0

        # Find all search cache keys
        pattern = f"{self.cache_prefix}*"
        keys = []

        async for key in self.redis_client.scan_iter(pattern):
            keys.append(key)

        if not keys:
            return 0

        deleted = await self.redis_client.delete(*keys)
        return deleted

    async def set_data_version(self, version: str) -> None:
        """Set current data version.

        Args:
            version: Data version string
        """
        if not self.redis_client:
            return

        await self.redis_client.set(self.data_version_key, version)

    async def get_data_version(self) -> str | None:
        """Get current data version.

        Returns:
            Data version string or None
        """
        if not self.redis_client:
            return None

        return await self.redis_client.get(self.data_version_key)

    async def check_and_invalidate_on_version_change(
        self,
        new_version: str,
    ) -> bool:
        """Check data version and invalidate cache if changed.

        Args:
            new_version: New data version

        Returns:
            True if cache was invalidated
        """
        if not self.redis_client:
            return False

        current_version = await self.get_data_version()

        if current_version != new_version:
            await self.invalidate_all()
            await self.set_data_version(new_version)
            return True

        return False
