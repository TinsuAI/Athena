"""Repository for HS code data access."""

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.hs_code import HSCode


class HSCodeRepository:
    """Repository for HS code database operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def get_by_code(self, code: str) -> HSCode | None:
        """Get an HS code by its code."""
        result = await self.session.execute(
            select(HSCode).where(HSCode.code == code)
        )
        return result.scalar_one_or_none()

    async def get_with_fta_rates(self, code: str) -> HSCode | None:
        """Get an HS code with its FTA rates eagerly loaded."""
        result = await self.session.execute(
            select(HSCode)
            .where(HSCode.code == code)
            .options(selectinload(HSCode.fta_rates))
        )
        return result.scalar_one_or_none()

    async def count_all(self) -> int:
        """Count total number of HS codes in database."""
        result = await self.session.execute(
            select(func.count()).select_from(HSCode)
        )
        return result.scalar() or 0

    async def get_all(self, limit: int = 100, offset: int = 0) -> list[HSCode]:
        """Get all HS codes with pagination."""
        result = await self.session.execute(
            select(HSCode)
            .limit(limit)
            .offset(offset)
            .order_by(HSCode.code)
        )
        return list(result.scalars().all())

    async def autocomplete(
        self,
        query: str,
        limit: int = 10,
    ) -> list[HSCode]:
        """Search HS codes by code prefix or description substring.

        Matches against code prefix (digits only) or Vietnamese/English descriptions.
        """
        # Strip dots for code prefix search
        code_query = query.replace(".", "")
        result = await self.session.execute(
            select(HSCode)
            .where(
                or_(
                    HSCode.code.startswith(code_query),
                    HSCode.description_vn.ilike(f"%{query}%"),
                    HSCode.description_en.ilike(f"%{query}%"),
                )
            )
            .order_by(HSCode.code)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def search_by_description(
        self,
        query: str,
        language: str = "both",
        limit: int = 20
    ) -> list[HSCode]:
        """Search HS codes by description using trigram similarity.

        Args:
            query: Search query
            language: "vn", "en", or "both"
            limit: Maximum number of results
        """
        conditions = []

        if language in ("vn", "both"):
            conditions.append(HSCode.description_vn.ilike(f"%{query}%"))

        if language in ("en", "both"):
            conditions.append(HSCode.description_en.ilike(f"%{query}%"))

        if not conditions:
            return []

        # Combine conditions with OR
        where_clause = conditions[0]
        for condition in conditions[1:]:
            where_clause = where_clause | condition

        result = await self.session.execute(
            select(HSCode)
            .where(where_clause)
            .limit(limit)
            .order_by(HSCode.code)
        )
        return list(result.scalars().all())
