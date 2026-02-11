"""Tests for browse service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.browse_service import BrowseService


def _make_mock_section(**kwargs):
    """Create a mock HSSection."""
    defaults = {
        "id": 1,
        "section_number": 1,
        "section_roman": "I",
        "name_vn": "Động vật sống",
        "name_en": "Live animals",
        "notes_vn": "Section I notes",
        "notes_en": "Section I notes EN",
    }
    defaults.update(kwargs)
    mock = MagicMock()
    for key, value in defaults.items():
        setattr(mock, key, value)
    return mock


def _make_mock_chapter(**kwargs):
    """Create a mock HSChapter."""
    defaults = {
        "id": 1,
        "chapter_code": "01",
        "name_vn": "Động vật sống",
        "name_en": "Live animals",
        "notes_vn": "Chapter 01 notes",
        "notes_en": "Chapter 01 notes EN",
        "headings": [],
    }
    defaults.update(kwargs)
    mock = MagicMock()
    for key, value in defaults.items():
        setattr(mock, key, value)
    return mock


def _make_mock_search_row(**kwargs):
    """Create a mock search result row."""
    defaults = {
        "id": 1,
        "code": "01012100",
        "description_vn": "Ngựa thuần chủng",
        "description_en": "Pure-bred horses",
        "unit": "Con",
        "duty_rate": 5.0,
        "vat_rate": 10.0,
        "export_duty_rate": "0",
        "section_roman": "I",
        "chapter_code": "01",
        "heading_code": "0101",
    }
    defaults.update(kwargs)
    mock = MagicMock()
    for key, value in defaults.items():
        setattr(mock, key, value)
    return mock


class TestListSections:
    """Tests for BrowseService.list_sections."""

    @pytest.mark.asyncio
    @patch("app.services.browse_service.BrowseRepository")
    async def test_returns_sections_with_counts(self, mock_repo_class):
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo

        section = _make_mock_section()
        mock_repo.get_all_sections.return_value = [(section, 5)]

        service = BrowseService(AsyncMock())
        result = await service.list_sections()

        assert len(result) == 1
        assert result[0]["section_roman"] == "I"
        assert result[0]["chapter_count"] == 5

    @pytest.mark.asyncio
    @patch("app.services.browse_service.BrowseRepository")
    async def test_returns_empty_list(self, mock_repo_class):
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_all_sections.return_value = []

        service = BrowseService(AsyncMock())
        result = await service.list_sections()

        assert result == []


class TestListChapters:
    """Tests for BrowseService.list_chapters."""

    @pytest.mark.asyncio
    @patch("app.services.browse_service.BrowseRepository")
    async def test_returns_chapters_with_section_notes(self, mock_repo_class):
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo

        section = _make_mock_section()
        mock_repo.get_section_by_id.return_value = section

        chapter = _make_mock_chapter()
        mock_repo.get_chapters_by_section.return_value = [(chapter, 10, 50)]

        service = BrowseService(AsyncMock())
        result = await service.list_chapters(1)

        assert result is not None
        assert result["section_notes_vn"] == "Section I notes"
        assert len(result["chapters"]) == 1
        assert result["chapters"][0]["chapter_code"] == "01"
        assert result["chapters"][0]["heading_count"] == 10
        assert result["chapters"][0]["hs_code_count"] == 50

    @pytest.mark.asyncio
    @patch("app.services.browse_service.BrowseRepository")
    async def test_returns_none_for_missing_section(self, mock_repo_class):
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_section_by_id.return_value = None

        service = BrowseService(AsyncMock())
        result = await service.list_chapters(99999)

        assert result is None


class TestGetChapterDetail:
    """Tests for BrowseService.get_chapter_detail."""

    @pytest.mark.asyncio
    @patch("app.services.browse_service.BrowseRepository")
    async def test_returns_none_for_missing_chapter(self, mock_repo_class):
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_chapter_by_code.return_value = None

        service = BrowseService(AsyncMock())
        result = await service.get_chapter_detail("99")

        assert result is None

    @pytest.mark.asyncio
    @patch("app.services.browse_service.BrowseRepository")
    async def test_returns_chapter_hierarchy(self, mock_repo_class):
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo

        # Build mock hierarchy
        fta_rate = MagicMock()
        fta_rate.agreement_code = "CPTPP"
        fta_rate.preferential_rate = 0.0
        fta_rate.conditions = None
        fta_rate.rate_year = 2024
        fta_rate.is_export = False
        fta_rate.legal_document = None
        fta_rate.effective_date = None

        hs_code = MagicMock()
        hs_code.id = 1
        hs_code.code = "01012100"
        hs_code.description_vn = "Ngựa thuần chủng"
        hs_code.description_en = "Pure-bred horses"
        hs_code.unit = "Con"
        hs_code.duty_rate = 5.0
        hs_code.vat_rate = 10.0
        hs_code.export_duty_rate = None
        hs_code.special_consumption_tax = None
        hs_code.environmental_tax = None
        hs_code.vat_reduction = None
        hs_code.policy_notes = None
        hs_code.fta_rates = [fta_rate]

        subheading = MagicMock()
        subheading.id = 1
        subheading.subheading_code = "010121"
        subheading.name_vn = "Loại thuần chủng"
        subheading.name_en = "Pure-bred"
        subheading.indent_level = 2
        subheading.hs_codes = [hs_code]

        heading = MagicMock()
        heading.id = 1
        heading.heading_code = "0101"
        heading.name_vn = "Ngựa, lừa, la"
        heading.name_en = "Horses, asses, mules"
        heading.subheadings = [subheading]

        chapter = _make_mock_chapter(headings=[heading])
        mock_repo.get_chapter_by_code.return_value = chapter

        service = BrowseService(AsyncMock())
        result = await service.get_chapter_detail("01")

        assert result is not None
        assert result["chapter_code"] == "01"
        assert len(result["headings"]) == 1
        assert result["headings"][0]["heading_code"] == "0101"
        assert len(result["headings"][0]["subheadings"]) == 1
        assert len(result["headings"][0]["subheadings"][0]["hs_codes"]) == 1
        hs = result["headings"][0]["subheadings"][0]["hs_codes"][0]
        assert hs["code"] == "01012100"
        assert len(hs["fta_rates"]) == 1
        assert hs["fta_rates"][0]["agreement_code"] == "CPTPP"


class TestSearch:
    """Tests for BrowseService.search."""

    @pytest.mark.asyncio
    @patch("app.services.browse_service.BrowseRepository")
    async def test_returns_paginated_results(self, mock_repo_class):
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo

        row = _make_mock_search_row()
        mock_repo.search_codes.return_value = [row]
        mock_repo.count_search_results.return_value = 1

        service = BrowseService(AsyncMock())
        result = await service.search("horses", limit=50, offset=0)

        assert result["total"] == 1
        assert result["limit"] == 50
        assert result["offset"] == 0
        assert len(result["items"]) == 1
        assert result["items"][0]["code"] == "01012100"
        assert result["items"][0]["section_roman"] == "I"

    @pytest.mark.asyncio
    @patch("app.services.browse_service.BrowseRepository")
    async def test_returns_empty_results(self, mock_repo_class):
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.search_codes.return_value = []
        mock_repo.count_search_results.return_value = 0

        service = BrowseService(AsyncMock())
        result = await service.search("xyznonexistent")

        assert result["total"] == 0
        assert result["items"] == []

    @pytest.mark.asyncio
    @patch("app.services.browse_service.BrowseRepository")
    async def test_passes_chapter_filter(self, mock_repo_class):
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.search_codes.return_value = []
        mock_repo.count_search_results.return_value = 0

        service = BrowseService(AsyncMock())
        await service.search("copper", chapter_code="74", limit=25, offset=10)

        mock_repo.search_codes.assert_awaited_once_with("copper", "74", 25, 10)
        mock_repo.count_search_results.assert_awaited_once_with("copper", "74")
