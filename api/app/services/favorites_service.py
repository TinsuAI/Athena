"""Service for favorites business logic."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hs_code import HSCode
from app.repositories.favorites_repository import FavoritesRepository


class DuplicateFavoriteError(Exception):
    """Raised when trying to favorite an already-favorited HS code."""

    pass


class FavoritesService:
    """Service for managing user favorites."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = FavoritesRepository(db)

    async def list_favorites(self, user_id: int) -> list[dict]:
        """Get all favorites for a user with HS code details."""
        favorites = await self.repo.get_by_user(user_id)
        return [self._to_response(f) for f in favorites]

    async def add_favorite(self, user_id: int, hs_code_id: int) -> dict:
        """Add an HS code to user's favorites.

        Validates HS code exists and checks for duplicates.
        """
        # Validate hs_code exists
        result = await self.db.execute(select(HSCode).where(HSCode.id == hs_code_id))
        if not result.scalar_one_or_none():
            raise ValueError("HS code not found")

        # Check duplicate
        existing = await self.repo.get_by_user_and_code(user_id, hs_code_id)
        if existing:
            raise DuplicateFavoriteError("Already favorited")

        favorite = await self.repo.create(user_id, hs_code_id)
        await self.db.commit()
        return self._to_response(favorite)

    async def update_notes(
        self, favorite_id: int, user_id: int, notes: str | None
    ) -> dict | None:
        """Update notes on a favorite. Empty string is normalized to None."""
        if notes is not None and notes.strip() == "":
            notes = None
        favorite = await self.repo.update_notes(favorite_id, user_id, notes)
        if not favorite:
            return None
        await self.db.commit()
        return self._to_response(favorite)

    async def remove_favorite(self, favorite_id: int, user_id: int) -> bool:
        """Remove a favorite. Returns True if deleted, False if not found."""
        deleted = await self.repo.delete(favorite_id, user_id)
        if deleted:
            await self.db.commit()
        return deleted

    def _to_response(self, favorite) -> dict:  # type: ignore[no-untyped-def]
        """Convert a Favorite model to response dict."""
        return {
            "id": favorite.id,
            "user_id": favorite.user_id,
            "hs_code_id": favorite.hs_code_id,
            "hs_code": favorite.hs_code.code if favorite.hs_code else "",
            "description_vn": (
                favorite.hs_code.description_vn if favorite.hs_code else ""
            ),
            "notes": favorite.notes,
            "created_at": favorite.created_at.isoformat(),
        }
