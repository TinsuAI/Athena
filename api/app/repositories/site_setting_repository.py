"""Repository for site_settings data access."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.site_setting import SiteSetting

VALID_KEYS = {"search_requires_auth"}


class SiteSettingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, key: str) -> SiteSetting | None:
        result = await self.session.execute(
            select(SiteSetting).where(SiteSetting.key == key)
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> list[SiteSetting]:
        result = await self.session.execute(select(SiteSetting))
        return list(result.scalars().all())

    async def upsert(self, key: str, value: str) -> SiteSetting:
        """Update an existing setting. Raises KeyError for unknown keys."""
        if key not in VALID_KEYS:
            raise KeyError(f"Unknown setting key: {key}")
        setting = await self.get(key)
        if setting is None:
            raise KeyError(f"Setting '{key}' not found in database")
        setting.value = value
        await self.session.flush()
        return setting
