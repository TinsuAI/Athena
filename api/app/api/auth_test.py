"""Tests for auth API endpoints."""

import pytest
from unittest.mock import AsyncMock, patch

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
