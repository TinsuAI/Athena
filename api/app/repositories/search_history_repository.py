"""Repository for search history data access."""

from sqlalchemy import and_, delete as delete_stmt, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.search_history import SearchHistory


class SearchHistoryRepository:
    """Repository for search history database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self, user_id: int, query: str, selected_hs_code_id: int | None
    ) -> SearchHistory:
        """Create a new search history entry."""
        entry = SearchHistory(
            user_id=user_id, query=query, selected_hs_code_id=selected_hs_code_id
        )
        self.db.add(entry)
        await self.db.flush()
        await self.db.refresh(entry, ["hs_code"])
        return entry

    async def get_by_user(
        self, user_id: int, limit: int = 20, offset: int = 0
    ) -> list[SearchHistory]:
        """Get paginated search history for a user, most recent first."""
        result = await self.db.execute(
            select(SearchHistory)
            .options(selectinload(SearchHistory.hs_code))
            .where(SearchHistory.user_id == user_id)
            .order_by(SearchHistory.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def count_by_user(self, user_id: int) -> int:
        """Count total search history entries for a user."""
        result = await self.db.execute(
            select(func.count())
            .select_from(SearchHistory)
            .where(SearchHistory.user_id == user_id)
        )
        return result.scalar_one()

    async def delete(self, entry_id: int, user_id: int) -> bool:
        """Delete a single history entry scoped to the owning user."""
        result = await self.db.execute(
            select(SearchHistory).where(
                and_(SearchHistory.id == entry_id, SearchHistory.user_id == user_id)
            )
        )
        entry = result.scalar_one_or_none()
        if entry:
            await self.db.delete(entry)
            await self.db.flush()
            return True
        return False

    async def delete_all_by_user(self, user_id: int) -> int:
        """Delete all history entries for a user. Returns count deleted."""
        result = await self.db.execute(
            delete_stmt(SearchHistory).where(SearchHistory.user_id == user_id)
        )
        await self.db.flush()
        return result.rowcount
