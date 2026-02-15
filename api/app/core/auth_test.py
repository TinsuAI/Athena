"""Tests for JWT validation middleware."""

import pytest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.core.auth import get_current_user


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
