"""Tests for favorites repository."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.favorite import Favorite
from app.repositories.favorites_repository import FavoritesRepository


class TestFavoritesRepositoryGetByUser:
    """Tests for FavoritesRepository.get_by_user."""

    @pytest.mark.asyncio
    async def test_get_by_user_returns_favorites(self):
        """Test returns list of favorites for a user."""
        db = AsyncMock()
        fav1 = MagicMock(spec=Favorite)
        fav1.id = 1
        fav1.user_id = 10
        fav1.hs_code_id = 100

        fav2 = MagicMock(spec=Favorite)
        fav2.id = 2
        fav2.user_id = 10
        fav2.hs_code_id = 200

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [fav1, fav2]
        db.execute.return_value = mock_result

        repo = FavoritesRepository(db)
        result = await repo.get_by_user(10)

        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 2
        db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_by_user_returns_empty_list(self):
        """Test returns empty list when user has no favorites."""
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute.return_value = mock_result

        repo = FavoritesRepository(db)
        result = await repo.get_by_user(999)

        assert result == []


class TestFavoritesRepositoryGetByUserAndCode:
    """Tests for FavoritesRepository.get_by_user_and_code."""

    @pytest.mark.asyncio
    async def test_returns_favorite_when_exists(self):
        """Test returns favorite when user+code combination exists."""
        db = AsyncMock()
        fav = MagicMock(spec=Favorite)
        fav.id = 1
        fav.user_id = 10
        fav.hs_code_id = 100

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = fav
        db.execute.return_value = mock_result

        repo = FavoritesRepository(db)
        result = await repo.get_by_user_and_code(10, 100)

        assert result is not None
        assert result.id == 1

    @pytest.mark.asyncio
    async def test_returns_none_when_not_exists(self):
        """Test returns None when user+code combination doesn't exist."""
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        repo = FavoritesRepository(db)
        result = await repo.get_by_user_and_code(10, 999)

        assert result is None


class TestFavoritesRepositoryCreate:
    """Tests for FavoritesRepository.create."""

    @pytest.mark.asyncio
    async def test_creates_and_returns_favorite(self):
        """Test creates a new favorite and returns it."""
        db = AsyncMock()

        repo = FavoritesRepository(db)
        result = await repo.create(10, 100)

        assert result.user_id == 10
        assert result.hs_code_id == 100
        db.add.assert_called_once()
        db.flush.assert_awaited_once()
        db.refresh.assert_awaited_once()


class TestFavoritesRepositoryUpdateNotes:
    """Tests for FavoritesRepository.update_notes."""

    @pytest.mark.asyncio
    async def test_update_notes_success(self):
        """Test updates notes on owned favorite."""
        db = AsyncMock()
        fav = MagicMock(spec=Favorite)
        fav.id = 1
        fav.user_id = 10
        fav.notes = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = fav
        db.execute.return_value = mock_result

        repo = FavoritesRepository(db)
        result = await repo.update_notes(1, 10, "My note")

        assert result is not None
        assert result.notes == "My note"
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_notes_clear(self):
        """Test sets notes to None."""
        db = AsyncMock()
        fav = MagicMock(spec=Favorite)
        fav.id = 1
        fav.user_id = 10
        fav.notes = "Old note"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = fav
        db.execute.return_value = mock_result

        repo = FavoritesRepository(db)
        result = await repo.update_notes(1, 10, None)

        assert result is not None
        assert result.notes is None

    @pytest.mark.asyncio
    async def test_update_notes_not_found(self):
        """Test returns None for nonexistent ID."""
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        repo = FavoritesRepository(db)
        result = await repo.update_notes(999, 10, "Note")

        assert result is None
        db.flush.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_update_notes_wrong_user(self):
        """Test returns None for other user's favorite."""
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        repo = FavoritesRepository(db)
        result = await repo.update_notes(1, 999, "Note")

        assert result is None


class TestFavoritesRepositoryDelete:
    """Tests for FavoritesRepository.delete."""

    @pytest.mark.asyncio
    async def test_deletes_existing_favorite(self):
        """Test deletes a favorite and returns True."""
        db = AsyncMock()
        fav = MagicMock(spec=Favorite)
        fav.id = 1
        fav.user_id = 10

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = fav
        db.execute.return_value = mock_result

        repo = FavoritesRepository(db)
        result = await repo.delete(1, 10)

        assert result is True
        db.delete.assert_awaited_once_with(fav)
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_false_when_not_found(self):
        """Test returns False when favorite doesn't exist."""
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        repo = FavoritesRepository(db)
        result = await repo.delete(999, 10)

        assert result is False
        db.delete.assert_not_awaited()
