"""Admin service for user management business logic."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.user_repository import UserRepository
from app.schemas.admin import UserListItem, UserListResponse
from app.schemas.user import UserResponse


class AdminService:
    """Service for admin user management operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.audit_repo = AuditLogRepository(session)

    async def list_users(self, page: int = 1, per_page: int = 20) -> dict:
        """Return paginated user list."""
        users, total = await self.user_repo.list_all(page, per_page)
        return UserListResponse(
            items=[
                UserListItem(
                    id=u.id,
                    email=u.email,
                    role=u.role,
                    created_at=u.created_at,
                )
                for u in users
            ],
            total=total,
            page=page,
            per_page=per_page,
            pages=(total + per_page - 1) // per_page,
        ).model_dump(mode="json")

    async def update_user_role(
        self, admin_user_id: int, target_user_id: int, new_role: str
    ) -> UserResponse | None:
        """Update a user's role and create audit log entry.

        Returns UserResponse on success, None if target user not found.
        Raises ValueError if admin tries to change own role.
        """
        if admin_user_id == target_user_id:
            raise ValueError("Cannot change your own role")

        # Check target exists
        target = await self.user_repo.get_by_id(target_user_id)
        if target is None:
            return None

        old_role = target.role

        # Update role
        updated = await self.user_repo.update_role(target_user_id, new_role)

        # Verify update succeeded before creating audit log
        if updated is None:
            return None

        # Create audit log entry only after successful update (NFR-SEC5)
        await self.audit_repo.create(
            admin_user_id=admin_user_id,
            action="role_change",
            target_user_id=target_user_id,
            details={"old_role": old_role, "new_role": new_role},
        )

        return UserResponse(
            id=updated.id,
            email=updated.email,
            role=updated.role,
            created_at=updated.created_at,
        )
