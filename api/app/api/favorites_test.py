"""Tests for favorites API endpoints."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.responses import JSONResponse

from app.api.favorites import (
    add_favorite,
    list_favorites,
    remove_favorite,
    update_favorite_notes,
)
from app.schemas.favorites import FavoriteCreate, FavoriteUpdateNotes
from app.services.favorites_service import DuplicateFavoriteError


class TestListFavorites:
    """Tests for GET /api/favorites."""

    @pytest.mark.asyncio
    async def test_returns_favorites_list(self):
        """Test returns favorites list for authenticated user."""
        mock_db = AsyncMock()
        user = {"id": 10, "email": "user@example.com", "role": "user"}

        with patch("app.api.favorites.FavoritesService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service.list_favorites.return_value = [
                {
                    "id": 1,
                    "user_id": 10,
                    "hs_code_id": 100,
                    "hs_code": "01012100",
                    "description_vn": "Ngựa thuần chủng",
                    "notes": None,
                    "created_at": "2026-02-21T00:00:00+00:00",
                }
            ]
            mock_service_cls.return_value = mock_service

            result = await list_favorites(current_user=user, db=mock_db)

        assert result["success"] is True
        assert len(result["data"]) == 1
        assert result["data"][0]["hs_code"] == "01012100"

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self):
        """Test unauthenticated request gets 401."""
        from app.core.auth import get_current_user

        mock_request = MagicMock()
        with patch("app.core.auth.JWT") as mock_jwt:
            mock_jwt.side_effect = Exception("No token")
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_request)
            assert exc_info.value.status_code == 401


class TestAddFavorite:
    """Tests for POST /api/favorites."""

    @pytest.mark.asyncio
    async def test_creates_favorite_returns_201(self):
        """Test creates favorite and returns envelope response."""
        mock_db = AsyncMock()
        user = {"id": 10, "email": "user@example.com", "role": "user"}
        body = FavoriteCreate(hs_code_id=100)

        with patch("app.api.favorites.FavoritesService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service.add_favorite.return_value = {
                "id": 1,
                "user_id": 10,
                "hs_code_id": 100,
                "hs_code": "01012100",
                "description_vn": "Ngựa thuần chủng",
                "notes": None,
                "created_at": "2026-02-21T00:00:00+00:00",
            }
            mock_service_cls.return_value = mock_service

            result = await add_favorite(body=body, current_user=user, db=mock_db)

        assert result["success"] is True
        assert result["data"]["id"] == 1
        assert result["data"]["hs_code"] == "01012100"

    @pytest.mark.asyncio
    async def test_duplicate_returns_409(self):
        """Test duplicate favorite returns 409 Conflict via JSONResponse."""
        mock_db = AsyncMock()
        user = {"id": 10, "email": "user@example.com", "role": "user"}
        body = FavoriteCreate(hs_code_id=100)

        with patch("app.api.favorites.FavoritesService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service.add_favorite.side_effect = DuplicateFavoriteError(
                "Already favorited"
            )
            mock_service_cls.return_value = mock_service

            result = await add_favorite(body=body, current_user=user, db=mock_db)

        assert isinstance(result, JSONResponse)
        assert result.status_code == 409
        body_content = json.loads(result.body.decode())
        assert body_content["success"] is False
        assert body_content["error"]["status"] == 409

    @pytest.mark.asyncio
    async def test_invalid_hs_code_returns_404(self):
        """Test nonexistent HS code returns 404 via JSONResponse."""
        mock_db = AsyncMock()
        user = {"id": 10, "email": "user@example.com", "role": "user"}
        body = FavoriteCreate(hs_code_id=99999)

        with patch("app.api.favorites.FavoritesService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service.add_favorite.side_effect = ValueError("HS code not found")
            mock_service_cls.return_value = mock_service

            result = await add_favorite(body=body, current_user=user, db=mock_db)

        assert isinstance(result, JSONResponse)
        assert result.status_code == 404
        body_content = json.loads(result.body.decode())
        assert body_content["success"] is False
        assert body_content["error"]["status"] == 404


class TestUpdateFavoriteNotes:
    """Tests for PATCH /api/favorites/{favorite_id}."""

    @pytest.mark.asyncio
    async def test_patch_notes_success(self):
        """Test 200 with updated notes."""
        mock_db = AsyncMock()
        user = {"id": 10, "email": "user@example.com", "role": "user"}
        body = FavoriteUpdateNotes(notes="My note")

        with patch("app.api.favorites.FavoritesService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service.update_notes.return_value = {
                "id": 1,
                "user_id": 10,
                "hs_code_id": 100,
                "hs_code": "01012100",
                "description_vn": "Ngựa thuần chủng",
                "notes": "My note",
                "created_at": "2026-02-21T00:00:00+00:00",
            }
            mock_service_cls.return_value = mock_service

            result = await update_favorite_notes(
                favorite_id=1, body=body, current_user=user, db=mock_db
            )

        assert result["success"] is True
        assert result["data"]["notes"] == "My note"

    @pytest.mark.asyncio
    async def test_patch_notes_clear(self):
        """Test 200 with null notes."""
        mock_db = AsyncMock()
        user = {"id": 10, "email": "user@example.com", "role": "user"}
        body = FavoriteUpdateNotes(notes=None)

        with patch("app.api.favorites.FavoritesService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service.update_notes.return_value = {
                "id": 1,
                "user_id": 10,
                "hs_code_id": 100,
                "hs_code": "01012100",
                "description_vn": "Ngựa thuần chủng",
                "notes": None,
                "created_at": "2026-02-21T00:00:00+00:00",
            }
            mock_service_cls.return_value = mock_service

            result = await update_favorite_notes(
                favorite_id=1, body=body, current_user=user, db=mock_db
            )

        assert result["success"] is True
        assert result["data"]["notes"] is None

    @pytest.mark.asyncio
    async def test_patch_notes_not_found(self):
        """Test 404 via JSONResponse when favorite not found."""
        mock_db = AsyncMock()
        user = {"id": 10, "email": "user@example.com", "role": "user"}
        body = FavoriteUpdateNotes(notes="Note")

        with patch("app.api.favorites.FavoritesService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service.update_notes.return_value = None
            mock_service_cls.return_value = mock_service

            result = await update_favorite_notes(
                favorite_id=999, body=body, current_user=user, db=mock_db
            )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 404
        body_content = json.loads(result.body.decode())
        assert body_content["success"] is False
        assert body_content["error"]["status"] == 404

    @pytest.mark.asyncio
    async def test_patch_notes_unauthenticated(self):
        """Test unauthenticated PATCH request gets 401 via require_authenticated."""
        from app.core.auth import require_authenticated

        mock_request = MagicMock()
        with pytest.raises(HTTPException) as exc_info:
            await require_authenticated(mock_request)
        assert exc_info.value.status_code == 401


class TestRemoveFavorite:
    """Tests for DELETE /api/favorites/{favorite_id}."""

    @pytest.mark.asyncio
    async def test_removes_favorite_returns_success(self):
        """Test removes favorite and returns success envelope."""
        mock_db = AsyncMock()
        user = {"id": 10, "email": "user@example.com", "role": "user"}

        with patch("app.api.favorites.FavoritesService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service.remove_favorite.return_value = True
            mock_service_cls.return_value = mock_service

            result = await remove_favorite(
                favorite_id=1, current_user=user, db=mock_db
            )

        assert result["success"] is True
        assert result["data"]["deleted"] is True

    @pytest.mark.asyncio
    async def test_not_found_returns_404(self):
        """Test returns 404 via JSONResponse when favorite doesn't exist."""
        mock_db = AsyncMock()
        user = {"id": 10, "email": "user@example.com", "role": "user"}

        with patch("app.api.favorites.FavoritesService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service.remove_favorite.return_value = False
            mock_service_cls.return_value = mock_service

            result = await remove_favorite(
                favorite_id=999, current_user=user, db=mock_db
            )

        assert isinstance(result, JSONResponse)
        assert result.status_code == 404
        body_content = json.loads(result.body.decode())
        assert body_content["success"] is False
        assert body_content["error"]["status"] == 404
