"""Tests for admin service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.user import User
from app.services.admin_service import AdminService


class TestAdminServiceListUsers:
    """Tests for AdminService.list_users."""

    @pytest.mark.asyncio
    async def test_list_users_returns_paginated_response(self):
        """Test list_users returns paginated response with user data."""
        session = AsyncMock()

        with (
            patch("app.services.admin_service.UserRepository") as mock_user_repo_class,
            patch("app.services.admin_service.AuditLogRepository"),
        ):
            mock_user_repo = AsyncMock()
            user1 = MagicMock(spec=User)
            user1.id = 1
            user1.email = "a@example.com"
            user1.role = "user"
            user1.created_at = "2026-02-15T00:00:00+00:00"

            user2 = MagicMock(spec=User)
            user2.id = 2
            user2.email = "b@example.com"
            user2.role = "admin"
            user2.created_at = "2026-02-15T00:00:00+00:00"

            mock_user_repo.list_all.return_value = ([user1, user2], 2)
            mock_user_repo_class.return_value = mock_user_repo

            service = AdminService(session)
            result = await service.list_users(page=1, per_page=20)

        assert result["total"] == 2
        assert result["page"] == 1
        assert result["per_page"] == 20
        assert result["pages"] == 1
        assert len(result["items"]) == 2
        assert result["items"][0]["email"] == "a@example.com"
        assert result["items"][1]["email"] == "b@example.com"


class TestAdminServiceUpdateUserRole:
    """Tests for AdminService.update_user_role."""

    @pytest.mark.asyncio
    async def test_update_user_role_success(self):
        """Test update_user_role changes role and creates audit log."""
        session = AsyncMock()

        with (
            patch("app.services.admin_service.UserRepository") as mock_user_repo_class,
            patch("app.services.admin_service.AuditLogRepository") as mock_audit_repo_class,
        ):
            mock_user_repo = AsyncMock()
            target = MagicMock(spec=User)
            target.id = 2
            target.email = "user@example.com"
            target.role = "user"
            target.created_at = "2026-02-15T00:00:00+00:00"
            mock_user_repo.get_by_id.return_value = target

            updated = MagicMock(spec=User)
            updated.id = 2
            updated.email = "user@example.com"
            updated.role = "admin"
            updated.created_at = "2026-02-15T00:00:00+00:00"
            mock_user_repo.update_role.return_value = updated
            mock_user_repo_class.return_value = mock_user_repo

            mock_audit_repo = AsyncMock()
            mock_audit_repo_class.return_value = mock_audit_repo

            service = AdminService(session)
            result = await service.update_user_role(
                admin_user_id=1, target_user_id=2, new_role="admin"
            )

        assert result is not None
        assert result.role == "admin"
        mock_user_repo.update_role.assert_awaited_once_with(2, "admin")
        mock_audit_repo.create.assert_awaited_once_with(
            admin_user_id=1,
            action="role_change",
            target_user_id=2,
            details={"old_role": "user", "new_role": "admin"},
        )

    @pytest.mark.asyncio
    async def test_update_user_role_not_found(self):
        """Test update_user_role with non-existent user returns None."""
        session = AsyncMock()

        with (
            patch("app.services.admin_service.UserRepository") as mock_user_repo_class,
            patch("app.services.admin_service.AuditLogRepository"),
        ):
            mock_user_repo = AsyncMock()
            mock_user_repo.get_by_id.return_value = None
            mock_user_repo_class.return_value = mock_user_repo

            service = AdminService(session)
            result = await service.update_user_role(
                admin_user_id=1, target_user_id=999, new_role="admin"
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_update_user_role_prevents_self_change(self):
        """Test update_user_role raises ValueError for self-role-change."""
        session = AsyncMock()

        with (
            patch("app.services.admin_service.UserRepository"),
            patch("app.services.admin_service.AuditLogRepository"),
        ):
            service = AdminService(session)

            with pytest.raises(ValueError, match="Cannot change your own role"):
                await service.update_user_role(
                    admin_user_id=1, target_user_id=1, new_role="user"
                )
