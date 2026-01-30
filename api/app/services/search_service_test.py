"""Tests for search service."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.search_service import SearchService


class TestSearchService:
    """Test cases for SearchService."""

    @pytest.mark.asyncio
    async def test_search_rejects_empty_query(self):
        """Test that empty query raises ValueError."""
        mock_session = AsyncMock()
        service = SearchService(session=mock_session)

        with pytest.raises(ValueError) as exc_info:
            await service.search("")

        assert "empty" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_search_rejects_whitespace_query(self):
        """Test that whitespace-only query raises ValueError."""
        mock_session = AsyncMock()
        service = SearchService(session=mock_session)

        with pytest.raises(ValueError) as exc_info:
            await service.search("   ")

        assert "empty" in str(exc_info.value).lower()

    def test_calculate_confidence_exact_match(self):
        """Test that exact match returns 100% confidence."""
        mock_session = AsyncMock()
        service = SearchService(session=mock_session)

        # Create mock result
        mock_hs_code = MagicMock()
        mock_result = MagicMock()
        mock_result.hs_code = mock_hs_code
        mock_result.vector_score = 0.95
        mock_result.fuzzy_score = 0.8
        mock_result.is_exact_match = True

        confidence = service._calculate_confidence(mock_result)
        assert confidence == 100

    def test_calculate_confidence_vector_only(self):
        """Test confidence calculation with vector score only."""
        mock_session = AsyncMock()
        service = SearchService(session=mock_session)

        mock_result = MagicMock()
        mock_result.vector_score = 0.85
        mock_result.fuzzy_score = None
        mock_result.is_exact_match = False

        confidence = service._calculate_confidence(mock_result)
        assert confidence == 85

    def test_calculate_confidence_fuzzy_only(self):
        """Test confidence calculation with fuzzy score only."""
        mock_session = AsyncMock()
        service = SearchService(session=mock_session)

        mock_result = MagicMock()
        mock_result.vector_score = None
        mock_result.fuzzy_score = 0.72
        mock_result.is_exact_match = False

        confidence = service._calculate_confidence(mock_result)
        assert confidence == 72

    def test_calculate_confidence_combined(self):
        """Test confidence calculation with both scores."""
        mock_session = AsyncMock()
        service = SearchService(session=mock_session)

        mock_result = MagicMock()
        mock_result.vector_score = 0.9  # 60% weight
        mock_result.fuzzy_score = 0.7   # 40% weight
        mock_result.is_exact_match = False

        confidence = service._calculate_confidence(mock_result)
        # Expected: 0.6 * 0.9 + 0.4 * 0.7 = 0.54 + 0.28 = 0.82 -> 82%
        assert confidence == 82

    def test_calculate_confidence_capped_at_99(self):
        """Test that non-exact match is capped at 99%."""
        mock_session = AsyncMock()
        service = SearchService(session=mock_session)

        mock_result = MagicMock()
        mock_result.vector_score = 1.0
        mock_result.fuzzy_score = 1.0
        mock_result.is_exact_match = False

        confidence = service._calculate_confidence(mock_result)
        assert confidence == 99  # Capped at 99 for non-exact

    def test_calculate_confidence_minimum_zero(self):
        """Test that confidence doesn't go below 0."""
        mock_session = AsyncMock()
        service = SearchService(session=mock_session)

        mock_result = MagicMock()
        mock_result.vector_score = -0.1  # Edge case
        mock_result.fuzzy_score = None
        mock_result.is_exact_match = False

        confidence = service._calculate_confidence(mock_result)
        assert confidence == 0

    @pytest.mark.asyncio
    async def test_search_single_returns_none_for_no_results(self):
        """Test search_single returns None when no results."""
        mock_session = AsyncMock()
        service = SearchService(session=mock_session)

        # Mock the search method to return empty list
        service.search = AsyncMock(return_value=[])

        result = await service.search_single("nonexistent query")
        assert result is None

    @pytest.mark.asyncio
    async def test_search_single_returns_first_result(self):
        """Test search_single returns first result."""
        mock_session = AsyncMock()
        service = SearchService(session=mock_session)

        mock_result = MagicMock()
        mock_result.hs_code = "74182000"

        # Mock the search method
        service.search = AsyncMock(return_value=[mock_result])

        result = await service.search_single("towel rack")
        assert result is not None
        assert result.hs_code == "74182000"
