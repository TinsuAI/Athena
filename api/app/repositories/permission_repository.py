"""Repository for permission data access."""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.permission import Permission, RolePermission, UserPermissionOverride


class PermissionRepository:
    """Repository for permissions, role_permissions, and user_permission_overrides."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_all_permissions(self) -> list[Permission]:
        """Return all permission records."""
        result = await self.session.execute(
            select(Permission).order_by(Permission.code)
        )
        return list(result.scalars().all())

    async def get_role_permissions(self, role: str) -> list[str]:
        """Return permission codes for a role."""
        result = await self.session.execute(
            select(RolePermission.permission_code).where(RolePermission.role == role)
        )
        return list(result.scalars().all())

    async def set_role_permissions(self, role: str, codes: list[str]) -> None:
        """Delete existing and insert new role_permissions for a role."""
        await self.session.execute(
            delete(RolePermission).where(RolePermission.role == role)
        )
        for code in codes:
            self.session.add(RolePermission(role=role, permission_code=code))
        await self.session.flush()

    async def get_user_overrides(
        self, user_id: int
    ) -> list[UserPermissionOverride]:
        """Return user's permission overrides."""
        result = await self.session.execute(
            select(UserPermissionOverride).where(
                UserPermissionOverride.user_id == user_id
            )
        )
        return list(result.scalars().all())

    async def set_user_overrides(
        self, user_id: int, overrides: list[dict]
    ) -> None:
        """Delete existing and insert new user_permission_overrides.

        Args:
            user_id: The user's ID.
            overrides: List of dicts with 'code' and 'granted' keys.
        """
        await self.session.execute(
            delete(UserPermissionOverride).where(
                UserPermissionOverride.user_id == user_id
            )
        )
        for override in overrides:
            self.session.add(
                UserPermissionOverride(
                    user_id=user_id,
                    permission_code=override["code"],
                    granted=override["granted"],
                )
            )
        await self.session.flush()

    async def get_user_override(
        self, user_id: int, permission_code: str
    ) -> UserPermissionOverride | None:
        """Return single override or None."""
        result = await self.session.execute(
            select(UserPermissionOverride).where(
                UserPermissionOverride.user_id == user_id,
                UserPermissionOverride.permission_code == permission_code,
            )
        )
        return result.scalar_one_or_none()

    async def check_permission_exists(self, code: str) -> bool:
        """Validate permission code exists."""
        result = await self.session.execute(
            select(Permission).where(Permission.code == code)
        )
        return result.scalar_one_or_none() is not None
