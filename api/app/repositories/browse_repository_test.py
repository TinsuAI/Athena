"""Tests for browse repository."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.data_version import DataVersion
from app.models.fta_rate import FTARate
from app.models.hs_chapter import HSChapter
from app.models.hs_code import HSCode
from app.models.hs_heading import HSHeading
from app.models.hs_section import HSSection
from app.models.hs_subheading import HSSubheading
from app.repositories.browse_repository import BrowseRepository


async def _create_full_hierarchy(db_session: AsyncSession) -> dict:
    """Create a full hierarchy for testing."""
    data_version = DataVersion(name="Test", source_file="test.xlsx", is_active=True)
    db_session.add(data_version)
    await db_session.flush()

    section = HSSection(
        section_number=1,
        section_roman="I",
        name_vn="Động vật sống",
        name_en="Live animals",
        notes_vn="Chú giải phần I",
        notes_en="Section I notes",
    )
    db_session.add(section)
    await db_session.flush()

    chapter = HSChapter(
        chapter_code="01",
        section_id=section.id,
        name_vn="Động vật sống",
        name_en="Live animals",
        notes_vn="Chú giải chương 01",
        notes_en="Chapter 01 notes",
    )
    db_session.add(chapter)
    await db_session.flush()

    heading = HSHeading(
        heading_code="0101",
        chapter_id=chapter.id,
        name_vn="Ngựa, lừa, la sống",
        name_en="Live horses, asses, mules",
    )
    db_session.add(heading)
    await db_session.flush()

    subheading = HSSubheading(
        subheading_code="010121",
        heading_id=heading.id,
        name_vn="Loại thuần chủng để nhân giống",
        name_en="Pure-bred breeding animals",
        indent_level=2,
    )
    db_session.add(subheading)
    await db_session.flush()

    hs_code = HSCode(
        code="01012100",
        subheading_id=subheading.id,
        description_vn="Ngựa thuần chủng để nhân giống",
        description_en="Pure-bred breeding horses",
        unit="Con",
        duty_rate=5.0,
        vat_rate=10.0,
        export_duty_rate="0",
        data_version_id=data_version.id,
    )
    db_session.add(hs_code)
    await db_session.flush()

    fta_rate = FTARate(
        hs_code_id=hs_code.id,
        agreement_code="CPTPP",
        preferential_rate=0.0,
        conditions="C/O required",
        rate_year=2024,
        is_export=False,
        legal_document="ND-123",
        effective_date="2024-01-01",
    )
    db_session.add(fta_rate)
    await db_session.commit()

    return {
        "data_version": data_version,
        "section": section,
        "chapter": chapter,
        "heading": heading,
        "subheading": subheading,
        "hs_code": hs_code,
        "fta_rate": fta_rate,
    }


@pytest.mark.asyncio
async def test_get_all_sections(db_session: AsyncSession):
    """Test getting all sections with chapter counts."""
    await _create_full_hierarchy(db_session)

    repo = BrowseRepository(db_session)
    rows = await repo.get_all_sections()

    assert len(rows) == 1
    section, chapter_count = rows[0]
    assert section.section_roman == "I"
    assert section.name_vn == "Động vật sống"
    assert chapter_count == 1


@pytest.mark.asyncio
async def test_get_all_sections_empty(db_session: AsyncSession):
    """Test getting sections when database is empty."""
    repo = BrowseRepository(db_session)
    rows = await repo.get_all_sections()
    assert len(rows) == 0


@pytest.mark.asyncio
async def test_get_chapters_by_section(db_session: AsyncSession):
    """Test getting chapters for a section with counts."""
    data = await _create_full_hierarchy(db_session)

    repo = BrowseRepository(db_session)
    rows = await repo.get_chapters_by_section(data["section"].id)

    assert len(rows) == 1
    chapter, heading_count, hs_code_count = rows[0]
    assert chapter.chapter_code == "01"
    assert heading_count == 1
    assert hs_code_count == 1


@pytest.mark.asyncio
async def test_get_chapters_by_nonexistent_section(db_session: AsyncSession):
    """Test getting chapters for a non-existent section returns empty."""
    repo = BrowseRepository(db_session)
    rows = await repo.get_chapters_by_section(99999)
    assert rows == []


@pytest.mark.asyncio
async def test_get_section_by_id(db_session: AsyncSession):
    """Test getting a single section by ID."""
    data = await _create_full_hierarchy(db_session)

    repo = BrowseRepository(db_session)
    section = await repo.get_section_by_id(data["section"].id)

    assert section is not None
    assert section.section_roman == "I"
    assert section.notes_vn == "Chú giải phần I"


@pytest.mark.asyncio
async def test_get_section_by_id_not_found(db_session: AsyncSession):
    """Test getting non-existent section returns None."""
    repo = BrowseRepository(db_session)
    section = await repo.get_section_by_id(99999)
    assert section is None


@pytest.mark.asyncio
async def test_get_chapter_by_code(db_session: AsyncSession):
    """Test getting full chapter with eager-loaded hierarchy."""
    await _create_full_hierarchy(db_session)

    repo = BrowseRepository(db_session)
    chapter = await repo.get_chapter_by_code("01")

    assert chapter is not None
    assert chapter.chapter_code == "01"
    assert chapter.notes_vn == "Chú giải chương 01"
    assert len(chapter.headings) == 1
    assert chapter.headings[0].heading_code == "0101"
    assert len(chapter.headings[0].subheadings) == 1
    assert chapter.headings[0].subheadings[0].subheading_code == "010121"
    assert len(chapter.headings[0].subheadings[0].hs_codes) == 1
    hs_code = chapter.headings[0].subheadings[0].hs_codes[0]
    assert hs_code.code == "01012100"
    assert len(hs_code.fta_rates) == 1
    assert hs_code.fta_rates[0].agreement_code == "CPTPP"


@pytest.mark.asyncio
async def test_get_chapter_by_code_not_found(db_session: AsyncSession):
    """Test getting non-existent chapter returns None."""
    repo = BrowseRepository(db_session)
    chapter = await repo.get_chapter_by_code("99")
    assert chapter is None


@pytest.mark.asyncio
async def test_search_codes_by_description(db_session: AsyncSession):
    """Test searching HS codes by description text."""
    await _create_full_hierarchy(db_session)

    repo = BrowseRepository(db_session)
    rows = await repo.search_codes("horses")

    assert len(rows) == 1
    row = rows[0]
    assert row.code == "01012100"
    assert row.section_roman == "I"
    assert row.chapter_code == "01"
    assert row.heading_code == "0101"


@pytest.mark.asyncio
async def test_search_codes_by_code_prefix(db_session: AsyncSession):
    """Test searching HS codes by exact code prefix."""
    await _create_full_hierarchy(db_session)

    repo = BrowseRepository(db_session)
    rows = await repo.search_codes("01012100")

    assert len(rows) == 1
    assert rows[0].code == "01012100"


@pytest.mark.asyncio
async def test_search_codes_with_chapter_filter(db_session: AsyncSession):
    """Test searching HS codes filtered to a specific chapter."""
    await _create_full_hierarchy(db_session)

    repo = BrowseRepository(db_session)

    # Matching chapter
    rows = await repo.search_codes("horses", chapter_code="01")
    assert len(rows) == 1

    # Non-matching chapter
    rows = await repo.search_codes("horses", chapter_code="74")
    assert len(rows) == 0


@pytest.mark.asyncio
async def test_search_codes_no_results(db_session: AsyncSession):
    """Test searching returns empty for non-matching query."""
    await _create_full_hierarchy(db_session)

    repo = BrowseRepository(db_session)
    rows = await repo.search_codes("xyznonexistent")
    assert rows == []


@pytest.mark.asyncio
async def test_count_search_results(db_session: AsyncSession):
    """Test counting search results for pagination."""
    await _create_full_hierarchy(db_session)

    repo = BrowseRepository(db_session)
    count = await repo.count_search_results("horses")
    assert count == 1

    count = await repo.count_search_results("xyznonexistent")
    assert count == 0


@pytest.mark.asyncio
async def test_search_codes_pagination(db_session: AsyncSession):
    """Test search pagination with limit and offset."""
    await _create_full_hierarchy(db_session)

    repo = BrowseRepository(db_session)

    # First page
    rows = await repo.search_codes("horses", limit=1, offset=0)
    assert len(rows) == 1

    # Beyond results
    rows = await repo.search_codes("horses", limit=1, offset=1)
    assert len(rows) == 0
