"""Repository for favorites data access."""

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.favorite import Favorite


class FavoritesRepository:
    """Repository for favorites database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user(self, user_id: int) -> list[Favorite]:
        """Get all favorites for a user, ordered by most recent first."""
        result = await self.db.execute(
            select(Favorite)
            .options(selectinload(Favorite.hs_code))
            .where(Favorite.user_id == user_id)
            .order_by(Favorite.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_user_and_code(
        self, user_id: int, hs_code_id: int
    ) -> Favorite | None:
        """Check if a user has already favorited a specific HS code."""
        result = await self.db.execute(
            select(Favorite).where(
                and_(Favorite.user_id == user_id, Favorite.hs_code_id == hs_code_id)
            )
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: int, hs_code_id: int) -> Favorite:
        """Create a new favorite."""
        favorite = Favorite(user_id=user_id, hs_code_id=hs_code_id)
        self.db.add(favorite)
        await self.db.flush()
        await self.db.refresh(favorite, ["hs_code"])
        return favorite

    async def delete(self, favorite_id: int, user_id: int) -> bool:
        """Delete a favorite, scoped to the owning user. Returns True if deleted."""
        result = await self.db.execute(
            select(Favorite).where(
                and_(Favorite.id == favorite_id, Favorite.user_id == user_id)
            )
        )
        favorite = result.scalar_one_or_none()
        if favorite:
            await self.db.delete(favorite)
            await self.db.flush()
            return True
        return False
