"""Authentication service for user registration and login."""

import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserResponse


def hash_password(password: str) -> str:
    """Hash a password using bcrypt with cost factor 12."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


class AuthService:
    """Service for authentication business logic."""

    def __init__(self, session: AsyncSession):
        self.repo = UserRepository(session)

    async def register_user(self, data: UserCreate) -> UserResponse | None:
        """Register a new user.

        Returns UserResponse on success, None if email already exists.
        """
        existing = await self.repo.get_by_email(data.email)
        if existing is not None:
            return None

        user = User(
            email=data.email,
            password_hash=hash_password(data.password),
            role="user",
        )
        created = await self.repo.create(user)

        return UserResponse(
            id=created.id,
            email=created.email,
            role=created.role,
            created_at=created.created_at,
        )

    async def authenticate_user(self, email: str, password: str) -> UserResponse | None:
        """Authenticate a user by email and password.

        Returns UserResponse on success, None if credentials are invalid.

        Note: Uses constant-time password verification to prevent timing attacks.
        """
        user = await self.repo.get_by_email(email)

        # Always verify password even if user doesn't exist (timing attack mitigation)
        # Use a dummy hash if user not found to maintain constant time
        dummy_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5UpJFUjJJaO4i"
        password_hash = user.password_hash if user is not None else dummy_hash

        password_valid = verify_password(password, password_hash)

        # Only return user if both user exists AND password is valid
        if user is not None and password_valid:
            return UserResponse(
                id=user.id,
                email=user.email,
                role=user.role,
                created_at=user.created_at,
            )

        return None
