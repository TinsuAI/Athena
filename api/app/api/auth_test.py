"""Tests for auth API endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.user import UserResponse


class TestRegisterEndpoint:
    """Tests for POST /api/auth/register."""

    @pytest.mark.asyncio
    async def test_register_success(self):
        """Test successful registration returns 200 with user data (AC #1)."""
        from app.api.auth import register
        from app.schemas.user import UserCreate

        mock_db = AsyncMock()
        user_data = UserCreate(email="new@example.com", password="securepass123")

        with patch("app.api.auth.AuthService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.register_user.return_value = UserResponse(
                id=1,
                email="new@example.com",
                role="user",
                created_at="2026-02-15T00:00:00+00:00",
            )
            mock_service_class.return_value = mock_service

            response = await register(user_data=user_data, db=mock_db)

        assert response["success"] is True
        assert response["data"]["id"] == 1
        assert response["data"]["email"] == "new@example.com"
        assert response["data"]["role"] == "user"
        assert response["error"] is None

    @pytest.mark.asyncio
    async def test_register_duplicate_email_409(self):
        """Test registration with existing email returns 409 error (AC #2)."""
        from app.api.auth import register
        from app.schemas.user import UserCreate

        mock_db = AsyncMock()
        user_data = UserCreate(email="existing@example.com", password="securepass123")

        with patch("app.api.auth.AuthService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.register_user.return_value = None
            mock_service_class.return_value = mock_service

            response = await register(user_data=user_data, db=mock_db)

        assert response["success"] is False
        assert response["error"]["status"] == 409
        assert "already exists" in response["error"]["detail"]

    def test_register_invalid_email_rejected(self):
        """Test registration with invalid email format is rejected by schema (AC #3)."""
        from pydantic import ValidationError
        from app.schemas.user import UserCreate

        with pytest.raises(ValidationError) as exc_info:
            UserCreate(email="not-an-email", password="securepass123")

        errors = exc_info.value.errors()
        assert any("email" in str(e).lower() for e in errors)

    def test_register_short_password_rejected(self):
        """Test registration with short password is rejected by schema (AC #4)."""
        from pydantic import ValidationError
        from app.schemas.user import UserCreate

        with pytest.raises(ValidationError) as exc_info:
            UserCreate(email="test@example.com", password="short")

        errors = exc_info.value.errors()
        assert any("8" in str(e) for e in errors)


class TestLoginEndpoint:
    """Tests for POST /api/auth/login."""

    @pytest.mark.asyncio
    async def test_login_success(self):
        """Test successful login returns user data."""
        from app.api.auth import login
        from app.schemas.user import UserLogin

        mock_db = AsyncMock()
        credentials = UserLogin(email="test@example.com", password="securepass123")

        with patch("app.api.auth.AuthService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.authenticate_user.return_value = UserResponse(
                id=1,
                email="test@example.com",
                role="user",
                created_at="2026-02-15T00:00:00+00:00",
            )
            mock_service_class.return_value = mock_service

            response = await login(credentials=credentials, db=mock_db)

        assert response["success"] is True
        assert response["data"]["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self):
        """Test login with wrong credentials returns 401 error."""
        from app.api.auth import login
        from app.schemas.user import UserLogin

        mock_db = AsyncMock()
        credentials = UserLogin(email="test@example.com", password="wrongpassword")

        with patch("app.api.auth.AuthService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.authenticate_user.return_value = None
            mock_service_class.return_value = mock_service

            response = await login(credentials=credentials, db=mock_db)

        assert response["success"] is False
        assert response["error"]["status"] == 401
        assert "Invalid" in response["error"]["detail"]


    @pytest.mark.asyncio
    async def test_login_inactive_user_returns_403_with_deactivated_message(self):
        """Test login with inactive user returns 403 with deactivated message."""
        from app.api.auth import login
        from app.schemas.user import UserLogin
        from app.services.auth_service import InactiveUserError

        mock_db = AsyncMock()
        credentials = UserLogin(email="inactive@example.com", password="securepass123")

        with patch("app.api.auth.AuthService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.authenticate_user.side_effect = InactiveUserError(
                "Account has been deactivated"
            )
            mock_service_class.return_value = mock_service

            response = await login(credentials=credentials, db=mock_db)

        assert response["success"] is False
        assert response["error"]["status"] == 403
        assert "Tai khoan da bi vo hieu hoa" in response["error"]["detail"]


class TestForgotPasswordEndpoint:
    """Tests for POST /api/auth/forgot-password."""

    @pytest.mark.asyncio
    async def test_forgot_password_valid_email(self):
        """Test forgot-password with valid email returns success."""
        from app.api.auth import forgot_password
        from app.schemas.user import PasswordResetRequest

        mock_db = AsyncMock()
        mock_settings = MagicMock()
        mock_redis = AsyncMock()
        mock_redis.incr.return_value = 1  # First request (not rate limited)
        data = PasswordResetRequest(email="user@example.com")

        with patch("app.api.auth.AuthService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.request_password_reset.return_value = True
            mock_service_class.return_value = mock_service

            response = await forgot_password(
                data=data, db=mock_db, settings=mock_settings, redis=mock_redis
            )

        assert response["success"] is True
        assert "reset link" in response["data"]["message"].lower()
        mock_service.request_password_reset.assert_awaited_once_with("user@example.com")

    @pytest.mark.asyncio
    async def test_forgot_password_unknown_email_still_success(self):
        """Test forgot-password with unknown email still returns success (no enumeration)."""
        from app.api.auth import forgot_password
        from app.schemas.user import PasswordResetRequest

        mock_db = AsyncMock()
        mock_settings = MagicMock()
        mock_redis = AsyncMock()
        mock_redis.incr.return_value = 1
        data = PasswordResetRequest(email="unknown@example.com")

        with patch("app.api.auth.AuthService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.request_password_reset.return_value = True
            mock_service_class.return_value = mock_service

            response = await forgot_password(
                data=data, db=mock_db, settings=mock_settings, redis=mock_redis
            )

        assert response["success"] is True
        assert "reset link" in response["data"]["message"].lower()

    def test_forgot_password_invalid_email_rejected(self):
        """Test forgot-password with invalid email is rejected by schema."""
        from pydantic import ValidationError
        from app.schemas.user import PasswordResetRequest

        with pytest.raises(ValidationError) as exc_info:
            PasswordResetRequest(email="not-an-email")

        errors = exc_info.value.errors()
        assert any("email" in str(e).lower() for e in errors)

    @pytest.mark.asyncio
    async def test_forgot_password_rate_limited(self):
        """Test forgot-password rate limiting after 3 requests (via Redis)."""
        from app.api.auth import forgot_password
        from app.schemas.user import PasswordResetRequest

        mock_db = AsyncMock()
        mock_settings = MagicMock()
        mock_redis = AsyncMock()
        data = PasswordResetRequest(email="ratelimit@example.com")

        with patch("app.api.auth.AuthService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.request_password_reset.return_value = True
            mock_service_class.return_value = mock_service

            # Simulate 4th request (count > 3, rate limited)
            mock_redis.incr.return_value = 4

            response = await forgot_password(
                data=data, db=mock_db, settings=mock_settings, redis=mock_redis
            )

        assert response["success"] is False
        assert response["error"]["status"] == 429

    @pytest.mark.asyncio
    async def test_forgot_password_email_send_failure(self):
        """Test forgot-password returns error when email service fails."""
        from app.api.auth import forgot_password
        from app.schemas.user import PasswordResetRequest

        mock_db = AsyncMock()
        mock_settings = MagicMock()
        mock_redis = AsyncMock()
        mock_redis.incr.return_value = 1
        data = PasswordResetRequest(email="user@example.com")

        with patch("app.api.auth.AuthService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.request_password_reset.return_value = False  # Email failed
            mock_service_class.return_value = mock_service

            response = await forgot_password(
                data=data, db=mock_db, settings=mock_settings, redis=mock_redis
            )

        assert response["success"] is False
        assert response["error"]["status"] == 503
        assert "email" in response["error"]["detail"].lower()


class TestResetPasswordEndpoint:
    """Tests for POST /api/auth/reset-password."""

    @pytest.mark.asyncio
    async def test_reset_password_success(self):
        """Test reset-password with valid token returns success."""
        from app.api.auth import reset_password
        from app.schemas.user import PasswordResetConfirm

        mock_db = AsyncMock()
        data = PasswordResetConfirm(
            token="valid-token",
            password="newpassword123",
            password_confirm="newpassword123",
        )

        with patch("app.api.auth.AuthService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.reset_password.return_value = True
            mock_service_class.return_value = mock_service

            response = await reset_password(data=data, db=mock_db)

        assert response["success"] is True
        assert "reset successfully" in response["data"]["message"].lower()

    @pytest.mark.asyncio
    async def test_reset_password_expired_token(self):
        """Test reset-password with expired token returns error."""
        from app.api.auth import reset_password
        from app.schemas.user import PasswordResetConfirm

        mock_db = AsyncMock()
        data = PasswordResetConfirm(
            token="expired-token",
            password="newpassword123",
            password_confirm="newpassword123",
        )

        with patch("app.api.auth.AuthService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.reset_password.return_value = False
            mock_service_class.return_value = mock_service

            response = await reset_password(data=data, db=mock_db)

        assert response["success"] is False
        assert response["error"]["status"] == 400
        assert "expired or is invalid" in response["error"]["detail"].lower()

    def test_reset_password_mismatched_passwords_rejected(self):
        """Test reset-password with mismatched passwords is rejected by schema."""
        from pydantic import ValidationError
        from app.schemas.user import PasswordResetConfirm

        with pytest.raises(ValidationError) as exc_info:
            PasswordResetConfirm(
                token="some-token",
                password="newpassword123",
                password_confirm="differentpassword",
            )

        errors = exc_info.value.errors()
        assert any("match" in str(e).lower() for e in errors)
