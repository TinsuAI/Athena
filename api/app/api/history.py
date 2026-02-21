"""Search history API for recording and listing user searches."""

from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.core.auth import require_authenticated
from app.schemas.base import success_response
from app.schemas.search_history import SearchHistoryCreate
from app.services.search_history_service import SearchHistoryService

router = APIRouter(prefix="/api/history", tags=["history"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def record_search(
    body: SearchHistoryCreate,
    current_user: dict = Depends(require_authenticated),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Record a search query in the user's history."""
    service = SearchHistoryService(db)
    entry = await service.record_search(
        current_user["id"], body.query, body.selected_hs_code_id
    )
    return success_response(entry)


@router.get("/")
async def list_history(
    current_user: dict = Depends(require_authenticated),
    db: AsyncSession = Depends(get_db_session),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    """List the authenticated user's search history."""
    service = SearchHistoryService(db)
    result = await service.list_history(current_user["id"], limit, offset)
    return success_response(result)
