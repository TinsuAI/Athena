"""Tests for search cache service."""

import pytest
from unittest.mock import AsyncMock

from app.services.search_cache import CachedSearchResult, SearchCacheService


class TestSearchCacheService:
    """Test cases for SearchCacheService."""

    @pytest.mark.asyncio
    async def test_get_returns_none_when_no_redis(self):
        """Test get returns None when Redis is not available."""
        service = SearchCacheService(redis_client=None)
        result = await service.get("test query")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_does_nothing_when_no_redis(self):
        """Test set does nothing when Redis is not available."""
        service = SearchCacheService(redis_client=None)
        # Should not raise
        await service.set("test query", [])

    @pytest.mark.asyncio
    async def test_get_returns_none_on_cache_miss(self):
        """Test get returns None when query not in cache."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None

        service = SearchCacheService(redis_client=mock_redis)
        result = await service.get("test query")

        assert result is None
        mock_redis.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_returns_cached_results(self):
        """Test get returns cached results."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = '''[
            {
                "hs_code": "74182000",
                "description_vn": "Test",
                "description_en": "Test EN",
                "duty_rate": 30.0,
                "vat_rate": 10.0,
                "unit": null,
                "confidence": 95,
                "is_exact_match": false
            }
        ]'''

        service = SearchCacheService(redis_client=mock_redis)
        results = await service.get("test query")

        assert results is not None
        assert len(results) == 1
        assert results[0].hs_code == "74182000"
        assert results[0].confidence == 95

    @pytest.mark.asyncio
    async def test_set_caches_results(self):
        """Test set caches results with TTL."""
        mock_redis = AsyncMock()

        service = SearchCacheService(redis_client=mock_redis)

        result = CachedSearchResult(
            hs_code="74182000",
            description_vn="Test",
            description_en="Test EN",
            duty_rate=30.0,
            vat_rate=10.0,
            unit=None,
            confidence=95,
            is_exact_match=False,
        )

        await service.set("test query", [result])

        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == 300  # 5 minute TTL

    @pytest.mark.asyncio
    async def test_cache_key_normalized(self):
        """Test cache key is normalized (lowercase, trimmed)."""
        service = SearchCacheService(redis_client=None)

        key1 = service._get_cache_key("Test Query")
        key2 = service._get_cache_key("test query")
        key3 = service._get_cache_key("  test query  ")

        assert key1 == key2
        assert key2 == key3

    @pytest.mark.asyncio
    async def test_cache_key_different_queries(self):
        """Test different queries produce different keys."""
        service = SearchCacheService(redis_client=None)

        key1 = service._get_cache_key("query one")
        key2 = service._get_cache_key("query two")

        assert key1 != key2

    @pytest.mark.asyncio
    async def test_invalidate_all(self):
        """Test invalidate all clears search cache."""
        mock_redis = AsyncMock()

        # Mock scan_iter to return an async generator
        async def mock_scan_iter(pattern):
            for key in ["search:abc123", "search:def456"]:
                yield key

        mock_redis.scan_iter = mock_scan_iter
        mock_redis.delete.return_value = 2

        service = SearchCacheService(redis_client=mock_redis)
        deleted = await service.invalidate_all()

        assert deleted == 2
        mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_and_invalidate_on_version_change(self):
        """Test cache invalidation on data version change."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = "v1"

        async def mock_scan_iter(pattern):
            for key in ["search:key1"]:
                yield key

        mock_redis.scan_iter = mock_scan_iter
        mock_redis.delete.return_value = 1

        service = SearchCacheService(redis_client=mock_redis)
        invalidated = await service.check_and_invalidate_on_version_change("v2")

        assert invalidated is True
        mock_redis.delete.assert_called()
        mock_redis.set.assert_called_with("data_version", "v2")

    @pytest.mark.asyncio
    async def test_no_invalidation_when_version_unchanged(self):
        """Test no invalidation when version unchanged."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = "v1"

        service = SearchCacheService(redis_client=mock_redis)
        invalidated = await service.check_and_invalidate_on_version_change("v1")

        assert invalidated is False
        mock_redis.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_handles_invalid_json(self):
        """Test get handles invalid JSON gracefully."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = "invalid json"

        service = SearchCacheService(redis_client=mock_redis)
        result = await service.get("test query")

        assert result is None


