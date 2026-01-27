"""Tests for application configuration."""

import os

from app.core.config import Settings


def test_cors_origins_list_single_origin():
    """Test parsing single CORS origin."""
    settings = Settings(cors_origins="http://localhost:3000")
    assert settings.cors_origins_list == ["http://localhost:3000"]


def test_cors_origins_list_multiple_origins():
    """Test parsing multiple comma-separated CORS origins."""
    settings = Settings(
        cors_origins="http://localhost:3000,http://example.com,https://prod.example.com"
    )
    assert settings.cors_origins_list == [
        "http://localhost:3000",
        "http://example.com",
        "https://prod.example.com",
    ]


def test_cors_origins_list_with_spaces():
    """Test parsing CORS origins with whitespace."""
    settings = Settings(cors_origins="http://localhost:3000, http://example.com , https://prod.example.com")
    assert settings.cors_origins_list == [
        "http://localhost:3000",
        "http://example.com",
        "https://prod.example.com",
    ]


def test_cors_origins_list_empty_values():
    """Test parsing CORS origins with empty values."""
    settings = Settings(cors_origins="http://localhost:3000,,,http://example.com")
    assert settings.cors_origins_list == [
        "http://localhost:3000",
        "http://example.com",
    ]


def test_cors_origins_default():
    """Test default CORS origin."""
    settings = Settings()
    assert settings.cors_origins_list == ["http://localhost:3000"]
