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

    async def list_all(self, page: int, per_page: int) -> tuple[list[User], int]:
        """Return paginated user list with total count."""
        # Get total count
        count_result = await self.session.execute(select(func.count(User.id)))
        total = count_result.scalar_one()

        # Get paginated users
        offset = (page - 1) * per_page
        result = await self.session.execute(
            select(User).order_by(User.id).offset(offset).limit(per_page)
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
