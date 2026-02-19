"""Tests for admin API endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException

from app.api.admin import (
    create_user,
    get_role_permissions,
    get_user_permissions,
    list_users,
    toggle_user_status,
    update_role_permissions,
    update_user,
    update_user_permissions,
    update_user_role,
    list_audit_log,
)
from app.schemas.admin import (
    AdminCreateUserRequest,
    AdminUpdateUserRequest,
    PermissionOverrideItem,
    RoleUpdateRequest,
    UpdateRolePermissionsRequest,
    UpdateUserPermissionsRequest,
    UserStatusRequest,
)
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
                    {"id": 1, "email": "admin@example.com", "role": "admin", "is_active": True, "created_at": "2026-02-15T00:00:00+00:00"},
                    {"id": 2, "email": "user@example.com", "role": "user", "is_active": True, "created_at": "2026-02-15T00:00:00+00:00"},
                ],
                "total": 2,
                "page": 1,
                "per_page": 20,
                "pages": 1,
            }
            mock_service_class.return_value = mock_service

            result = await list_users(page=1, per_page=20, search="", current_user=admin_user, db=mock_db)

        assert result["success"] is True
        assert len(result["data"]["items"]) == 2

    @pytest.mark.asyncio
    async def test_list_users_with_search_filters_by_email(self):
        """Test list_users passes search parameter to service."""
        mock_db = AsyncMock()
        admin_user = {"id": 1, "email": "admin@example.com", "role": "admin"}

        with patch("app.api.admin.AdminService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.list_users.return_value = {
                "items": [
                    {"id": 2, "email": "user@example.com", "role": "user", "is_active": True, "created_at": "2026-02-15T00:00:00+00:00"},
                ],
                "total": 1,
                "page": 1,
                "per_page": 20,
                "pages": 1,
            }
            mock_service_class.return_value = mock_service

            result = await list_users(page=1, per_page=20, search="user@", current_user=admin_user, db=mock_db)

        assert result["success"] is True
        assert len(result["data"]["items"]) == 1
        mock_service.list_users.assert_awaited_once_with(page=1, per_page=20, search="user@")

    @pytest.mark.asyncio
    async def test_standard_user_gets_403(self):
        """Test non-admin user is blocked by require_admin dependency."""
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


class TestCreateUser:
    """Tests for POST /api/admin/users."""

    @pytest.mark.asyncio
    async def test_create_user_success(self):
        """Test POST create user returns success with user data."""
        mock_db = AsyncMock()
        admin_user = {"id": 1, "email": "admin@example.com", "role": "admin"}

        with patch("app.api.admin.AdminService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.create_user.return_value = {
                "id": 3,
                "email": "new@example.com",
                "role": "user",
                "is_active": True,
                "created_at": "2026-02-18T00:00:00+00:00",
            }
            mock_service_class.return_value = mock_service

            body = AdminCreateUserRequest(
                email="new@example.com", password="password123", role="user"
            )
            result = await create_user(body=body, current_user=admin_user, db=mock_db)

        assert result["success"] is True
        assert result["data"]["email"] == "new@example.com"
        assert result["data"]["role"] == "user"

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email_returns_400(self):
        """Test POST create user with duplicate email returns 400."""
        mock_db = AsyncMock()
        admin_user = {"id": 1, "email": "admin@example.com", "role": "admin"}

        with patch("app.api.admin.AdminService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.create_user.return_value = None
            mock_service_class.return_value = mock_service

            body = AdminCreateUserRequest(
                email="existing@example.com", password="password123", role="user"
            )
            result = await create_user(body=body, current_user=admin_user, db=mock_db)

        assert result["success"] is False
        assert result["error"]["status"] == 400
        assert "Email already exists" in result["error"]["detail"]

    def test_create_user_invalid_email_returns_422(self):
        """Test Pydantic validation rejects invalid email."""
        with pytest.raises(Exception):
            AdminCreateUserRequest(
                email="not-an-email", password="password123", role="user"
            )

    def test_create_user_short_password_returns_422(self):
        """Test Pydantic validation rejects short password."""
        with pytest.raises(Exception):
            AdminCreateUserRequest(
                email="test@example.com", password="short", role="user"
            )


class TestUpdateUser:
    """Tests for PATCH /api/admin/users/{user_id}."""

    @pytest.mark.asyncio
    async def test_update_user_email_and_role(self):
        """Test PATCH update user email and role."""
        mock_db = AsyncMock()
        admin_user = {"id": 1, "email": "admin@example.com", "role": "admin"}

        with patch("app.api.admin.AdminService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.update_user.return_value = {
                "id": 2,
                "email": "updated@example.com",
                "role": "expert",
                "is_active": True,
                "created_at": "2026-02-15T00:00:00+00:00",
            }
            mock_service_class.return_value = mock_service

            body = AdminUpdateUserRequest(email="updated@example.com", role="expert")
            result = await update_user(
                user_id=2, body=body, current_user=admin_user, db=mock_db
            )

        assert result["success"] is True
        assert result["data"]["email"] == "updated@example.com"
        assert result["data"]["role"] == "expert"

    @pytest.mark.asyncio
    async def test_update_user_not_found_returns_404(self):
        """Test PATCH update non-existent user returns 404."""
        mock_db = AsyncMock()
        admin_user = {"id": 1, "email": "admin@example.com", "role": "admin"}

        with patch("app.api.admin.AdminService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.update_user.return_value = "not_found"
            mock_service_class.return_value = mock_service

            body = AdminUpdateUserRequest(email="updated@example.com")
            result = await update_user(
                user_id=999, body=body, current_user=admin_user, db=mock_db
            )

        assert result["success"] is False
        assert result["error"]["status"] == 404

    @pytest.mark.asyncio
    async def test_update_user_email_conflict_returns_400(self):
        """Test PATCH update user with conflicting email returns 400."""
        mock_db = AsyncMock()
        admin_user = {"id": 1, "email": "admin@example.com", "role": "admin"}

        with patch("app.api.admin.AdminService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.update_user.return_value = "email_exists"
            mock_service_class.return_value = mock_service

            body = AdminUpdateUserRequest(email="existing@example.com")
            result = await update_user(
                user_id=2, body=body, current_user=admin_user, db=mock_db
            )

        assert result["success"] is False
        assert result["error"]["status"] == 400
        assert "Email already exists" in result["error"]["detail"]


class TestToggleUserStatus:
    """Tests for PATCH /api/admin/users/{user_id}/status."""

    @pytest.mark.asyncio
    async def test_toggle_status_deactivates_user(self):
        """Test PATCH toggle user status deactivates user."""
        mock_db = AsyncMock()
        admin_user = {"id": 1, "email": "admin@example.com", "role": "admin"}

        with patch("app.api.admin.AdminService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.toggle_user_status.return_value = {
                "id": 2,
                "email": "user@example.com",
                "role": "user",
                "is_active": False,
                "created_at": "2026-02-15T00:00:00+00:00",
            }
            mock_service_class.return_value = mock_service

            body = UserStatusRequest(is_active=False)
            result = await toggle_user_status(
                user_id=2, body=body, current_user=admin_user, db=mock_db
            )

        assert result["success"] is True
        assert result["data"]["is_active"] is False

    @pytest.mark.asyncio
    async def test_toggle_status_reactivates_user(self):
        """Test PATCH toggle user status reactivates user."""
        mock_db = AsyncMock()
        admin_user = {"id": 1, "email": "admin@example.com", "role": "admin"}

        with patch("app.api.admin.AdminService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.toggle_user_status.return_value = {
                "id": 2,
                "email": "user@example.com",
                "role": "user",
                "is_active": True,
                "created_at": "2026-02-15T00:00:00+00:00",
            }
            mock_service_class.return_value = mock_service

            body = UserStatusRequest(is_active=True)
            result = await toggle_user_status(
                user_id=2, body=body, current_user=admin_user, db=mock_db
            )

        assert result["success"] is True
        assert result["data"]["is_active"] is True

    @pytest.mark.asyncio
    async def test_self_deactivation_returns_400(self):
        """Test self-deactivation returns 400."""
        mock_db = AsyncMock()
        admin_user = {"id": 1, "email": "admin@example.com", "role": "admin"}

        with patch("app.api.admin.AdminService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.toggle_user_status.return_value = "self_deactivation"
            mock_service_class.return_value = mock_service

            body = UserStatusRequest(is_active=False)
            result = await toggle_user_status(
                user_id=1, body=body, current_user=admin_user, db=mock_db
            )

        assert result["success"] is False
        assert result["error"]["status"] == 400
        assert "Khong the vo hieu hoa tai khoan cua chinh minh" in result["error"]["detail"]

    @pytest.mark.asyncio
    async def test_toggle_status_not_found_returns_404(self):
        """Test toggle status for non-existent user returns 404."""
        mock_db = AsyncMock()
        admin_user = {"id": 1, "email": "admin@example.com", "role": "admin"}

        with patch("app.api.admin.AdminService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.toggle_user_status.return_value = "not_found"
            mock_service_class.return_value = mock_service

            body = UserStatusRequest(is_active=False)
            result = await toggle_user_status(
                user_id=999, body=body, current_user=admin_user, db=mock_db
            )

        assert result["success"] is False
        assert result["error"]["status"] == 404


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


class TestAdminEndpointsRequireAdminRole:
    """Tests that all admin endpoints require admin role (403 for user/expert)."""

    @pytest.mark.asyncio
    async def test_admin_endpoints_require_admin_role(self):
        """Test require_admin dependency raises 403 for non-admin roles."""
        from app.core.auth import require_admin

        mock_request = MagicMock()

        # Test with "user" role
        with patch("app.core.auth.JWT") as mock_jwt:
            mock_jwt.return_value = {"id": "2", "email": "user@example.com", "role": "user"}
            with pytest.raises(HTTPException) as exc_info:
                await require_admin(mock_request)
            assert exc_info.value.status_code == 403

        # Test with "expert" role
        with patch("app.core.auth.JWT") as mock_jwt:
            mock_jwt.return_value = {"id": "3", "email": "expert@example.com", "role": "expert"}
            with pytest.raises(HTTPException) as exc_info:
                await require_admin(mock_request)
            assert exc_info.value.status_code == 403


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


# ==================== Permission endpoint tests ====================


class TestGetRolePermissions:
    """Tests for GET /api/admin/permissions/roles."""

    @pytest.mark.asyncio
    async def test_get_role_permissions_returns_all_roles(self):
        """Test GET role permissions returns all roles with their permissions."""
        mock_db = AsyncMock()
        admin_user = {"id": 1, "email": "admin@example.com", "role": "admin"}

        with patch("app.api.admin.PermissionService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_all_role_permissions.return_value = {
                "all_permissions": [
                    {"code": "correction.submit", "name": "Gui chinh sua", "description": None},
                    {"code": "user.manage", "name": "Quan ly nguoi dung", "description": None},
                ],
                "roles": [
                    {"role": "user", "permissions": ["correction.submit"]},
                    {"role": "expert", "permissions": ["correction.submit", "correction.approve"]},
                    {"role": "admin", "permissions": ["correction.submit", "user.manage"]},
                ],
            }
            mock_service_class.return_value = mock_service

            result = await get_role_permissions(current_user=admin_user, db=mock_db)

        assert result["success"] is True
        assert len(result["data"]["roles"]) == 3
        assert len(result["data"]["all_permissions"]) == 2


class TestUpdateRolePermissions:
    """Tests for PUT /api/admin/permissions/roles/{role}."""

    @pytest.mark.asyncio
    async def test_put_role_permissions_updates_role(self):
        """Test PUT role permissions updates a role's permissions."""
        mock_db = AsyncMock()
        admin_user = {"id": 1, "email": "admin@example.com", "role": "admin"}

        with (
            patch("app.api.admin.PermissionService") as mock_service_class,
            patch("app.api.admin.AuditLogRepository") as mock_audit_class,
        ):
            mock_service = AsyncMock()
            mock_service.update_role_permissions.return_value = ["correction.submit", "user.manage"]
            mock_service_class.return_value = mock_service

            mock_audit = AsyncMock()
            mock_audit_class.return_value = mock_audit

            body = UpdateRolePermissionsRequest(permissions=["correction.submit", "user.manage"])
            result = await update_role_permissions(
                role="expert", body=body, current_user=admin_user, db=mock_db
            )

        assert result["success"] is True
        assert result["data"]["role"] == "expert"
        assert result["data"]["permissions"] == ["correction.submit", "user.manage"]
        mock_audit.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_put_role_permissions_invalid_code_returns_400(self):
        """Test PUT role permissions with invalid code returns 400."""
        mock_db = AsyncMock()
        admin_user = {"id": 1, "email": "admin@example.com", "role": "admin"}

        with patch("app.api.admin.PermissionService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.update_role_permissions.side_effect = ValueError(
                "Unknown permission code: fake.perm"
            )
            mock_service_class.return_value = mock_service

            body = UpdateRolePermissionsRequest(permissions=["fake.perm"])
            result = await update_role_permissions(
                role="user", body=body, current_user=admin_user, db=mock_db
            )

        assert result["success"] is False
        assert result["error"]["status"] == 400
        assert "Unknown permission code" in result["error"]["detail"]


class TestGetUserPermissions:
    """Tests for GET /api/admin/permissions/users/{user_id}."""

    @pytest.mark.asyncio
    async def test_get_user_permissions_returns_effective(self):
        """Test GET user permissions returns effective permissions."""
        mock_db = AsyncMock()
        admin_user = {"id": 1, "email": "admin@example.com", "role": "admin"}

        with (
            patch("app.api.admin.UserRepository") as mock_user_repo_class,
            patch("app.api.admin.PermissionService") as mock_service_class,
        ):
            mock_user_repo = AsyncMock()
            target = MagicMock()
            target.role = "expert"
            mock_user_repo.get_by_id.return_value = target
            mock_user_repo_class.return_value = mock_user_repo

            mock_service = AsyncMock()
            mock_service.get_user_effective_permissions.return_value = {
                "user_id": 2,
                "role": "expert",
                "role_permissions": ["correction.submit", "correction.approve"],
                "overrides": [{"code": "correction.approve", "granted": False}],
                "effective": ["correction.submit"],
            }
            mock_service_class.return_value = mock_service

            result = await get_user_permissions(
                user_id=2, current_user=admin_user, db=mock_db
            )

        assert result["success"] is True
        assert result["data"]["user_id"] == 2
        assert "correction.submit" in result["data"]["effective"]
        assert "correction.approve" not in result["data"]["effective"]

    @pytest.mark.asyncio
    async def test_get_user_permissions_not_found_returns_404(self):
        """Test GET user permissions for non-existent user returns 404."""
        mock_db = AsyncMock()
        admin_user = {"id": 1, "email": "admin@example.com", "role": "admin"}

        with patch("app.api.admin.UserRepository") as mock_user_repo_class:
            mock_user_repo = AsyncMock()
            mock_user_repo.get_by_id.return_value = None
            mock_user_repo_class.return_value = mock_user_repo

            result = await get_user_permissions(
                user_id=999, current_user=admin_user, db=mock_db
            )

        assert result["success"] is False
        assert result["error"]["status"] == 404


class TestUpdateUserPermissions:
    """Tests for PUT /api/admin/permissions/users/{user_id}."""

    @pytest.mark.asyncio
    async def test_put_user_permissions_updates_overrides(self):
        """Test PUT user permissions updates overrides."""
        mock_db = AsyncMock()
        admin_user = {"id": 1, "email": "admin@example.com", "role": "admin"}

        with (
            patch("app.api.admin.UserRepository") as mock_user_repo_class,
            patch("app.api.admin.PermissionService") as mock_service_class,
            patch("app.api.admin.AuditLogRepository") as mock_audit_class,
        ):
            mock_user_repo = AsyncMock()
            target = MagicMock()
            target.role = "expert"
            mock_user_repo.get_by_id.return_value = target
            mock_user_repo_class.return_value = mock_user_repo

            mock_service = AsyncMock()
            mock_service.get_user_effective_permissions.return_value = {
                "user_id": 2,
                "role": "expert",
                "role_permissions": ["correction.submit", "correction.approve"],
                "overrides": [{"code": "correction.approve", "granted": False}],
                "effective": ["correction.submit"],
            }
            mock_service_class.return_value = mock_service

            mock_audit = AsyncMock()
            mock_audit_class.return_value = mock_audit

            body = UpdateUserPermissionsRequest(
                overrides=[PermissionOverrideItem(code="correction.approve", granted=False)]
            )
            result = await update_user_permissions(
                user_id=2, body=body, current_user=admin_user, db=mock_db
            )

        assert result["success"] is True
        assert result["data"]["user_id"] == 2
        mock_service.update_user_overrides.assert_awaited_once()
        mock_audit.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_put_user_permissions_invalid_code_returns_400(self):
        """Test PUT user permissions with invalid code returns 400."""
        mock_db = AsyncMock()
        admin_user = {"id": 1, "email": "admin@example.com", "role": "admin"}

        with (
            patch("app.api.admin.UserRepository") as mock_user_repo_class,
            patch("app.api.admin.PermissionService") as mock_service_class,
        ):
            mock_user_repo = AsyncMock()
            target = MagicMock()
            target.role = "expert"
            mock_user_repo.get_by_id.return_value = target
            mock_user_repo_class.return_value = mock_user_repo

            mock_service = AsyncMock()
            mock_service.update_user_overrides.side_effect = ValueError(
                "Unknown permission code: fake.perm"
            )
            mock_service_class.return_value = mock_service

            body = UpdateUserPermissionsRequest(
                overrides=[PermissionOverrideItem(code="fake.perm", granted=True)]
            )
            result = await update_user_permissions(
                user_id=2, body=body, current_user=admin_user, db=mock_db
            )

        assert result["success"] is False
        assert result["error"]["status"] == 400


class TestPermissionEndpointsRequireAdmin:
    """Tests that permission endpoints require admin role (403 for user/expert)."""

    @pytest.mark.asyncio
    async def test_permission_endpoints_require_admin_role(self):
        """Test require_admin dependency raises 403 for non-admin roles on permission endpoints."""
        from app.core.auth import require_admin

        mock_request = MagicMock()

        # Test with "user" role
        with patch("app.core.auth.JWT") as mock_jwt:
            mock_jwt.return_value = {"id": "2", "email": "user@example.com", "role": "user"}
            with pytest.raises(HTTPException) as exc_info:
                await require_admin(mock_request)
            assert exc_info.value.status_code == 403

        # Test with "expert" role
        with patch("app.core.auth.JWT") as mock_jwt:
            mock_jwt.return_value = {"id": "3", "email": "expert@example.com", "role": "expert"}
            with pytest.raises(HTTPException) as exc_info:
                await require_admin(mock_request)
            assert exc_info.value.status_code == 403
