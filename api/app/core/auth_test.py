"""Tests for JWT validation middleware."""

import pytest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.core.auth import (
    get_current_user,
    get_optional_user,
    require_admin,
    require_authenticated,
    require_expert,
)


class TestGetCurrentUser:
    """Tests for get_current_user dependency."""

    @pytest.mark.asyncio
    async def test_returns_user_from_valid_token(self):
        """Test that valid JWT returns user dict with id, email, role."""
        mock_request = MagicMock()

        with patch("app.core.auth.JWT") as mock_jwt:
            mock_jwt.return_value = {
                "id": "1",
                "email": "test@example.com",
                "role": "user",
                "sub": "test@example.com",
            }

            result = await get_current_user(mock_request)

        assert result["id"] == "1"
        assert result["email"] == "test@example.com"
        assert result["role"] == "user"

    @pytest.mark.asyncio
    async def test_raises_401_on_invalid_token(self):
        """Test that invalid JWT raises 401 HTTPException."""
        mock_request = MagicMock()

        with patch("app.core.auth.JWT") as mock_jwt:
            mock_jwt.side_effect = Exception("Invalid token")

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_request)

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_raises_401_on_missing_token(self):
        """Test that missing JWT raises 401 HTTPException."""
        mock_request = MagicMock()

        with patch("app.core.auth.JWT") as mock_jwt:
            mock_jwt.side_effect = Exception("No token found")

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_request)

            assert exc_info.value.status_code == 401
            assert "Not authenticated" in str(exc_info.value.detail)


class TestRequireAdmin:
    """Tests for require_admin dependency."""

    @pytest.mark.asyncio
    async def test_admin_user_passes(self):
        """Test that admin user passes require_admin check."""
        mock_request = MagicMock()

        with patch("app.core.auth.JWT") as mock_jwt:
            mock_jwt.return_value = {
                "id": "1",
                "email": "admin@example.com",
                "role": "admin",
                "sub": "admin@example.com",
            }

            result = await require_admin(mock_request)

        assert result["id"] == "1"
        assert result["email"] == "admin@example.com"
        assert result["role"] == "admin"

    @pytest.mark.asyncio
    async def test_standard_user_gets_403(self):
        """Test that standard user gets 403 from require_admin."""
        mock_request = MagicMock()

        with patch("app.core.auth.JWT") as mock_jwt:
            mock_jwt.return_value = {
                "id": "2",
                "email": "user@example.com",
                "role": "user",
                "sub": "user@example.com",
            }

            with pytest.raises(HTTPException) as exc_info:
                await require_admin(mock_request)

            assert exc_info.value.status_code == 403
            assert "Admin access required" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_unauthenticated_gets_401(self):
        """Test that unauthenticated user gets 401 from require_admin."""
        mock_request = MagicMock()

        with patch("app.core.auth.JWT") as mock_jwt:
            mock_jwt.side_effect = Exception("No token found")

            with pytest.raises(HTTPException) as exc_info:
                await require_admin(mock_request)

            assert exc_info.value.status_code == 401


class TestRequireAuthenticated:
    """Tests for require_authenticated dependency."""

    @pytest.mark.asyncio
    async def test_valid_user_passes(self):
        """Test that any authenticated user passes require_authenticated."""
        mock_request = MagicMock()

        with patch("app.core.auth.JWT") as mock_jwt:
            mock_jwt.return_value = {
                "id": "1",
                "email": "user@example.com",
                "role": "user",
                "sub": "user@example.com",
            }

            result = await require_authenticated(mock_request)

        assert result["id"] == "1"
        assert result["email"] == "user@example.com"
        assert result["role"] == "user"

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self):
        """Test that unauthenticated user gets 401 from require_authenticated."""
        mock_request = MagicMock()

        with patch("app.core.auth.JWT") as mock_jwt:
            mock_jwt.side_effect = Exception("No token found")

            with pytest.raises(HTTPException) as exc_info:
                await require_authenticated(mock_request)

            assert exc_info.value.status_code == 401


class TestRequireExpert:
    """Tests for require_expert dependency."""

    @pytest.mark.asyncio
    async def test_expert_user_passes(self):
        """Test that expert user passes require_expert check."""
        mock_request = MagicMock()

        with patch("app.core.auth.JWT") as mock_jwt:
            mock_jwt.return_value = {
                "id": "1",
                "email": "expert@example.com",
                "role": "expert",
                "sub": "expert@example.com",
            }

            result = await require_expert(mock_request)

        assert result["id"] == "1"
        assert result["email"] == "expert@example.com"
        assert result["role"] == "expert"

    @pytest.mark.asyncio
    async def test_admin_user_passes(self):
        """Test that admin user also passes require_expert check."""
        mock_request = MagicMock()

        with patch("app.core.auth.JWT") as mock_jwt:
            mock_jwt.return_value = {
                "id": "1",
                "email": "admin@example.com",
                "role": "admin",
                "sub": "admin@example.com",
            }

            result = await require_expert(mock_request)

        assert result["id"] == "1"
        assert result["role"] == "admin"

    @pytest.mark.asyncio
    async def test_standard_user_returns_403(self):
        """Test that standard user gets 403 from require_expert."""
        mock_request = MagicMock()

        with patch("app.core.auth.JWT") as mock_jwt:
            mock_jwt.return_value = {
                "id": "2",
                "email": "user@example.com",
                "role": "user",
                "sub": "user@example.com",
            }

            with pytest.raises(HTTPException) as exc_info:
                await require_expert(mock_request)

            assert exc_info.value.status_code == 403
            assert "Expert access required" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self):
        """Test that unauthenticated user gets 401 from require_expert."""
        mock_request = MagicMock()

        with patch("app.core.auth.JWT") as mock_jwt:
            mock_jwt.side_effect = Exception("No token found")

            with pytest.raises(HTTPException) as exc_info:
                await require_expert(mock_request)

            assert exc_info.value.status_code == 401


class TestGetOptionalUser:
    """Tests for get_optional_user dependency."""

    @pytest.mark.asyncio
    async def test_returns_user_when_authenticated(self):
        """Test that get_optional_user returns user dict when JWT present."""
        mock_request = MagicMock()

        with patch("app.core.auth.JWT") as mock_jwt:
            mock_jwt.return_value = {
                "id": "1",
                "email": "user@example.com",
                "role": "user",
                "sub": "user@example.com",
            }

            result = await get_optional_user(mock_request)

        assert result is not None
        assert result["id"] == "1"
        assert result["email"] == "user@example.com"

    @pytest.mark.asyncio
    async def test_returns_none_when_unauthenticated(self):
        """Test that get_optional_user returns None when no JWT present."""
        mock_request = MagicMock()

        with patch("app.core.auth.JWT") as mock_jwt:
            mock_jwt.side_effect = Exception("No token found")

            result = await get_optional_user(mock_request)

        assert result is None
