"""Repository for hybrid search data access."""

import re
from typing import NamedTuple

from pgvector.sqlalchemy import Vector
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.hs_code import HSCode
from app.models.hs_subheading import HSSubheading
from app.models.hs_heading import HSHeading


class SearchResult(NamedTuple):
    """Search result with HS code and scores."""

    hs_code: HSCode
    vector_score: float | None  # Cosine similarity (0-1)
    fuzzy_score: float | None  # pg_trgm similarity (0-1)
    is_exact_match: bool


class SearchRepository:
    """Repository for hybrid search database operations.

    Implements three search strategies:
    1. Vector similarity search using pgvector (cosine similarity)
    2. Fuzzy text search using pg_trgm on descriptions
    3. Exact HS code match for 8-digit codes
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    @staticmethod
    def is_hs_code_pattern(query: str) -> bool:
        """Check if query looks like an HS code (8 digits, with or without periods).

        Args:
            query: The search query

        Returns:
            True if query matches HS code pattern
        """
        # Remove periods and whitespace
        cleaned = re.sub(r"[\s.]", "", query)
        return bool(re.match(r"^\d{8}$", cleaned))

    @staticmethod
    def normalize_hs_code(query: str) -> str:
        """Normalize HS code by removing periods and whitespace.

        Args:
            query: The HS code query (e.g., "7418.20.00" or "74182000")

        Returns:
            Normalized 8-digit code (e.g., "74182000")
        """
        return re.sub(r"[\s.]", "", query)

    async def search_exact_match(self, code: str) -> SearchResult | None:
        """Search for exact HS code match.

        Args:
            code: The 8-digit HS code (normalized, no periods)

        Returns:
            SearchResult with 100% confidence if found, None otherwise
        """
        result = await self.session.execute(
            select(HSCode)
            .where(HSCode.code == code)
            .options(
                selectinload(HSCode.fta_rates),
                selectinload(HSCode.subheading).selectinload(HSSubheading.heading).selectinload(HSHeading.chapter),
            )
        )
        hs_code = result.scalar_one_or_none()

        if hs_code:
            return SearchResult(
                hs_code=hs_code,
                vector_score=1.0,
                fuzzy_score=1.0,
                is_exact_match=True,
            )
        return None

    async def search_by_vector(
        self,
        embedding: list[float],
        limit: int = 20,
    ) -> list[SearchResult]:
        """Search using vector similarity (cosine).

        Args:
            embedding: Query embedding (3072 dimensions)
            limit: Maximum results to return

        Returns:
            List of SearchResults with vector scores
        """
        # Use pgvector cosine distance operator (<=>)
        # Lower distance = more similar, so we compute 1 - distance for similarity
        distance = HSCode.embedding.cosine_distance(embedding)

        result = await self.session.execute(
            select(HSCode, (1 - distance).label("similarity"))
            .where(HSCode.embedding.is_not(None))
            .order_by(distance)
            .limit(limit)
            .options(
                selectinload(HSCode.fta_rates),
                selectinload(HSCode.subheading).selectinload(HSSubheading.heading).selectinload(HSHeading.chapter),
            )
        )

        return [
            SearchResult(
                hs_code=row.HSCode,
                vector_score=float(row.similarity),
                fuzzy_score=None,
                is_exact_match=False,
            )
            for row in result.all()
        ]

    async def search_by_fuzzy(
        self,
        query: str,
        limit: int = 20,
    ) -> list[SearchResult]:
        """Search using pg_trgm fuzzy matching on descriptions.

        Args:
            query: Search query text
            limit: Maximum results to return

        Returns:
            List of SearchResults with fuzzy scores
        """
        # Use pg_trgm similarity function on both Vietnamese and English descriptions
        vn_similarity = func.similarity(HSCode.description_vn, query)
        en_similarity = func.similarity(HSCode.description_en, query)
        # Take the maximum similarity from either language
        max_similarity = func.greatest(vn_similarity, en_similarity)

        result = await self.session.execute(
            select(HSCode, max_similarity.label("similarity"))
            .where(max_similarity > 0.1)  # Minimum threshold
            .order_by(max_similarity.desc())
            .limit(limit)
            .options(
                selectinload(HSCode.fta_rates),
                selectinload(HSCode.subheading).selectinload(HSSubheading.heading).selectinload(HSHeading.chapter),
            )
        )

        return [
            SearchResult(
                hs_code=row.HSCode,
                vector_score=None,
                fuzzy_score=float(row.similarity),
                is_exact_match=False,
            )
            for row in result.all()
        ]

    async def hybrid_search(
        self,
        query: str,
        embedding: list[float] | None,
        limit: int = 20,
    ) -> list[SearchResult]:
        """Perform hybrid search combining all strategies.

        Search strategy:
        1. Check for exact HS code match first
        2. Run vector and fuzzy search in parallel
        3. Merge and deduplicate results

        Args:
            query: Search query text
            embedding: Query embedding (can be None if not available)
            limit: Maximum results to return

        Returns:
            List of SearchResults with combined scores
        """
        # Check for exact HS code match first
        if self.is_hs_code_pattern(query):
            normalized_code = self.normalize_hs_code(query)
            exact_result = await self.search_exact_match(normalized_code)
            if exact_result:
                return [exact_result]

        results_map: dict[str, SearchResult] = {}

        # Fetch slightly more than limit to account for merging/deduplication
        # but not too much to avoid over-fetching
        internal_limit = min(limit * 2, 30)

        # Vector search if embedding available
        if embedding:
            vector_results = await self.search_by_vector(embedding, internal_limit)
            for result in vector_results:
                code = result.hs_code.code
                results_map[code] = result

        # Fuzzy search
        fuzzy_results = await self.search_by_fuzzy(query, internal_limit)
        for result in fuzzy_results:
            code = result.hs_code.code
            if code in results_map:
                # Merge scores - keep existing result but add fuzzy score
                existing = results_map[code]
                results_map[code] = SearchResult(
                    hs_code=existing.hs_code,
                    vector_score=existing.vector_score,
                    fuzzy_score=result.fuzzy_score,
                    is_exact_match=False,
                )
            else:
                results_map[code] = result

        # Sort by combined score
        def combined_score(result: SearchResult) -> float:
            """Calculate combined score (weighted average)."""
            v_score = result.vector_score or 0
            f_score = result.fuzzy_score or 0

            # If both scores present, weighted average (60% vector, 40% fuzzy)
            if result.vector_score is not None and result.fuzzy_score is not None:
                return 0.6 * v_score + 0.4 * f_score
            # If only one score, use it
            return max(v_score, f_score)

        sorted_results = sorted(
            results_map.values(),
            key=combined_score,
            reverse=True,
        )

        return sorted_results[:limit]
