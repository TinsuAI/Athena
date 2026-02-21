"""Favorites API for managing user bookmarked HS codes."""

from typing import Any

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.core.auth import require_authenticated
from app.schemas.base import error_response, success_response
from app.schemas.favorites import FavoriteCreate, FavoriteUpdateNotes
from app.services.favorites_service import DuplicateFavoriteError, FavoritesService

router = APIRouter(prefix="/api/favorites", tags=["favorites"])


@router.get("")
async def list_favorites(
    current_user: dict = Depends(require_authenticated),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """List all favorites for the authenticated user."""
    service = FavoritesService(db)
    favorites = await service.list_favorites(current_user["id"])
    return success_response(favorites)


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_favorite(
    body: FavoriteCreate,
    current_user: dict = Depends(require_authenticated),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Add an HS code to the user's favorites."""
    service = FavoritesService(db)
    try:
        favorite = await service.add_favorite(current_user["id"], body.hs_code_id)
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error_response(
                "https://athena.example/errors/not-found",
                "Not Found",
                404,
                str(e),
                "/api/favorites",
            ),
        )
    except DuplicateFavoriteError:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=error_response(
                "https://athena.example/errors/conflict",
                "Conflict",
                409,
                "HS code already in favorites",
                "/api/favorites",
            ),
        )
    return success_response(favorite)


@router.patch("/{favorite_id}")
async def update_favorite_notes(
    favorite_id: int,
    body: FavoriteUpdateNotes,
    current_user: dict = Depends(require_authenticated),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Update notes on a favorite."""
    service = FavoritesService(db)
    result = await service.update_notes(favorite_id, current_user["id"], body.notes)
    if result is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error_response(
                "https://athena.example/errors/not-found",
                "Not Found",
                404,
                "Favorite not found",
                f"/api/favorites/{favorite_id}",
            ),
        )
    return success_response(result)


@router.delete("/{favorite_id}")
async def remove_favorite(
    favorite_id: int,
    current_user: dict = Depends(require_authenticated),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Remove a favorite by ID."""
    service = FavoritesService(db)
    deleted = await service.remove_favorite(favorite_id, current_user["id"])
    if not deleted:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error_response(
                "https://athena.example/errors/not-found",
                "Not Found",
                404,
                "Favorite not found",
                f"/api/favorites/{favorite_id}",
            ),
        )
    return success_response({"deleted": True})
