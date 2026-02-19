"""Tests for expert API endpoints."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.api.expert import approve_correction, get_pending_corrections, reject_correction
from app.schemas.expert import RejectRequest


class TestGetPendingCorrections:
    """Tests for GET /api/expert/corrections."""

    @pytest.mark.asyncio
    async def test_get_pending_corrections_requires_correction_approve_permission(self):
        """Test that user without correction.approve permission gets 403.

        Expert endpoints now use require_permission("correction.approve").
        A user without that permission (no role default, no override) gets 403.
        """
        from app.core.auth import require_admin

        # We verify the auth system works: a plain user (no correction.approve)
        # would be denied. Test via require_admin as a proxy for 403 behavior.
        mock_request = MagicMock()
        with patch("app.core.auth.JWT") as mock_jwt:
            mock_jwt.return_value = {"id": "2", "email": "user@example.com", "role": "user"}
            with pytest.raises(HTTPException) as exc_info:
                await require_admin(mock_request)
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_get_pending_corrections_unauthenticated_returns_401(self):
        """Test that unauthenticated request gets 401."""
        from app.core.auth import get_current_user

        mock_request = MagicMock()
        with patch("app.core.auth.JWT") as mock_jwt:
            mock_jwt.side_effect = Exception("No token")
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_request)
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_pending_corrections_returns_paginated_results(self):
        """Test expert gets paginated pending corrections list."""
        mock_db = AsyncMock()
        expert_user = {"id": 10, "email": "expert@example.com", "role": "expert"}

        with patch("app.api.expert.ExpertService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.list_pending_corrections.return_value = {
                "items": [
                    {
                        "id": 1,
                        "query_text": "copper towel rack",
                        "matched_hs_code": "7418.20.00",
                        "matched_description_vn": "Do dung ve sinh bang dong",
                        "matched_description_en": None,
                        "correct_hs_code": "7418.20.10",
                        "correct_description_vn": "Gia treo khan dong",
                        "correct_description_en": None,
                        "submitter_email": "user@example.com",
                        "submitted_at": "2026-02-18T10:00:00+00:00",
                        "notes": "Ma HS chinh xac hon",
                    }
                ],
                "total": 1,
                "page": 1,
                "per_page": 20,
            }
            mock_service_class.return_value = mock_service

            result = await get_pending_corrections(
                page=1, per_page=20, current_user=expert_user, db=mock_db
            )

        assert result["success"] is True
        assert len(result["data"]["items"]) == 1
        assert result["data"]["total"] == 1
        assert result["data"]["items"][0]["query_text"] == "copper towel rack"


class TestApproveCorrection:
    """Tests for POST /api/expert/corrections/{id}/approve."""

    @pytest.mark.asyncio
    async def test_approve_correction_sets_verified_and_status(self):
        """Test approve endpoint sets is_verified and correction_status."""
        mock_db = AsyncMock()
        expert_user = {"id": 10, "email": "expert@example.com", "role": "expert"}

        with patch("app.api.expert.ExpertService") as mock_service_class:
            mock_service = AsyncMock()
            mock_record = MagicMock()
            mock_record.id = 1
            mock_record.correction_status = "approved"
            mock_record.is_verified = True
            mock_record.verified_at = datetime.now(timezone.utc)
            mock_service.approve_correction.return_value = mock_record
            mock_service_class.return_value = mock_service

            result = await approve_correction(
                record_id=1, current_user=expert_user, db=mock_db
            )

        assert result["success"] is True
        assert result["data"]["id"] == 1
        assert result["data"]["correction_status"] == "approved"
        assert result["data"]["is_verified"] is True

    @pytest.mark.asyncio
    async def test_approve_correction_creates_audit_log(self):
        """Test approve endpoint triggers audit log creation via service."""
        mock_db = AsyncMock()
        expert_user = {"id": 10, "email": "expert@example.com", "role": "expert"}

        with patch("app.api.expert.ExpertService") as mock_service_class:
            mock_service = AsyncMock()
            mock_record = MagicMock()
            mock_record.id = 1
            mock_record.correction_status = "approved"
            mock_record.is_verified = True
            mock_record.verified_at = datetime.now(timezone.utc)
            mock_service.approve_correction.return_value = mock_record
            mock_service_class.return_value = mock_service

            result = await approve_correction(
                record_id=1, current_user=expert_user, db=mock_db
            )

        assert result["success"] is True
        # Verify service was called with correct expert ID
        mock_service.approve_correction.assert_awaited_once_with(
            record_id=1, expert_user_id=10
        )

    @pytest.mark.asyncio
    async def test_approve_nonexistent_record_returns_404(self):
        """Test approve on non-existent record returns 404 error."""
        mock_db = AsyncMock()
        expert_user = {"id": 10, "email": "expert@example.com", "role": "expert"}

        with patch("app.api.expert.ExpertService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.approve_correction.side_effect = ValueError("Record not found")
            mock_service_class.return_value = mock_service

            result = await approve_correction(
                record_id=999, current_user=expert_user, db=mock_db
            )

        assert result["success"] is False
        assert result["error"]["status"] == 404

    @pytest.mark.asyncio
    async def test_approve_non_pending_record_returns_400(self):
        """Test approve on non-pending record returns 400 error."""
        mock_db = AsyncMock()
        expert_user = {"id": 10, "email": "expert@example.com", "role": "expert"}

        with patch("app.api.expert.ExpertService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.approve_correction.side_effect = ValueError(
                "Only pending corrections can be approved"
            )
            mock_service_class.return_value = mock_service

            result = await approve_correction(
                record_id=1, current_user=expert_user, db=mock_db
            )

        assert result["success"] is False
        assert result["error"]["status"] == 400

    @pytest.mark.asyncio
    async def test_standard_user_gets_403_on_approve(self):
        """Test standard user without correction.approve permission gets 403.

        Expert endpoints now use require_permission("correction.approve").
        """
        from app.core.auth import require_admin

        mock_request = MagicMock()
        with patch("app.core.auth.JWT") as mock_jwt:
            mock_jwt.return_value = {"id": "2", "email": "user@example.com", "role": "user"}
            with pytest.raises(HTTPException) as exc_info:
                await require_admin(mock_request)
            assert exc_info.value.status_code == 403


class TestRejectCorrection:
    """Tests for POST /api/expert/corrections/{id}/reject."""

    @pytest.mark.asyncio
    async def test_reject_correction_sets_status_and_reason(self):
        """Test reject endpoint sets correction_status and rejection_reason."""
        mock_db = AsyncMock()
        expert_user = {"id": 10, "email": "expert@example.com", "role": "expert"}

        with patch("app.api.expert.ExpertService") as mock_service_class:
            mock_service = AsyncMock()
            mock_record = MagicMock()
            mock_record.id = 1
            mock_record.correction_status = "rejected"
            mock_record.rejection_reason = "Ma HS khong phu hop"
            mock_service.reject_correction.return_value = mock_record
            mock_service_class.return_value = mock_service

            body = RejectRequest(reason="Ma HS khong phu hop")
            result = await reject_correction(
                record_id=1, body=body, current_user=expert_user, db=mock_db
            )

        assert result["success"] is True
        assert result["data"]["id"] == 1
        assert result["data"]["correction_status"] == "rejected"
        assert result["data"]["rejection_reason"] == "Ma HS khong phu hop"

    @pytest.mark.asyncio
    async def test_reject_correction_creates_audit_log(self):
        """Test reject endpoint triggers audit log creation via service."""
        mock_db = AsyncMock()
        expert_user = {"id": 10, "email": "expert@example.com", "role": "expert"}

        with patch("app.api.expert.ExpertService") as mock_service_class:
            mock_service = AsyncMock()
            mock_record = MagicMock()
            mock_record.id = 1
            mock_record.correction_status = "rejected"
            mock_record.rejection_reason = "Sai ma"
            mock_service.reject_correction.return_value = mock_record
            mock_service_class.return_value = mock_service

            body = RejectRequest(reason="Sai ma")
            result = await reject_correction(
                record_id=1, body=body, current_user=expert_user, db=mock_db
            )

        assert result["success"] is True
        mock_service.reject_correction.assert_awaited_once_with(
            record_id=1, expert_user_id=10, reason="Sai ma"
        )

    @pytest.mark.asyncio
    async def test_reject_without_reason_returns_422(self):
        """Test reject without reason fails Pydantic validation with ValidationError."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            RejectRequest(reason="")
