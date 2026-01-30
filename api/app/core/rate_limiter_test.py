"""Tests for rate limiter."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.core.rate_limiter import RateLimiter, get_client_ip


class AsyncContextManager:
    """Helper for mocking async context managers."""

    def __init__(self, return_value):
        self.return_value = return_value

    async def __aenter__(self):
        return self.return_value

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class TestRateLimiter:
    """Test cases for RateLimiter."""

    @pytest.mark.asyncio
    async def test_is_allowed_without_redis(self):
        """Test rate limiter allows all requests when no Redis."""
        limiter = RateLimiter(redis_client=None)
        allowed, remaining, reset = await limiter.is_allowed("127.0.0.1")

        assert allowed is True
        assert remaining == 100  # Default limit
        assert reset == 60  # 1 minute window

    @pytest.mark.asyncio
    async def test_is_allowed_with_redis_under_limit(self):
        """Test rate limiter allows requests under limit."""
        mock_redis = AsyncMock()

        # Create a proper async context manager mock
        mock_pipeline = MagicMock()
        mock_pipeline.zremrangebyscore = AsyncMock()
        mock_pipeline.zcard = AsyncMock()
        mock_pipeline.zadd = AsyncMock()
        mock_pipeline.expire = AsyncMock()
        mock_pipeline.execute = AsyncMock(return_value=[None, 50, None, None])

        async def mock_pipeline_ctx(*args, **kwargs):
            return mock_pipeline

        mock_redis.pipeline = MagicMock(return_value=AsyncContextManager(mock_pipeline))

        limiter = RateLimiter(redis_client=mock_redis)
        allowed, remaining, reset = await limiter.is_allowed("127.0.0.1")

        assert allowed is True
        assert remaining == 49  # 100 - 50 - 1 (current request)

    @pytest.mark.asyncio
    async def test_is_allowed_with_redis_at_limit(self):
        """Test rate limiter blocks requests at limit."""
        mock_redis = AsyncMock()

        # Create a proper async context manager mock
        mock_pipeline = MagicMock()
        mock_pipeline.zremrangebyscore = AsyncMock()
        mock_pipeline.zcard = AsyncMock()
        mock_pipeline.zadd = AsyncMock()
        mock_pipeline.expire = AsyncMock()
        mock_pipeline.execute = AsyncMock(return_value=[None, 100, None, None])

        mock_redis.pipeline = MagicMock(return_value=AsyncContextManager(mock_pipeline))

        limiter = RateLimiter(redis_client=mock_redis)
        allowed, remaining, reset = await limiter.is_allowed("127.0.0.1")

        assert allowed is False
        assert remaining == 0

    @pytest.mark.asyncio
    async def test_is_allowed_fails_open_on_error(self):
        """Test rate limiter allows requests on Redis error."""
        mock_redis = AsyncMock()
        mock_redis.pipeline.side_effect = Exception("Redis connection error")

        limiter = RateLimiter(redis_client=mock_redis)
        allowed, remaining, reset = await limiter.is_allowed("127.0.0.1")

        assert allowed is True  # Fail open

    def test_get_client_key(self):
        """Test Redis key generation."""
        limiter = RateLimiter(redis_client=None)
        key = limiter._get_client_key("192.168.1.1")

        assert key == "rate_limit:192.168.1.1"


class TestGetClientIp:
    """Test cases for get_client_ip."""

    def test_direct_connection(self):
        """Test extracting IP from direct connection."""
        mock_request = MagicMock()
        mock_request.headers.get.return_value = None
        mock_request.client.host = "192.168.1.100"

        ip = get_client_ip(mock_request)
        assert ip == "192.168.1.100"

    def test_forwarded_single_ip(self):
        """Test extracting IP from X-Forwarded-For header."""
        mock_request = MagicMock()
        mock_request.headers.get.return_value = "10.0.0.1"

        ip = get_client_ip(mock_request)
        assert ip == "10.0.0.1"

    def test_forwarded_multiple_ips(self):
        """Test extracting first IP from X-Forwarded-For chain."""
        mock_request = MagicMock()
        mock_request.headers.get.return_value = "10.0.0.1, 10.0.0.2, 10.0.0.3"

        ip = get_client_ip(mock_request)
        assert ip == "10.0.0.1"

    def test_forwarded_with_spaces(self):
        """Test handling spaces in X-Forwarded-For."""
        mock_request = MagicMock()
        mock_request.headers.get.return_value = "  10.0.0.1 , 10.0.0.2"

        ip = get_client_ip(mock_request)
        assert ip == "10.0.0.1"

    def test_no_client_info(self):
        """Test handling missing client info."""
        mock_request = MagicMock()
        mock_request.headers.get.return_value = None
        mock_request.client = None

        ip = get_client_ip(mock_request)
        assert ip == "unknown"
