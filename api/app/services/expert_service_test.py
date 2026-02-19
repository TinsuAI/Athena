"""Tests for expert service business logic."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.models.lookup_record import LookupRecord
from app.services.expert_service import ExpertService


class TestExpertService:
    """Test cases for ExpertService."""

    def _make_record(self, **kwargs) -> LookupRecord:
        """Create a LookupRecord with default values for testing."""
        defaults = {
            "id": 1,
            "query_text": "copper towel rack",
            "query_hash": "abc123",
            "search_method": "vector",
            "is_verified": False,
            "confidence_score": 85.0,
            "correction_status": "pending",
            "correct_hs_code_id": 55,
            "submitted_by_user_id": 42,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        defaults.update(kwargs)
        record = LookupRecord()
        for key, value in defaults.items():
            setattr(record, key, value)
        return record

    @pytest.mark.asyncio
    @patch("app.services.expert_service.AuditLogRepository")
    @patch("app.services.expert_service.LookupRecordRepository")
    async def test_approve_correction_calls_repo_and_audit(
        self, mock_lookup_repo_cls, mock_audit_repo_cls
    ):
        """Test approve_correction calls repository approve and creates audit log."""
        mock_session = AsyncMock()
        mock_lookup_repo = mock_lookup_repo_cls.return_value
        mock_audit_repo = mock_audit_repo_cls.return_value

        pending_record = self._make_record(correction_status="pending")
        approved_record = self._make_record(
            correction_status="approved",
            is_verified=True,
            verified_by_user_id=10,
        )

        mock_lookup_repo.find_by_id = AsyncMock(return_value=pending_record)
        mock_lookup_repo.approve_correction = AsyncMock(return_value=approved_record)
        mock_audit_repo.create = AsyncMock()

        service = ExpertService(mock_session)
        result = await service.approve_correction(record_id=1, expert_user_id=10)

        assert result is approved_record
        mock_lookup_repo.find_by_id.assert_awaited_once_with(1)
        mock_lookup_repo.approve_correction.assert_awaited_once_with(1, 10)
        mock_audit_repo.create.assert_awaited_once()

        # Verify audit log details
        audit_call = mock_audit_repo.create.call_args
        assert audit_call.kwargs["admin_user_id"] == 10
        assert audit_call.kwargs["action"] == "correction_approved"
        assert audit_call.kwargs["details"]["lookup_record_id"] == 1

    @pytest.mark.asyncio
    @patch("app.services.expert_service.AuditLogRepository")
    @patch("app.services.expert_service.LookupRecordRepository")
    async def test_reject_correction_calls_repo_and_audit(
        self, mock_lookup_repo_cls, mock_audit_repo_cls
    ):
        """Test reject_correction calls repository reject and creates audit log."""
        mock_session = AsyncMock()
        mock_lookup_repo = mock_lookup_repo_cls.return_value
        mock_audit_repo = mock_audit_repo_cls.return_value

        pending_record = self._make_record(correction_status="pending")
        rejected_record = self._make_record(
            correction_status="rejected",
            rejection_reason="Ma HS khong phu hop",
        )

        mock_lookup_repo.find_by_id = AsyncMock(return_value=pending_record)
        mock_lookup_repo.reject_correction = AsyncMock(return_value=rejected_record)
        mock_audit_repo.create = AsyncMock()

        service = ExpertService(mock_session)
        result = await service.reject_correction(
            record_id=1, expert_user_id=10, reason="Ma HS khong phu hop"
        )

        assert result is rejected_record
        mock_lookup_repo.find_by_id.assert_awaited_once_with(1)
        mock_lookup_repo.reject_correction.assert_awaited_once_with(
            1, "Ma HS khong phu hop"
        )
        mock_audit_repo.create.assert_awaited_once()

        audit_call = mock_audit_repo.create.call_args
        assert audit_call.kwargs["admin_user_id"] == 10
        assert audit_call.kwargs["action"] == "correction_rejected"
        assert audit_call.kwargs["details"]["reason"] == "Ma HS khong phu hop"

    @pytest.mark.asyncio
    @patch("app.services.expert_service.AuditLogRepository")
    @patch("app.services.expert_service.LookupRecordRepository")
    async def test_approve_non_pending_raises_error(
        self, mock_lookup_repo_cls, mock_audit_repo_cls
    ):
        """Test approve_correction raises ValueError for non-pending correction."""
        mock_session = AsyncMock()
        mock_lookup_repo = mock_lookup_repo_cls.return_value

        approved_record = self._make_record(correction_status="approved")
        mock_lookup_repo.find_by_id = AsyncMock(return_value=approved_record)

        service = ExpertService(mock_session)
        with pytest.raises(ValueError, match="Only pending corrections can be approved"):
            await service.approve_correction(record_id=1, expert_user_id=10)

    @pytest.mark.asyncio
    @patch("app.services.expert_service.AuditLogRepository")
    @patch("app.services.expert_service.LookupRecordRepository")
    async def test_reject_non_pending_raises_error(
        self, mock_lookup_repo_cls, mock_audit_repo_cls
    ):
        """Test reject_correction raises ValueError for non-pending correction."""
        mock_session = AsyncMock()
        mock_lookup_repo = mock_lookup_repo_cls.return_value

        approved_record = self._make_record(correction_status="approved")
        mock_lookup_repo.find_by_id = AsyncMock(return_value=approved_record)

        service = ExpertService(mock_session)
        with pytest.raises(ValueError, match="Only pending corrections can be rejected"):
            await service.reject_correction(
                record_id=1, expert_user_id=10, reason="test"
            )

    @pytest.mark.asyncio
    @patch("app.services.expert_service.AuditLogRepository")
    @patch("app.services.expert_service.LookupRecordRepository")
    async def test_approve_nonexistent_raises_error(
        self, mock_lookup_repo_cls, mock_audit_repo_cls
    ):
        """Test approve_correction raises ValueError for non-existent record."""
        mock_session = AsyncMock()
        mock_lookup_repo = mock_lookup_repo_cls.return_value

        mock_lookup_repo.find_by_id = AsyncMock(return_value=None)

        service = ExpertService(mock_session)
        with pytest.raises(ValueError, match="Record not found"):
            await service.approve_correction(record_id=999, expert_user_id=10)
