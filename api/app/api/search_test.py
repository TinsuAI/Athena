"""Tests for search API endpoint."""

import hashlib

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import status
from fastapi.testclient import TestClient

from app.api.search import _detect_query_language, _format_hs_code, _format_rate, _record_lookup


class TestSearchEndpointHelpers:
    """Test helper functions."""

    def test_format_hs_code_8_digits(self):
        """Test HS code formatting with 8 digits."""
        assert _format_hs_code("74182000") == "7418.20.00"

    def test_format_hs_code_already_formatted(self):
        """Test HS code formatting preserves non-8-digit codes."""
        assert _format_hs_code("7418") == "7418"

    def test_format_rate_integer(self):
        """Test rate formatting for integer rates."""
        assert _format_rate(30.0) == "30%"
        assert _format_rate(10.0) == "10%"

    def test_format_rate_decimal(self):
        """Test rate formatting for decimal rates."""
        assert _format_rate(8.5) == "8.5%"
        assert _format_rate(10.25) == "10.25%"

    def test_detect_query_language_vietnamese(self):
        """Test Vietnamese language detection."""
        assert _detect_query_language("thanh treo khăn đồng") == "vi"
        assert _detect_query_language("máy xay sinh tố") == "vi"

    def test_detect_query_language_english(self):
        """Test English language detection."""
        assert _detect_query_language("copper towel rack") == "en"
        assert _detect_query_language("kitchen blender") == "en"

    def test_detect_query_language_chinese(self):
        """Test Chinese language detection."""
        assert _detect_query_language("铜毛巾架") == "zh"
        assert _detect_query_language("搅拌机") == "zh"

    def test_detect_query_language_empty(self):
        """Test empty query returns None."""
        assert _detect_query_language("") is None
        assert _detect_query_language("   ") is None

    def test_detect_query_language_numbers_only(self):
        """Test query with only numbers returns None."""
        assert _detect_query_language("74182000") is None
        assert _detect_query_language("123456") is None


class TestSearchRequestValidation:
    """Test request validation."""

    def test_search_request_valid(self):
        """Test valid search request."""
        from app.schemas.search import SearchRequest

        request = SearchRequest(query="máy xay sinh tố", limit=10)
        assert request.query == "máy xay sinh tố"
        assert request.limit == 10

    def test_search_request_default_limit(self):
        """Test default limit value."""
        from app.schemas.search import SearchRequest

        request = SearchRequest(query="test")
        assert request.limit == 10

    def test_search_request_empty_query_rejected(self):
        """Test that empty query is rejected."""
        from app.schemas.search import SearchRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SearchRequest(query="")

    def test_search_request_limit_bounds(self):
        """Test limit validation bounds."""
        from app.schemas.search import SearchRequest
        from pydantic import ValidationError

        # Too low
        with pytest.raises(ValidationError):
            SearchRequest(query="test", limit=0)

        # Too high
        with pytest.raises(ValidationError):
            SearchRequest(query="test", limit=100)

        # Valid bounds
        SearchRequest(query="test", limit=1)
        SearchRequest(query="test", limit=50)


class TestSearchResponseSchema:
    """Test response schema."""

    def test_search_response_data_valid(self):
        """Test valid search response data."""
        from app.schemas.search import ClassificationSchema, SearchResponseData

        response = SearchResponseData(
            hs_code="7418.20.00",
            description="Đồ trang bị trong nhà vệ sinh",
            duty_rate="30%",
            vat_rate="10%",
            classification=ClassificationSchema(
                material="Sản phẩm bằng đồng",
                function="Đồ dùng nhà vệ sinh",
            ),
            practical_notes=["Note 1", "Note 2"],
            confidence=95,
        )

        assert response.hs_code == "7418.20.00"
        assert response.confidence == 95

    def test_classification_schema(self):
        """Test classification schema."""
        from app.schemas.search import ClassificationSchema

        classification = ClassificationSchema(
            material="Copper material",
            function="Bathroom fixture",
        )

        assert classification.material == "Copper material"
        assert classification.function == "Bathroom fixture"


class TestSearchEndpointIntegration:
    """Integration tests for search endpoint (mocked services)."""

    @pytest.mark.asyncio
    async def test_search_success_flow(self):
        """Test successful search flow."""
        from app.api.search import search_hs_codes
        from app.schemas.search import SearchRequest

        # Create mocks
        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"

        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        # Mock search result
        mock_hs_code = MagicMock()
        mock_hs_code.code = "74182000"
        mock_hs_code.description_vn = "Đồ trang bị trong nhà vệ sinh"
        mock_hs_code.description_en = "Sanitary ware"
        mock_hs_code.duty_rate = 30.0
        mock_hs_code.vat_rate = 10.0
        mock_hs_code.unit = "Chiếc"
        mock_hs_code.fta_rates = []
        mock_hs_code.subheading = None

        mock_result = MagicMock()
        mock_result.hs_code = "74182000"
        mock_result.description_vn = "Đồ trang bị trong nhà vệ sinh"
        mock_result.description_en = "Sanitary ware"
        mock_result.duty_rate = 30.0
        mock_result.vat_rate = 10.0
        mock_result.unit = "Chiếc"
        mock_result.confidence = 95
        mock_result.is_exact_match = False
        mock_result._hs_code_obj = mock_hs_code

        search_request = SearchRequest(query="thanh treo khăn đồng")

        with patch("app.api.search.SearchService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.search.return_value = [mock_result]
            mock_service_class.return_value = mock_service

            response = await search_hs_codes(
                request=mock_request,
                body=search_request,
                db=mock_db,
                redis_client=mock_redis,
            )

        assert response["success"] is True
        assert response["data"]["hs_code"] == "7418.20.00"
        assert response["data"]["confidence"] == 95

    @pytest.mark.asyncio
    async def test_search_no_results(self):
        """Test search with no results."""
        from app.api.search import search_hs_codes
        from app.schemas.search import SearchRequest

        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"

        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        search_request = SearchRequest(query="xyznonexistent123")

        with patch("app.api.search.SearchService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.search.return_value = []
            mock_service_class.return_value = mock_service

            response = await search_hs_codes(
                request=mock_request,
                body=search_request,
                db=mock_db,
                redis_client=mock_redis,
            )

        assert response["success"] is False
        assert response["error"]["status"] == 404
        assert "No matching HS code found" in response["error"]["detail"]

    @pytest.mark.asyncio
    async def test_search_handles_value_error(self):
        """Test search handles ValueError from service."""
        from app.api.search import search_hs_codes
        from app.schemas.search import SearchRequest

        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"

        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        search_request = SearchRequest(query="test")

        with patch("app.api.search.SearchService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.search.side_effect = ValueError("Invalid input")
            mock_service_class.return_value = mock_service

            response = await search_hs_codes(
                request=mock_request,
                body=search_request,
                db=mock_db,
                redis_client=mock_redis,
            )

        assert response["success"] is False
        assert response["error"]["status"] == 400


class TestRecordLookup:
    """Tests for _record_lookup helper function."""

    @pytest.mark.asyncio
    async def test_creates_new_lookup_record(self):
        """Test that a new lookup record is created when no duplicate exists."""
        mock_db = AsyncMock()

        with patch("app.api.search.LookupRecordRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.find_by_query_hash.return_value = None
            mock_repo_class.return_value = mock_repo

            await _record_lookup(
                db=mock_db,
                query="copper towel rack",
                matched_hs_code_id=42,
                confidence_score=85.0,
                search_method="vector",
            )

            mock_repo.find_by_query_hash.assert_awaited_once()
            mock_repo.create.assert_awaited_once()
            created_record = mock_repo.create.call_args[0][0]
            assert created_record.query_text == "copper towel rack"
            assert created_record.query_language == "en"  # Should detect English
            assert created_record.matched_hs_code_id == 42
            assert created_record.confidence_score == 85.0
            assert created_record.search_method == "vector"
            assert created_record.is_verified is False

    @pytest.mark.asyncio
    async def test_deduplicates_within_24h_window(self):
        """Test that duplicate query within 24h updates timestamp instead of creating."""
        mock_db = AsyncMock()
        existing_record = MagicMock()
        existing_record.id = 99

        with patch("app.api.search.LookupRecordRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.find_by_query_hash.return_value = existing_record
            mock_repo_class.return_value = mock_repo

            await _record_lookup(
                db=mock_db,
                query="copper towel rack",
                matched_hs_code_id=42,
                confidence_score=85.0,
                search_method="vector",
            )

            mock_repo.touch_updated_at.assert_awaited_once_with(99)
            mock_repo.create.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_handles_no_results_lookup(self):
        """Test lookup record creation when search returns no results."""
        mock_db = AsyncMock()

        with patch("app.api.search.LookupRecordRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.find_by_query_hash.return_value = None
            mock_repo_class.return_value = mock_repo

            await _record_lookup(
                db=mock_db,
                query="nonexistent product",
                matched_hs_code_id=None,
                confidence_score=None,
                search_method="vector",
            )

            mock_repo.create.assert_awaited_once()
            created_record = mock_repo.create.call_args[0][0]
            assert created_record.matched_hs_code_id is None
            assert created_record.confidence_score is None

    @pytest.mark.asyncio
    async def test_lookup_failure_does_not_raise(self):
        """Test that lookup failure is silently logged and doesn't break search."""
        mock_db = AsyncMock()

        with patch("app.api.search.LookupRecordRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.find_by_query_hash.side_effect = Exception("DB error")
            mock_repo_class.return_value = mock_repo

            # Should not raise
            await _record_lookup(
                db=mock_db,
                query="copper towel rack",
                matched_hs_code_id=42,
                confidence_score=85.0,
                search_method="vector",
            )

    @pytest.mark.asyncio
    async def test_query_hash_is_computed_correctly(self):
        """Test that query hash uses SHA-256 of normalized text."""
        mock_db = AsyncMock()

        with patch("app.api.search.LookupRecordRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.find_by_query_hash.return_value = None
            mock_repo_class.return_value = mock_repo

            await _record_lookup(
                db=mock_db,
                query="  COPPER Towel RACK  ",
                matched_hs_code_id=42,
                confidence_score=85.0,
                search_method="vector",
            )

            created_record = mock_repo.create.call_args[0][0]
            expected_hash = hashlib.sha256(
                "copper towel rack".encode("utf-8")
            ).hexdigest()
            assert created_record.query_hash == expected_hash

    @pytest.mark.asyncio
    async def test_detects_vietnamese_query_language(self):
        """Test that Vietnamese query language is detected and stored."""
        mock_db = AsyncMock()

        with patch("app.api.search.LookupRecordRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.find_by_query_hash.return_value = None
            mock_repo_class.return_value = mock_repo

            await _record_lookup(
                db=mock_db,
                query="thanh treo khăn đồng",
                matched_hs_code_id=42,
                confidence_score=85.0,
                search_method="vector",
            )

            created_record = mock_repo.create.call_args[0][0]
            assert created_record.query_language == "vi"
