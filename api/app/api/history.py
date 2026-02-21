"""Search history API for recording and listing user searches."""

from typing import Any

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.core.auth import require_authenticated
from app.schemas.base import error_response, success_response
from app.schemas.search_history import SearchHistoryCreate
from app.services.search_history_service import SearchHistoryService

router = APIRouter(prefix="/api/history", tags=["history"])


@router.post("", status_code=status.HTTP_201_CREATED)
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


@router.delete("/clear")
async def clear_history(
    current_user: dict = Depends(require_authenticated),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Clear all search history for the current user."""
    service = SearchHistoryService(db)
    count = await service.clear_history(current_user["id"])
    return success_response({"deleted_count": count})


@router.delete("/{entry_id}")
async def delete_history_entry(
    entry_id: int,
    current_user: dict = Depends(require_authenticated),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Delete a single search history entry."""
    service = SearchHistoryService(db)
    deleted = await service.delete_entry(entry_id, current_user["id"])
    if not deleted:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error_response(
                "https://athena.example/errors/not-found",
                "Not Found",
                404,
                "History entry not found",
                f"/api/history/{entry_id}",
            ),
        )
    return success_response({"deleted": True})


@router.get("")
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
