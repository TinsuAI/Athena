"""Public settings API endpoint."""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.schemas.base import success_response
from app.services.site_setting_service import SiteSettingService

router = APIRouter(prefix="/api/settings", tags=["settings"])

PUBLIC_KEYS = {"search_requires_auth"}


@router.get("", response_model=None)
async def get_public_settings(
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Return allowlisted public settings. No auth required."""
    service = SiteSettingService(db)
    all_settings = await service.get_all()
    public = {s["key"]: s["value"] for s in all_settings if s["key"] in PUBLIC_KEYS}
    return success_response(public)
