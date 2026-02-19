"""Tests for permission repository."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.models.permission import Permission, RolePermission, UserPermissionOverride
from app.repositories.permission_repository import PermissionRepository


class TestPermissionRepositoryListAll:
    """Tests for PermissionRepository.list_all_permissions."""

    @pytest.mark.asyncio
    async def test_list_all_permissions_returns_seeded_data(self):
        """Test list_all_permissions returns all permission records."""
        session = AsyncMock()

        perm1 = MagicMock(spec=Permission)
        perm1.code = "correction.submit"
        perm1.name = "Gui chinh sua"

        perm2 = MagicMock(spec=Permission)
        perm2.code = "user.manage"
        perm2.name = "Quan ly nguoi dung"

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [perm1, perm2]
        mock_result.scalars.return_value = mock_scalars
        session.execute.return_value = mock_result

        repo = PermissionRepository(session)
        result = await repo.list_all_permissions()

        assert len(result) == 2
        assert result[0].code == "correction.submit"
        assert result[1].code == "user.manage"


class TestPermissionRepositoryRolePermissions:
    """Tests for PermissionRepository role permission methods."""

    @pytest.mark.asyncio
    async def test_get_role_permissions_returns_correct_codes(self):
        """Test get_role_permissions returns permission codes for a role."""
        session = AsyncMock()

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [
            "correction.submit",
            "correction.approve",
        ]
        mock_result.scalars.return_value = mock_scalars
        session.execute.return_value = mock_result

        repo = PermissionRepository(session)
        result = await repo.get_role_permissions("expert")

        assert result == ["correction.submit", "correction.approve"]

    @pytest.mark.asyncio
    async def test_set_role_permissions_replaces_entries(self):
        """Test set_role_permissions deletes existing and inserts new entries."""
        session = AsyncMock()

        repo = PermissionRepository(session)
        await repo.set_role_permissions(
            "expert", ["correction.submit", "user.manage"]
        )

        # Should have called execute (delete) + add (for each code) + flush
        assert session.execute.await_count >= 1
        assert session.add.call_count == 2
        session.flush.assert_awaited_once()


class TestPermissionRepositoryUserOverrides:
    """Tests for PermissionRepository user override methods."""

    @pytest.mark.asyncio
    async def test_get_user_overrides_returns_overrides(self):
        """Test get_user_overrides returns user's permission overrides."""
        session = AsyncMock()

        override1 = MagicMock(spec=UserPermissionOverride)
        override1.permission_code = "correction.submit"
        override1.granted = False

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [override1]
        mock_result.scalars.return_value = mock_scalars
        session.execute.return_value = mock_result

        repo = PermissionRepository(session)
        result = await repo.get_user_overrides(1)

        assert len(result) == 1
        assert result[0].permission_code == "correction.submit"
        assert result[0].granted is False

    @pytest.mark.asyncio
    async def test_set_user_overrides_replaces_entries(self):
        """Test set_user_overrides deletes existing and inserts new overrides."""
        session = AsyncMock()

        repo = PermissionRepository(session)
        overrides = [
            {"code": "correction.submit", "granted": False},
            {"code": "user.manage", "granted": True},
        ]
        await repo.set_user_overrides(1, overrides)

        # Should have called execute (delete) + add (for each override) + flush
        assert session.execute.await_count >= 1
        assert session.add.call_count == 2
        session.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_user_override_returns_single_override(self):
        """Test get_user_override returns a single override or None."""
        session = AsyncMock()

        override = MagicMock(spec=UserPermissionOverride)
        override.permission_code = "correction.submit"
        override.granted = False

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = override
        session.execute.return_value = mock_result

        repo = PermissionRepository(session)
        result = await repo.get_user_override(1, "correction.submit")

        assert result is not None
        assert result.granted is False

    @pytest.mark.asyncio
    async def test_get_user_override_returns_none_when_not_found(self):
        """Test get_user_override returns None when no override exists."""
        session = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        repo = PermissionRepository(session)
        result = await repo.get_user_override(1, "user.manage")

        assert result is None


class TestPermissionRepositoryCheckExists:
    """Tests for PermissionRepository.check_permission_exists."""

    @pytest.mark.asyncio
    async def test_check_permission_exists_returns_true(self):
        """Test check_permission_exists returns True for existing code."""
        session = AsyncMock()

        perm = MagicMock(spec=Permission)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = perm
        session.execute.return_value = mock_result

        repo = PermissionRepository(session)
        result = await repo.check_permission_exists("correction.submit")

        assert result is True

    @pytest.mark.asyncio
    async def test_check_permission_exists_returns_false(self):
        """Test check_permission_exists returns False for non-existing code."""
        session = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        repo = PermissionRepository(session)
        result = await repo.check_permission_exists("fake.perm")

        assert result is False
