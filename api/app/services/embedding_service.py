"""Embedding service for generating text embeddings via OpenRouter API."""

import asyncio
import hashlib
import json
from typing import Any

import httpx
import redis.asyncio as redis

from app.core.config import get_settings

settings = get_settings()

# OpenRouter API configuration
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/embeddings"
OPENROUTER_MODEL = "openai/text-embedding-3-large"

# Cache TTL constants
EMBEDDING_CACHE_TTL = 86400  # 24 hours for embedding cache


class EmbeddingService:
    """Service for generating text embeddings using OpenRouter API.

    Features:
    - Integrates with OpenRouter API for embedding generation
    - Redis caching for repeated queries (24-hour TTL)
    - Retry logic with exponential backoff for API failures
    - Batch processing support for multiple texts
    """

    def __init__(self, redis_client: redis.Redis | None = None):  # type: ignore[type-arg]
        """Initialize embedding service.

        Args:
            redis_client: Redis client for caching. If None, caching is disabled.

        Raises:
            ValueError: If OPENROUTER_API_KEY is not configured
        """
        self.redis_client = redis_client
        self.api_key = settings.openrouter_api_key
        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY environment variable is required but not set. "
                "Please configure it in your .env file."
            )
        self.max_retries = 3
        self.base_delay = 1.0  # Base delay for exponential backoff (seconds)

    def _get_cache_key(self, text: str) -> str:
        """Generate a cache key for the given text.

        Uses MD5 hash to create a consistent, compact key.

        Args:
            text: The input text to hash

        Returns:
            Cache key with 'emb:' prefix
        """
        text_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
        return f"emb:{text_hash}"

    async def _make_api_request(
        self,
        texts: list[str],
    ) -> httpx.Response:
        """Make HTTP request to OpenRouter API.

        Args:
            texts: List of texts to embed

        Returns:
            HTTP response from OpenRouter
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://athena.example.com",  # Required by OpenRouter
            "X-Title": "Athena HS Code Lookup",
        }

        payload = {
            "model": OPENROUTER_MODEL,
            "input": texts if len(texts) > 1 else texts[0],
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                OPENROUTER_API_URL,
                headers=headers,
                json=payload,
            )
            return response

    async def _get_from_cache(self, text: str) -> list[float] | None:
        """Try to get embedding from cache.

        Args:
            text: The input text

        Returns:
            Cached embedding or None if not found
        """
        if not self.redis_client:
            return None

        cache_key = self._get_cache_key(text)
        cached = await self.redis_client.get(cache_key)

        if cached:
            return json.loads(cached)

        return None

    async def _save_to_cache(self, text: str, embedding: list[float]) -> None:
        """Save embedding to cache.

        Args:
            text: The input text
            embedding: The embedding to cache
        """
        if not self.redis_client:
            return

        cache_key = self._get_cache_key(text)
        await self.redis_client.setex(
            cache_key,
            EMBEDDING_CACHE_TTL,
            json.dumps(embedding),
        )

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for a single text.

        Features:
        - Checks cache first for repeated queries
        - Retries with exponential backoff on API failures
        - Caches successful results

        Args:
            text: The text to embed

        Returns:
            3072-dimensional embedding vector

        Raises:
            ValueError: If text is empty or whitespace-only
            Exception: If API fails after max retries
        """
        # Validate input
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty or whitespace-only")

        text = text.strip()

        # Try cache first
        cached = await self._get_from_cache(text)
        if cached:
            return cached

        # Make API request with retries
        embedding = await self._generate_with_retry([text])

        # Cache the result
        await self._save_to_cache(text, embedding[0])

        return embedding[0]

    async def _generate_with_retry(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings with retry logic.

        Args:
            texts: List of texts to embed

        Returns:
            List of embeddings

        Raises:
            Exception: If all retries fail
        """
        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                response = await self._make_api_request(texts)

                if response.status_code == 200:
                    data = response.json()
                    # Sort by index to ensure correct order
                    sorted_data = sorted(data["data"], key=lambda x: x["index"])
                    return [item["embedding"] for item in sorted_data]

                # Non-200 response, will retry
                last_error = Exception(
                    f"OpenRouter API error: {response.status_code} - {response.text}"
                )

            except httpx.RequestError as e:
                last_error = e

            # Exponential backoff before retry
            if attempt < self.max_retries - 1:
                delay = self.base_delay * (2 ** attempt)
                await asyncio.sleep(delay)

        raise Exception(
            f"Failed to generate embedding after {self.max_retries} retries. "
            f"Last error: {last_error}"
        )

    async def generate_batch_embeddings(
        self,
        texts: list[str],
        batch_size: int = 100,
    ) -> list[list[float]]:
        """Generate embeddings for multiple texts in batches.

        Respects API rate limits by batching requests.

        Args:
            texts: List of texts to embed
            batch_size: Number of texts per API call (default 100)

        Returns:
            List of embeddings in same order as input texts
        """
        if not texts:
            return []

        all_embeddings: list[list[float]] = []
        uncached_texts: list[str] = []
        uncached_indices: list[int] = []
        results: dict[int, list[float]] = {}

        # Check cache for each text
        for i, text in enumerate(texts):
            text = text.strip()
            if not text:
                raise ValueError(f"Text at index {i} is empty or whitespace-only")

            try:
                cached = await self._get_from_cache(text)
                if cached:
                    results[i] = cached
                else:
                    uncached_texts.append(text)
                    uncached_indices.append(i)
            except Exception:
                # Cache lookup failed, treat as cache miss
                uncached_texts.append(text)
                uncached_indices.append(i)

        # Generate embeddings for uncached texts in batches
        for batch_start in range(0, len(uncached_texts), batch_size):
            batch_end = min(batch_start + batch_size, len(uncached_texts))
            batch = uncached_texts[batch_start:batch_end]
            batch_indices = uncached_indices[batch_start:batch_end]

            embeddings = await self._generate_with_retry(batch)

            # Cache and store results
            for idx, text, embedding in zip(batch_indices, batch, embeddings):
                await self._save_to_cache(text, embedding)
                results[idx] = embedding

        # Return embeddings in original order
        return [results[i] for i in range(len(texts))]
