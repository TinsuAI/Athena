"""Tests for browse API endpoints."""

from unittest.mock import AsyncMock, patch

import pytest

from app.api.browse import get_chapter_detail, list_chapters, list_sections, search_browse


class TestListSections:
    """Tests for GET /api/browse/sections."""

    @pytest.mark.asyncio
    @patch("app.api.browse.BrowseService")
    async def test_returns_sections(self, mock_service_class):
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        mock_service.list_sections.return_value = [
            {
                "id": 1,
                "section_number": 1,
                "section_roman": "I",
                "name_vn": "Động vật sống",
                "name_en": "Live animals",
                "chapter_count": 5,
            }
        ]

        result = await list_sections(db=AsyncMock())

        assert result["success"] is True
        assert len(result["data"]) == 1
        assert result["data"][0]["section_roman"] == "I"
        assert result["data"][0]["chapter_count"] == 5

    @pytest.mark.asyncio
    @patch("app.api.browse.BrowseService")
    async def test_returns_empty_list(self, mock_service_class):
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        mock_service.list_sections.return_value = []

        result = await list_sections(db=AsyncMock())

        assert result["success"] is True
        assert result["data"] == []


class TestListChapters:
    """Tests for GET /api/browse/chapters."""

    @pytest.mark.asyncio
    @patch("app.api.browse.BrowseService")
    async def test_returns_chapters_with_section_notes(self, mock_service_class):
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        mock_service.list_chapters.return_value = {
            "section_notes_vn": "Chú giải phần I",
            "section_notes_en": "Section I notes",
            "chapters": [
                {
                    "id": 1,
                    "chapter_code": "01",
                    "name_vn": "Động vật sống",
                    "name_en": "Live animals",
                    "heading_count": 10,
                    "hs_code_count": 50,
                }
            ],
        }

        result = await list_chapters(section_id=1, db=AsyncMock())

        assert result["success"] is True
        assert result["data"]["section_notes_vn"] == "Chú giải phần I"
        assert len(result["data"]["chapters"]) == 1
        assert result["data"]["chapters"][0]["chapter_code"] == "01"

    @pytest.mark.asyncio
    @patch("app.api.browse.BrowseService")
    async def test_section_not_found_returns_404(self, mock_service_class):
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        mock_service.list_chapters.return_value = None

        result = await list_chapters(section_id=99999, db=AsyncMock())

        assert result["success"] is False
        assert result["error"]["status"] == 404
        assert result["error"]["title"] == "Section Not Found"
        assert "99999" in result["error"]["detail"]


class TestGetChapterDetail:
    """Tests for GET /api/browse/chapters/{chapter_code}."""

    @pytest.mark.asyncio
    @patch("app.api.browse.BrowseService")
    async def test_returns_full_hierarchy(self, mock_service_class):
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        mock_service.get_chapter_detail.return_value = {
            "id": 1,
            "chapter_code": "01",
            "name_vn": "Động vật sống",
            "name_en": "Live animals",
            "notes_vn": "Chú giải chương 01",
            "notes_en": "Chapter 01 notes",
            "headings": [
                {
                    "id": 1,
                    "heading_code": "0101",
                    "name_vn": "Ngựa, lừa, la",
                    "name_en": "Horses, asses, mules",
                    "subheadings": [
                        {
                            "id": 1,
                            "subheading_code": "010121",
                            "name_vn": "Loại thuần chủng",
                            "name_en": "Pure-bred",
                            "indent_level": 2,
                            "hs_codes": [
                                {
                                    "id": 1,
                                    "code": "01012100",
                                    "description_vn": "Ngựa thuần chủng",
                                    "description_en": "Pure-bred horses",
                                    "unit": "Con",
                                    "duty_rate": 5.0,
                                    "vat_rate": 10.0,
                                    "export_duty_rate": "0",
                                    "special_consumption_tax": None,
                                    "environmental_tax": None,
                                    "vat_reduction": None,
                                    "policy_notes": None,
                                    "fta_rates": [
                                        {
                                            "agreement_code": "CPTPP",
                                            "preferential_rate": 0.0,
                                            "conditions": "C/O required",
                                            "rate_year": 2024,
                                            "is_export": False,
                                            "legal_document": "ND-123",
                                            "effective_date": "2024-01-01",
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ],
        }

        result = await get_chapter_detail(chapter_code="01", db=AsyncMock())

        assert result["success"] is True
        chapter = result["data"]
        assert chapter["chapter_code"] == "01"
        assert chapter["notes_vn"] == "Chú giải chương 01"
        assert len(chapter["headings"]) == 1
        hs_code = chapter["headings"][0]["subheadings"][0]["hs_codes"][0]
        assert hs_code["code"] == "01012100"
        assert hs_code["duty_rate"] == 5.0
        assert len(hs_code["fta_rates"]) == 1
        assert hs_code["fta_rates"][0]["agreement_code"] == "CPTPP"

    @pytest.mark.asyncio
    @patch("app.api.browse.BrowseService")
    async def test_chapter_not_found_returns_404(self, mock_service_class):
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        mock_service.get_chapter_detail.return_value = None

        result = await get_chapter_detail(chapter_code="99", db=AsyncMock())

        assert result["success"] is False
        assert result["error"]["status"] == 404
        assert result["error"]["title"] == "Chapter Not Found"
        assert "'99'" in result["error"]["detail"]


class TestSearchBrowse:
    """Tests for GET /api/browse/search."""

    @pytest.mark.asyncio
    @patch("app.api.browse.BrowseService")
    async def test_returns_search_results(self, mock_service_class):
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        mock_service.search.return_value = {
            "items": [
                {
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
            ],
            "total": 1,
            "limit": 50,
            "offset": 0,
        }

        result = await search_browse(q="horses", chapter=None, limit=50, offset=0, db=AsyncMock())

        assert result["success"] is True
        assert result["data"]["total"] == 1
        assert len(result["data"]["items"]) == 1
        assert result["data"]["items"][0]["code"] == "01012100"
        assert result["data"]["items"][0]["section_roman"] == "I"

    @pytest.mark.asyncio
    @patch("app.api.browse.BrowseService")
    async def test_empty_results(self, mock_service_class):
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        mock_service.search.return_value = {
            "items": [],
            "total": 0,
            "limit": 50,
            "offset": 0,
        }

        result = await search_browse(
            q="xyznonexistent", chapter=None, limit=50, offset=0, db=AsyncMock()
        )

        assert result["success"] is True
        assert result["data"]["total"] == 0
        assert result["data"]["items"] == []

    @pytest.mark.asyncio
    @patch("app.api.browse.BrowseService")
    async def test_with_chapter_filter(self, mock_service_class):
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        mock_service.search.return_value = {
            "items": [],
            "total": 0,
            "limit": 50,
            "offset": 0,
        }

        await search_browse(q="copper", chapter="74", limit=25, offset=10, db=AsyncMock())

        mock_service.search.assert_awaited_once_with("copper", "74", 25, 10)

    @pytest.mark.asyncio
    @patch("app.api.browse.BrowseService")
    async def test_code_prefix_search(self, mock_service_class):
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        mock_service.search.return_value = {
            "items": [
                {
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
            ],
            "total": 1,
            "limit": 50,
            "offset": 0,
        }

        result = await search_browse(q="01012100", chapter=None, limit=50, offset=0, db=AsyncMock())

        assert result["success"] is True
        assert result["data"]["items"][0]["code"] == "01012100"

    @pytest.mark.asyncio
    @patch("app.api.browse.BrowseService")
    async def test_pagination_params(self, mock_service_class):
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        mock_service.search.return_value = {
            "items": [],
            "total": 100,
            "limit": 10,
            "offset": 20,
        }

        result = await search_browse(q="horses", chapter=None, limit=10, offset=20, db=AsyncMock())

        assert result["data"]["limit"] == 10
        assert result["data"]["offset"] == 20
        assert result["data"]["total"] == 100
