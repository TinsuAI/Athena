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

    @pytest.mark.asyncio
    async def test_list_all_returns_paginated_results(self):
        """Test list_all returns paginated users and total count."""
        repo, session = self._make_repo()
        user1 = User(id=1, email="a@example.com", password_hash="h", role="user")
        user2 = User(id=2, email="b@example.com", password_hash="h", role="admin")

        # First call: count query
        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 2

        # Second call: paginated query
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [user1, user2]
        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value = mock_scalars

        session.execute.side_effect = [mock_count_result, mock_list_result]

        users, total = await repo.list_all(page=1, per_page=20)

        assert total == 2
        assert len(users) == 2
        assert users[0] is user1
        assert users[1] is user2

    @pytest.mark.asyncio
    async def test_list_all_pagination(self):
        """Test list_all page 2 returns different results."""
        repo, session = self._make_repo()
        user3 = User(id=3, email="c@example.com", password_hash="h", role="user")

        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 3

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [user3]
        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value = mock_scalars

        session.execute.side_effect = [mock_count_result, mock_list_result]

        users, total = await repo.list_all(page=2, per_page=2)

        assert total == 3
        assert len(users) == 1

    @pytest.mark.asyncio
    async def test_list_all_with_search_filters_by_email(self):
        """Test list_all with search parameter filters by email."""
        repo, session = self._make_repo()
        user1 = User(id=1, email="admin@example.com", password_hash="h", role="admin")

        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 1

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [user1]
        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value = mock_scalars

        session.execute.side_effect = [mock_count_result, mock_list_result]

        users, total = await repo.list_all(page=1, per_page=20, search="admin")

        assert total == 1
        assert len(users) == 1
        assert users[0].email == "admin@example.com"
        # Verify execute was called twice (count + query)
        assert session.execute.await_count == 2

    @pytest.mark.asyncio
    async def test_list_all_without_search_returns_all(self):
        """Test list_all without search returns all users."""
        repo, session = self._make_repo()
        user1 = User(id=1, email="a@example.com", password_hash="h", role="user")
        user2 = User(id=2, email="b@example.com", password_hash="h", role="admin")

        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 2

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [user1, user2]
        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value = mock_scalars

        session.execute.side_effect = [mock_count_result, mock_list_result]

        users, total = await repo.list_all(page=1, per_page=20)

        assert total == 2
        assert len(users) == 2

    @pytest.mark.asyncio
    async def test_update_role_changes_role(self):
        """Test update_role changes user role and returns updated user."""
        repo, session = self._make_repo()
        updated_user = User(id=1, email="a@example.com", password_hash="h", role="admin")

        # First call: execute update
        # Second call: get_by_id query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = updated_user
        session.execute.side_effect = [MagicMock(), mock_result]

        result = await repo.update_role(1, "admin")

        assert result is updated_user
        assert result.role == "admin"

    @pytest.mark.asyncio
    async def test_update_role_not_found(self):
        """Test update_role with non-existent user returns None."""
        repo, session = self._make_repo()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.side_effect = [MagicMock(), mock_result]

        result = await repo.update_role(999, "admin")

        assert result is None

    @pytest.mark.asyncio
    async def test_update_user_changes_email_and_role(self):
        """Test update_user changes email and role fields."""
        repo, session = self._make_repo()
        updated_user = User(id=1, email="new@example.com", password_hash="h", role="expert")

        # First call: execute update
        # Second call: get_by_id query (via flush + get_by_id)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = updated_user
        session.execute.side_effect = [MagicMock(), mock_result]

        result = await repo.update_user(1, email="new@example.com", role="expert")

        assert result is updated_user
        assert result.email == "new@example.com"
        assert result.role == "expert"
        # Verify flush was called (update triggers flush)
        session.flush.assert_awaited()

    @pytest.mark.asyncio
    async def test_update_user_no_fields_returns_user(self):
        """Test update_user with no fields returns the existing user."""
        repo, session = self._make_repo()
        existing_user = User(id=1, email="a@example.com", password_hash="h", role="user")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_user
        session.execute.return_value = mock_result

        result = await repo.update_user(1)

        assert result is existing_user
        # Flush should NOT be called since no update was made
        session.flush.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_update_status_changes_is_active(self):
        """Test update_status changes the is_active field."""
        repo, session = self._make_repo()
        updated_user = User(id=1, email="a@example.com", password_hash="h", role="user")
        updated_user.is_active = False

        # First call: execute update
        # Second call: get_by_id query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = updated_user
        session.execute.side_effect = [MagicMock(), mock_result]

        result = await repo.update_status(1, False)

        assert result is updated_user
        assert result.is_active is False
        session.flush.assert_awaited()
