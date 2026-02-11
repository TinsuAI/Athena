"""Pytest configuration and fixtures for API tests."""

import asyncio
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models.base import Base

settings = get_settings()


def _get_test_database_url() -> str:
    """Derive test database URL by replacing the database name with athena_test."""
    url = settings.database_url
    # Replace /athena at end of URL with /athena_test
    if url.endswith("/athena"):
        return url[:-7] + "/athena_test"
    # Fallback: use TEST_DATABASE_URL env var or the original URL
    return url


# Create test database engine — uses athena_test to avoid destroying dev data
test_engine = create_async_engine(
    _get_test_database_url(),
    echo=False,
    pool_pre_ping=True,
)

# Create test session factory
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session for testing.

    Each test gets a session that is committed after successful test.
    """
    # Create tables
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    # Create session
    async with TestSessionLocal() as session:
        yield session

    # Drop tables after test
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
