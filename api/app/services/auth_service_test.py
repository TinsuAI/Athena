"""Tests for auth service."""

import bcrypt
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.user import User
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService, hash_password, verify_password


class TestPasswordHashing:
    """Tests for password hashing utilities."""

    def test_hash_password_returns_bcrypt_hash(self):
        """Test that hash_password returns a valid bcrypt hash."""
        hashed = hash_password("testpassword")
        assert hashed.startswith("$2b$")

    def test_hash_password_uses_sufficient_rounds(self):
        """Test that bcrypt cost factor is >= 10 (AC #5)."""
        hashed = hash_password("testpassword")
        # bcrypt hash format: $2b$rounds$salt+hash
        rounds = int(hashed.split("$")[2])
        assert rounds >= 10

    def test_hash_password_different_each_time(self):
        """Test that hashing the same password produces different hashes (unique salts)."""
        hash1 = hash_password("testpassword")
        hash2 = hash_password("testpassword")
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Test that verify_password returns True for correct password."""
        hashed = hash_password("mypassword123")
        assert verify_password("mypassword123", hashed) is True

    def test_verify_password_incorrect(self):
        """Test that verify_password returns False for wrong password."""
        hashed = hash_password("mypassword123")
        assert verify_password("wrongpassword", hashed) is False


class TestAuthServiceRegister:
    """Tests for AuthService.register_user."""

    @pytest.mark.asyncio
    async def test_register_user_success(self):
        """Test successful user registration returns UserResponse."""
        session = AsyncMock()

        with patch("app.services.auth_service.UserRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_by_email.return_value = None

            mock_user = MagicMock(spec=User)
            mock_user.id = 1
            mock_user.email = "new@example.com"
            mock_user.role = "user"
            mock_user.created_at = "2026-02-15T00:00:00+00:00"
            mock_repo.create.return_value = mock_user
            mock_repo_class.return_value = mock_repo

            service = AuthService(session)
            data = UserCreate(email="new@example.com", password="securepass123")
            result = await service.register_user(data)

        assert result is not None
        assert result.id == 1
        assert result.email == "new@example.com"
        assert result.role == "user"
        mock_repo.get_by_email.assert_awaited_once_with("new@example.com")
        mock_repo.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self):
        """Test registration with existing email returns None (AC #2)."""
        session = AsyncMock()

        with patch("app.services.auth_service.UserRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            existing = MagicMock(spec=User)
            existing.email = "existing@example.com"
            mock_repo.get_by_email.return_value = existing
            mock_repo_class.return_value = mock_repo

            service = AuthService(session)
            data = UserCreate(email="existing@example.com", password="securepass123")
            result = await service.register_user(data)

        assert result is None
        mock_repo.create.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_register_user_default_role(self):
        """Test that registered user gets 'user' role by default (AC #5)."""
        session = AsyncMock()

        with patch("app.services.auth_service.UserRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_by_email.return_value = None

            mock_user = MagicMock(spec=User)
            mock_user.id = 2
            mock_user.email = "test@example.com"
            mock_user.role = "user"
            mock_user.created_at = "2026-02-15T00:00:00+00:00"
            mock_repo.create.return_value = mock_user
            mock_repo_class.return_value = mock_repo

            service = AuthService(session)
            data = UserCreate(email="test@example.com", password="securepass123")
            result = await service.register_user(data)

        assert result is not None
        assert result.role == "user"

        # Verify the User model was created with role="user"
        create_call = mock_repo.create.call_args[0][0]
        assert create_call.role == "user"


class TestAuthServiceAuthenticate:
    """Tests for AuthService.authenticate_user."""

    @pytest.mark.asyncio
    async def test_authenticate_success(self):
        """Test successful authentication returns UserResponse."""
        session = AsyncMock()
        hashed = hash_password("securepass123")

        with patch("app.services.auth_service.UserRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_user = MagicMock(spec=User)
            mock_user.id = 1
            mock_user.email = "test@example.com"
            mock_user.password_hash = hashed
            mock_user.role = "user"
            mock_user.created_at = "2026-02-15T00:00:00+00:00"
            mock_repo.get_by_email.return_value = mock_user
            mock_repo_class.return_value = mock_repo

            service = AuthService(session)
            result = await service.authenticate_user("test@example.com", "securepass123")

        assert result is not None
        assert result.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_authenticate_wrong_password(self):
        """Test authentication with wrong password returns None."""
        session = AsyncMock()
        hashed = hash_password("correctpassword")

        with patch("app.services.auth_service.UserRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_user = MagicMock(spec=User)
            mock_user.password_hash = hashed
            mock_repo.get_by_email.return_value = mock_user
            mock_repo_class.return_value = mock_repo

            service = AuthService(session)
            result = await service.authenticate_user("test@example.com", "wrongpassword")

        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_nonexistent_user(self):
        """Test authentication with nonexistent email returns None."""
        session = AsyncMock()

        with patch("app.services.auth_service.UserRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_by_email.return_value = None
            mock_repo_class.return_value = mock_repo

            service = AuthService(session)
            result = await service.authenticate_user("nobody@example.com", "anypassword")

        assert result is None
