"""Tests for admin API endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException

from app.api.admin import list_users, update_user_role, list_audit_log
from app.schemas.admin import RoleUpdateRequest
from app.schemas.user import UserResponse


class TestListUsers:
    """Tests for GET /api/admin/users."""

    @pytest.mark.asyncio
    async def test_admin_returns_user_list(self):
        """Test admin user gets paginated user list."""
        mock_db = AsyncMock()
        admin_user = {"id": 1, "email": "admin@example.com", "role": "admin"}

        with patch("app.api.admin.AdminService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.list_users.return_value = {
                "items": [
                    {"id": 1, "email": "admin@example.com", "role": "admin", "created_at": "2026-02-15T00:00:00+00:00"},
                    {"id": 2, "email": "user@example.com", "role": "user", "created_at": "2026-02-15T00:00:00+00:00"},
                ],
                "total": 2,
                "page": 1,
                "per_page": 20,
                "pages": 1,
            }
            mock_service_class.return_value = mock_service

            result = await list_users(page=1, per_page=20, current_user=admin_user, db=mock_db)

        assert result["success"] is True
        assert len(result["data"]["items"]) == 2

    @pytest.mark.asyncio
    async def test_standard_user_gets_403(self):
        """Test non-admin user is blocked by require_admin dependency."""
        # require_admin raises HTTPException(403) before the endpoint is called.
        # This test verifies the dependency raises 403 for non-admin users.
        from app.core.auth import require_admin

        mock_request = MagicMock()
        with patch("app.core.auth.JWT") as mock_jwt:
            mock_jwt.return_value = {"id": "2", "email": "user@example.com", "role": "user"}
            with pytest.raises(HTTPException) as exc_info:
                await require_admin(mock_request)
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_unauthenticated_gets_401(self):
        """Test unauthenticated user gets 401."""
        from app.core.auth import require_admin

        mock_request = MagicMock()
        with patch("app.core.auth.JWT") as mock_jwt:
            mock_jwt.side_effect = Exception("No token")
            with pytest.raises(HTTPException) as exc_info:
                await require_admin(mock_request)
            assert exc_info.value.status_code == 401


class TestUpdateUserRole:
    """Tests for PATCH /api/admin/users/{user_id}/role."""

    @pytest.mark.asyncio
    async def test_admin_updates_role(self):
        """Test admin can update another user's role."""
        mock_db = AsyncMock()
        mock_redis = AsyncMock()
        mock_redis.incr.return_value = 1  # First request, not rate limited
        admin_user = {"id": 1, "email": "admin@example.com", "role": "admin"}

        with patch("app.api.admin.AdminService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.update_user_role.return_value = UserResponse(
                id=2, email="user@example.com", role="admin", created_at="2026-02-15T00:00:00+00:00"
            )
            mock_service_class.return_value = mock_service

            body = RoleUpdateRequest(role="admin")
            result = await update_user_role(user_id=2, body=body, current_user=admin_user, db=mock_db, redis=mock_redis)

        assert result["success"] is True
        assert result["data"]["role"] == "admin"

    def test_invalid_role_returns_422(self):
        """Test invalid role value is rejected by schema validation."""
        with pytest.raises(Exception):
            RoleUpdateRequest(role="superadmin")

    @pytest.mark.asyncio
    async def test_self_change_returns_400(self):
        """Test admin cannot change their own role."""
        mock_db = AsyncMock()
        mock_redis = AsyncMock()
        mock_redis.incr.return_value = 1  # Not rate limited
        admin_user = {"id": 1, "email": "admin@example.com", "role": "admin"}

        with patch("app.api.admin.AdminService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.update_user_role.side_effect = ValueError("Cannot change your own role")
            mock_service_class.return_value = mock_service

            body = RoleUpdateRequest(role="user")
            result = await update_user_role(user_id=1, body=body, current_user=admin_user, db=mock_db, redis=mock_redis)

        assert result["success"] is False
        assert result["error"]["status"] == 400

    @pytest.mark.asyncio
    async def test_nonexistent_user_returns_404(self):
        """Test updating non-existent user returns 404."""
        mock_db = AsyncMock()
        mock_redis = AsyncMock()
        mock_redis.incr.return_value = 1  # Not rate limited
        admin_user = {"id": 1, "email": "admin@example.com", "role": "admin"}

        with patch("app.api.admin.AdminService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.update_user_role.return_value = None
            mock_service_class.return_value = mock_service

            body = RoleUpdateRequest(role="admin")
            result = await update_user_role(user_id=999, body=body, current_user=admin_user, db=mock_db, redis=mock_redis)

        assert result["success"] is False
        assert result["error"]["status"] == 404

    @pytest.mark.asyncio
    async def test_rate_limit_returns_429(self):
        """Test role change endpoint enforces rate limiting."""
        mock_db = AsyncMock()
        mock_redis = AsyncMock()
        mock_redis.incr.return_value = 11  # Over the limit of 10
        admin_user = {"id": 1, "email": "admin@example.com", "role": "admin"}

        body = RoleUpdateRequest(role="admin")
        result = await update_user_role(user_id=2, body=body, current_user=admin_user, db=mock_db, redis=mock_redis)

        assert result["success"] is False
        assert result["error"]["status"] == 429
        assert "rate limit" in result["error"]["detail"].lower()


class TestListAuditLog:
    """Tests for GET /api/admin/audit-log."""

    @pytest.mark.asyncio
    async def test_admin_gets_audit_log(self):
        """Test admin user gets audit log entries with eager-loaded relationships."""
        mock_db = AsyncMock()
        admin_user = {"id": 1, "email": "admin@example.com", "role": "admin"}

        with patch("app.api.admin.AuditLogRepository") as mock_audit_class:
            mock_audit_repo = AsyncMock()
            mock_entry = MagicMock()
            mock_entry.id = 1
            mock_entry.admin_user_id = 1
            mock_entry.action = "role_change"
            mock_entry.target_user_id = 2
            mock_entry.details = {"old_role": "user", "new_role": "admin"}
            mock_entry.created_at = "2026-02-15T00:00:00+00:00"

            # Mock eager-loaded relationships
            admin_mock = MagicMock()
            admin_mock.email = "admin@example.com"
            target_mock = MagicMock()
            target_mock.email = "user@example.com"
            mock_entry.admin_user = admin_mock
            mock_entry.target_user = target_mock

            mock_audit_repo.list_recent.return_value = [mock_entry]
            mock_audit_class.return_value = mock_audit_repo

            result = await list_audit_log(limit=50, current_user=admin_user, db=mock_db)

        assert result["success"] is True
        assert len(result["data"]) == 1
        assert result["data"][0]["action"] == "role_change"
        assert result["data"][0]["admin_email"] == "admin@example.com"
        assert result["data"][0]["target_email"] == "user@example.com"
