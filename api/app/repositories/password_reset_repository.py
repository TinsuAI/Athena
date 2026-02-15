"""Repository for password reset token data access."""

from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.password_reset_token import PasswordResetToken


class PasswordResetRepository:
    """Repository for password_reset_tokens database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self, user_id: int, token_hash: str, expires_at: datetime
    ) -> PasswordResetToken:
        """Create a new password reset token record."""
        token = PasswordResetToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.session.add(token)
        await self.session.flush()
        return token

    async def get_by_token_hash(self, token_hash: str) -> PasswordResetToken | None:
        """Find a password reset token by its SHA-256 hash."""
        result = await self.session.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.token_hash == token_hash
            )
        )
        return result.scalar_one_or_none()

    async def mark_used(self, token_id: int) -> None:
        """Mark a token as used by setting used_at to current time."""
        from sqlalchemy import func

        await self.session.execute(
            update(PasswordResetToken)
            .where(PasswordResetToken.id == token_id)
            .values(used_at=func.now())
        )
        await self.session.flush()

    async def invalidate_all_for_user(self, user_id: int) -> None:
        """Invalidate all unused tokens for a user by setting used_at."""
        from sqlalchemy import func

        await self.session.execute(
            update(PasswordResetToken)
            .where(
                PasswordResetToken.user_id == user_id,
                PasswordResetToken.used_at.is_(None),
            )
            .values(used_at=func.now())
        )
        await self.session.flush()
