"""Admin service for user management business logic."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.user_repository import UserRepository
from app.schemas.admin import UserListItem, UserListResponse
from app.schemas.user import UserResponse
from app.services.auth_service import hash_password


class AdminService:
    """Service for admin user management operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.audit_repo = AuditLogRepository(session)

    async def list_users(self, page: int = 1, per_page: int = 20, search: str = "") -> dict:
        """Return paginated user list, optionally filtered by email search."""
        users, total = await self.user_repo.list_all(page, per_page, search)
        return UserListResponse(
            items=[
                UserListItem(
                    id=u.id,
                    email=u.email,
                    role=u.role,
                    is_active=u.is_active,
                    created_at=u.created_at,
                )
                for u in users
            ],
            total=total,
            page=page,
            per_page=per_page,
            pages=(total + per_page - 1) // per_page,
        ).model_dump(mode="json")

    async def create_user(
        self, admin_user_id: int, email: str, password: str, role: str
    ) -> dict | None:
        """Create a new user. Returns None if email already exists."""
        existing = await self.user_repo.get_by_email(email)
        if existing is not None:
            return None

        user = User(email=email, password_hash=hash_password(password), role=role)
        created = await self.user_repo.create(user)

        await self.audit_repo.create(
            admin_user_id=admin_user_id,
            action="user_created",
            target_user_id=created.id,
            details={"email": email, "role": role},
        )

        return UserListItem(
            id=created.id,
            email=created.email,
            role=created.role,
            is_active=created.is_active,
            created_at=created.created_at,
        ).model_dump(mode="json")

    async def update_user(
        self,
        admin_user_id: int,
        target_user_id: int,
        email: str | None = None,
        role: str | None = None,
    ) -> dict | str:
        """Update user email and/or role. Returns dict on success, error string on failure."""
        target = await self.user_repo.get_by_id(target_user_id)
        if target is None:
            return "not_found"

        # Check email uniqueness if changing
        if email is not None and email != target.email:
            existing = await self.user_repo.get_by_email(email)
            if existing is not None:
                return "email_exists"

        fields: dict[str, str] = {}
        if email is not None:
            fields["email"] = email
        if role is not None:
            fields["role"] = role

        old_email = target.email
        old_role = target.role

        updated = await self.user_repo.update_user(target_user_id, **fields)
        if updated is None:
            return "not_found"

        await self.audit_repo.create(
            admin_user_id=admin_user_id,
            action="user_updated",
            target_user_id=target_user_id,
            details={
                "old_email": old_email,
                "new_email": email or old_email,
                "old_role": old_role,
                "new_role": role or old_role,
            },
        )

        return UserListItem(
            id=updated.id,
            email=updated.email,
            role=updated.role,
            is_active=updated.is_active,
            created_at=updated.created_at,
        ).model_dump(mode="json")

    async def toggle_user_status(
        self, admin_user_id: int, target_user_id: int, is_active: bool
    ) -> dict | str:
        """Toggle user active status. Returns dict on success, error string on failure."""
        if admin_user_id == target_user_id:
            return "self_deactivation"

        target = await self.user_repo.get_by_id(target_user_id)
        if target is None:
            return "not_found"

        updated = await self.user_repo.update_status(target_user_id, is_active)
        if updated is None:
            return "not_found"

        await self.audit_repo.create(
            admin_user_id=admin_user_id,
            action="user_status_changed",
            target_user_id=target_user_id,
            details={"is_active": is_active},
        )

        return UserListItem(
            id=updated.id,
            email=updated.email,
            role=updated.role,
            is_active=updated.is_active,
            created_at=updated.created_at,
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
