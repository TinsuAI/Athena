"""Repository for user data access."""

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Repository for users database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user: User) -> User:
        """Create a new user."""
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_by_email(self, email: str) -> User | None:
        """Find a user by email address."""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        """Find a user by primary key ID."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_password(self, user_id: int, password_hash: str) -> None:
        """Update a user's password hash."""
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(password_hash=password_hash)
        )
        await self.session.flush()

    async def update_user(self, user_id: int, **fields: str) -> User | None:
        """Update user fields (email and/or role). Returns updated user or None."""
        if not fields:
            return await self.get_by_id(user_id)
        await self.session.execute(
            update(User).where(User.id == user_id).values(**fields)
        )
        await self.session.flush()
        return await self.get_by_id(user_id)

    async def update_status(self, user_id: int, is_active: bool) -> User | None:
        """Update user is_active status. Returns updated user or None."""
        await self.session.execute(
            update(User).where(User.id == user_id).values(is_active=is_active)
        )
        await self.session.flush()
        return await self.get_by_id(user_id)

    async def list_all(self, page: int, per_page: int, search: str = "") -> tuple[list[User], int]:
        """Return paginated user list with total count, optionally filtered by email."""
        base_query = select(User)
        count_query = select(func.count(User.id))

        if search:
            base_query = base_query.where(User.email.ilike(f"%{search}%"))
            count_query = count_query.where(User.email.ilike(f"%{search}%"))

        count_result = await self.session.execute(count_query)
        total = count_result.scalar_one()

        offset = (page - 1) * per_page
        result = await self.session.execute(
            base_query.order_by(User.id).offset(offset).limit(per_page)
        )
        users = list(result.scalars().all())

        return users, total

    async def update_role(self, user_id: int, role: str) -> User | None:
        """Update a user's role. Returns updated user or None if not found."""
        await self.session.execute(
            update(User).where(User.id == user_id).values(role=role)
        )
        await self.session.flush()
        return await self.get_by_id(user_id)
