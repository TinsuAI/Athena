"""Tests for search history repository."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.repositories.search_history_repository import SearchHistoryRepository


class TestCreate:
    """Tests for SearchHistoryRepository.create."""

    @pytest.mark.asyncio
    async def test_create_adds_entry(self):
        """Test create adds entry to session and flushes."""
        mock_db = AsyncMock()
        repo = SearchHistoryRepository(mock_db)

        with patch(
            "app.repositories.search_history_repository.SearchHistory"
        ) as mock_model:
            mock_entry = MagicMock()
            mock_model.return_value = mock_entry

            result = await repo.create(10, "laptop", 100)

        mock_db.add.assert_called_once_with(mock_entry)
        mock_db.flush.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_entry, ["hs_code"])
        assert result == mock_entry

    @pytest.mark.asyncio
    async def test_create_with_null_hs_code(self):
        """Test create with null selected_hs_code_id."""
        mock_db = AsyncMock()
        repo = SearchHistoryRepository(mock_db)

        with patch(
            "app.repositories.search_history_repository.SearchHistory"
        ) as mock_model:
            mock_entry = MagicMock()
            mock_model.return_value = mock_entry

            result = await repo.create(10, "unknown item", None)

        mock_model.assert_called_once_with(
            user_id=10, query="unknown item", selected_hs_code_id=None
        )
        assert result == mock_entry


class TestGetByUser:
    """Tests for SearchHistoryRepository.get_by_user."""

    @pytest.mark.asyncio
    async def test_get_by_user_returns_list(self):
        """Test get_by_user executes query and returns list."""
        mock_db = AsyncMock()
        mock_entries = [MagicMock(), MagicMock()]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_entries
        mock_db.execute.return_value = mock_result

        repo = SearchHistoryRepository(mock_db)
        result = await repo.get_by_user(10, limit=5, offset=0)

        assert len(result) == 2
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_user_pagination(self):
        """Test get_by_user passes limit and offset to query."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [MagicMock()]
        mock_db.execute.return_value = mock_result

        repo = SearchHistoryRepository(mock_db)
        result = await repo.get_by_user(10, limit=3, offset=6)

        assert len(result) == 1
        # Verify the query was built — the execute call contains the compiled statement
        stmt = mock_db.execute.call_args[0][0]
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "LIMIT 3" in compiled
        assert "OFFSET 6" in compiled


class TestCountByUser:
    """Tests for SearchHistoryRepository.count_by_user."""

    @pytest.mark.asyncio
    async def test_count_by_user_returns_count(self):
        """Test count_by_user returns integer count."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 42
        mock_db.execute.return_value = mock_result

        repo = SearchHistoryRepository(mock_db)
        result = await repo.count_by_user(10)

        assert result == 42
        mock_db.execute.assert_called_once()
