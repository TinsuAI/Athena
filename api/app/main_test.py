"""Tests for main FastAPI application."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    """Create async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_endpoint_returns_envelope_format(client: AsyncClient):
    """Test health endpoint returns proper envelope format."""
    response = await client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert "success" in data
    assert "data" in data
    assert "error" in data
    assert data["success"] is True
    assert data["error"] is None


@pytest.mark.asyncio
async def test_health_endpoint_returns_status_healthy(client: AsyncClient):
    """Test health endpoint returns healthy status."""
    response = await client.get("/health")
    data = response.json()

    assert data["data"]["status"] == "healthy"


@pytest.mark.asyncio
async def test_health_endpoint_includes_database_status(client: AsyncClient):
    """Test health endpoint includes database connection status."""
    response = await client.get("/health")
    data = response.json()

    assert "database" in data["data"]
    assert isinstance(data["data"]["database"], bool)


@pytest.mark.asyncio
async def test_health_endpoint_includes_redis_status(client: AsyncClient):
    """Test health endpoint includes redis connection status."""
    response = await client.get("/health")
    data = response.json()

    assert "redis" in data["data"]
    assert isinstance(data["data"]["redis"], bool)
