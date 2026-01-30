"""Pytest configuration for API tests."""

import pytest


def pytest_addoption(parser):
    """Add --integration option to pytest."""
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="Run integration tests that require live database and Redis"
    )


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test (requires --integration flag)"
    )
