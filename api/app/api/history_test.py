"""Tests for search history API endpoints."""

from unittest.mock import AsyncMock, patch

import pytest

from app.api.history import list_history, record_search
from app.schemas.search_history import SearchHistoryCreate


class TestRecordSearch:
    """Tests for POST /api/history."""

    @pytest.mark.asyncio
    async def test_records_search_returns_201(self):
        """Test records search and returns envelope response."""
        mock_db = AsyncMock()
        user = {"id": 10, "email": "user@example.com", "role": "user"}
        body = SearchHistoryCreate(query="laptop", selected_hs_code_id=100)

        with patch("app.api.history.SearchHistoryService") as mock_cls:
            mock_service = AsyncMock()
            mock_service.record_search.return_value = {
                "id": 1,
                "user_id": 10,
                "query": "laptop",
                "selected_hs_code_id": 100,
                "selected_hs_code": "84713000",
                "selected_description_vn": "Máy tính xách tay",
                "created_at": "2026-02-21T00:00:00+00:00",
            }
            mock_cls.return_value = mock_service

            result = await record_search(body=body, current_user=user, db=mock_db)

        assert result["success"] is True
        assert result["data"]["id"] == 1
        assert result["data"]["query"] == "laptop"
        assert result["data"]["selected_hs_code"] == "84713000"

    @pytest.mark.asyncio
    async def test_records_search_without_hs_code(self):
        """Test records search with null selected_hs_code_id."""
        mock_db = AsyncMock()
        user = {"id": 10, "email": "user@example.com", "role": "user"}
        body = SearchHistoryCreate(query="unknown item", selected_hs_code_id=None)

        with patch("app.api.history.SearchHistoryService") as mock_cls:
            mock_service = AsyncMock()
            mock_service.record_search.return_value = {
                "id": 2,
                "user_id": 10,
                "query": "unknown item",
                "selected_hs_code_id": None,
                "selected_hs_code": None,
                "selected_description_vn": None,
                "created_at": "2026-02-21T00:00:00+00:00",
            }
            mock_cls.return_value = mock_service

            result = await record_search(body=body, current_user=user, db=mock_db)

        assert result["success"] is True
        assert result["data"]["selected_hs_code_id"] is None
        assert result["data"]["selected_hs_code"] is None


class TestListHistory:
    """Tests for GET /api/history."""

    @pytest.mark.asyncio
    async def test_returns_paginated_history(self):
        """Test returns paginated history list."""
        mock_db = AsyncMock()
        user = {"id": 10, "email": "user@example.com", "role": "user"}

        with patch("app.api.history.SearchHistoryService") as mock_cls:
            mock_service = AsyncMock()
            mock_service.list_history.return_value = {
                "items": [
                    {
                        "id": 1,
                        "user_id": 10,
                        "query": "laptop",
                        "selected_hs_code_id": 100,
                        "selected_hs_code": "84713000",
                        "selected_description_vn": "Máy tính xách tay",
                        "created_at": "2026-02-21T00:00:00+00:00",
                    }
                ],
                "total": 1,
            }
            mock_cls.return_value = mock_service

            result = await list_history(
                current_user=user, db=mock_db, limit=20, offset=0
            )

        assert result["success"] is True
        assert result["data"]["total"] == 1
        assert len(result["data"]["items"]) == 1

    @pytest.mark.asyncio
    async def test_returns_empty_history(self):
        """Test returns empty list when no history."""
        mock_db = AsyncMock()
        user = {"id": 10, "email": "user@example.com", "role": "user"}

        with patch("app.api.history.SearchHistoryService") as mock_cls:
            mock_service = AsyncMock()
            mock_service.list_history.return_value = {"items": [], "total": 0}
            mock_cls.return_value = mock_service

            result = await list_history(
                current_user=user, db=mock_db, limit=20, offset=0
            )

        assert result["success"] is True
        assert result["data"]["total"] == 0
        assert result["data"]["items"] == []

    @pytest.mark.asyncio
    async def test_passes_pagination_params(self):
        """Test passes limit and offset to service."""
        mock_db = AsyncMock()
        user = {"id": 10, "email": "user@example.com", "role": "user"}

        with patch("app.api.history.SearchHistoryService") as mock_cls:
            mock_service = AsyncMock()
            mock_service.list_history.return_value = {"items": [], "total": 0}
            mock_cls.return_value = mock_service

            await list_history(current_user=user, db=mock_db, limit=5, offset=10)

            mock_service.list_history.assert_called_once_with(10, 5, 10)
