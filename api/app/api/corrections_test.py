"""Tests for corrections API endpoint."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.corrections import (
    CORRECTION_RATE_LIMIT,
    CORRECTION_RATE_PREFIX,
    CORRECTION_RATE_WINDOW,
    check_correction_rate_limit,
)
from app.schemas.correction import CorrectionRequest
from app.services.knowledge_base_service import KnowledgeBaseService


class TestCheckCorrectionRateLimit:
    """Test the correction rate limiting function."""

    def _make_mock_redis(self, current_count: int):
        """Create a mock Redis client with pipeline for rate limiting."""
        mock_redis = AsyncMock()
        mock_pipe = AsyncMock()
        mock_pipe.execute.return_value = [None, current_count, None, None]

        # pipeline() is a sync method returning an async context manager
        mock_ctx = MagicMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_pipe)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_redis.pipeline = MagicMock(return_value=mock_ctx)

        return mock_redis, mock_pipe

    @pytest.mark.asyncio
    async def test_allows_when_under_limit(self):
        """Test allows request when under rate limit."""
        mock_redis, _ = self._make_mock_redis(current_count=5)

        allowed, remaining, reset = await check_correction_rate_limit(
            mock_redis, "127.0.0.1"
        )

        assert allowed is True
        assert remaining == 4  # 10 - 5 - 1
        assert reset == CORRECTION_RATE_WINDOW

    @pytest.mark.asyncio
    async def test_blocks_when_at_limit(self):
        """Test blocks request when at rate limit."""
        mock_redis, _ = self._make_mock_redis(current_count=10)

        allowed, remaining, reset = await check_correction_rate_limit(
            mock_redis, "127.0.0.1"
        )

        assert allowed is False
        assert remaining == 0

    @pytest.mark.asyncio
    async def test_allows_when_no_redis(self):
        """Test allows all requests when Redis is unavailable."""
        allowed, remaining, reset = await check_correction_rate_limit(
            None, "127.0.0.1"
        )

        assert allowed is True
        assert remaining == CORRECTION_RATE_LIMIT

    @pytest.mark.asyncio
    async def test_fails_open_on_redis_error(self):
        """Test fails open on Redis errors."""
        mock_redis = AsyncMock()
        mock_redis.pipeline.side_effect = Exception("Redis down")

        allowed, remaining, reset = await check_correction_rate_limit(
            mock_redis, "127.0.0.1"
        )

        assert allowed is True
        assert remaining == CORRECTION_RATE_LIMIT

    @pytest.mark.asyncio
    async def test_uses_correct_key_prefix(self):
        """Test uses correction-specific key prefix."""
        mock_redis, mock_pipe = self._make_mock_redis(current_count=0)

        await check_correction_rate_limit(mock_redis, "192.168.1.1")

        calls = mock_pipe.zremrangebyscore.call_args_list
        assert len(calls) == 1
        key_arg = calls[0][0][0]
        assert key_arg.startswith(CORRECTION_RATE_PREFIX)
        assert "192.168.1.1" in key_arg


class TestCorrectionSchemas:
    """Test Pydantic validation for correction schemas."""

    def test_correction_request_valid(self):
        """Test valid correction request."""
        req = CorrectionRequest(lookup_id=1, correct_hs_code_id=42, notes="test")
        assert req.lookup_id == 1
        assert req.correct_hs_code_id == 42
        assert req.notes == "test"

    def test_correction_request_without_notes(self):
        """Test correction request without optional notes."""
        req = CorrectionRequest(lookup_id=1, correct_hs_code_id=42)
        assert req.notes is None

    def test_correction_request_notes_max_length(self):
        """Test notes field enforces max_length of 200."""
        with pytest.raises(Exception):
            CorrectionRequest(
                lookup_id=1,
                correct_hs_code_id=42,
                notes="x" * 201,
            )

    def test_correction_request_notes_at_max_length(self):
        """Test notes field accepts exactly 200 chars."""
        req = CorrectionRequest(
            lookup_id=1,
            correct_hs_code_id=42,
            notes="x" * 200,
        )
        assert len(req.notes) == 200


class TestGetUnverifiedLookups:
    """Test GET /api/corrections/lookups endpoint."""

    @pytest.mark.asyncio
    @patch("app.api.corrections.LookupRecordRepository")
    async def test_returns_paginated_results(self, mock_repo_class):
        """Test endpoint returns paginated unverified records with HS code details."""
        from app.api.corrections import get_unverified_lookups

        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo

        mock_hs_code = MagicMock()
        mock_hs_code.code = "74182000"
        mock_hs_code.description_vn = "Bộ đồ bàn nhà bếp"
        mock_hs_code.description_en = "Kitchen table set"

        mock_record = MagicMock()
        mock_record.id = 1
        mock_record.query_text = "copper towel rack"
        mock_record.query_language = "en"
        mock_record.matched_hs_code_id = 42
        mock_record.matched_hs_code = mock_hs_code
        mock_record.confidence_score = 85.0
        mock_record.search_method = "vector"
        mock_record.created_at = datetime(2026, 2, 10, tzinfo=timezone.utc)

        mock_repo.get_unverified_with_hs_codes.return_value = [mock_record]
        mock_repo.count_unverified.return_value = 1

        mock_db = AsyncMock()
        result = await get_unverified_lookups(limit=20, offset=0, db=mock_db)

        assert result["success"] is True
        assert result["data"]["total"] == 1
        assert len(result["data"]["items"]) == 1
        assert result["data"]["items"][0]["id"] == 1
        assert result["data"]["items"][0]["matched_hs_code"] == "74182000"
        assert result["data"]["items"][0]["matched_description_vn"] == "Bộ đồ bàn nhà bếp"

    @pytest.mark.asyncio
    @patch("app.api.corrections.LookupRecordRepository")
    async def test_returns_empty_list(self, mock_repo_class):
        """Test endpoint returns empty list when no unverified records."""
        from app.api.corrections import get_unverified_lookups

        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_unverified_with_hs_codes.return_value = []
        mock_repo.count_unverified.return_value = 0

        mock_db = AsyncMock()
        result = await get_unverified_lookups(limit=20, offset=0, db=mock_db)

        assert result["success"] is True
        assert result["data"]["total"] == 0
        assert result["data"]["items"] == []

    @pytest.mark.asyncio
    @patch("app.api.corrections.LookupRecordRepository")
    async def test_handles_records_without_matched_hs_code(self, mock_repo_class):
        """Test endpoint handles records with no matched HS code."""
        from app.api.corrections import get_unverified_lookups

        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo

        mock_record = MagicMock()
        mock_record.id = 2
        mock_record.query_text = "unknown product"
        mock_record.query_language = "en"
        mock_record.matched_hs_code_id = None
        mock_record.matched_hs_code = None
        mock_record.confidence_score = None
        mock_record.search_method = "vector"
        mock_record.created_at = datetime(2026, 2, 10, tzinfo=timezone.utc)

        mock_repo.get_unverified_with_hs_codes.return_value = [mock_record]
        mock_repo.count_unverified.return_value = 1

        mock_db = AsyncMock()
        result = await get_unverified_lookups(limit=20, offset=0, db=mock_db)

        assert result["success"] is True
        item = result["data"]["items"][0]
        assert item["matched_hs_code"] is None
        assert item["matched_description_vn"] is None
        assert item["matched_description_en"] is None

    @pytest.mark.asyncio
    @patch("app.api.corrections.LookupRecordRepository")
    async def test_passes_pagination_params(self, mock_repo_class):
        """Test endpoint passes limit and offset to repository."""
        from app.api.corrections import get_unverified_lookups

        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_unverified_with_hs_codes.return_value = []
        mock_repo.count_unverified.return_value = 0

        mock_db = AsyncMock()
        result = await get_unverified_lookups(limit=5, offset=10, db=mock_db)

        mock_repo.get_unverified_with_hs_codes.assert_awaited_once_with(
            limit=5, offset=10
        )
        assert result["data"]["limit"] == 5
        assert result["data"]["offset"] == 10


class TestSubmitCorrection:
    """Test POST /api/corrections endpoint."""

    def _make_mock_request(self, client_ip: str = "127.0.0.1"):
        """Create mock FastAPI request."""
        mock_request = MagicMock()
        mock_request.client = MagicMock()
        mock_request.client.host = client_ip
        mock_request.headers = {}
        return mock_request

    def _make_mock_record(self, **kwargs):
        """Create mock LookupRecord."""
        defaults = {
            "id": 1,
            "query_text": "copper towel rack",
            "matched_hs_code_id": 42,
            "correct_hs_code_id": 55,
            "is_verified": True,
            "verified_at": datetime(2026, 2, 10, tzinfo=timezone.utc),
            "notes": "test note",
        }
        defaults.update(kwargs)
        mock_record = MagicMock()
        for key, value in defaults.items():
            setattr(mock_record, key, value)
        return mock_record

    @pytest.mark.asyncio
    @patch("app.api.corrections.check_correction_rate_limit")
    @patch("app.api.corrections.LookupRecordRepository")
    async def test_successful_correction(self, mock_repo_class, mock_rate_limit):
        """Test successful correction submission."""
        from app.api.corrections import submit_correction

        mock_rate_limit.return_value = (True, 9, 3600)

        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.find_by_id.return_value = self._make_mock_record()
        mock_repo.apply_correction.return_value = self._make_mock_record(
            correct_hs_code_id=55,
            is_verified=True,
            verified_at=datetime(2026, 2, 10, tzinfo=timezone.utc),
        )

        mock_db = AsyncMock()
        mock_hs_result = MagicMock()
        mock_hs_result.scalar_one_or_none.return_value = MagicMock()
        mock_db.execute.return_value = mock_hs_result

        mock_redis = AsyncMock()
        body = CorrectionRequest(lookup_id=1, correct_hs_code_id=55, notes="test")
        request = self._make_mock_request()

        result = await submit_correction(
            request=request, body=body, db=mock_db, redis_client=mock_redis
        )

        assert result["success"] is True
        assert result["data"]["id"] == 1
        assert result["data"]["correct_hs_code_id"] == 55
        assert result["data"]["is_verified"] is True

    @pytest.mark.asyncio
    @patch("app.api.corrections.check_correction_rate_limit")
    async def test_rate_limited(self, mock_rate_limit):
        """Test correction blocked by rate limit."""
        from app.api.corrections import submit_correction

        mock_rate_limit.return_value = (False, 0, 3600)

        body = CorrectionRequest(lookup_id=1, correct_hs_code_id=55)
        request = self._make_mock_request()
        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        result = await submit_correction(
            request=request, body=body, db=mock_db, redis_client=mock_redis
        )

        assert result["success"] is False
        assert result["error"]["status"] == 429
        assert "Rate limit" in result["error"]["detail"]

    @pytest.mark.asyncio
    @patch("app.api.corrections.check_correction_rate_limit")
    @patch("app.api.corrections.LookupRecordRepository")
    async def test_invalid_lookup_id(self, mock_repo_class, mock_rate_limit):
        """Test correction with invalid lookup_id returns 404."""
        from app.api.corrections import submit_correction

        mock_rate_limit.return_value = (True, 9, 3600)

        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.find_by_id.return_value = None

        body = CorrectionRequest(lookup_id=999, correct_hs_code_id=55)
        request = self._make_mock_request()
        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        result = await submit_correction(
            request=request, body=body, db=mock_db, redis_client=mock_redis
        )

        assert result["success"] is False
        assert result["error"]["status"] == 404

    @pytest.mark.asyncio
    @patch("app.api.corrections.check_correction_rate_limit")
    @patch("app.api.corrections.LookupRecordRepository")
    async def test_invalid_hs_code_id(self, mock_repo_class, mock_rate_limit):
        """Test correction with invalid hs_code_id returns 400."""
        from app.api.corrections import submit_correction

        mock_rate_limit.return_value = (True, 9, 3600)

        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.find_by_id.return_value = self._make_mock_record()

        mock_db = AsyncMock()
        mock_hs_result = MagicMock()
        mock_hs_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_hs_result

        body = CorrectionRequest(lookup_id=1, correct_hs_code_id=999)
        request = self._make_mock_request()
        mock_redis = AsyncMock()

        result = await submit_correction(
            request=request, body=body, db=mock_db, redis_client=mock_redis
        )

        assert result["success"] is False
        assert result["error"]["status"] == 400

    @pytest.mark.asyncio
    @patch("app.api.corrections.check_correction_rate_limit")
    @patch("app.api.corrections.LookupRecordRepository")
    async def test_no_auth_required(self, mock_repo_class, mock_rate_limit):
        """Test that no authentication is required (anonymous access)."""
        from app.api.corrections import submit_correction

        mock_rate_limit.return_value = (True, 9, 3600)

        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_record = self._make_mock_record()
        mock_repo.find_by_id.return_value = mock_record
        mock_repo.apply_correction.return_value = mock_record

        mock_db = AsyncMock()
        mock_hs_result = MagicMock()
        mock_hs_result.scalar_one_or_none.return_value = MagicMock()
        mock_db.execute.return_value = mock_hs_result

        # No auth headers set on request - should still succeed
        request = self._make_mock_request()
        body = CorrectionRequest(lookup_id=1, correct_hs_code_id=55)
        mock_redis = AsyncMock()

        result = await submit_correction(
            request=request, body=body, db=mock_db, redis_client=mock_redis
        )

        assert result["success"] is True

    @pytest.mark.asyncio
    @patch("app.api.corrections.check_correction_rate_limit")
    @patch("app.api.corrections.LookupRecordRepository")
    async def test_correction_with_notes(self, mock_repo_class, mock_rate_limit):
        """Test correction submission includes notes."""
        from app.api.corrections import submit_correction

        mock_rate_limit.return_value = (True, 9, 3600)

        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_record = self._make_mock_record(notes="Wrong category, should be copper")
        mock_repo.find_by_id.return_value = mock_record
        mock_repo.apply_correction.return_value = mock_record

        mock_db = AsyncMock()
        mock_hs_result = MagicMock()
        mock_hs_result.scalar_one_or_none.return_value = MagicMock()
        mock_db.execute.return_value = mock_hs_result

        body = CorrectionRequest(
            lookup_id=1,
            correct_hs_code_id=55,
            notes="Wrong category, should be copper",
        )
        request = self._make_mock_request()
        mock_redis = AsyncMock()

        result = await submit_correction(
            request=request, body=body, db=mock_db, redis_client=mock_redis
        )

        assert result["success"] is True
        assert result["data"]["notes"] == "Wrong category, should be copper"
        mock_repo.apply_correction.assert_awaited_once_with(
            record_id=1,
            correct_hs_code_id=55,
            notes="Wrong category, should be copper",
        )

    @pytest.mark.asyncio
    @patch("app.api.corrections.check_correction_rate_limit")
    @patch("app.api.corrections.LookupRecordRepository")
    async def test_rejects_duplicate_correction(self, mock_repo_class, mock_rate_limit):
        """Test correction rejected when correct_hs_code_id equals matched_hs_code_id."""
        from app.api.corrections import submit_correction

        mock_rate_limit.return_value = (True, 9, 3600)

        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        # Record with matched_hs_code_id = 42
        mock_record = self._make_mock_record(matched_hs_code_id=42)
        mock_repo.find_by_id.return_value = mock_record

        mock_db = AsyncMock()
        mock_hs_result = MagicMock()
        mock_hs_result.scalar_one_or_none.return_value = MagicMock()
        mock_db.execute.return_value = mock_hs_result

        # Try to "correct" to the same code (42)
        body = CorrectionRequest(lookup_id=1, correct_hs_code_id=42)
        request = self._make_mock_request()
        mock_redis = AsyncMock()

        result = await submit_correction(
            request=request, body=body, db=mock_db, redis_client=mock_redis
        )

        assert result["success"] is False
        assert result["error"]["status"] == 400
        assert "same as the current match" in result["error"]["detail"]
        # apply_correction should NOT be called
        mock_repo.apply_correction.assert_not_awaited()

    @pytest.mark.asyncio
    @patch("app.api.corrections.check_correction_rate_limit")
    @patch("app.api.corrections.LookupRecordRepository")
    async def test_rejects_already_corrected(self, mock_repo_class, mock_rate_limit):
        """Test correction rejected when record already has a verified correction."""
        from app.api.corrections import submit_correction

        mock_rate_limit.return_value = (True, 9, 3600)

        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        # Record already verified with correct_hs_code_id = 99
        mock_record = self._make_mock_record(
            matched_hs_code_id=42,
            correct_hs_code_id=99,
            is_verified=True,
        )
        mock_repo.find_by_id.return_value = mock_record

        mock_db = AsyncMock()
        mock_hs_result = MagicMock()
        mock_hs_result.scalar_one_or_none.return_value = MagicMock()
        mock_db.execute.return_value = mock_hs_result

        # Try to correct again
        body = CorrectionRequest(lookup_id=1, correct_hs_code_id=55)
        request = self._make_mock_request()
        mock_redis = AsyncMock()

        result = await submit_correction(
            request=request, body=body, db=mock_db, redis_client=mock_redis
        )

        assert result["success"] is False
        assert result["error"]["status"] == 409
        assert "already been corrected" in result["error"]["detail"]
        # apply_correction should NOT be called
        mock_repo.apply_correction.assert_not_awaited()


class TestCorrectionKBIntegration:
    """Test 8.6: Corrected records appear in KB search via KnowledgeBaseService."""

    @pytest.mark.asyncio
    async def test_correction_makes_record_findable_by_exact_hash(self):
        """After apply_correction, KnowledgeBaseService.lookup finds it via exact hash."""
        mock_session = AsyncMock()

        # Simulate a verified record that would be returned by find_verified_exact
        mock_verified_record = MagicMock()
        mock_verified_record.id = 1
        mock_verified_record.correct_hs_code_id = 55
        mock_verified_record.verified_by_user_id = None
        mock_verified_record.verified_at = datetime(2026, 2, 10, tzinfo=timezone.utc)
        mock_verified_record.is_verified = True

        with patch.object(
            KnowledgeBaseService, "__init__", lambda self, session: setattr(self, "repo", AsyncMock())
        ):
            kb = KnowledgeBaseService(mock_session)
            kb.repo.find_verified_exact.return_value = mock_verified_record
            kb.repo.find_verified_similar.return_value = []

            result = await kb.lookup("copper towel rack")

        assert result is not None
        assert result.hs_code_id == 55
        assert result.match_type == "exact"
        assert result.confidence == 100

    @pytest.mark.asyncio
    async def test_correction_makes_record_findable_by_similar_text(self):
        """After apply_correction, KnowledgeBaseService.lookup finds it via pg_trgm."""
        mock_session = AsyncMock()

        mock_verified_record = MagicMock()
        mock_verified_record.id = 2
        mock_verified_record.correct_hs_code_id = 55
        mock_verified_record.verified_by_user_id = None
        mock_verified_record.verified_at = datetime(2026, 2, 10, tzinfo=timezone.utc)

        with patch.object(
            KnowledgeBaseService, "__init__", lambda self, session: setattr(self, "repo", AsyncMock())
        ):
            kb = KnowledgeBaseService(mock_session)
            kb.repo.find_verified_exact.return_value = None
            kb.repo.find_verified_similar.return_value = [(mock_verified_record, 0.92)]

            result = await kb.lookup("copper towel holder")

        assert result is not None
        assert result.hs_code_id == 55
        assert result.match_type == "similar"
        assert result.confidence == 92

    @pytest.mark.asyncio
    async def test_correction_auto_verifies_for_kb_visibility(self):
        """Correction sets is_verified=True so KB queries find it."""
        from app.api.corrections import submit_correction

        mock_rate_limit_return = (True, 9, 3600)

        # Create a mock record that simulates apply_correction output
        updated = MagicMock()
        updated.id = 1
        updated.query_text = "copper towel rack"
        updated.matched_hs_code_id = 42
        updated.correct_hs_code_id = 55
        updated.is_verified = True
        updated.verified_at = datetime(2026, 2, 10, tzinfo=timezone.utc)
        updated.notes = None

        mock_repo = AsyncMock()
        mock_repo.find_by_id.return_value = MagicMock()
        mock_repo.apply_correction.return_value = updated

        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {}

        mock_db = AsyncMock()
        mock_hs_result = MagicMock()
        mock_hs_result.scalar_one_or_none.return_value = MagicMock()
        mock_db.execute.return_value = mock_hs_result

        body = CorrectionRequest(lookup_id=1, correct_hs_code_id=55)

        with patch("app.api.corrections.check_correction_rate_limit", return_value=mock_rate_limit_return), \
             patch("app.api.corrections.LookupRecordRepository", return_value=mock_repo):
            result = await submit_correction(
                request=mock_request,
                body=body,
                db=mock_db,
                redis_client=AsyncMock(),
            )

        assert result["success"] is True
        assert result["data"]["is_verified"] is True
        assert result["data"]["verified_at"] is not None
        assert result["data"]["correct_hs_code_id"] == 55

        # Verify apply_correction was called (which sets is_verified=True)
        mock_repo.apply_correction.assert_awaited_once_with(
            record_id=1, correct_hs_code_id=55, notes=None
        )
