"""Service for search history business logic."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.search_history_repository import SearchHistoryRepository


class SearchHistoryService:
    """Service for managing user search history."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SearchHistoryRepository(db)

    async def record_search(
        self, user_id: int, query: str, selected_hs_code_id: int | None
    ) -> dict:
        """Record a search and return response dict."""
        entry = await self.repo.create(user_id, query, selected_hs_code_id)
        await self.db.commit()
        return self._to_response(entry)

    async def list_history(
        self, user_id: int, limit: int = 20, offset: int = 0
    ) -> dict:
        """Get paginated search history for a user."""
        items = await self.repo.get_by_user(user_id, limit, offset)
        total = await self.repo.count_by_user(user_id)
        return {
            "items": [self._to_response(item) for item in items],
            "total": total,
        }

    async def delete_entry(self, entry_id: int, user_id: int) -> bool:
        """Delete a single history entry. Returns True if deleted."""
        deleted = await self.repo.delete(entry_id, user_id)
        if deleted:
            await self.db.commit()
        return deleted

    async def clear_history(self, user_id: int) -> int:
        """Delete all history entries for user. Returns count deleted."""
        count = await self.repo.delete_all_by_user(user_id)
        await self.db.commit()
        return count

    def _to_response(self, entry) -> dict:  # type: ignore[no-untyped-def]
        """Convert a SearchHistory model to response dict."""
        return {
            "id": entry.id,
            "user_id": entry.user_id,
            "query": entry.query,
            "selected_hs_code_id": entry.selected_hs_code_id,
            "selected_hs_code": entry.hs_code.code if entry.hs_code else None,
            "selected_description_vn": (
                entry.hs_code.description_vn if entry.hs_code else None
            ),
            "created_at": entry.created_at.isoformat(),
        }
