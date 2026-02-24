"""Service for site settings business logic."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.site_setting_repository import SiteSettingRepository


class SiteSettingService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_bool(self, key: str, default: bool = True) -> bool:
        """Get a boolean setting. Returns default (True) on any error — fail-safe."""
        try:
            repo = SiteSettingRepository(self.session)
            setting = await repo.get(key)
            if setting is None:
                return default
            return setting.value.lower() == "true"
        except Exception:
            return default

    async def get_all(self) -> list[dict]:
        """Return all settings as list of dicts."""
        repo = SiteSettingRepository(self.session)
        settings = await repo.get_all()
        return [
            {"key": s.key, "value": s.value, "description": s.description}
            for s in settings
        ]

    async def update(self, key: str, value: str, admin_id: int) -> dict:
        """Update a setting and write audit log. Raises KeyError for unknown keys."""
        repo = SiteSettingRepository(self.session)
        setting = await repo.upsert(key, value)

        audit_repo = AuditLogRepository(self.session)
        await audit_repo.create(
            admin_user_id=admin_id,
            action="site_setting_updated",
            details={"key": key, "value": value},
        )

        return {
            "key": setting.key,
            "value": setting.value,
            "description": setting.description,
        }
