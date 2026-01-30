"""Tests for HS code service."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.hs_code_service import HSCodeService


class TestHSCodeService:
    """Test cases for HSCodeService."""

    @pytest.mark.asyncio
    async def test_validate_hs_code_format_valid(self):
        """Test validation of valid HS codes."""
        # Use a mock session (service doesn't need real DB for validation)
        service = HSCodeService(None)  # type: ignore

        # Valid 8-digit code
        is_valid, error = await service.validate_hs_code_format("85094010")
        assert is_valid is True
        assert error is None

    @pytest.mark.asyncio
    async def test_validate_hs_code_format_too_short(self):
        """Test validation rejects codes that are too short."""
        service = HSCodeService(None)  # type: ignore

        is_valid, error = await service.validate_hs_code_format("850940")
        assert is_valid is False
        assert "8 digits" in error

    @pytest.mark.asyncio
    async def test_validate_hs_code_format_too_long(self):
        """Test validation rejects codes that are too long."""
        service = HSCodeService(None)  # type: ignore

        is_valid, error = await service.validate_hs_code_format("850940101")
        assert is_valid is False
        assert "8 digits" in error

    @pytest.mark.asyncio
    async def test_validate_hs_code_format_non_digit(self):
        """Test validation rejects codes with non-digit characters."""
        service = HSCodeService(None)  # type: ignore

        is_valid, error = await service.validate_hs_code_format("8509401A")
        assert is_valid is False
        assert "digits" in error

    @pytest.mark.asyncio
    async def test_validate_hs_code_format_invalid_chapter(self):
        """Test validation rejects codes with invalid chapter (00)."""
        service = HSCodeService(None)  # type: ignore

        is_valid, error = await service.validate_hs_code_format("00094010")
        assert is_valid is False
        assert "00" in error
