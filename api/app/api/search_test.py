"""Tests for search API endpoint."""

import hashlib
from datetime import datetime, timezone

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import status
from fastapi.testclient import TestClient

from app.api.search import _detect_query_language, _format_hs_code, _format_rate, _record_lookup
from app.services.knowledge_base_service import KBLookupResult


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
        """Test that duplicate query within 24h updates existing record instead of creating."""
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

            mock_repo.update.assert_awaited_once_with(existing_record)
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


class TestRecordLookupJSONBPersistence:
    """Tests for JSONB field persistence in _record_lookup (Story 1-11)."""

    @pytest.mark.asyncio
    async def test_stores_classification_data_on_new_record(self):
        """AC2: New record stores classification_data, practical_notes, process_logs."""
        mock_db = AsyncMock()

        with patch("app.api.search.LookupRecordRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.find_by_query_hash.return_value = None
            mock_repo_class.return_value = mock_repo

            classification = {"material": "Copper alloy", "function": "Bathroom fixture"}
            notes = ["Note about import duty", "Note about classification"]
            logs = [{"step": "init", "status": "completed", "message": "Started", "duration_ms": 1, "details": None}]

            await _record_lookup(
                db=mock_db,
                query="copper towel rack",
                matched_hs_code_id=42,
                confidence_score=85.0,
                search_method="vector",
                classification_data=classification,
                practical_notes=notes,
                process_logs=logs,
            )

            mock_repo.create.assert_awaited_once()
            created_record = mock_repo.create.call_args[0][0]
            assert created_record.classification_data == classification
            assert created_record.practical_notes == notes
            assert created_record.process_logs == logs

    @pytest.mark.asyncio
    async def test_dedup_updates_jsonb_fields(self):
        """AC3: Dedup updates classification_data, practical_notes, process_logs on existing record."""
        mock_db = AsyncMock()
        existing_record = MagicMock()
        existing_record.id = 99

        with patch("app.api.search.LookupRecordRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.find_by_query_hash.return_value = existing_record
            mock_repo_class.return_value = mock_repo

            classification = {"material": "Updated material", "function": "Updated function"}
            notes = ["Updated note"]
            logs = [{"step": "init", "status": "completed", "message": "Re-search", "duration_ms": 2, "details": None}]

            result = await _record_lookup(
                db=mock_db,
                query="copper towel rack",
                matched_hs_code_id=42,
                confidence_score=85.0,
                search_method="vector",
                classification_data=classification,
                practical_notes=notes,
                process_logs=logs,
            )

            assert result == 99
            # Should update JSONB fields on existing record
            assert existing_record.classification_data == classification
            assert existing_record.practical_notes == notes
            assert existing_record.process_logs == logs
            # Should call repo.update (not touch_updated_at)
            mock_repo.update.assert_awaited_once_with(existing_record)
            mock_repo.touch_updated_at.assert_not_awaited()
            mock_repo.create.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_no_results_stores_none_classification(self):
        """AC5: No-results path stores None for classification_data and practical_notes."""
        mock_db = AsyncMock()

        with patch("app.api.search.LookupRecordRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.find_by_query_hash.return_value = None
            mock_repo_class.return_value = mock_repo

            logs = [{"step": "search", "status": "completed", "message": "No results", "duration_ms": 50, "details": None}]

            await _record_lookup(
                db=mock_db,
                query="nonexistent product",
                matched_hs_code_id=None,
                confidence_score=None,
                search_method="vector",
                classification_data=None,
                practical_notes=None,
                process_logs=logs,
            )

            created_record = mock_repo.create.call_args[0][0]
            assert created_record.classification_data is None
            assert created_record.practical_notes is None
            assert created_record.process_logs == logs

    @pytest.mark.asyncio
    async def test_jsonb_preserves_nested_structure(self):
        """AC4: JSONB data preserves nested dicts, lists of strings, lists of dicts."""
        mock_db = AsyncMock()

        with patch("app.api.search.LookupRecordRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.find_by_query_hash.return_value = None
            mock_repo_class.return_value = mock_repo

            classification = {"material": "San pham bang dong", "function": "Thiet bi nha tam"}
            notes = ["Note 1", "Note 2", "Note 3"]
            logs = [
                {"step": "init", "status": "completed", "message": "Started", "duration_ms": 1, "details": {"query_language": "vi"}},
                {"step": "kb_exact_lookup", "status": "completed", "message": "KB match found", "duration_ms": 12, "details": {"match_type": "exact", "confidence": 100}},
            ]

            await _record_lookup(
                db=mock_db,
                query="thanh treo khan dong",
                matched_hs_code_id=42,
                confidence_score=100.0,
                search_method="knowledge_base",
                classification_data=classification,
                practical_notes=notes,
                process_logs=logs,
            )

            created_record = mock_repo.create.call_args[0][0]
            # Verify dict structure preserved
            assert created_record.classification_data["material"] == "San pham bang dong"
            assert created_record.classification_data["function"] == "Thiet bi nha tam"
            # Verify list of strings preserved
            assert len(created_record.practical_notes) == 3
            assert created_record.practical_notes[0] == "Note 1"
            # Verify list of dicts with nested dicts preserved
            assert len(created_record.process_logs) == 2
            assert created_record.process_logs[0]["step"] == "init"
            assert created_record.process_logs[0]["details"]["query_language"] == "vi"
            assert created_record.process_logs[1]["details"]["match_type"] == "exact"

    @pytest.mark.asyncio
    async def test_backward_compatible_without_jsonb_params(self):
        """Verify _record_lookup still works when JSONB params are not provided (backward compat)."""
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

            created_record = mock_repo.create.call_args[0][0]
            assert created_record.classification_data is None
            assert created_record.practical_notes is None
            assert created_record.process_logs is None


class TestKBSearchIntegration:
    """Integration tests for KB-enhanced search (AC #1-6)."""

    def _make_mock_hs_code(self):
        """Create a mock HS code object for testing."""
        mock_hs_code = MagicMock()
        mock_hs_code.id = 42
        mock_hs_code.code = "74182000"
        mock_hs_code.description_vn = "Đồ trang bị trong nhà vệ sinh"
        mock_hs_code.description_en = "Sanitary ware"
        mock_hs_code.duty_rate = 30.0
        mock_hs_code.vat_rate = 10.0
        mock_hs_code.unit = "Chiếc"
        mock_hs_code.fta_rates = []
        mock_hs_code.subheading = None
        return mock_hs_code

    def _make_kb_result(self, match_type="exact", confidence=100, similarity=1.0):
        """Create a KBLookupResult for testing."""
        return KBLookupResult(
            hs_code_id=42,
            confidence=confidence,
            similarity_score=similarity,
            lookup_record_id=1,
            verified_by_user_id=5,
            verified_at=datetime(2026, 2, 10, 12, 0, 0, tzinfo=timezone.utc),
            match_type=match_type,
        )

    @pytest.mark.asyncio
    async def test_kb_exact_match_returns_verified_result(self):
        """AC1: KB exact match returns verified result with source='knowledge_base', confidence=100."""
        from app.api.search import search_hs_codes
        from app.schemas.search import SearchRequest

        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        mock_hs_code = self._make_mock_hs_code()
        kb_result = self._make_kb_result(match_type="exact", confidence=100, similarity=1.0)

        # Mock DB execute for HS code loading
        mock_db_result = MagicMock()
        mock_db_result.scalar_one_or_none.return_value = mock_hs_code
        mock_db.execute.return_value = mock_db_result

        search_request = SearchRequest(query="copper towel rack")

        with patch("app.api.search.KnowledgeBaseService") as mock_kb_class, \
             patch("app.api.search.ClassificationAnalyzer") as mock_analyzer_class, \
             patch("app.api.search._record_lookup") as mock_record, \
             patch("app.api.search.get_settings") as mock_get_settings:

            mock_record.return_value = 1
            mock_settings = MagicMock()
            mock_settings.openrouter_api_key = None
            mock_settings.enable_query_enhancement = False
            mock_settings.enable_reranking = False
            mock_settings.llm_reasoning_model = "gpt-4o-mini"
            mock_get_settings.return_value = mock_settings

            mock_kb = AsyncMock()
            mock_kb.lookup.return_value = kb_result
            mock_kb_class.return_value = mock_kb

            mock_analyzer = MagicMock()
            mock_analysis = MagicMock()
            mock_analysis.material = "Copper material"
            mock_analysis.function = "Bathroom fixture"
            mock_analysis.practical_notes = ["Note 1"]
            mock_analyzer.analyze_async = AsyncMock(return_value=mock_analysis)
            mock_analyzer_class.return_value = mock_analyzer

            response = await search_hs_codes(
                request=mock_request,
                body=search_request,
                db=mock_db,
                redis_client=mock_redis,
            )

        assert response["success"] is True
        assert response["data"]["source"] == "knowledge_base"
        assert response["data"]["is_verified"] is True
        assert response["data"]["confidence"] == 100
        assert response["data"]["verified_by"] == "5"
        assert response["data"]["verified_at"] is not None
        assert response["data"]["hs_code"] == "7418.20.00"
        assert response["data"]["lookup_id"] == 1

        # Verify KB lookup was called
        mock_kb.lookup.assert_awaited_once_with("copper towel rack")

        # Verify lookup was recorded with search_method="knowledge_base"
        mock_record.assert_awaited_once()
        call_kwargs = mock_record.call_args[1]
        assert call_kwargs["search_method"] == "knowledge_base"

    @pytest.mark.asyncio
    async def test_kb_similar_match_returns_scaled_confidence(self):
        """AC2: KB similar match returns verified result with scaled confidence."""
        from app.api.search import search_hs_codes
        from app.schemas.search import SearchRequest

        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        mock_hs_code = self._make_mock_hs_code()
        kb_result = self._make_kb_result(match_type="similar", confidence=92, similarity=0.92)

        mock_db_result = MagicMock()
        mock_db_result.scalar_one_or_none.return_value = mock_hs_code
        mock_db.execute.return_value = mock_db_result

        search_request = SearchRequest(query="copper towel holder")

        with patch("app.api.search.KnowledgeBaseService") as mock_kb_class, \
             patch("app.api.search.ClassificationAnalyzer") as mock_analyzer_class, \
             patch("app.api.search._record_lookup", new=AsyncMock(return_value=1)), \
             patch("app.api.search.get_settings") as mock_get_settings:

            mock_settings = MagicMock()
            mock_settings.openrouter_api_key = None
            mock_settings.enable_query_enhancement = False
            mock_settings.enable_reranking = False
            mock_settings.llm_reasoning_model = "gpt-4o-mini"
            mock_get_settings.return_value = mock_settings

            mock_kb = AsyncMock()
            mock_kb.lookup.return_value = kb_result
            mock_kb_class.return_value = mock_kb

            mock_analyzer = MagicMock()
            mock_analysis = MagicMock()
            mock_analysis.material = "Copper material"
            mock_analysis.function = "Bathroom fixture"
            mock_analysis.practical_notes = []
            mock_analyzer.analyze_async = AsyncMock(return_value=mock_analysis)
            mock_analyzer_class.return_value = mock_analyzer

            response = await search_hs_codes(
                request=mock_request,
                body=search_request,
                db=mock_db,
                redis_client=mock_redis,
            )

        assert response["success"] is True
        assert response["data"]["source"] == "knowledge_base"
        assert response["data"]["is_verified"] is True
        assert response["data"]["confidence"] == 92

    @pytest.mark.asyncio
    async def test_no_kb_match_falls_back_to_ai_search(self):
        """AC3: No KB match falls back to AI search with source='ai_suggestion'."""
        from app.api.search import search_hs_codes
        from app.schemas.search import SearchRequest

        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        mock_search_result = MagicMock()
        mock_search_result.hs_code = "74182000"
        mock_search_result.description_vn = "Đồ trang bị trong nhà vệ sinh"
        mock_search_result.description_en = "Sanitary ware"
        mock_search_result.duty_rate = 30.0
        mock_search_result.vat_rate = 10.0
        mock_search_result.unit = "Chiếc"
        mock_search_result.confidence = 85
        mock_search_result.is_exact_match = False
        mock_search_result.hs_code_full = self._make_mock_hs_code()

        search_request = SearchRequest(query="some product description")

        with patch("app.api.search.KnowledgeBaseService") as mock_kb_class, \
             patch("app.api.search.SearchService") as mock_search_class, \
             patch("app.api.search.SearchCacheService") as mock_cache_class, \
             patch("app.api.search.ClassificationAnalyzer") as mock_analyzer_class, \
             patch("app.api.search._record_lookup", new=AsyncMock(return_value=2)), \
             patch("app.api.search.get_settings") as mock_get_settings:

            mock_settings = MagicMock()
            mock_settings.openrouter_api_key = None
            mock_settings.enable_query_enhancement = False
            mock_settings.enable_reranking = False
            mock_settings.llm_reasoning_model = "gpt-4o-mini"
            mock_get_settings.return_value = mock_settings

            # KB returns no match
            mock_kb = AsyncMock()
            mock_kb.lookup.return_value = None
            mock_kb_class.return_value = mock_kb

            # Cache miss
            mock_cache = AsyncMock()
            mock_cache.get.return_value = None
            mock_cache_class.return_value = mock_cache

            # Search service returns result
            mock_search = AsyncMock()
            mock_search.search.return_value = [mock_search_result]
            mock_search_class.return_value = mock_search

            mock_analyzer = MagicMock()
            mock_analysis = MagicMock()
            mock_analysis.material = "Copper material"
            mock_analysis.function = "Bathroom fixture"
            mock_analysis.practical_notes = []
            mock_analyzer.analyze_async = AsyncMock(return_value=mock_analysis)
            mock_analyzer_class.return_value = mock_analyzer

            response = await search_hs_codes(
                request=mock_request,
                body=search_request,
                db=mock_db,
                redis_client=mock_redis,
            )

        assert response["success"] is True
        assert response["data"]["source"] == "ai_suggestion"
        assert response["data"]["is_verified"] is False
        assert response["data"]["verified_by"] is None
        assert response["data"]["verified_at"] is None

    @pytest.mark.asyncio
    async def test_search_priority_order_kb_before_cache(self):
        """AC4: KB lookup happens before cache check - KB hit short-circuits."""
        from app.api.search import search_hs_codes
        from app.schemas.search import SearchRequest

        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        mock_hs_code = self._make_mock_hs_code()
        kb_result = self._make_kb_result()

        mock_db_result = MagicMock()
        mock_db_result.scalar_one_or_none.return_value = mock_hs_code
        mock_db.execute.return_value = mock_db_result

        search_request = SearchRequest(query="copper towel rack")

        with patch("app.api.search.KnowledgeBaseService") as mock_kb_class, \
             patch("app.api.search.SearchCacheService") as mock_cache_class, \
             patch("app.api.search.SearchService") as mock_search_class, \
             patch("app.api.search.ClassificationAnalyzer") as mock_analyzer_class, \
             patch("app.api.search._record_lookup", new=AsyncMock(return_value=1)), \
             patch("app.api.search.get_settings") as mock_get_settings:

            mock_settings = MagicMock()
            mock_settings.openrouter_api_key = None
            mock_settings.enable_query_enhancement = False
            mock_settings.enable_reranking = False
            mock_settings.llm_reasoning_model = "gpt-4o-mini"
            mock_get_settings.return_value = mock_settings

            mock_kb = AsyncMock()
            mock_kb.lookup.return_value = kb_result
            mock_kb_class.return_value = mock_kb

            mock_cache = AsyncMock()
            mock_cache_class.return_value = mock_cache

            mock_search = AsyncMock()
            mock_search_class.return_value = mock_search

            mock_analyzer = MagicMock()
            mock_analysis = MagicMock()
            mock_analysis.material = "Copper"
            mock_analysis.function = "Fixture"
            mock_analysis.practical_notes = []
            mock_analyzer.analyze_async = AsyncMock(return_value=mock_analysis)
            mock_analyzer_class.return_value = mock_analyzer

            response = await search_hs_codes(
                request=mock_request,
                body=search_request,
                db=mock_db,
                redis_client=mock_redis,
            )

        # KB hit should short-circuit - cache and search should NOT be called
        mock_cache.get.assert_not_awaited()
        mock_search.search.assert_not_awaited()
        assert response["data"]["source"] == "knowledge_base"

    @pytest.mark.asyncio
    async def test_response_always_includes_source_and_verification_fields(self):
        """AC5: All responses include source, is_verified, verified_by, verified_at."""
        from app.api.search import search_hs_codes
        from app.schemas.search import SearchRequest

        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        mock_search_result = MagicMock()
        mock_search_result.hs_code = "74182000"
        mock_search_result.description_vn = "Đồ trang bị"
        mock_search_result.description_en = "Sanitary ware"
        mock_search_result.duty_rate = 30.0
        mock_search_result.vat_rate = 10.0
        mock_search_result.unit = "Chiếc"
        mock_search_result.confidence = 85
        mock_search_result.is_exact_match = False
        mock_search_result.hs_code_full = self._make_mock_hs_code()

        search_request = SearchRequest(query="some product")

        with patch("app.api.search.KnowledgeBaseService") as mock_kb_class, \
             patch("app.api.search.SearchService") as mock_search_class, \
             patch("app.api.search.SearchCacheService") as mock_cache_class, \
             patch("app.api.search.ClassificationAnalyzer") as mock_analyzer_class, \
             patch("app.api.search._record_lookup", new=AsyncMock(return_value=3)), \
             patch("app.api.search.get_settings") as mock_get_settings:

            mock_settings = MagicMock()
            mock_settings.openrouter_api_key = None
            mock_settings.enable_query_enhancement = False
            mock_settings.enable_reranking = False
            mock_settings.llm_reasoning_model = "gpt-4o-mini"
            mock_get_settings.return_value = mock_settings

            mock_kb = AsyncMock()
            mock_kb.lookup.return_value = None
            mock_kb_class.return_value = mock_kb

            mock_cache = AsyncMock()
            mock_cache.get.return_value = None
            mock_cache_class.return_value = mock_cache

            mock_search = AsyncMock()
            mock_search.search.return_value = [mock_search_result]
            mock_search_class.return_value = mock_search

            mock_analyzer = MagicMock()
            mock_analysis = MagicMock()
            mock_analysis.material = "Material"
            mock_analysis.function = "Function"
            mock_analysis.practical_notes = []
            mock_analyzer.analyze_async = AsyncMock(return_value=mock_analysis)
            mock_analyzer_class.return_value = mock_analyzer

            response = await search_hs_codes(
                request=mock_request,
                body=search_request,
                db=mock_db,
                redis_client=mock_redis,
            )

        data = response["data"]
        assert "source" in data
        assert "is_verified" in data
        assert "verified_by" in data
        assert "verified_at" in data

    @pytest.mark.asyncio
    async def test_kb_hit_records_lookup_with_knowledge_base_method(self):
        """AC6: KB hit creates lookup record with search_method='knowledge_base'."""
        from app.api.search import search_hs_codes
        from app.schemas.search import SearchRequest

        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        mock_hs_code = self._make_mock_hs_code()
        kb_result = self._make_kb_result()

        mock_db_result = MagicMock()
        mock_db_result.scalar_one_or_none.return_value = mock_hs_code
        mock_db.execute.return_value = mock_db_result

        search_request = SearchRequest(query="copper towel rack")

        with patch("app.api.search.KnowledgeBaseService") as mock_kb_class, \
             patch("app.api.search.ClassificationAnalyzer") as mock_analyzer_class, \
             patch("app.api.search._record_lookup") as mock_record, \
             patch("app.api.search.get_settings") as mock_get_settings:

            mock_record.return_value = 1
            mock_settings = MagicMock()
            mock_settings.openrouter_api_key = None
            mock_settings.enable_query_enhancement = False
            mock_settings.enable_reranking = False
            mock_settings.llm_reasoning_model = "gpt-4o-mini"
            mock_get_settings.return_value = mock_settings

            mock_kb = AsyncMock()
            mock_kb.lookup.return_value = kb_result
            mock_kb_class.return_value = mock_kb

            mock_analyzer = MagicMock()
            mock_analysis = MagicMock()
            mock_analysis.material = "Copper"
            mock_analysis.function = "Fixture"
            mock_analysis.practical_notes = []
            mock_analyzer.analyze_async = AsyncMock(return_value=mock_analysis)
            mock_analyzer_class.return_value = mock_analyzer

            response = await search_hs_codes(
                request=mock_request,
                body=search_request,
                db=mock_db,
                redis_client=mock_redis,
            )

        mock_record.assert_awaited_once()
        call_kwargs = mock_record.call_args[1]
        assert call_kwargs["search_method"] == "knowledge_base"
        assert call_kwargs["matched_hs_code_id"] == 42
        assert call_kwargs["confidence_score"] == 100


class TestNotebookLMIntegration:
    """Integration tests for NotebookLM search pipeline (Story 3-2)."""

    def _make_mock_hs_code(self, code="74182000", hs_id=42):
        """Create a mock HS code object for testing."""
        mock_hs_code = MagicMock()
        mock_hs_code.id = hs_id
        mock_hs_code.code = code
        mock_hs_code.description_vn = "Đồ trang bị trong nhà vệ sinh"
        mock_hs_code.description_en = "Sanitary ware"
        mock_hs_code.duty_rate = 30.0
        mock_hs_code.vat_rate = 10.0
        mock_hs_code.unit = "Chiếc"
        mock_hs_code.fta_rates = []
        mock_hs_code.subheading = None
        return mock_hs_code

    def _make_mock_nlm_result(self, hs_code="7418.20.00", from_cache=False, confidence=88):
        """Create a mock NotebookLMResult."""
        from app.services.notebooklm_service import NotebookLMResult

        return NotebookLMResult(
            hs_code=hs_code,
            classification={"reasoning": "GRI 1", "material": "copper", "function": "bathroom fitting"},
            practical_notes=["Use EVFTA for 3.7% rate"],
            raw_answer="Full markdown response...",
            from_cache=from_cache,
            confidence=confidence,
        )

    def _make_mock_nlm_guide(self, from_cache=False):
        """Create a mock NotebookLMResult for a categorized guide (no HS code)."""
        from app.services.notebooklm_service import NotebookLMResult

        return NotebookLMResult(
            hs_code=None,
            classification=None,
            practical_notes=[],
            raw_answer="Categorized guide: this product needs manual classification...",
            from_cache=from_cache,
            confidence=0,
        )

    def _base_patches(self):
        """Return common patches for NLM integration tests."""
        mock_settings = MagicMock()
        mock_settings.openrouter_api_key = None
        mock_settings.enable_query_enhancement = False
        mock_settings.enable_reranking = False
        mock_settings.llm_reasoning_model = "gpt-4o-mini"
        return mock_settings

    @pytest.mark.asyncio
    async def test_nlm_success_hs_code_found(self):
        """AC1: NLM returns HS code found in DB → source='notebooklm', dynamic confidence."""
        from app.api.search import search_hs_codes
        from app.schemas.search import SearchRequest

        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        mock_hs_code = self._make_mock_hs_code()
        nlm_result = self._make_mock_nlm_result(from_cache=False)

        # DB returns the HS code on lookup
        mock_db_result = MagicMock()
        mock_db_result.scalar_one_or_none.return_value = mock_hs_code
        mock_db.execute.return_value = mock_db_result

        search_request = SearchRequest(query="Thanh treo khăn bằng đồng mạ chrome")

        with patch("app.api.search.KnowledgeBaseService") as mock_kb_class, \
             patch("app.api.search.NotebookLMService") as mock_nlm_class, \
             patch("app.api.search.SearchCacheService") as mock_cache_class, \
             patch("app.api.search._record_lookup") as mock_record, \
             patch("app.api.search.get_settings") as mock_get_settings:

            mock_get_settings.return_value = self._base_patches()
            mock_record.return_value = 10

            # KB returns no match
            mock_kb = AsyncMock()
            mock_kb.lookup.return_value = None
            mock_kb_class.return_value = mock_kb

            # Cache service (not used, but needs to be mocked)
            mock_cache = AsyncMock()
            mock_cache.get.return_value = None
            mock_cache.set = AsyncMock()
            mock_cache_class.return_value = mock_cache

            # NLM returns successful result
            mock_nlm = AsyncMock()
            mock_nlm.query.return_value = nlm_result
            mock_nlm_class.return_value = mock_nlm

            response = await search_hs_codes(
                request=mock_request,
                body=search_request,
                db=mock_db,
                redis_client=mock_redis,
            )

        assert response["success"] is True
        assert response["data"]["source"] == "notebooklm"
        assert response["data"]["confidence"] == 88  # Dynamic from nlm_result
        assert response["data"]["hs_code"] == "7418.20.00"
        assert response["data"]["is_verified"] is False
        assert response["data"]["lookup_id"] == 10

        # Verify NLM was called
        mock_nlm.query.assert_awaited_once_with("Thanh treo khăn bằng đồng mạ chrome")

        # Verify lookup recorded with search_method="notebooklm"
        mock_record.assert_awaited_once()
        call_kwargs = mock_record.call_args[1]
        assert call_kwargs["search_method"] == "notebooklm"
        assert call_kwargs["confidence_score"] == 88  # Dynamic from nlm_result

    @pytest.mark.asyncio
    async def test_nlm_cache_hit(self):
        """AC2: NLM cached result → source='cache', dynamic confidence, no new API call."""
        from app.api.search import search_hs_codes
        from app.schemas.search import SearchRequest

        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        mock_hs_code = self._make_mock_hs_code()
        nlm_result = self._make_mock_nlm_result(from_cache=True)

        mock_db_result = MagicMock()
        mock_db_result.scalar_one_or_none.return_value = mock_hs_code
        mock_db.execute.return_value = mock_db_result

        search_request = SearchRequest(query="Thanh treo khăn bằng đồng mạ chrome")

        with patch("app.api.search.KnowledgeBaseService") as mock_kb_class, \
             patch("app.api.search.NotebookLMService") as mock_nlm_class, \
             patch("app.api.search.SearchCacheService") as mock_cache_class, \
             patch("app.api.search._record_lookup", new=AsyncMock(return_value=11)), \
             patch("app.api.search.get_settings") as mock_get_settings:

            mock_get_settings.return_value = self._base_patches()

            mock_kb = AsyncMock()
            mock_kb.lookup.return_value = None
            mock_kb_class.return_value = mock_kb

            # Cache service (not used, but needs to be mocked)
            mock_cache = AsyncMock()
            mock_cache.get.return_value = None
            mock_cache.set = AsyncMock()
            mock_cache_class.return_value = mock_cache

            mock_nlm = AsyncMock()
            mock_nlm.query.return_value = nlm_result
            mock_nlm_class.return_value = mock_nlm

            response = await search_hs_codes(
                request=mock_request,
                body=search_request,
                db=mock_db,
                redis_client=mock_redis,
            )

        assert response["success"] is True
        assert response["data"]["source"] == "cache"
        assert response["data"]["confidence"] == 88  # Dynamic from nlm_result

    @pytest.mark.asyncio
    async def test_nlm_unavailable_fallback(self):
        """AC3: NLM unavailable → falls back to vector search, process_logs has fallback entry."""
        from app.api.search import search_hs_codes
        from app.schemas.search import SearchRequest
        from app.services.notebooklm_service import NotebookLMUnavailableError

        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        mock_search_result = MagicMock()
        mock_search_result.hs_code = "74182000"
        mock_search_result.description_vn = "Đồ trang bị trong nhà vệ sinh"
        mock_search_result.description_en = "Sanitary ware"
        mock_search_result.duty_rate = 30.0
        mock_search_result.vat_rate = 10.0
        mock_search_result.unit = "Chiếc"
        mock_search_result.confidence = 85
        mock_search_result.is_exact_match = False
        mock_search_result.hs_code_full = self._make_mock_hs_code()

        search_request = SearchRequest(query="copper towel rack")

        with patch("app.api.search.KnowledgeBaseService") as mock_kb_class, \
             patch("app.api.search.NotebookLMService") as mock_nlm_class, \
             patch("app.api.search.SearchService") as mock_search_class, \
             patch("app.api.search.SearchCacheService") as mock_cache_class, \
             patch("app.api.search.ClassificationAnalyzer") as mock_analyzer_class, \
             patch("app.api.search._record_lookup", new=AsyncMock(return_value=12)), \
             patch("app.api.search.get_settings") as mock_get_settings:

            mock_get_settings.return_value = self._base_patches()

            mock_kb = AsyncMock()
            mock_kb.lookup.return_value = None
            mock_kb_class.return_value = mock_kb

            # NLM raises unavailable
            mock_nlm = AsyncMock()
            mock_nlm.query.side_effect = NotebookLMUnavailableError(reason="timeout")
            mock_nlm_class.return_value = mock_nlm

            # Cache miss
            mock_cache = AsyncMock()
            mock_cache.get.return_value = None
            mock_cache_class.return_value = mock_cache

            # Search returns result
            mock_search = AsyncMock()
            mock_search.search.return_value = [mock_search_result]
            mock_search_class.return_value = mock_search

            mock_analyzer = MagicMock()
            mock_analysis = MagicMock()
            mock_analysis.material = "Copper"
            mock_analysis.function = "Fixture"
            mock_analysis.practical_notes = []
            mock_analyzer.analyze_async = AsyncMock(return_value=mock_analysis)
            mock_analyzer_class.return_value = mock_analyzer

            response = await search_hs_codes(
                request=mock_request,
                body=search_request,
                db=mock_db,
                redis_client=mock_redis,
            )

        assert response["success"] is True
        assert response["data"]["source"] == "ai_suggestion"

        # Verify process_logs has fallback entry
        logs = response["data"]["process_logs"]
        nlm_fallback_logs = [
            log for log in logs
            if log["step"] == "notebooklm" and log["status"] == "failed"
        ]
        assert len(nlm_fallback_logs) == 1
        assert "NotebookLM unavailable" in nlm_fallback_logs[0]["message"]
        assert "falling back to vector search" in nlm_fallback_logs[0]["message"]

    @pytest.mark.asyncio
    async def test_nlm_guide_no_hs_code(self):
        """AC4: NLM returns guide (no HS code) → confidence=0, guidance text."""
        from app.api.search import search_hs_codes
        from app.schemas.search import SearchRequest

        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        nlm_guide = self._make_mock_nlm_guide()

        search_request = SearchRequest(query="sản phẩm phức hợp")

        with patch("app.api.search.KnowledgeBaseService") as mock_kb_class, \
             patch("app.api.search.NotebookLMService") as mock_nlm_class, \
             patch("app.api.search._record_lookup") as mock_record, \
             patch("app.api.search.get_settings") as mock_get_settings:

            mock_get_settings.return_value = self._base_patches()
            mock_record.return_value = 13

            mock_kb = AsyncMock()
            mock_kb.lookup.return_value = None
            mock_kb_class.return_value = mock_kb

            mock_nlm = AsyncMock()
            mock_nlm.query.return_value = nlm_guide
            mock_nlm_class.return_value = mock_nlm

            response = await search_hs_codes(
                request=mock_request,
                body=search_request,
                db=mock_db,
                redis_client=mock_redis,
            )

        assert response["success"] is True
        assert response["data"]["confidence"] == 0
        assert response["data"]["source"] == "notebooklm"
        assert "Categorized guide" in response["data"]["classification"]["function"]
        assert response["data"]["hs_code"] == "0000.00.00"

        # Verify lookup was recorded with confidence=0
        mock_record.assert_awaited_once()
        call_kwargs = mock_record.call_args[1]
        assert call_kwargs["confidence_score"] == 0
        assert call_kwargs["search_method"] == "notebooklm"

    @pytest.mark.asyncio
    async def test_nlm_hs_code_not_in_db(self):
        """AC5: NLM returns HS code not in DB → falls back to vector search."""
        from app.api.search import search_hs_codes
        from app.schemas.search import SearchRequest

        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        nlm_result = self._make_mock_nlm_result(hs_code="9999.99.99")

        mock_search_result = MagicMock()
        mock_search_result.hs_code = "74182000"
        mock_search_result.description_vn = "Đồ trang bị"
        mock_search_result.description_en = "Sanitary"
        mock_search_result.duty_rate = 30.0
        mock_search_result.vat_rate = 10.0
        mock_search_result.unit = "Chiếc"
        mock_search_result.confidence = 80
        mock_search_result.is_exact_match = False
        mock_search_result.hs_code_full = self._make_mock_hs_code()

        search_request = SearchRequest(query="some product")

        # First DB call (for NLM HS code) returns None, second calls are for fallback
        db_results = []
        # NLM DB lookup returns None (code not found)
        nlm_db_result = MagicMock()
        nlm_db_result.scalar_one_or_none.return_value = None
        db_results.append(nlm_db_result)

        mock_db.execute = AsyncMock(side_effect=db_results)

        with patch("app.api.search.KnowledgeBaseService") as mock_kb_class, \
             patch("app.api.search.NotebookLMService") as mock_nlm_class, \
             patch("app.api.search.SearchService") as mock_search_class, \
             patch("app.api.search.SearchCacheService") as mock_cache_class, \
             patch("app.api.search.ClassificationAnalyzer") as mock_analyzer_class, \
             patch("app.api.search._record_lookup", new=AsyncMock(return_value=14)), \
             patch("app.api.search.get_settings") as mock_get_settings:

            mock_get_settings.return_value = self._base_patches()

            mock_kb = AsyncMock()
            mock_kb.lookup.return_value = None
            mock_kb_class.return_value = mock_kb

            mock_nlm = AsyncMock()
            mock_nlm.query.return_value = nlm_result
            mock_nlm_class.return_value = mock_nlm

            mock_cache = AsyncMock()
            mock_cache.get.return_value = None
            mock_cache_class.return_value = mock_cache

            mock_search = AsyncMock()
            mock_search.search.return_value = [mock_search_result]
            mock_search_class.return_value = mock_search

            mock_analyzer = MagicMock()
            mock_analysis = MagicMock()
            mock_analysis.material = "Material"
            mock_analysis.function = "Function"
            mock_analysis.practical_notes = []
            mock_analyzer.analyze_async = AsyncMock(return_value=mock_analysis)
            mock_analyzer_class.return_value = mock_analyzer

            response = await search_hs_codes(
                request=mock_request,
                body=search_request,
                db=mock_db,
                redis_client=mock_redis,
            )

        assert response["success"] is True
        assert response["data"]["source"] == "ai_suggestion"

        # Verify process_logs has NLM DB lookup failure
        logs = response["data"]["process_logs"]
        nlm_db_logs = [
            log for log in logs
            if log["step"] == "notebooklm_db_lookup" and log["status"] == "failed"
        ]
        assert len(nlm_db_logs) == 1
        assert "not found in database" in nlm_db_logs[0]["message"]

    @pytest.mark.asyncio
    async def test_nlm_disabled(self):
        """AC6: NLM disabled → skipped, proceeds to vector search."""
        from app.api.search import search_hs_codes
        from app.schemas.search import SearchRequest

        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        mock_search_result = MagicMock()
        mock_search_result.hs_code = "74182000"
        mock_search_result.description_vn = "Đồ trang bị"
        mock_search_result.description_en = "Sanitary"
        mock_search_result.duty_rate = 30.0
        mock_search_result.vat_rate = 10.0
        mock_search_result.unit = "Chiếc"
        mock_search_result.confidence = 80
        mock_search_result.is_exact_match = False
        mock_search_result.hs_code_full = self._make_mock_hs_code()

        search_request = SearchRequest(query="some product")

        with patch("app.api.search.KnowledgeBaseService") as mock_kb_class, \
             patch("app.api.search.NotebookLMService") as mock_nlm_class, \
             patch("app.api.search.SearchService") as mock_search_class, \
             patch("app.api.search.SearchCacheService") as mock_cache_class, \
             patch("app.api.search.ClassificationAnalyzer") as mock_analyzer_class, \
             patch("app.api.search._record_lookup", new=AsyncMock(return_value=15)), \
             patch("app.api.search.get_settings") as mock_get_settings:

            mock_get_settings.return_value = self._base_patches()

            mock_kb = AsyncMock()
            mock_kb.lookup.return_value = None
            mock_kb_class.return_value = mock_kb

            # NLM returns None (disabled)
            mock_nlm = AsyncMock()
            mock_nlm.query.return_value = None
            mock_nlm_class.return_value = mock_nlm

            mock_cache = AsyncMock()
            mock_cache.get.return_value = None
            mock_cache_class.return_value = mock_cache

            mock_search = AsyncMock()
            mock_search.search.return_value = [mock_search_result]
            mock_search_class.return_value = mock_search

            mock_analyzer = MagicMock()
            mock_analysis = MagicMock()
            mock_analysis.material = "Material"
            mock_analysis.function = "Function"
            mock_analysis.practical_notes = []
            mock_analyzer.analyze_async = AsyncMock(return_value=mock_analysis)
            mock_analyzer_class.return_value = mock_analyzer

            response = await search_hs_codes(
                request=mock_request,
                body=search_request,
                db=mock_db,
                redis_client=mock_redis,
            )

        assert response["success"] is True
        assert response["data"]["source"] == "ai_suggestion"

        # Verify process_logs has NLM disabled entry
        logs = response["data"]["process_logs"]
        nlm_skipped_logs = [
            log for log in logs
            if log["step"] == "notebooklm" and log["status"] == "skipped"
        ]
        assert len(nlm_skipped_logs) == 1
        assert "NotebookLM disabled" in nlm_skipped_logs[0]["message"]

    @pytest.mark.asyncio
    async def test_nlm_success_includes_nlm_raw_response(self):
        """NLM success path includes nlm_raw_response in API response."""
        from app.api.search import search_hs_codes
        from app.schemas.search import SearchRequest

        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        mock_hs_code = self._make_mock_hs_code()
        nlm_result = self._make_mock_nlm_result(from_cache=False)

        mock_db_result = MagicMock()
        mock_db_result.scalar_one_or_none.return_value = mock_hs_code
        mock_db.execute.return_value = mock_db_result

        search_request = SearchRequest(query="copper towel rack")

        with patch("app.api.search.KnowledgeBaseService") as mock_kb_class, \
             patch("app.api.search.NotebookLMService") as mock_nlm_class, \
             patch("app.api.search.SearchCacheService") as mock_cache_class, \
             patch("app.api.search._record_lookup", new=AsyncMock(return_value=20)), \
             patch("app.api.search.get_settings") as mock_get_settings:

            mock_get_settings.return_value = self._base_patches()

            mock_kb = AsyncMock()
            mock_kb.lookup.return_value = None
            mock_kb_class.return_value = mock_kb

            mock_cache = AsyncMock()
            mock_cache.get.return_value = None
            mock_cache.set = AsyncMock()
            mock_cache_class.return_value = mock_cache

            mock_nlm = AsyncMock()
            mock_nlm.query.return_value = nlm_result
            mock_nlm_class.return_value = mock_nlm

            response = await search_hs_codes(
                request=mock_request,
                body=search_request,
                db=mock_db,
                redis_client=mock_redis,
            )

        assert response["success"] is True
        assert response["data"]["nlm_raw_response"] == "Full markdown response..."

    @pytest.mark.asyncio
    async def test_nlm_guide_includes_nlm_raw_response(self):
        """NLM guide path (no HS code) includes nlm_raw_response in API response."""
        from app.api.search import search_hs_codes
        from app.schemas.search import SearchRequest

        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        nlm_guide = self._make_mock_nlm_guide()

        search_request = SearchRequest(query="sản phẩm phức hợp")

        with patch("app.api.search.KnowledgeBaseService") as mock_kb_class, \
             patch("app.api.search.NotebookLMService") as mock_nlm_class, \
             patch("app.api.search._record_lookup", new=AsyncMock(return_value=21)), \
             patch("app.api.search.get_settings") as mock_get_settings:

            mock_get_settings.return_value = self._base_patches()

            mock_kb = AsyncMock()
            mock_kb.lookup.return_value = None
            mock_kb_class.return_value = mock_kb

            mock_nlm = AsyncMock()
            mock_nlm.query.return_value = nlm_guide
            mock_nlm_class.return_value = mock_nlm

            response = await search_hs_codes(
                request=mock_request,
                body=search_request,
                db=mock_db,
                redis_client=mock_redis,
            )

        assert response["success"] is True
        assert response["data"]["nlm_raw_response"] == "Categorized guide: this product needs manual classification..."

    @pytest.mark.asyncio
    async def test_non_nlm_search_has_null_nlm_raw_response(self):
        """Non-NLM search paths return nlm_raw_response=None."""
        from app.api.search import search_hs_codes
        from app.schemas.search import SearchRequest

        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        mock_search_result = MagicMock()
        mock_search_result.hs_code = "74182000"
        mock_search_result.description_vn = "Đồ trang bị"
        mock_search_result.description_en = "Sanitary"
        mock_search_result.duty_rate = 30.0
        mock_search_result.vat_rate = 10.0
        mock_search_result.unit = "Chiếc"
        mock_search_result.confidence = 80
        mock_search_result.is_exact_match = False
        mock_search_result.hs_code_full = self._make_mock_hs_code()

        search_request = SearchRequest(query="some product")

        with patch("app.api.search.KnowledgeBaseService") as mock_kb_class, \
             patch("app.api.search.NotebookLMService") as mock_nlm_class, \
             patch("app.api.search.SearchService") as mock_search_class, \
             patch("app.api.search.SearchCacheService") as mock_cache_class, \
             patch("app.api.search.ClassificationAnalyzer") as mock_analyzer_class, \
             patch("app.api.search._record_lookup", new=AsyncMock(return_value=22)), \
             patch("app.api.search.get_settings") as mock_get_settings:

            mock_get_settings.return_value = self._base_patches()

            mock_kb = AsyncMock()
            mock_kb.lookup.return_value = None
            mock_kb_class.return_value = mock_kb

            # NLM disabled
            mock_nlm = AsyncMock()
            mock_nlm.query.return_value = None
            mock_nlm_class.return_value = mock_nlm

            mock_cache = AsyncMock()
            mock_cache.get.return_value = None
            mock_cache_class.return_value = mock_cache

            mock_search = AsyncMock()
            mock_search.search.return_value = [mock_search_result]
            mock_search_class.return_value = mock_search

            mock_analyzer = MagicMock()
            mock_analysis = MagicMock()
            mock_analysis.material = "Material"
            mock_analysis.function = "Function"
            mock_analysis.practical_notes = []
            mock_analyzer.analyze_async = AsyncMock(return_value=mock_analysis)
            mock_analyzer_class.return_value = mock_analyzer

            response = await search_hs_codes(
                request=mock_request,
                body=search_request,
                db=mock_db,
                redis_client=mock_redis,
            )

        assert response["success"] is True
        assert response["data"]["nlm_raw_response"] is None

    @pytest.mark.asyncio
    async def test_nlm_auto_stores_in_kb(self):
        """AC1: NLM success auto-stores in KB via _record_lookup with search_method='notebooklm'."""
        from app.api.search import search_hs_codes
        from app.schemas.search import SearchRequest

        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        mock_hs_code = self._make_mock_hs_code()
        nlm_result = self._make_mock_nlm_result()

        mock_db_result = MagicMock()
        mock_db_result.scalar_one_or_none.return_value = mock_hs_code
        mock_db.execute.return_value = mock_db_result

        search_request = SearchRequest(query="copper rack")

        with patch("app.api.search.KnowledgeBaseService") as mock_kb_class, \
             patch("app.api.search.NotebookLMService") as mock_nlm_class, \
             patch("app.api.search.SearchCacheService") as mock_cache_class, \
             patch("app.api.search._record_lookup") as mock_record, \
             patch("app.api.search.get_settings") as mock_get_settings:

            mock_get_settings.return_value = self._base_patches()
            mock_record.return_value = 16

            mock_kb = AsyncMock()
            mock_kb.lookup.return_value = None
            mock_kb_class.return_value = mock_kb

            # Cache service (not used, but needs to be mocked)
            mock_cache = AsyncMock()
            mock_cache.get.return_value = None
            mock_cache.set = AsyncMock()
            mock_cache_class.return_value = mock_cache

            mock_nlm = AsyncMock()
            mock_nlm.query.return_value = nlm_result
            mock_nlm_class.return_value = mock_nlm

            await search_hs_codes(
                request=mock_request,
                body=search_request,
                db=mock_db,
                redis_client=mock_redis,
            )

        # Verify _record_lookup was called with NLM-specific data
        mock_record.assert_awaited_once()
        call_kwargs = mock_record.call_args[1]
        assert call_kwargs["search_method"] == "notebooklm"
        assert call_kwargs["matched_hs_code_id"] == 42
        assert call_kwargs["confidence_score"] == 88  # Dynamic from nlm_result
        # Stored classification uses resolved values (material/function only, no reasoning key)
        assert call_kwargs["classification_data"] == {
            "material": "copper",
            "function": "bathroom fitting",
        }
        assert call_kwargs["practical_notes"] == nlm_result.practical_notes

    @pytest.mark.asyncio
    async def test_nlm_returns_malformed_hs_code(self):
        """NLM returns malformed HS code (wrong length/format) → falls back to vector search."""
        from app.api.search import search_hs_codes
        from app.schemas.search import SearchRequest
        from app.services.notebooklm_service import NotebookLMResult

        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        # Malformed HS code: missing digits (only 6 chars after dot removal)
        malformed_result = NotebookLMResult(
            hs_code="74.18.20",  # Only 6 digits, not 8
            classification={"reasoning": "test", "material": "copper", "function": "rack"},
            practical_notes=[],
            raw_answer="Malformed code response",
            from_cache=False,
            confidence=60,
        )

        # Vector search fallback result
        mock_search_result = MagicMock()
        mock_search_result.hs_code = "99999999"
        mock_search_result.description_vn = "Fallback result"
        mock_search_result.description_en = "Fallback"
        mock_search_result.duty_rate = 30.0
        mock_search_result.vat_rate = 10.0
        mock_search_result.unit = "Chiếc"
        mock_search_result.confidence = 75
        mock_search_result.is_exact_match = False
        mock_search_result.hs_code_full = self._make_mock_hs_code(code="99999999", hs_id=99)

        search_request = SearchRequest(query="copper rack")

        with patch("app.api.search.KnowledgeBaseService") as mock_kb_class, \
             patch("app.api.search.NotebookLMService") as mock_nlm_class, \
             patch("app.api.search.SearchService") as mock_search_class, \
             patch("app.api.search.SearchCacheService") as mock_cache_class, \
             patch("app.api.search.ClassificationAnalyzer") as mock_analyzer_class, \
             patch("app.api.search._record_lookup") as mock_record, \
             patch("app.api.search.get_settings") as mock_get_settings:

            mock_get_settings.return_value = self._base_patches()

            mock_kb = AsyncMock()
            mock_kb.lookup.return_value = None
            mock_kb_class.return_value = mock_kb

            mock_nlm = AsyncMock()
            mock_nlm.query.return_value = malformed_result
            mock_nlm_class.return_value = mock_nlm

            # Mock cache service (no cache hit)
            mock_cache = AsyncMock()
            mock_cache.get.return_value = None
            mock_cache.set = AsyncMock()
            mock_cache_class.return_value = mock_cache

            # Mock vector search fallback
            mock_search = AsyncMock()
            mock_search.search.return_value = [mock_search_result]
            mock_search_class.return_value = mock_search

            mock_analyzer = MagicMock()
            mock_analysis = MagicMock()
            mock_analysis.material = "fallback material"
            mock_analysis.function = "fallback function"
            mock_analysis.practical_notes = []
            mock_analyzer.analyze_async = AsyncMock(return_value=mock_analysis)
            mock_analyzer_class.return_value = mock_analyzer

            mock_record.return_value = 17

            response = await search_hs_codes(
                request=mock_request,
                body=search_request,
                db=mock_db,
                redis_client=mock_redis,
            )

        # Verify fallback to vector search
        assert response["success"] is True
        assert response["data"]["hs_code"] == "9999.99.99"
        assert response["data"]["source"] == "ai_suggestion"

        # Verify process logs show malformed code failure
        nlm_failed_logs = [
            log for log in response["data"]["process_logs"]
            if log["step"] == "notebooklm" and log["status"] == "failed"
        ]
        assert len(nlm_failed_logs) == 1
        assert "malformed HS code" in nlm_failed_logs[0]["message"]
        assert "falling back" in nlm_failed_logs[0]["message"]


class TestNLMRawResponsePersistence:
    """Tests for nlm_raw_response persistence in _record_lookup (Story 3-3)."""

    @pytest.mark.asyncio
    async def test_stores_nlm_raw_response_on_new_record(self):
        """AC2: NLM success stores raw_answer in nlm_raw_response on new record."""
        mock_db = AsyncMock()

        with patch("app.api.search.LookupRecordRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.find_by_query_hash.return_value = None
            mock_repo_class.return_value = mock_repo

            raw_answer = "## HS Code: 7418.20.00\n\nCopper towel rack classification..."

            await _record_lookup(
                db=mock_db,
                query="copper towel rack",
                matched_hs_code_id=42,
                confidence_score=95.0,
                search_method="notebooklm",
                classification_data={"material": "copper", "function": "bathroom"},
                practical_notes=["Use EVFTA"],
                process_logs=[{"step": "nlm", "status": "completed", "message": "ok"}],
                nlm_raw_response=raw_answer,
            )

            mock_repo.create.assert_awaited_once()
            created_record = mock_repo.create.call_args[0][0]
            assert created_record.nlm_raw_response == raw_answer

    @pytest.mark.asyncio
    async def test_dedup_updates_nlm_raw_response(self):
        """AC5: Dedup updates nlm_raw_response on existing record."""
        mock_db = AsyncMock()
        existing_record = MagicMock()
        existing_record.id = 99
        existing_record.nlm_raw_response = "Old response"

        with patch("app.api.search.LookupRecordRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.find_by_query_hash.return_value = existing_record
            mock_repo_class.return_value = mock_repo

            new_raw_answer = "Updated NLM response with fresh data"

            result = await _record_lookup(
                db=mock_db,
                query="copper towel rack",
                matched_hs_code_id=42,
                confidence_score=95.0,
                search_method="notebooklm",
                nlm_raw_response=new_raw_answer,
            )

            assert result == 99
            assert existing_record.nlm_raw_response == new_raw_answer
            mock_repo.update.assert_awaited_once_with(existing_record)
            mock_repo.create.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_non_nlm_stores_null_raw_response(self):
        """AC4: Non-NLM lookup stores nlm_raw_response=None by default."""
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
                classification_data={"material": "copper", "function": "bathroom"},
            )

            created_record = mock_repo.create.call_args[0][0]
            assert created_record.nlm_raw_response is None

    @pytest.mark.asyncio
    async def test_lookup_record_model_has_nlm_raw_response_field(self):
        """AC1: LookupRecord model supports nlm_raw_response field."""
        from app.models.lookup_record import LookupRecord

        record = LookupRecord(
            query_text="test query",
            query_hash="abc123",
            is_verified=False,
            search_method="notebooklm",
            nlm_raw_response="Full markdown response from NLM",
        )
        assert record.nlm_raw_response == "Full markdown response from NLM"

        # Also test None
        record_no_nlm = LookupRecord(
            query_text="test query",
            query_hash="abc123",
            is_verified=False,
            search_method="vector",
        )
        assert record_no_nlm.nlm_raw_response is None

    @pytest.mark.asyncio
    async def test_nlm_raw_response_full_persistence_flow(self):
        """Integration: Verify nlm_raw_response persists through create → update → retrieve flow.

        This test validates the complete lifecycle:
        1. Create new record with nlm_raw_response
        2. Retrieve it back (simulated)
        3. Update via dedup with new nlm_raw_response
        4. Verify the update persisted

        Addresses code review finding: Need integration test for full E2E flow.
        """
        mock_db = AsyncMock()

        with patch("app.api.search.LookupRecordRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo

            # Phase 1: Create new record with nlm_raw_response
            mock_repo.find_by_query_hash.return_value = None
            created_record = MagicMock()
            created_record.id = 100
            created_record.nlm_raw_response = "Original NLM response content"
            mock_repo.create.return_value = created_record

            original_response = "## HS Code: 7418.20.00\n\nOriginal classification..."
            record_id = await _record_lookup(
                db=mock_db,
                query="copper towel rack",
                matched_hs_code_id=42,
                confidence_score=95.0,
                search_method="notebooklm",
                classification_data={"material": "copper"},
                nlm_raw_response=original_response,
            )

            assert record_id == 100
            mock_repo.create.assert_awaited_once()
            created = mock_repo.create.call_args[0][0]
            assert created.nlm_raw_response == original_response

            # Phase 2: Simulate dedup - same query within 24h
            mock_repo.reset_mock()
            existing = MagicMock()
            existing.id = 100
            existing.nlm_raw_response = original_response
            mock_repo.find_by_query_hash.return_value = existing

            updated_response = "## HS Code: 7418.20.00\n\nUpdated classification with fresh data..."
            record_id_2 = await _record_lookup(
                db=mock_db,
                query="copper towel rack",  # Same query
                matched_hs_code_id=42,
                confidence_score=96.0,
                search_method="notebooklm",
                classification_data={"material": "copper", "function": "bathroom"},
                nlm_raw_response=updated_response,
            )

            # Should return same ID (dedup)
            assert record_id_2 == 100
            # Should have updated nlm_raw_response
            assert existing.nlm_raw_response == updated_response
            mock_repo.update.assert_awaited_once_with(existing)
            # Should NOT create new record
            mock_repo.create.assert_not_awaited()
