"""Tests for favorites service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.favorite import Favorite
from app.models.hs_code import HSCode
from app.services.favorites_service import (
    DuplicateFavoriteError,
    FavoritesService,
)


def _make_favorite(fav_id=1, user_id=10, hs_code_id=100):
    """Create a mock Favorite with hs_code relationship."""
    fav = MagicMock(spec=Favorite)
    fav.id = fav_id
    fav.user_id = user_id
    fav.hs_code_id = hs_code_id
    fav.notes = None
    fav.created_at = MagicMock()
    fav.created_at.isoformat.return_value = "2026-02-21T00:00:00+00:00"

    hs = MagicMock(spec=HSCode)
    hs.code = "01012100"
    hs.description_vn = "Ngựa thuần chủng"
    fav.hs_code = hs
    return fav


class TestFavoritesServiceListFavorites:
    """Tests for FavoritesService.list_favorites."""

    @pytest.mark.asyncio
    async def test_returns_formatted_list(self):
        """Test list_favorites returns list of dicts with HS code details."""
        db = AsyncMock()

        with patch(
            "app.services.favorites_service.FavoritesRepository"
        ) as mock_repo_cls:
            mock_repo = AsyncMock()
            mock_repo.get_by_user.return_value = [
                _make_favorite(1, 10, 100),
                _make_favorite(2, 10, 200),
            ]
            mock_repo_cls.return_value = mock_repo

            service = FavoritesService(db)
            result = await service.list_favorites(10)

        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[0]["hs_code"] == "01012100"
        assert result[0]["description_vn"] == "Ngựa thuần chủng"
        assert result[1]["id"] == 2

    @pytest.mark.asyncio
    async def test_returns_empty_list(self):
        """Test returns empty list when user has no favorites."""
        db = AsyncMock()

        with patch(
            "app.services.favorites_service.FavoritesRepository"
        ) as mock_repo_cls:
            mock_repo = AsyncMock()
            mock_repo.get_by_user.return_value = []
            mock_repo_cls.return_value = mock_repo

            service = FavoritesService(db)
            result = await service.list_favorites(10)

        assert result == []


class TestFavoritesServiceAddFavorite:
    """Tests for FavoritesService.add_favorite."""

    @pytest.mark.asyncio
    async def test_creates_and_returns_response(self):
        """Test add_favorite creates favorite and returns response dict."""
        db = AsyncMock()
        hs_code = MagicMock(spec=HSCode)
        hs_code.id = 100

        mock_exec_result = MagicMock()
        mock_exec_result.scalar_one_or_none.return_value = hs_code
        db.execute.return_value = mock_exec_result

        with patch(
            "app.services.favorites_service.FavoritesRepository"
        ) as mock_repo_cls:
            mock_repo = AsyncMock()
            mock_repo.get_by_user_and_code.return_value = None
            mock_repo.create.return_value = _make_favorite(1, 10, 100)
            mock_repo_cls.return_value = mock_repo

            service = FavoritesService(db)
            result = await service.add_favorite(10, 100)

        assert result["id"] == 1
        assert result["hs_code"] == "01012100"
        db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_raises_on_duplicate(self):
        """Test add_favorite raises DuplicateFavoriteError for existing favorite."""
        db = AsyncMock()
        hs_code = MagicMock(spec=HSCode)
        hs_code.id = 100

        mock_exec_result = MagicMock()
        mock_exec_result.scalar_one_or_none.return_value = hs_code
        db.execute.return_value = mock_exec_result

        with patch(
            "app.services.favorites_service.FavoritesRepository"
        ) as mock_repo_cls:
            mock_repo = AsyncMock()
            mock_repo.get_by_user_and_code.return_value = _make_favorite(1, 10, 100)
            mock_repo_cls.return_value = mock_repo

            service = FavoritesService(db)
            with pytest.raises(DuplicateFavoriteError):
                await service.add_favorite(10, 100)

    @pytest.mark.asyncio
    async def test_raises_on_invalid_hs_code(self):
        """Test add_favorite raises ValueError for nonexistent HS code."""
        db = AsyncMock()

        mock_exec_result = MagicMock()
        mock_exec_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_exec_result

        with patch(
            "app.services.favorites_service.FavoritesRepository"
        ) as mock_repo_cls:
            mock_repo_cls.return_value = AsyncMock()

            service = FavoritesService(db)
            with pytest.raises(ValueError, match="HS code not found"):
                await service.add_favorite(10, 99999)


class TestFavoritesServiceRemoveFavorite:
    """Tests for FavoritesService.remove_favorite."""

    @pytest.mark.asyncio
    async def test_removes_and_commits(self):
        """Test remove_favorite deletes and commits."""
        db = AsyncMock()

        with patch(
            "app.services.favorites_service.FavoritesRepository"
        ) as mock_repo_cls:
            mock_repo = AsyncMock()
            mock_repo.delete.return_value = True
            mock_repo_cls.return_value = mock_repo

            service = FavoritesService(db)
            result = await service.remove_favorite(1, 10)

        assert result is True
        db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_false_when_not_found(self):
        """Test remove_favorite returns False and does not commit."""
        db = AsyncMock()

        with patch(
            "app.services.favorites_service.FavoritesRepository"
        ) as mock_repo_cls:
            mock_repo = AsyncMock()
            mock_repo.delete.return_value = False
            mock_repo_cls.return_value = mock_repo

            service = FavoritesService(db)
            result = await service.remove_favorite(999, 10)

        assert result is False
        db.commit.assert_not_awaited()
