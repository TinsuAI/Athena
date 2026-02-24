"""Tests for public settings API."""

import pytest
from unittest.mock import AsyncMock, patch

from app.api.settings import get_public_settings


class TestGetPublicSettings:

    @pytest.mark.asyncio
    async def test_returns_public_settings(self):
        mock_db = AsyncMock()
        with patch("app.api.settings.SiteSettingService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_all.return_value = [
                {
                    "key": "search_requires_auth",
                    "value": "true",
                    "description": "test",
                },
            ]
            mock_service_class.return_value = mock_service

            result = await get_public_settings(db=mock_db)

        assert result["success"] is True
        assert result["data"]["search_requires_auth"] == "true"

    @pytest.mark.asyncio
    async def test_filters_non_public_keys(self):
        mock_db = AsyncMock()
        with patch("app.api.settings.SiteSettingService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_all.return_value = [
                {
                    "key": "search_requires_auth",
                    "value": "true",
                    "description": "t",
                },
                {"key": "secret_key", "value": "secret", "description": "s"},
            ]
            mock_service_class.return_value = mock_service

            result = await get_public_settings(db=mock_db)

        assert "secret_key" not in result["data"]
        assert "search_requires_auth" in result["data"]
