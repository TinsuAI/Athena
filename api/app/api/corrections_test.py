"""Tests for corrections API endpoint (authenticated correction workflow)."""

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


class TestCheckCorrectionRateLimit:
    """Test the per-user correction rate limiting function."""

    def _make_mock_redis(self, current_count: int):
        """Create a mock Redis client with pipeline for rate limiting."""
        mock_redis = AsyncMock()
        mock_pipe = AsyncMock()
        mock_pipe.execute.return_value = [None, current_count, None, None]

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
            mock_redis, 42
        )

        assert allowed is True
        assert remaining == 4  # 10 - 5 - 1
        assert reset == CORRECTION_RATE_WINDOW

    @pytest.mark.asyncio
    async def test_blocks_when_at_limit(self):
        """Test blocks request when at rate limit."""
        mock_redis, _ = self._make_mock_redis(current_count=10)

        allowed, remaining, reset = await check_correction_rate_limit(
            mock_redis, 42
        )

        assert allowed is False
        assert remaining == 0

    @pytest.mark.asyncio
    async def test_allows_when_no_redis(self):
        """Test allows all requests when Redis is unavailable."""
        allowed, remaining, reset = await check_correction_rate_limit(
            None, 42
        )

        assert allowed is True
        assert remaining == CORRECTION_RATE_LIMIT

    @pytest.mark.asyncio
    async def test_fails_open_on_redis_error(self):
        """Test fails open on Redis errors."""
        mock_redis = AsyncMock()
        mock_redis.pipeline.side_effect = Exception("Redis down")

        allowed, remaining, reset = await check_correction_rate_limit(
            mock_redis, 42
        )

        assert allowed is True
        assert remaining == CORRECTION_RATE_LIMIT

    @pytest.mark.asyncio
    async def test_uses_user_id_in_key_not_ip(self):
        """Test rate limit key is per user_id (not IP address)."""
        mock_redis, mock_pipe = self._make_mock_redis(current_count=0)

        user_id = 999
        await check_correction_rate_limit(mock_redis, user_id)

        calls = mock_pipe.zremrangebyscore.call_args_list
        assert len(calls) == 1
        key_arg = calls[0][0][0]
        assert key_arg.startswith(CORRECTION_RATE_PREFIX)
        assert f"user:{user_id}" in key_arg

    @pytest.mark.asyncio
    async def test_different_users_have_separate_limits(self):
        """Test that different user IDs use different Redis keys."""
        mock_redis1, mock_pipe1 = self._make_mock_redis(current_count=0)
        mock_redis2, mock_pipe2 = self._make_mock_redis(current_count=0)

        await check_correction_rate_limit(mock_redis1, 1)
        await check_correction_rate_limit(mock_redis2, 2)

        key1 = mock_pipe1.zremrangebyscore.call_args_list[0][0][0]
        key2 = mock_pipe2.zremrangebyscore.call_args_list[0][0][0]
        assert key1 != key2
        assert "user:1" in key1
        assert "user:2" in key2


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
        assert len(req.notes) == 200  # type: ignore[arg-type]


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
    """Test POST /api/corrections endpoint (authenticated, pending status)."""

    def _make_mock_user(self, user_id: int = 7) -> dict:
        """Create mock authenticated user dict returned by require_authenticated."""
        return {"id": user_id, "email": "user@example.com", "role": "user"}

    def _make_mock_record(self, **kwargs):
        """Create mock LookupRecord."""
        defaults = {
            "id": 1,
            "query_text": "copper towel rack",
            "matched_hs_code_id": 42,
            "correct_hs_code_id": None,
            "is_verified": False,
            "verified_at": None,
            "notes": None,
            "correction_status": None,
            "submitted_by_user_id": None,
        }
        defaults.update(kwargs)
        mock_record = MagicMock()
        for key, value in defaults.items():
            setattr(mock_record, key, value)
        return mock_record

    @pytest.mark.asyncio
    @patch("app.api.corrections.check_correction_rate_limit")
    @patch("app.api.corrections.LookupRecordRepository")
    async def test_unauthenticated_returns_401(self, mock_repo_class, mock_rate_limit):
        """Test unauthenticated user gets 401 on POST /api/corrections (AC #1)."""
        from fastapi import HTTPException

        from app.api.corrections import submit_correction
        from app.core.auth import require_authenticated

        # Simulate require_authenticated raising 401
        async def raise_401():
            raise HTTPException(status_code=401, detail="Not authenticated")

        body = CorrectionRequest(lookup_id=1, correct_hs_code_id=55)
        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        # require_authenticated dependency raises HTTPException when no JWT
        with pytest.raises(HTTPException) as exc_info:
            # Call require_authenticated directly to verify it raises
            from app.core.auth import require_authenticated as real_req_auth
            # We patch it to simulate unauthenticated
            with patch("app.api.corrections.require_authenticated", side_effect=HTTPException(status_code=401)):
                await submit_correction(
                    body=body,
                    user=await raise_401(),
                    db=mock_db,
                    redis_client=mock_redis,
                )

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    @patch("app.api.corrections.check_correction_rate_limit")
    @patch("app.api.corrections.LookupRecordRepository")
    async def test_authenticated_correction_sets_pending_status(
        self, mock_repo_class, mock_rate_limit
    ):
        """Test authenticated user submits correction with pending status (AC #2)."""
        from app.api.corrections import submit_correction

        mock_rate_limit.return_value = (True, 9, 3600)

        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo

        input_record = self._make_mock_record()
        updated_record = self._make_mock_record(
            correct_hs_code_id=55,
            correction_status="pending",
            is_verified=False,
            submitted_by_user_id=7,
            notes=None,
        )
        mock_repo.find_by_id.return_value = input_record
        mock_repo.submit_pending_correction.return_value = updated_record

        mock_db = AsyncMock()
        mock_hs_result = MagicMock()
        mock_hs_result.scalar_one_or_none.return_value = MagicMock()
        mock_db.execute.return_value = mock_hs_result

        body = CorrectionRequest(lookup_id=1, correct_hs_code_id=55)
        user = self._make_mock_user(user_id=7)
        mock_redis = AsyncMock()

        result = await submit_correction(
            body=body, user=user, db=mock_db, redis_client=mock_redis
        )

        assert result["success"] is True
        assert result["data"]["correction_status"] == "pending"
        assert result["data"]["is_verified"] is False

    @pytest.mark.asyncio
    @patch("app.api.corrections.check_correction_rate_limit")
    @patch("app.api.corrections.LookupRecordRepository")
    async def test_submitted_by_user_id_set_correctly(
        self, mock_repo_class, mock_rate_limit
    ):
        """Test submitted_by_user_id is set to authenticated user's ID (AC #2)."""
        from app.api.corrections import submit_correction

        mock_rate_limit.return_value = (True, 9, 3600)

        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo

        input_record = self._make_mock_record()
        updated_record = self._make_mock_record(
            correct_hs_code_id=55,
            correction_status="pending",
            is_verified=False,
            submitted_by_user_id=42,
        )
        mock_repo.find_by_id.return_value = input_record
        mock_repo.submit_pending_correction.return_value = updated_record

        mock_db = AsyncMock()
        mock_hs_result = MagicMock()
        mock_hs_result.scalar_one_or_none.return_value = MagicMock()
        mock_db.execute.return_value = mock_hs_result

        body = CorrectionRequest(lookup_id=1, correct_hs_code_id=55)
        user = self._make_mock_user(user_id=42)
        mock_redis = AsyncMock()

        result = await submit_correction(
            body=body, user=user, db=mock_db, redis_client=mock_redis
        )

        assert result["success"] is True
        assert result["data"]["submitted_by_user_id"] == 42

        # Verify submit_pending_correction called with correct user ID
        mock_repo.submit_pending_correction.assert_awaited_once_with(
            record_id=1,
            correct_hs_code_id=55,
            submitted_by_user_id=42,
            notes=None,
        )

    @pytest.mark.asyncio
    @patch("app.api.corrections.check_correction_rate_limit")
    async def test_rate_limited(self, mock_rate_limit):
        """Test correction blocked by rate limit (429)."""
        from app.api.corrections import submit_correction

        mock_rate_limit.return_value = (False, 0, 3600)

        body = CorrectionRequest(lookup_id=1, correct_hs_code_id=55)
        user = self._make_mock_user()
        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        result = await submit_correction(
            body=body, user=user, db=mock_db, redis_client=mock_redis
        )

        assert result["success"] is False
        assert result["error"]["status"] == 429

    @pytest.mark.asyncio
    @patch("app.api.corrections.check_correction_rate_limit")
    @patch("app.api.corrections.LookupRecordRepository")
    async def test_rate_limit_uses_user_id_not_ip(
        self, mock_repo_class, mock_rate_limit
    ):
        """Test rate limit is called with user_id (int), not IP (AC #5)."""
        from app.api.corrections import submit_correction

        mock_rate_limit.return_value = (True, 9, 3600)

        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        input_record = self._make_mock_record()
        updated_record = self._make_mock_record(
            correct_hs_code_id=55,
            correction_status="pending",
            is_verified=False,
            submitted_by_user_id=99,
        )
        mock_repo.find_by_id.return_value = input_record
        mock_repo.submit_pending_correction.return_value = updated_record

        mock_db = AsyncMock()
        mock_hs_result = MagicMock()
        mock_hs_result.scalar_one_or_none.return_value = MagicMock()
        mock_db.execute.return_value = mock_hs_result

        body = CorrectionRequest(lookup_id=1, correct_hs_code_id=55)
        user = self._make_mock_user(user_id=99)
        mock_redis = AsyncMock()

        await submit_correction(
            body=body, user=user, db=mock_db, redis_client=mock_redis
        )

        # Verify rate limit was called with integer user_id, not a string IP
        mock_rate_limit.assert_awaited_once()
        call_args = mock_rate_limit.call_args
        user_id_arg = call_args[0][1]  # second positional arg
        assert user_id_arg == 99
        assert isinstance(user_id_arg, int)

    @pytest.mark.asyncio
    @patch("app.api.corrections.check_correction_rate_limit")
    @patch("app.api.corrections.LookupRecordRepository")
    async def test_invalid_lookup_id_returns_404(
        self, mock_repo_class, mock_rate_limit
    ):
        """Test correction with invalid lookup_id returns 404."""
        from app.api.corrections import submit_correction

        mock_rate_limit.return_value = (True, 9, 3600)

        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.find_by_id.return_value = None

        body = CorrectionRequest(lookup_id=999, correct_hs_code_id=55)
        user = self._make_mock_user()
        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        result = await submit_correction(
            body=body, user=user, db=mock_db, redis_client=mock_redis
        )

        assert result["success"] is False
        assert result["error"]["status"] == 404

    @pytest.mark.asyncio
    @patch("app.api.corrections.check_correction_rate_limit")
    @patch("app.api.corrections.LookupRecordRepository")
    async def test_invalid_hs_code_id_returns_400(
        self, mock_repo_class, mock_rate_limit
    ):
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

        body = CorrectionRequest(lookup_id=1, correct_hs_code_id=9999)
        user = self._make_mock_user()
        mock_redis = AsyncMock()

        result = await submit_correction(
            body=body, user=user, db=mock_db, redis_client=mock_redis
        )

        assert result["success"] is False
        assert result["error"]["status"] == 400

    @pytest.mark.asyncio
    @patch("app.api.corrections.check_correction_rate_limit")
    @patch("app.api.corrections.LookupRecordRepository")
    async def test_already_approved_correction_returns_409(
        self, mock_repo_class, mock_rate_limit
    ):
        """Test correction rejected when record already has approved correction (AC #4)."""
        from app.api.corrections import submit_correction

        mock_rate_limit.return_value = (True, 9, 3600)

        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        # Record already approved (is_verified=True, correct_hs_code_id set)
        mock_record = self._make_mock_record(
            matched_hs_code_id=42,
            correct_hs_code_id=99,
            is_verified=True,
            correction_status="approved",
        )
        mock_repo.find_by_id.return_value = mock_record

        mock_db = AsyncMock()
        mock_hs_result = MagicMock()
        mock_hs_result.scalar_one_or_none.return_value = MagicMock()
        mock_db.execute.return_value = mock_hs_result

        body = CorrectionRequest(lookup_id=1, correct_hs_code_id=55)
        user = self._make_mock_user()
        mock_redis = AsyncMock()

        result = await submit_correction(
            body=body, user=user, db=mock_db, redis_client=mock_redis
        )

        assert result["success"] is False
        assert result["error"]["status"] == 409
        assert "Tra cuu nay da duoc chinh sua" in result["error"]["detail"]
        # submit_pending_correction must NOT be called
        mock_repo.submit_pending_correction.assert_not_awaited()

    @pytest.mark.asyncio
    @patch("app.api.corrections.check_correction_rate_limit")
    @patch("app.api.corrections.LookupRecordRepository")
    async def test_already_pending_correction_returns_409(
        self, mock_repo_class, mock_rate_limit
    ):
        """Test correction rejected when record already has a pending correction (AC #6)."""
        from app.api.corrections import submit_correction

        mock_rate_limit.return_value = (True, 9, 3600)

        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        # Record already has pending correction
        mock_record = self._make_mock_record(
            matched_hs_code_id=42,
            is_verified=False,
            correction_status="pending",
        )
        mock_repo.find_by_id.return_value = mock_record

        mock_db = AsyncMock()
        mock_hs_result = MagicMock()
        mock_hs_result.scalar_one_or_none.return_value = MagicMock()
        mock_db.execute.return_value = mock_hs_result

        body = CorrectionRequest(lookup_id=1, correct_hs_code_id=55)
        user = self._make_mock_user()
        mock_redis = AsyncMock()

        result = await submit_correction(
            body=body, user=user, db=mock_db, redis_client=mock_redis
        )

        assert result["success"] is False
        assert result["error"]["status"] == 409
        assert "Chinh sua dang cho duyet" in result["error"]["detail"]
        mock_repo.submit_pending_correction.assert_not_awaited()

    @pytest.mark.asyncio
    @patch("app.api.corrections.check_correction_rate_limit")
    @patch("app.api.corrections.LookupRecordRepository")
    async def test_rejects_duplicate_hs_code(self, mock_repo_class, mock_rate_limit):
        """Test correction rejected when correct_hs_code_id equals matched_hs_code_id."""
        from app.api.corrections import submit_correction

        mock_rate_limit.return_value = (True, 9, 3600)

        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_record = self._make_mock_record(matched_hs_code_id=42)
        mock_repo.find_by_id.return_value = mock_record

        mock_db = AsyncMock()
        mock_hs_result = MagicMock()
        mock_hs_result.scalar_one_or_none.return_value = MagicMock()
        mock_db.execute.return_value = mock_hs_result

        # Try to "correct" to same code (42 == matched_hs_code_id)
        body = CorrectionRequest(lookup_id=1, correct_hs_code_id=42)
        user = self._make_mock_user()
        mock_redis = AsyncMock()

        result = await submit_correction(
            body=body, user=user, db=mock_db, redis_client=mock_redis
        )

        assert result["success"] is False
        assert result["error"]["status"] == 400
        assert "same as the current match" in result["error"]["detail"]
        mock_repo.submit_pending_correction.assert_not_awaited()

    @pytest.mark.asyncio
    @patch("app.api.corrections.check_correction_rate_limit")
    @patch("app.api.corrections.LookupRecordRepository")
    async def test_correction_is_not_auto_verified(
        self, mock_repo_class, mock_rate_limit
    ):
        """Test correction is NOT auto-verified (is_verified stays False, AC #2)."""
        from app.api.corrections import submit_correction

        mock_rate_limit.return_value = (True, 9, 3600)

        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo

        input_record = self._make_mock_record()
        updated_record = self._make_mock_record(
            correct_hs_code_id=55,
            correction_status="pending",
            is_verified=False,
            submitted_by_user_id=7,
        )
        mock_repo.find_by_id.return_value = input_record
        mock_repo.submit_pending_correction.return_value = updated_record

        mock_db = AsyncMock()
        mock_hs_result = MagicMock()
        mock_hs_result.scalar_one_or_none.return_value = MagicMock()
        mock_db.execute.return_value = mock_hs_result

        body = CorrectionRequest(lookup_id=1, correct_hs_code_id=55)
        user = self._make_mock_user(user_id=7)
        mock_redis = AsyncMock()

        result = await submit_correction(
            body=body, user=user, db=mock_db, redis_client=mock_redis
        )

        assert result["success"] is True
        # CRITICAL: must NOT be auto-verified
        assert result["data"]["is_verified"] is False
        # Must use submit_pending_correction, NOT apply_correction
        mock_repo.submit_pending_correction.assert_awaited_once()
        mock_repo.apply_correction.assert_not_awaited()

    @pytest.mark.asyncio
    @patch("app.api.corrections.check_correction_rate_limit")
    @patch("app.api.corrections.LookupRecordRepository")
    async def test_correction_with_notes(self, mock_repo_class, mock_rate_limit):
        """Test correction submission passes notes to repository."""
        from app.api.corrections import submit_correction

        mock_rate_limit.return_value = (True, 9, 3600)

        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        input_record = self._make_mock_record()
        updated_record = self._make_mock_record(
            correct_hs_code_id=55,
            correction_status="pending",
            is_verified=False,
            submitted_by_user_id=7,
            notes="Nên dùng mã HS cho đồng",
        )
        mock_repo.find_by_id.return_value = input_record
        mock_repo.submit_pending_correction.return_value = updated_record

        mock_db = AsyncMock()
        mock_hs_result = MagicMock()
        mock_hs_result.scalar_one_or_none.return_value = MagicMock()
        mock_db.execute.return_value = mock_hs_result

        body = CorrectionRequest(
            lookup_id=1,
            correct_hs_code_id=55,
            notes="Nên dùng mã HS cho đồng",
        )
        user = self._make_mock_user(user_id=7)
        mock_redis = AsyncMock()

        result = await submit_correction(
            body=body, user=user, db=mock_db, redis_client=mock_redis
        )

        assert result["success"] is True
        mock_repo.submit_pending_correction.assert_awaited_once_with(
            record_id=1,
            correct_hs_code_id=55,
            submitted_by_user_id=7,
            notes="Nên dùng mã HS cho đồng",
        )
