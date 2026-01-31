"""Tests for embedding service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.embedding_service import EmbeddingService


class TestEmbeddingService:
    """Test cases for EmbeddingService."""

    @pytest.mark.asyncio
    async def test_generate_embedding_returns_3072_dimensions(self):
        """Test that embedding generation returns correct dimensions."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None  # Cache miss
        mock_redis.setex = AsyncMock()

        service = EmbeddingService(redis_client=mock_redis)

        # Mock the HTTP client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"embedding": [0.1] * 3072, "index": 0}
            ]
        }

        with patch.object(service, "_make_api_request", return_value=mock_response):
            embedding = await service.generate_embedding("máy xay sinh tố")

        assert embedding is not None
        assert len(embedding) == 3072

    @pytest.mark.asyncio
    async def test_generate_embedding_uses_cache(self):
        """Test that embedding service uses cache for repeated queries."""
        mock_redis = AsyncMock()
        # Return cached embedding
        cached_embedding = "[" + ",".join(["0.1"] * 3072) + "]"
        mock_redis.get.return_value = cached_embedding

        service = EmbeddingService(redis_client=mock_redis)

        embedding = await service.generate_embedding("máy xay sinh tố")

        assert embedding is not None
        assert len(embedding) == 3072
        # Should not call setex since cache hit
        mock_redis.setex.assert_not_called()

    @pytest.mark.asyncio
    async def test_generate_embedding_caches_result(self):
        """Test that new embeddings are cached."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None  # Cache miss
        mock_redis.setex = AsyncMock()

        service = EmbeddingService(redis_client=mock_redis)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"embedding": [0.1] * 3072, "index": 0}
            ]
        }

        with patch.object(service, "_make_api_request", return_value=mock_response):
            await service.generate_embedding("máy xay sinh tố")

        # Should cache the result
        mock_redis.setex.assert_called_once()
        # Verify TTL is 24 hours (86400 seconds)
        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == 86400

    @pytest.mark.asyncio
    async def test_generate_embedding_retries_on_failure(self):
        """Test that API calls retry on failure with exponential backoff."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.setex = AsyncMock()

        service = EmbeddingService(redis_client=mock_redis)

        # First call fails, second succeeds
        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 500

        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "data": [{"embedding": [0.1] * 3072, "index": 0}]
        }

        call_count = 0
        async def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_response_fail
            return mock_response_success

        with patch.object(service, "_make_api_request", side_effect=mock_request):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                embedding = await service.generate_embedding("test query")

        assert embedding is not None
        assert call_count == 2  # Retried once

    @pytest.mark.asyncio
    async def test_generate_embedding_raises_after_max_retries(self):
        """Test that service raises after exhausting retries."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None

        service = EmbeddingService(redis_client=mock_redis)

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch.object(service, "_make_api_request", return_value=mock_response):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(Exception) as exc_info:
                    await service.generate_embedding("test query")

        assert "Failed to generate embedding" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_batch_embeddings(self):
        """Test batch embedding generation for multiple texts."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.setex = AsyncMock()

        service = EmbeddingService(redis_client=mock_redis)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"embedding": [0.1] * 3072, "index": 0},
                {"embedding": [0.2] * 3072, "index": 1},
            ]
        }

        with patch.object(service, "_make_api_request", return_value=mock_response):
            embeddings = await service.generate_batch_embeddings(
                ["text 1", "text 2"]
            )

        assert len(embeddings) == 2
        assert all(len(e) == 3072 for e in embeddings)

    @pytest.mark.asyncio
    async def test_cache_key_generation(self):
        """Test that cache keys are generated correctly."""
        service = EmbeddingService(redis_client=None)  # type: ignore

        key1 = service._get_cache_key("máy xay sinh tố")
        key2 = service._get_cache_key("máy xay sinh tố")
        key3 = service._get_cache_key("different query")

        # Same query should produce same key
        assert key1 == key2
        # Different query should produce different key
        assert key1 != key3
        # Key should have prefix
        assert key1.startswith("emb:")

    @pytest.mark.asyncio
    async def test_generate_embedding_handles_empty_input(self):
        """Test that empty input raises appropriate error."""
        mock_redis = AsyncMock()
        service = EmbeddingService(redis_client=mock_redis)

        with pytest.raises(ValueError) as exc_info:
            await service.generate_embedding("")

        assert "empty" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_generate_embedding_handles_whitespace_input(self):
        """Test that whitespace-only input raises appropriate error."""
        mock_redis = AsyncMock()
        service = EmbeddingService(redis_client=mock_redis)

        with pytest.raises(ValueError) as exc_info:
            await service.generate_embedding("   ")

        assert "empty" in str(exc_info.value).lower()
