"""Permission service for role-based and per-user permission management."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.permission_repository import PermissionRepository


class PermissionService:
    """Service for permission resolution, role/user permission CRUD."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.permission_repo = PermissionRepository(session)

    async def has_permission(
        self, user_id: int, role: str, permission_code: str
    ) -> bool:
        """Check if user has a specific permission.

        Resolution order:
        1. Check user_permission_overrides for explicit grant/revoke
        2. If no override, check role_permissions for role default
        3. If neither, permission is denied
        """
        # Check user-specific override first (overrides win)
        override = await self.permission_repo.get_user_override(
            user_id, permission_code
        )
        if override is not None:
            return override.granted

        # Fall back to role default
        role_perms = await self.permission_repo.get_role_permissions(role)
        return permission_code in role_perms

    async def get_role_permissions(self, role: str) -> list[str]:
        """Return list of permission codes for a role."""
        return await self.permission_repo.get_role_permissions(role)

    async def get_all_role_permissions(self) -> dict:
        """Return all roles with their permissions and full permission list.

        Returns dict with 'all_permissions' and 'roles' keys.
        """
        all_perms = await self.permission_repo.list_all_permissions()
        roles = ["user", "expert", "admin"]

        role_data = []
        for role in roles:
            perms = await self.permission_repo.get_role_permissions(role)
            role_data.append({"role": role, "permissions": perms})

        return {
            "all_permissions": [
                {
                    "code": p.code,
                    "name": p.name,
                    "description": p.description,
                }
                for p in all_perms
            ],
            "roles": role_data,
        }

    async def update_role_permissions(
        self, role: str, permission_codes: list[str]
    ) -> list[str]:
        """Replace role's permissions. Validates all codes exist.

        Returns the updated list of permission codes.
        Raises ValueError if any permission code is invalid.
        """
        # Validate role
        if role not in ("user", "expert", "admin"):
            raise ValueError(f"Invalid role: {role}")

        # Validate all permission codes exist
        for code in permission_codes:
            exists = await self.permission_repo.check_permission_exists(code)
            if not exists:
                raise ValueError(f"Unknown permission code: {code}")

        await self.permission_repo.set_role_permissions(role, permission_codes)
        return permission_codes

    async def get_user_effective_permissions(
        self, user_id: int, role: str
    ) -> dict:
        """Return effective permissions (role defaults + overrides applied).

        Returns dict with role_permissions, overrides, and effective lists.
        """
        role_perms = await self.permission_repo.get_role_permissions(role)
        overrides = await self.permission_repo.get_user_overrides(user_id)

        # Build override map: code -> granted
        override_map: dict[str, bool] = {}
        for ov in overrides:
            override_map[ov.permission_code] = ov.granted

        # Compute effective permissions
        effective = set(role_perms)
        for code, granted in override_map.items():
            if granted:
                effective.add(code)
            else:
                effective.discard(code)

        return {
            "user_id": user_id,
            "role": role,
            "role_permissions": sorted(role_perms),
            "overrides": [
                {"code": ov.permission_code, "granted": ov.granted}
                for ov in overrides
            ],
            "effective": sorted(effective),
        }

    async def get_user_overrides(self, user_id: int) -> list[dict]:
        """Return list of user-specific overrides."""
        overrides = await self.permission_repo.get_user_overrides(user_id)
        return [
            {"code": ov.permission_code, "granted": ov.granted}
            for ov in overrides
        ]

    async def update_user_overrides(
        self, user_id: int, overrides: list[dict]
    ) -> list[dict]:
        """Replace user's permission overrides. Validates all codes exist.

        Args:
            user_id: Target user ID.
            overrides: List of dicts with 'code' and 'granted' keys.

        Returns the updated list of overrides.
        Raises ValueError if any permission code is invalid.
        """
        # Validate all permission codes exist
        for override in overrides:
            exists = await self.permission_repo.check_permission_exists(
                override["code"]
            )
            if not exists:
                raise ValueError(f"Unknown permission code: {override['code']}")

        await self.permission_repo.set_user_overrides(user_id, overrides)
        return overrides
