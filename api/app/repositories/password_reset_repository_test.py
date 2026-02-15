"""Tests for password reset repository."""

from datetime import datetime, timezone

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.password_reset_token import PasswordResetToken
from app.repositories.password_reset_repository import PasswordResetRepository


class TestPasswordResetRepository:
    """Tests for PasswordResetRepository."""

    @pytest.mark.asyncio
    async def test_create_token(self):
        """Test creating a password reset token record."""
        session = AsyncMock()
        repo = PasswordResetRepository(session)
        expires = datetime(2026, 2, 15, 12, 0, 0, tzinfo=timezone.utc)

        token = await repo.create(
            user_id=1,
            token_hash="abc123hash",
            expires_at=expires,
        )

        session.add.assert_called_once()
        session.flush.assert_awaited_once()
        assert token.user_id == 1
        assert token.token_hash == "abc123hash"
        assert token.expires_at == expires

    @pytest.mark.asyncio
    async def test_get_by_token_hash_found(self):
        """Test finding a token by its hash."""
        session = AsyncMock()
        mock_token = MagicMock(spec=PasswordResetToken)
        mock_token.id = 1
        mock_token.token_hash = "abc123hash"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_token
        session.execute.return_value = mock_result

        repo = PasswordResetRepository(session)
        result = await repo.get_by_token_hash("abc123hash")

        assert result is not None
        assert result.token_hash == "abc123hash"
        session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_by_token_hash_not_found(self):
        """Test getting a token that doesn't exist returns None."""
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        repo = PasswordResetRepository(session)
        result = await repo.get_by_token_hash("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_mark_used(self):
        """Test marking a token as used sets used_at."""
        session = AsyncMock()
        repo = PasswordResetRepository(session)

        await repo.mark_used(token_id=1)

        session.execute.assert_awaited_once()
        session.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_invalidate_all_for_user(self):
        """Test invalidating all unused tokens for a user."""
        session = AsyncMock()
        repo = PasswordResetRepository(session)

        await repo.invalidate_all_for_user(user_id=1)

        session.execute.assert_awaited_once()
        session.flush.assert_awaited_once()
