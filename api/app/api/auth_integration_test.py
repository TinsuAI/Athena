"""Integration tests for auth endpoints with real database."""

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.user import User
from app.services.auth_service import verify_password


class TestRegisterIntegration:
    """Integration tests for user registration with real database."""

    @pytest.mark.asyncio
    async def test_register_creates_user_in_database(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test that registration actually creates user in database with hashed password."""
        response = await async_client.post(
            "/api/auth/register",
            json={"email": "integration@example.com", "password": "securepass123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["email"] == "integration@example.com"
        assert data["data"]["role"] == "user"

        # Verify user exists in database
        result = await db_session.execute(select(User).where(User.email == "integration@example.com"))
        user = result.scalar_one()
        assert user.email == "integration@example.com"
        assert user.password_hash.startswith("$2b$")
        assert verify_password("securepass123", user.password_hash) is True

    @pytest.mark.asyncio
    async def test_register_enforces_unique_email_constraint(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test that database unique constraint prevents duplicate emails."""
        # Create first user
        await async_client.post(
            "/api/auth/register",
            json={"email": "unique@example.com", "password": "password123"},
        )

        # Try to create duplicate
        response = await async_client.post(
            "/api/auth/register",
            json={"email": "unique@example.com", "password": "different456"},
        )

        assert response.status_code == 200  # Envelope format returns 200
        data = response.json()
        assert data["success"] is False
        assert data["error"]["status"] == 409
        assert "already exists" in data["error"]["detail"]

    @pytest.mark.asyncio
    async def test_register_normalizes_email_case(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test that email normalization works end-to-end (Test@Example.COM -> test@example.com)."""
        response = await async_client.post(
            "/api/auth/register",
            json={"email": "Test@Example.COM", "password": "securepass123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["email"] == "test@example.com"

        # Verify normalized in database
        result = await db_session.execute(select(User).where(User.email == "test@example.com"))
        user = result.scalar_one()
        assert user.email == "test@example.com"

        # Verify duplicate with different case is rejected
        response2 = await async_client.post(
            "/api/auth/register",
            json={"email": "TEST@example.com", "password": "other789"},
        )
        data2 = response2.json()
        assert data2["success"] is False
        assert data2["error"]["status"] == 409


class TestLoginIntegration:
    """Integration tests for login endpoint."""

    @pytest.mark.asyncio
    async def test_login_with_valid_credentials(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test successful login with correct credentials."""
        # Register user
        await async_client.post(
            "/api/auth/register",
            json={"email": "login@example.com", "password": "mypassword123"},
        )

        # Login
        response = await async_client.post(
            "/api/auth/login",
            json={"email": "login@example.com", "password": "mypassword123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["email"] == "login@example.com"

    @pytest.mark.asyncio
    async def test_login_with_wrong_password(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test login fails with wrong password."""
        # Register user
        await async_client.post(
            "/api/auth/register",
            json={"email": "wrongpw@example.com", "password": "correctpass123"},
        )

        # Login with wrong password
        response = await async_client.post(
            "/api/auth/login",
            json={"email": "wrongpw@example.com", "password": "wrongpass456"},
        )

        assert response.status_code == 200  # Envelope format
        data = response.json()
        assert data["success"] is False
        assert data["error"]["status"] == 401
