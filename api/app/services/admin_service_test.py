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
            user1.is_active = True
            user1.created_at = "2026-02-15T00:00:00+00:00"

            user2 = MagicMock(spec=User)
            user2.id = 2
            user2.email = "b@example.com"
            user2.role = "admin"
            user2.is_active = True
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

    @pytest.mark.asyncio
    async def test_list_users_passes_search_to_repo(self):
        """Test list_users passes search parameter to repository."""
        session = AsyncMock()

        with (
            patch("app.services.admin_service.UserRepository") as mock_user_repo_class,
            patch("app.services.admin_service.AuditLogRepository"),
        ):
            mock_user_repo = AsyncMock()
            mock_user_repo.list_all.return_value = ([], 0)
            mock_user_repo_class.return_value = mock_user_repo

            service = AdminService(session)
            await service.list_users(page=1, per_page=20, search="test@")

        mock_user_repo.list_all.assert_awaited_once_with(1, 20, "test@")


class TestAdminServiceCreateUser:
    """Tests for AdminService.create_user."""

    @pytest.mark.asyncio
    async def test_create_user_hashes_password_and_creates_audit_log(self):
        """Test create_user hashes password and creates audit log entry."""
        session = AsyncMock()

        with (
            patch("app.services.admin_service.UserRepository") as mock_user_repo_class,
            patch("app.services.admin_service.AuditLogRepository") as mock_audit_repo_class,
            patch("app.services.admin_service.hash_password") as mock_hash,
        ):
            mock_hash.return_value = "hashed_password_123"

            mock_user_repo = AsyncMock()
            mock_user_repo.get_by_email.return_value = None

            created_user = MagicMock(spec=User)
            created_user.id = 3
            created_user.email = "new@example.com"
            created_user.role = "user"
            created_user.is_active = True
            created_user.created_at = "2026-02-18T00:00:00+00:00"
            mock_user_repo.create.return_value = created_user
            mock_user_repo_class.return_value = mock_user_repo

            mock_audit_repo = AsyncMock()
            mock_audit_repo_class.return_value = mock_audit_repo

            service = AdminService(session)
            result = await service.create_user(
                admin_user_id=1, email="new@example.com", password="password123", role="user"
            )

        assert result is not None
        assert result["email"] == "new@example.com"
        assert result["role"] == "user"
        mock_hash.assert_called_once_with("password123")
        mock_audit_repo.create.assert_awaited_once_with(
            admin_user_id=1,
            action="user_created",
            target_user_id=3,
            details={"email": "new@example.com", "role": "user"},
        )

    @pytest.mark.asyncio
    async def test_create_user_returns_none_for_duplicate_email(self):
        """Test create_user returns None when email already exists."""
        session = AsyncMock()

        with (
            patch("app.services.admin_service.UserRepository") as mock_user_repo_class,
            patch("app.services.admin_service.AuditLogRepository"),
        ):
            mock_user_repo = AsyncMock()
            existing = MagicMock(spec=User)
            mock_user_repo.get_by_email.return_value = existing
            mock_user_repo_class.return_value = mock_user_repo

            service = AdminService(session)
            result = await service.create_user(
                admin_user_id=1, email="existing@example.com", password="password123", role="user"
            )

        assert result is None


class TestAdminServiceUpdateUser:
    """Tests for AdminService.update_user."""

    @pytest.mark.asyncio
    async def test_update_user_validates_email_uniqueness(self):
        """Test update_user returns email_exists when email conflicts."""
        session = AsyncMock()

        with (
            patch("app.services.admin_service.UserRepository") as mock_user_repo_class,
            patch("app.services.admin_service.AuditLogRepository"),
        ):
            mock_user_repo = AsyncMock()

            target = MagicMock(spec=User)
            target.id = 2
            target.email = "old@example.com"
            target.role = "user"
            mock_user_repo.get_by_id.return_value = target

            existing = MagicMock(spec=User)
            mock_user_repo.get_by_email.return_value = existing
            mock_user_repo_class.return_value = mock_user_repo

            service = AdminService(session)
            result = await service.update_user(
                admin_user_id=1, target_user_id=2, email="existing@example.com"
            )

        assert result == "email_exists"

    @pytest.mark.asyncio
    async def test_update_user_returns_not_found_for_missing_user(self):
        """Test update_user returns not_found when target user doesn't exist."""
        session = AsyncMock()

        with (
            patch("app.services.admin_service.UserRepository") as mock_user_repo_class,
            patch("app.services.admin_service.AuditLogRepository"),
        ):
            mock_user_repo = AsyncMock()
            mock_user_repo.get_by_id.return_value = None
            mock_user_repo_class.return_value = mock_user_repo

            service = AdminService(session)
            result = await service.update_user(
                admin_user_id=1, target_user_id=999, email="new@example.com"
            )

        assert result == "not_found"

    @pytest.mark.asyncio
    async def test_update_user_creates_audit_log(self):
        """Test update_user creates an audit log entry on success."""
        session = AsyncMock()

        with (
            patch("app.services.admin_service.UserRepository") as mock_user_repo_class,
            patch("app.services.admin_service.AuditLogRepository") as mock_audit_repo_class,
        ):
            mock_user_repo = AsyncMock()

            target = MagicMock(spec=User)
            target.id = 2
            target.email = "old@example.com"
            target.role = "user"
            mock_user_repo.get_by_id.return_value = target

            updated = MagicMock(spec=User)
            updated.id = 2
            updated.email = "new@example.com"
            updated.role = "expert"
            updated.is_active = True
            updated.created_at = "2026-02-15T00:00:00+00:00"
            mock_user_repo.update_user.return_value = updated
            mock_user_repo.get_by_email.return_value = None
            mock_user_repo_class.return_value = mock_user_repo

            mock_audit_repo = AsyncMock()
            mock_audit_repo_class.return_value = mock_audit_repo

            service = AdminService(session)
            result = await service.update_user(
                admin_user_id=1, target_user_id=2, email="new@example.com", role="expert"
            )

        assert isinstance(result, dict)
        assert result["email"] == "new@example.com"
        mock_audit_repo.create.assert_awaited_once_with(
            admin_user_id=1,
            action="user_updated",
            target_user_id=2,
            details={
                "old_email": "old@example.com",
                "new_email": "new@example.com",
                "old_role": "user",
                "new_role": "expert",
            },
        )


class TestAdminServiceToggleUserStatus:
    """Tests for AdminService.toggle_user_status."""

    @pytest.mark.asyncio
    async def test_toggle_user_status_prevents_self_deactivation(self):
        """Test toggle_user_status prevents admin from deactivating themselves."""
        session = AsyncMock()

        with (
            patch("app.services.admin_service.UserRepository"),
            patch("app.services.admin_service.AuditLogRepository"),
        ):
            service = AdminService(session)
            result = await service.toggle_user_status(
                admin_user_id=1, target_user_id=1, is_active=False
            )

        assert result == "self_deactivation"

    @pytest.mark.asyncio
    async def test_toggle_user_status_creates_audit_log(self):
        """Test toggle_user_status creates audit log on success."""
        session = AsyncMock()

        with (
            patch("app.services.admin_service.UserRepository") as mock_user_repo_class,
            patch("app.services.admin_service.AuditLogRepository") as mock_audit_repo_class,
        ):
            mock_user_repo = AsyncMock()

            target = MagicMock(spec=User)
            target.id = 2
            mock_user_repo.get_by_id.return_value = target

            updated = MagicMock(spec=User)
            updated.id = 2
            updated.email = "user@example.com"
            updated.role = "user"
            updated.is_active = False
            updated.created_at = "2026-02-15T00:00:00+00:00"
            mock_user_repo.update_status.return_value = updated
            mock_user_repo_class.return_value = mock_user_repo

            mock_audit_repo = AsyncMock()
            mock_audit_repo_class.return_value = mock_audit_repo

            service = AdminService(session)
            result = await service.toggle_user_status(
                admin_user_id=1, target_user_id=2, is_active=False
            )

        assert isinstance(result, dict)
        assert result["is_active"] is False
        mock_audit_repo.create.assert_awaited_once_with(
            admin_user_id=1,
            action="user_status_changed",
            target_user_id=2,
            details={"is_active": False},
        )

    @pytest.mark.asyncio
    async def test_toggle_user_status_not_found(self):
        """Test toggle_user_status returns not_found when user doesn't exist."""
        session = AsyncMock()

        with (
            patch("app.services.admin_service.UserRepository") as mock_user_repo_class,
            patch("app.services.admin_service.AuditLogRepository"),
        ):
            mock_user_repo = AsyncMock()
            mock_user_repo.get_by_id.return_value = None
            mock_user_repo_class.return_value = mock_user_repo

            service = AdminService(session)
            result = await service.toggle_user_status(
                admin_user_id=1, target_user_id=999, is_active=False
            )

        assert result == "not_found"


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
