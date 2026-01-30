"""Search service for hybrid HS code search."""

from dataclasses import dataclass

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.search_repository import SearchRepository, SearchResult
from app.services.embedding_service import EmbeddingService


@dataclass
class SearchResultItem:
    """A single search result with all relevant data."""

    hs_code: str
    description_vn: str
    description_en: str
    duty_rate: float
    vat_rate: float
    unit: str | None
    confidence: int  # 0-100 percentage
    is_exact_match: bool
    # Full HS code object for classification analysis
    hs_code_full: object = None


class SearchService:
    """Service for hybrid HS code search.

    Combines three search strategies:
    1. Vector similarity (pgvector) - semantic matching
    2. Fuzzy text (pg_trgm) - typo tolerance
    3. Exact match - direct HS code lookup

    Confidence calculation:
    - Exact match: 100%
    - Vector/fuzzy: normalized to 0-100%
    - Combined: weighted average (60% vector, 40% fuzzy)
    """

    def __init__(
        self,
        session: AsyncSession,
        redis_client: redis.Redis | None = None,  # type: ignore[type-arg]
    ):
        """Initialize search service.

        Args:
            session: Database session for queries
            redis_client: Redis client for embedding cache
        """
        self.repository = SearchRepository(session)
        self.embedding_service = EmbeddingService(redis_client=redis_client)

    def _calculate_confidence(self, result: SearchResult) -> int:
        """Calculate confidence score as percentage (0-100).

        Args:
            result: Search result with scores

        Returns:
            Confidence percentage (0-100)
        """
        if result.is_exact_match:
            return 100

        v_score = result.vector_score or 0
        f_score = result.fuzzy_score or 0

        # If both scores present, weighted average
        if result.vector_score is not None and result.fuzzy_score is not None:
            combined = 0.6 * v_score + 0.4 * f_score
        else:
            # Use whichever is available
            combined = max(v_score, f_score)

        # Convert to percentage and cap at 99 for non-exact matches
        confidence = min(int(combined * 100), 99)
        return max(confidence, 0)

    async def search(
        self,
        query: str,
        limit: int = 10,
    ) -> list[SearchResultItem]:
        """Search for HS codes using hybrid search.

        Args:
            query: Search query (product description or HS code)
            limit: Maximum number of results

        Returns:
            List of SearchResultItem with confidence scores

        Raises:
            ValueError: If query is empty
        """
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty")

        query = query.strip()

        # Check if query is an HS code pattern - don't generate embedding
        is_code_query = self.repository.is_hs_code_pattern(query)

        # Generate embedding for text queries
        embedding: list[float] | None = None
        if not is_code_query:
            try:
                embedding = await self.embedding_service.generate_embedding(query)
            except Exception:
                # If embedding fails, fall back to fuzzy search only
                embedding = None

        # Perform hybrid search
        results = await self.repository.hybrid_search(
            query=query,
            embedding=embedding,
            limit=limit,
        )

        # Convert to SearchResultItem
        return [
            SearchResultItem(
                hs_code=r.hs_code.code,
                description_vn=r.hs_code.description_vn,
                description_en=r.hs_code.description_en,
                duty_rate=float(r.hs_code.duty_rate),
                vat_rate=float(r.hs_code.vat_rate),
                unit=r.hs_code.unit,
                confidence=self._calculate_confidence(r),
                is_exact_match=r.is_exact_match,
                hs_code_full=r.hs_code,
            )
            for r in results
        ]

    async def search_single(self, query: str) -> SearchResultItem | None:
        """Search and return the best matching result.

        Args:
            query: Search query

        Returns:
            Best matching result or None if no results
        """
        results = await self.search(query, limit=1)
        return results[0] if results else None
