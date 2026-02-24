"""Tests for SiteSettingRepository."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.models.site_setting import SiteSetting
from app.repositories.site_setting_repository import VALID_KEYS, SiteSettingRepository


class TestSiteSettingRepository:

    @pytest.mark.asyncio
    async def test_get_returns_setting(self):
        session = AsyncMock()
        mock_result = MagicMock()
        mock_setting = MagicMock(spec=SiteSetting)
        mock_setting.key = "search_requires_auth"
        mock_setting.value = "true"
        mock_result.scalar_one_or_none.return_value = mock_setting
        session.execute.return_value = mock_result

        repo = SiteSettingRepository(session)
        result = await repo.get("search_requires_auth")

        assert result is mock_setting

    @pytest.mark.asyncio
    async def test_get_returns_none_for_missing(self):
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        repo = SiteSettingRepository(session)
        result = await repo.get("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_all_returns_list(self):
        session = AsyncMock()
        mock_result = MagicMock()
        setting = MagicMock(spec=SiteSetting)
        mock_result.scalars.return_value.all.return_value = [setting]
        session.execute.return_value = mock_result

        repo = SiteSettingRepository(session)
        result = await repo.get_all()

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_upsert_raises_for_unknown_key(self):
        session = AsyncMock()
        repo = SiteSettingRepository(session)

        with pytest.raises(KeyError, match="Unknown setting key"):
            await repo.upsert("unknown_key", "value")

    @pytest.mark.asyncio
    async def test_upsert_updates_existing(self):
        session = AsyncMock()
        mock_result = MagicMock()
        mock_setting = MagicMock(spec=SiteSetting)
        mock_setting.key = "search_requires_auth"
        mock_setting.value = "true"
        mock_result.scalar_one_or_none.return_value = mock_setting
        session.execute.return_value = mock_result

        repo = SiteSettingRepository(session)
        result = await repo.upsert("search_requires_auth", "false")

        assert mock_setting.value == "false"
        session.flush.assert_called_once()
