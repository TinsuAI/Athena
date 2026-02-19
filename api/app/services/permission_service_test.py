"""Tests for permission service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.permission import UserPermissionOverride
from app.services.permission_service import PermissionService


class TestPermissionServiceHasPermission:
    """Tests for PermissionService.has_permission."""

    @pytest.mark.asyncio
    async def test_has_permission_returns_true_for_role_default(self):
        """Test has_permission returns True when permission is in role defaults."""
        session = AsyncMock()

        with patch(
            "app.services.permission_service.PermissionRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_user_override.return_value = None
            mock_repo.get_role_permissions.return_value = [
                "correction.submit",
                "correction.approve",
            ]
            mock_repo_class.return_value = mock_repo

            service = PermissionService(session)
            result = await service.has_permission(
                user_id=1, role="expert", permission_code="correction.submit"
            )

        assert result is True

    @pytest.mark.asyncio
    async def test_has_permission_returns_false_for_missing_permission(self):
        """Test has_permission returns False when permission is not in role defaults."""
        session = AsyncMock()

        with patch(
            "app.services.permission_service.PermissionRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_user_override.return_value = None
            mock_repo.get_role_permissions.return_value = ["correction.submit"]
            mock_repo_class.return_value = mock_repo

            service = PermissionService(session)
            result = await service.has_permission(
                user_id=1, role="user", permission_code="user.manage"
            )

        assert result is False

    @pytest.mark.asyncio
    async def test_has_permission_override_revoke_wins_over_role_default(self):
        """Test user override revoking takes priority over role default."""
        session = AsyncMock()

        with patch(
            "app.services.permission_service.PermissionRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            override = MagicMock(spec=UserPermissionOverride)
            override.granted = False
            mock_repo.get_user_override.return_value = override
            mock_repo_class.return_value = mock_repo

            service = PermissionService(session)
            result = await service.has_permission(
                user_id=1, role="expert", permission_code="correction.submit"
            )

        assert result is False
        # Should NOT check role_permissions because override exists
        mock_repo.get_role_permissions.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_has_permission_override_grant_adds_new_permission(self):
        """Test user override granting adds permission not in role defaults."""
        session = AsyncMock()

        with patch(
            "app.services.permission_service.PermissionRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            override = MagicMock(spec=UserPermissionOverride)
            override.granted = True
            mock_repo.get_user_override.return_value = override
            mock_repo_class.return_value = mock_repo

            service = PermissionService(session)
            result = await service.has_permission(
                user_id=1, role="user", permission_code="user.manage"
            )

        assert result is True


class TestPermissionServiceGetAllRolePermissions:
    """Tests for PermissionService.get_all_role_permissions."""

    @pytest.mark.asyncio
    async def test_get_all_role_permissions_returns_all_roles_and_permissions(self):
        """Test get_all_role_permissions returns all roles with their permissions and the full permission list."""
        from app.models.permission import Permission

        session = AsyncMock()

        with patch(
            "app.services.permission_service.PermissionRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()

            perm1 = MagicMock(spec=Permission)
            perm1.code = "correction.submit"
            perm1.name = "Gui chinh sua"
            perm1.description = None

            perm2 = MagicMock(spec=Permission)
            perm2.code = "user.manage"
            perm2.name = "Quan ly nguoi dung"
            perm2.description = None

            mock_repo.list_all_permissions.return_value = [perm1, perm2]
            mock_repo.get_role_permissions.side_effect = lambda role: {
                "user": ["correction.submit"],
                "expert": ["correction.submit"],
                "admin": ["correction.submit", "user.manage"],
            }[role]
            mock_repo_class.return_value = mock_repo

            service = PermissionService(session)
            result = await service.get_all_role_permissions()

        assert "all_permissions" in result
        assert "roles" in result
        assert len(result["all_permissions"]) == 2
        assert len(result["roles"]) == 3
        role_names = [r["role"] for r in result["roles"]]
        assert "user" in role_names
        assert "expert" in role_names
        assert "admin" in role_names
        # Check user role has correction.submit
        user_role = next(r for r in result["roles"] if r["role"] == "user")
        assert "correction.submit" in user_role["permissions"]


class TestPermissionServiceEffectivePermissions:
    """Tests for PermissionService.get_user_effective_permissions."""

    @pytest.mark.asyncio
    async def test_get_user_effective_permissions_merges_role_and_overrides(self):
        """Test effective permissions merges role defaults with overrides."""
        session = AsyncMock()

        with patch(
            "app.services.permission_service.PermissionRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_role_permissions.return_value = [
                "correction.submit",
                "correction.approve",
            ]

            # Override: revoke correction.approve, grant user.manage
            override1 = MagicMock(spec=UserPermissionOverride)
            override1.permission_code = "correction.approve"
            override1.granted = False

            override2 = MagicMock(spec=UserPermissionOverride)
            override2.permission_code = "user.manage"
            override2.granted = True

            mock_repo.get_user_overrides.return_value = [override1, override2]
            mock_repo_class.return_value = mock_repo

            service = PermissionService(session)
            result = await service.get_user_effective_permissions(
                user_id=1, role="expert"
            )

        assert result["user_id"] == 1
        assert result["role"] == "expert"
        assert "correction.submit" in result["effective"]
        assert "correction.approve" not in result["effective"]
        assert "user.manage" in result["effective"]
        assert len(result["overrides"]) == 2


class TestPermissionServiceUpdateRole:
    """Tests for PermissionService.update_role_permissions."""

    @pytest.mark.asyncio
    async def test_update_role_permissions_replaces_existing(self):
        """Test update_role_permissions replaces all permissions for a role."""
        session = AsyncMock()

        with patch(
            "app.services.permission_service.PermissionRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.check_permission_exists.return_value = True
            mock_repo_class.return_value = mock_repo

            service = PermissionService(session)
            result = await service.update_role_permissions(
                "expert", ["correction.submit", "user.manage"]
            )

        assert result == ["correction.submit", "user.manage"]
        mock_repo.set_role_permissions.assert_awaited_once_with(
            "expert", ["correction.submit", "user.manage"]
        )

    @pytest.mark.asyncio
    async def test_update_role_permissions_rejects_invalid_role(self):
        """Test update_role_permissions raises ValueError for invalid role."""
        session = AsyncMock()

        with patch(
            "app.services.permission_service.PermissionRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo

            service = PermissionService(session)
            with pytest.raises(ValueError, match="Invalid role"):
                await service.update_role_permissions(
                    "superadmin", ["correction.submit"]
                )

    @pytest.mark.asyncio
    async def test_update_role_permissions_rejects_unknown_code(self):
        """Test update_role_permissions raises ValueError for unknown permission code."""
        session = AsyncMock()

        with patch(
            "app.services.permission_service.PermissionRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.check_permission_exists.return_value = False
            mock_repo_class.return_value = mock_repo

            service = PermissionService(session)
            with pytest.raises(ValueError, match="Unknown permission code"):
                await service.update_role_permissions(
                    "user", ["nonexistent.perm"]
                )


class TestPermissionServiceUpdateUserOverrides:
    """Tests for PermissionService.update_user_overrides."""

    @pytest.mark.asyncio
    async def test_update_user_overrides_replaces_existing(self):
        """Test update_user_overrides replaces all overrides for a user."""
        session = AsyncMock()

        with patch(
            "app.services.permission_service.PermissionRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.check_permission_exists.return_value = True
            mock_repo_class.return_value = mock_repo

            overrides = [
                {"code": "correction.submit", "granted": False},
                {"code": "user.manage", "granted": True},
            ]

            service = PermissionService(session)
            result = await service.update_user_overrides(1, overrides)

        assert result == overrides
        mock_repo.set_user_overrides.assert_awaited_once_with(1, overrides)

    @pytest.mark.asyncio
    async def test_update_user_overrides_rejects_unknown_code(self):
        """Test update_user_overrides raises ValueError for unknown permission code."""
        session = AsyncMock()

        with patch(
            "app.services.permission_service.PermissionRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.check_permission_exists.return_value = False
            mock_repo_class.return_value = mock_repo

            service = PermissionService(session)
            with pytest.raises(ValueError, match="Unknown permission code"):
                await service.update_user_overrides(
                    1, [{"code": "fake.perm", "granted": True}]
                )
