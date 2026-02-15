"""Tests for user repository."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.models.user import User
from app.repositories.user_repository import UserRepository


class TestUserRepository:
    """Tests for UserRepository."""

    def _make_repo(self) -> tuple[UserRepository, AsyncMock]:
        """Create a UserRepository with a mock session."""
        session = AsyncMock()
        repo = UserRepository(session)
        return repo, session

    @pytest.mark.asyncio
    async def test_create_user(self):
        """Test creating a new user adds it to session and flushes."""
        repo, session = self._make_repo()
        user = User(email="test@example.com", password_hash="hashed", role="user")

        result = await repo.create(user)

        session.add.assert_called_once_with(user)
        session.flush.assert_awaited_once()
        assert result is user

    @pytest.mark.asyncio
    async def test_get_by_email_found(self):
        """Test finding a user by email when user exists."""
        repo, session = self._make_repo()
        mock_user = User(id=1, email="test@example.com", password_hash="hashed", role="user")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        session.execute.return_value = mock_result

        result = await repo.get_by_email("test@example.com")

        assert result is mock_user
        session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_by_email_not_found(self):
        """Test finding a user by email when user does not exist."""
        repo, session = self._make_repo()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        result = await repo.get_by_email("nonexistent@example.com")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_found(self):
        """Test finding a user by ID when user exists."""
        repo, session = self._make_repo()
        mock_user = User(id=42, email="test@example.com", password_hash="hashed", role="user")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        session.execute.return_value = mock_result

        result = await repo.get_by_id(42)

        assert result is mock_user

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self):
        """Test finding a user by ID when user does not exist."""
        repo, session = self._make_repo()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        result = await repo.get_by_id(999)

        assert result is None
