"""Repository for tariff browse data access."""

from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.engine import Row
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.hs_chapter import HSChapter
from app.models.hs_code import HSCode
from app.models.hs_heading import HSHeading
from app.models.hs_section import HSSection
from app.models.hs_subheading import HSSubheading


class BrowseRepository:
    """Repository for tariff browse database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_sections(self) -> list[Any]:
        """Get all sections with chapter count via correlated subquery.

        Returns list of Row objects with (HSSection, chapter_count).
        """
        chapter_count_subquery = (
            select(func.count(HSChapter.id))
            .where(HSChapter.section_id == HSSection.id)
            .correlate(HSSection)
            .scalar_subquery()
        )
        stmt = select(HSSection, chapter_count_subquery.label("chapter_count")).order_by(
            HSSection.section_number
        )
        result = await self.session.execute(stmt)
        return list(result.all())

    async def get_chapters_by_section(self, section_id: int) -> list[Any]:
        """Get chapters for a section with heading_count and hs_code_count.

        Returns list of Row objects with (HSChapter, heading_count, hs_code_count).
        """
        heading_count = (
            select(func.count(HSHeading.id))
            .where(HSHeading.chapter_id == HSChapter.id)
            .correlate(HSChapter)
            .scalar_subquery()
        )
        hs_code_count = (
            select(func.count(HSCode.id))
            .join(HSSubheading, HSCode.subheading_id == HSSubheading.id)
            .join(HSHeading, HSSubheading.heading_id == HSHeading.id)
            .where(HSHeading.chapter_id == HSChapter.id)
            .correlate(HSChapter)
            .scalar_subquery()
        )
        stmt = (
            select(
                HSChapter,
                heading_count.label("heading_count"),
                hs_code_count.label("hs_code_count"),
            )
            .where(HSChapter.section_id == section_id)
            .order_by(HSChapter.chapter_code)
        )
        result = await self.session.execute(stmt)
        return list(result.all())

    async def get_section_by_id(self, section_id: int) -> HSSection | None:
        """Get a single section by ID."""
        result = await self.session.execute(select(HSSection).where(HSSection.id == section_id))
        return result.scalar_one_or_none()

    async def get_chapter_by_code(self, chapter_code: str) -> HSChapter | None:
        """Get full chapter with eager-loaded hierarchy."""
        stmt = (
            select(HSChapter)
            .where(HSChapter.chapter_code == chapter_code)
            .options(
                selectinload(HSChapter.headings)
                .selectinload(HSHeading.subheadings)
                .selectinload(HSSubheading.hs_codes)
                .selectinload(HSCode.fta_rates)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def search_codes(
        self,
        query: str,
        chapter_code: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Any]:
        """Search HS codes with hierarchy path via pg_trgm + exact code prefix.

        Returns list of Row objects with columns: id, code, description_vn, description_en,
        unit, duty_rate, vat_rate, export_duty_rate, section_roman, chapter_code, heading_code.
        """
        stmt = (
            select(
                HSCode.id,
                HSCode.code,
                HSCode.description_vn,
                HSCode.description_en,
                HSCode.unit,
                HSCode.duty_rate,
                HSCode.vat_rate,
                HSCode.export_duty_rate,
                HSSection.section_roman,
                HSChapter.chapter_code,
                HSHeading.heading_code,
            )
            .join(HSSubheading, HSCode.subheading_id == HSSubheading.id)
            .join(HSHeading, HSSubheading.heading_id == HSHeading.id)
            .join(HSChapter, HSHeading.chapter_id == HSChapter.id)
            .join(HSSection, HSChapter.section_id == HSSection.id)
            .where(
                or_(
                    HSCode.code.startswith(query),
                    HSCode.description_vn.ilike(f"%{query}%"),
                    HSCode.description_en.ilike(f"%{query}%"),
                )
            )
            .order_by(HSCode.code)
        )
        if chapter_code:
            stmt = stmt.where(HSChapter.chapter_code == chapter_code)
        stmt = stmt.limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.all())

    async def count_search_results(
        self,
        query: str,
        chapter_code: str | None = None,
    ) -> int:
        """Count total matching HS codes for pagination."""
        stmt = (
            select(func.count(HSCode.id))
            .join(HSSubheading, HSCode.subheading_id == HSSubheading.id)
            .join(HSHeading, HSSubheading.heading_id == HSHeading.id)
            .join(HSChapter, HSHeading.chapter_id == HSChapter.id)
            .join(HSSection, HSChapter.section_id == HSSection.id)
            .where(
                or_(
                    HSCode.code.startswith(query),
                    HSCode.description_vn.ilike(f"%{query}%"),
                    HSCode.description_en.ilike(f"%{query}%"),
                )
            )
        )
        if chapter_code:
            stmt = stmt.where(HSChapter.chapter_code == chapter_code)
        result = await self.session.execute(stmt)
        return result.scalar() or 0
