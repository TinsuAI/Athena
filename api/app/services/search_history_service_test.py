"""Tests for search history service."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.search_history_service import SearchHistoryService


def _make_entry(
    id: int = 1,
    user_id: int = 10,
    query: str = "laptop",
    selected_hs_code_id: int | None = 100,
    hs_code_code: str | None = "84713000",
    hs_code_desc: str | None = "Máy tính xách tay",
) -> MagicMock:
    """Create a mock SearchHistory entry."""
    entry = MagicMock()
    entry.id = id
    entry.user_id = user_id
    entry.query = query
    entry.selected_hs_code_id = selected_hs_code_id
    entry.created_at = datetime(2026, 2, 21, tzinfo=timezone.utc)

    if hs_code_code:
        entry.hs_code = MagicMock()
        entry.hs_code.code = hs_code_code
        entry.hs_code.description_vn = hs_code_desc
    else:
        entry.hs_code = None

    return entry


class TestRecordSearch:
    """Tests for SearchHistoryService.record_search."""

    @pytest.mark.asyncio
    async def test_record_search_with_hs_code(self):
        """Test recording search with a selected HS code."""
        mock_db = AsyncMock()
        entry = _make_entry()

        with patch(
            "app.services.search_history_service.SearchHistoryRepository"
        ) as mock_repo_cls:
            mock_repo = AsyncMock()
            mock_repo.create.return_value = entry
            mock_repo_cls.return_value = mock_repo

            service = SearchHistoryService(mock_db)
            result = await service.record_search(10, "laptop", 100)

        assert result["id"] == 1
        assert result["query"] == "laptop"
        assert result["selected_hs_code"] == "84713000"
        assert result["selected_description_vn"] == "Máy tính xách tay"
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_search_without_hs_code(self):
        """Test recording search without a selected HS code."""
        mock_db = AsyncMock()
        entry = _make_entry(selected_hs_code_id=None, hs_code_code=None, hs_code_desc=None)

        with patch(
            "app.services.search_history_service.SearchHistoryRepository"
        ) as mock_repo_cls:
            mock_repo = AsyncMock()
            mock_repo.create.return_value = entry
            mock_repo_cls.return_value = mock_repo

            service = SearchHistoryService(mock_db)
            result = await service.record_search(10, "unknown", None)

        assert result["selected_hs_code"] is None
        assert result["selected_description_vn"] is None


class TestListHistory:
    """Tests for SearchHistoryService.list_history."""

    @pytest.mark.asyncio
    async def test_list_history_returns_items_and_total(self):
        """Test listing history returns items with total count."""
        mock_db = AsyncMock()
        entries = [_make_entry(id=1), _make_entry(id=2, query="phone")]

        with patch(
            "app.services.search_history_service.SearchHistoryRepository"
        ) as mock_repo_cls:
            mock_repo = AsyncMock()
            mock_repo.get_by_user.return_value = entries
            mock_repo.count_by_user.return_value = 5
            mock_repo_cls.return_value = mock_repo

            service = SearchHistoryService(mock_db)
            result = await service.list_history(10, 2, 0)

        assert len(result["items"]) == 2
        assert result["total"] == 5

    @pytest.mark.asyncio
    async def test_list_history_empty(self):
        """Test listing history when no entries exist."""
        mock_db = AsyncMock()

        with patch(
            "app.services.search_history_service.SearchHistoryRepository"
        ) as mock_repo_cls:
            mock_repo = AsyncMock()
            mock_repo.get_by_user.return_value = []
            mock_repo.count_by_user.return_value = 0
            mock_repo_cls.return_value = mock_repo

            service = SearchHistoryService(mock_db)
            result = await service.list_history(10, 20, 0)

        assert result["items"] == []
        assert result["total"] == 0
