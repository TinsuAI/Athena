"""Authentication service for user registration and login."""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.user import User
from app.repositories.password_reset_repository import PasswordResetRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserResponse
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt with cost factor 12."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


class AuthService:
    """Service for authentication business logic."""

    def __init__(self, session: AsyncSession, settings: Settings | None = None):
        self.session = session
        self.repo = UserRepository(session)
        self.reset_repo = PasswordResetRepository(session)
        self.settings = settings

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

    async def request_password_reset(self, email: str) -> bool:
        """Request a password reset for the given email.

        Returns True if email was sent successfully, False if email send failed.
        Returns True for non-existent emails (no enumeration - we just don't send).
        Generates a secure token, stores its hash, and sends the reset email.
        """
        user = await self.repo.get_by_email(email)
        if user is None:
            # Return True to prevent email enumeration (pretend we sent it)
            return True

        # Invalidate any existing unused tokens for this user
        await self.reset_repo.invalidate_all_for_user(user.id)

        # Generate secure token and hash it
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        # Store hashed token in database
        await self.reset_repo.create(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        # Send reset email
        if self.settings:
            reset_url = f"{self.settings.frontend_url}/reset-password?token={token}"
            email_service = EmailService(self.settings)
            try:
                await email_service.send_password_reset_email(user.email, reset_url)
                return True
            except Exception:
                logger.exception("Failed to send password reset email to %s", email)
                return False

        return True

    async def reset_password(self, token: str, new_password: str) -> bool:
        """Reset a user's password using a valid reset token.

        Returns True on success, False if token is invalid/expired/used.
        """
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        reset_token = await self.reset_repo.get_by_token_hash(token_hash)

        if reset_token is None:
            return False

        # Check if token is expired
        if reset_token.expires_at < datetime.now(timezone.utc):
            return False

        # Check if token is already used
        if reset_token.used_at is not None:
            return False

        # Update user's password
        new_hash = hash_password(new_password)
        await self.repo.update_password(reset_token.user_id, new_hash)

        # Mark token as used
        await self.reset_repo.mark_used(reset_token.id)

        # Invalidate all other tokens for this user
        await self.reset_repo.invalidate_all_for_user(reset_token.user_id)

        return True
