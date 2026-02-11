"""Business logic service for tariff browsing."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.browse_repository import BrowseRepository
from app.schemas.browse import (
    BrowseChapterDetailResponse,
    BrowseChapterItem,
    BrowseChaptersResponse,
    BrowseFTARateItem,
    BrowseHeadingItem,
    BrowseHSCodeItem,
    BrowseSearchResultItem,
    BrowseSectionItem,
    BrowseSubheadingItem,
    PaginatedBrowseSearchResponse,
)


class BrowseService:
    """Service for tariff browse business logic."""

    def __init__(self, session: AsyncSession):
        self.repository = BrowseRepository(session)

    async def list_sections(self) -> list[dict[str, Any]]:
        """List all sections with chapter counts."""
        rows = await self.repository.get_all_sections()
        return [
            BrowseSectionItem(
                id=section.id,
                section_number=section.section_number,
                section_roman=section.section_roman,
                name_vn=section.name_vn,
                name_en=section.name_en,
                chapter_count=chapter_count,
            ).model_dump()
            for section, chapter_count in rows
        ]

    async def list_chapters(self, section_id: int) -> dict[str, Any] | None:
        """List chapters for a section with section notes. Returns None if section not found."""
        section = await self.repository.get_section_by_id(section_id)
        if section is None:
            return None

        rows = await self.repository.get_chapters_by_section(section_id)
        chapter_items = [
            BrowseChapterItem(
                id=chapter.id,
                chapter_code=chapter.chapter_code,
                name_vn=chapter.name_vn,
                name_en=chapter.name_en,
                heading_count=heading_count,
                hs_code_count=hs_code_count,
            )
            for chapter, heading_count, hs_code_count in rows
        ]

        return BrowseChaptersResponse(
            section_notes_vn=section.notes_vn,
            section_notes_en=section.notes_en,
            chapters=chapter_items,
        ).model_dump()

    async def get_chapter_detail(self, chapter_code: str) -> dict[str, Any] | None:
        """Get full chapter hierarchy with rates. Returns None if chapter not found."""
        chapter = await self.repository.get_chapter_by_code(chapter_code)
        if chapter is None:
            return None

        heading_items = []
        for heading in chapter.headings:
            subheading_items = []
            for subheading in heading.subheadings:
                hs_code_items = []
                for hs_code in subheading.hs_codes:
                    fta_rate_items = [
                        BrowseFTARateItem.model_validate(rate) for rate in hs_code.fta_rates
                    ]
                    hs_code_items.append(
                        BrowseHSCodeItem(
                            id=hs_code.id,
                            code=hs_code.code,
                            description_vn=hs_code.description_vn,
                            description_en=hs_code.description_en,
                            unit=hs_code.unit,
                            duty_rate=float(hs_code.duty_rate),
                            vat_rate=float(hs_code.vat_rate),
                            export_duty_rate=hs_code.export_duty_rate,
                            special_consumption_tax=hs_code.special_consumption_tax,
                            environmental_tax=hs_code.environmental_tax,
                            vat_reduction=hs_code.vat_reduction,
                            policy_notes=hs_code.policy_notes,
                            fta_rates=fta_rate_items,
                        )
                    )
                subheading_items.append(
                    BrowseSubheadingItem(
                        id=subheading.id,
                        subheading_code=subheading.subheading_code,
                        name_vn=subheading.name_vn,
                        name_en=subheading.name_en,
                        indent_level=subheading.indent_level,
                        hs_codes=hs_code_items,
                    )
                )
            heading_items.append(
                BrowseHeadingItem(
                    id=heading.id,
                    heading_code=heading.heading_code,
                    name_vn=heading.name_vn,
                    name_en=heading.name_en,
                    subheadings=subheading_items,
                )
            )

        return BrowseChapterDetailResponse(
            id=chapter.id,
            chapter_code=chapter.chapter_code,
            name_vn=chapter.name_vn,
            name_en=chapter.name_en,
            notes_vn=chapter.notes_vn,
            notes_en=chapter.notes_en,
            headings=heading_items,
        ).model_dump()

    async def search(
        self,
        query: str,
        chapter_code: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Search HS codes within the tariff browser."""
        rows = await self.repository.search_codes(query, chapter_code, limit, offset)
        total = await self.repository.count_search_results(query, chapter_code)

        item_models = [
            BrowseSearchResultItem(
                id=row.id,
                code=row.code,
                description_vn=row.description_vn,
                description_en=row.description_en,
                unit=row.unit,
                duty_rate=float(row.duty_rate),
                vat_rate=float(row.vat_rate),
                export_duty_rate=row.export_duty_rate,
                section_roman=row.section_roman,
                chapter_code=row.chapter_code,
                heading_code=row.heading_code,
            )
            for row in rows
        ]

        return PaginatedBrowseSearchResponse(
            items=item_models,
            total=total,
            limit=limit,
            offset=offset,
        ).model_dump()
