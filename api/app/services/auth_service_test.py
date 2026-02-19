"""Tests for auth service."""

import hashlib
import bcrypt
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService, InactiveUserError, hash_password, verify_password


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

    @pytest.mark.asyncio
    async def test_authenticate_inactive_user_raises_error(self):
        """Test that inactive user login raises InactiveUserError.

        Note: is_active is checked after password verification to preserve constant-time
        behavior (prevent timing attacks that reveal account existence). The InactiveUserError
        is only raised when both user exists AND password is valid AND is_active=False.
        """
        session = AsyncMock()
        hashed = hash_password("securepass123")

        with patch("app.services.auth_service.UserRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_user = MagicMock(spec=User)
            mock_user.id = 1
            mock_user.email = "inactive@example.com"
            mock_user.password_hash = hashed
            mock_user.role = "user"
            mock_user.is_active = False
            mock_user.created_at = "2026-02-15T00:00:00+00:00"
            mock_repo.get_by_email.return_value = mock_user
            mock_repo_class.return_value = mock_repo

            service = AuthService(session)
            with pytest.raises(InactiveUserError):
                await service.authenticate_user("inactive@example.com", "securepass123")

    @pytest.mark.asyncio
    async def test_authenticate_active_user_succeeds(self):
        """Test that active user login succeeds normally."""
        session = AsyncMock()
        hashed = hash_password("securepass123")

        with patch("app.services.auth_service.UserRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_user = MagicMock(spec=User)
            mock_user.id = 1
            mock_user.email = "active@example.com"
            mock_user.password_hash = hashed
            mock_user.role = "user"
            mock_user.is_active = True
            mock_user.created_at = "2026-02-15T00:00:00+00:00"
            mock_repo.get_by_email.return_value = mock_user
            mock_repo_class.return_value = mock_repo

            service = AuthService(session)
            result = await service.authenticate_user("active@example.com", "securepass123")

        assert result is not None
        assert result.email == "active@example.com"


class TestRequestPasswordReset:
    """Tests for AuthService.request_password_reset."""

    @pytest.mark.asyncio
    async def test_request_reset_existing_email(self):
        """Test password reset with existing email sends email and creates token."""
        session = AsyncMock()
        mock_settings = MagicMock()
        mock_settings.frontend_url = "http://localhost:8979"

        with (
            patch("app.services.auth_service.UserRepository") as mock_user_repo_class,
            patch("app.services.auth_service.PasswordResetRepository") as mock_reset_repo_class,
            patch("app.services.auth_service.EmailService") as mock_email_class,
        ):
            mock_user_repo = AsyncMock()
            mock_user = MagicMock(spec=User)
            mock_user.id = 1
            mock_user.email = "user@example.com"
            mock_user_repo.get_by_email.return_value = mock_user
            mock_user_repo_class.return_value = mock_user_repo

            mock_reset_repo = AsyncMock()
            mock_reset_repo_class.return_value = mock_reset_repo

            mock_email_service = AsyncMock()
            mock_email_class.return_value = mock_email_service

            service = AuthService(session, settings=mock_settings)
            await service.request_password_reset("user@example.com")

        mock_reset_repo.invalidate_all_for_user.assert_awaited_once_with(1)
        mock_reset_repo.create.assert_awaited_once()
        mock_email_service.send_password_reset_email.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_request_reset_nonexistent_email(self):
        """Test password reset with unknown email does nothing (no enumeration)."""
        session = AsyncMock()

        with (
            patch("app.services.auth_service.UserRepository") as mock_user_repo_class,
            patch("app.services.auth_service.PasswordResetRepository") as mock_reset_repo_class,
        ):
            mock_user_repo = AsyncMock()
            mock_user_repo.get_by_email.return_value = None
            mock_user_repo_class.return_value = mock_user_repo

            mock_reset_repo = AsyncMock()
            mock_reset_repo_class.return_value = mock_reset_repo

            service = AuthService(session)
            await service.request_password_reset("nobody@example.com")

        mock_reset_repo.create.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_request_reset_email_failure_does_not_raise(self):
        """Test that email sending failure is logged but doesn't raise."""
        session = AsyncMock()
        mock_settings = MagicMock()
        mock_settings.frontend_url = "http://localhost:8979"

        with (
            patch("app.services.auth_service.UserRepository") as mock_user_repo_class,
            patch("app.services.auth_service.PasswordResetRepository") as mock_reset_repo_class,
            patch("app.services.auth_service.EmailService") as mock_email_class,
        ):
            mock_user_repo = AsyncMock()
            mock_user = MagicMock(spec=User)
            mock_user.id = 1
            mock_user.email = "user@example.com"
            mock_user_repo.get_by_email.return_value = mock_user
            mock_user_repo_class.return_value = mock_user_repo

            mock_reset_repo = AsyncMock()
            mock_reset_repo_class.return_value = mock_reset_repo

            mock_email_service = AsyncMock()
            mock_email_service.send_password_reset_email.side_effect = ConnectionRefusedError()
            mock_email_class.return_value = mock_email_service

            service = AuthService(session, settings=mock_settings)
            # Should not raise
            await service.request_password_reset("user@example.com")

        # Token was still created even though email failed
        mock_reset_repo.create.assert_awaited_once()


class TestResetPassword:
    """Tests for AuthService.reset_password."""

    @pytest.mark.asyncio
    async def test_reset_password_valid_token(self):
        """Test password reset with valid token succeeds."""
        session = AsyncMock()
        token = "valid-token-string"
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        with (
            patch("app.services.auth_service.UserRepository") as mock_user_repo_class,
            patch("app.services.auth_service.PasswordResetRepository") as mock_reset_repo_class,
        ):
            mock_user_repo = AsyncMock()
            mock_user_repo_class.return_value = mock_user_repo

            mock_reset_repo = AsyncMock()
            mock_token = MagicMock(spec=PasswordResetToken)
            mock_token.id = 1
            mock_token.user_id = 42
            mock_token.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
            mock_token.used_at = None
            mock_reset_repo.get_by_token_hash.return_value = mock_token
            mock_reset_repo_class.return_value = mock_reset_repo

            service = AuthService(session)
            result = await service.reset_password(token, "newpassword123")

        assert result is True
        mock_user_repo.update_password.assert_awaited_once()
        mock_reset_repo.mark_used.assert_awaited_once_with(1)
        mock_reset_repo.invalidate_all_for_user.assert_awaited_once_with(42)

    @pytest.mark.asyncio
    async def test_reset_password_expired_token(self):
        """Test password reset with expired token returns False."""
        session = AsyncMock()
        token = "expired-token-string"

        with (
            patch("app.services.auth_service.UserRepository") as mock_user_repo_class,
            patch("app.services.auth_service.PasswordResetRepository") as mock_reset_repo_class,
        ):
            mock_user_repo = AsyncMock()
            mock_user_repo_class.return_value = mock_user_repo

            mock_reset_repo = AsyncMock()
            mock_token = MagicMock(spec=PasswordResetToken)
            mock_token.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
            mock_token.used_at = None
            mock_reset_repo.get_by_token_hash.return_value = mock_token
            mock_reset_repo_class.return_value = mock_reset_repo

            service = AuthService(session)
            result = await service.reset_password(token, "newpassword123")

        assert result is False
        mock_user_repo.update_password.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_reset_password_used_token(self):
        """Test password reset with already-used token returns False."""
        session = AsyncMock()
        token = "used-token-string"

        with (
            patch("app.services.auth_service.UserRepository") as mock_user_repo_class,
            patch("app.services.auth_service.PasswordResetRepository") as mock_reset_repo_class,
        ):
            mock_user_repo = AsyncMock()
            mock_user_repo_class.return_value = mock_user_repo

            mock_reset_repo = AsyncMock()
            mock_token = MagicMock(spec=PasswordResetToken)
            mock_token.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
            mock_token.used_at = datetime.now(timezone.utc) - timedelta(minutes=30)
            mock_reset_repo.get_by_token_hash.return_value = mock_token
            mock_reset_repo_class.return_value = mock_reset_repo

            service = AuthService(session)
            result = await service.reset_password(token, "newpassword123")

        assert result is False
        mock_user_repo.update_password.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_reset_password_invalid_token(self):
        """Test password reset with nonexistent token returns False."""
        session = AsyncMock()
        token = "nonexistent-token"

        with (
            patch("app.services.auth_service.UserRepository") as mock_user_repo_class,
            patch("app.services.auth_service.PasswordResetRepository") as mock_reset_repo_class,
        ):
            mock_user_repo = AsyncMock()
            mock_user_repo_class.return_value = mock_user_repo

            mock_reset_repo = AsyncMock()
            mock_reset_repo.get_by_token_hash.return_value = None
            mock_reset_repo_class.return_value = mock_reset_repo

            service = AuthService(session)
            result = await service.reset_password(token, "newpassword123")

        assert result is False
        mock_user_repo.update_password.assert_not_awaited()
