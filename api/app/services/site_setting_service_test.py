"""Tests for SiteSettingService."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.site_setting import SiteSetting
from app.services.site_setting_service import SiteSettingService


class TestSiteSettingServiceGetBool:

    @pytest.mark.asyncio
    async def test_returns_true_when_value_is_true(self):
        session = AsyncMock()
        with patch(
            "app.services.site_setting_service.SiteSettingRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_setting = MagicMock(spec=SiteSetting)
            mock_setting.value = "true"
            mock_repo.get.return_value = mock_setting
            mock_repo_class.return_value = mock_repo

            service = SiteSettingService(session)
            result = await service.get_bool("search_requires_auth")

        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_when_value_is_false(self):
        session = AsyncMock()
        with patch(
            "app.services.site_setting_service.SiteSettingRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_setting = MagicMock(spec=SiteSetting)
            mock_setting.value = "false"
            mock_repo.get.return_value = mock_setting
            mock_repo_class.return_value = mock_repo

            service = SiteSettingService(session)
            result = await service.get_bool("search_requires_auth")

        assert result is False

    @pytest.mark.asyncio
    async def test_fail_safe_returns_default_on_exception(self):
        session = AsyncMock()
        with patch(
            "app.services.site_setting_service.SiteSettingRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get.side_effect = Exception("DB error")
            mock_repo_class.return_value = mock_repo

            service = SiteSettingService(session)
            result = await service.get_bool("search_requires_auth", default=True)

        assert result is True

    @pytest.mark.asyncio
    async def test_returns_default_when_setting_missing(self):
        session = AsyncMock()
        with patch(
            "app.services.site_setting_service.SiteSettingRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get.return_value = None
            mock_repo_class.return_value = mock_repo

            service = SiteSettingService(session)
            result = await service.get_bool("search_requires_auth", default=True)

        assert result is True


class TestSiteSettingServiceUpdate:

    @pytest.mark.asyncio
    async def test_update_calls_repo_and_audit_log(self):
        session = AsyncMock()
        with (
            patch(
                "app.services.site_setting_service.SiteSettingRepository"
            ) as mock_repo_class,
            patch(
                "app.services.site_setting_service.AuditLogRepository"
            ) as mock_audit_class,
        ):
            mock_repo = AsyncMock()
            mock_setting = MagicMock(spec=SiteSetting)
            mock_setting.key = "search_requires_auth"
            mock_setting.value = "false"
            mock_setting.description = "test"
            mock_repo.upsert.return_value = mock_setting
            mock_repo_class.return_value = mock_repo

            mock_audit = AsyncMock()
            mock_audit_class.return_value = mock_audit

            service = SiteSettingService(session)
            result = await service.update("search_requires_auth", "false", admin_id=1)

        assert result["key"] == "search_requires_auth"
        assert result["value"] == "false"
        mock_audit.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_raises_key_error_for_unknown_key(self):
        session = AsyncMock()
        with patch(
            "app.services.site_setting_service.SiteSettingRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.upsert.side_effect = KeyError("Unknown setting key: bad_key")
            mock_repo_class.return_value = mock_repo

            service = SiteSettingService(session)
            with pytest.raises(KeyError):
                await service.update("bad_key", "value", admin_id=1)
