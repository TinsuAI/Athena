"""Lookups API for browsing lookup history."""

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.lookup_record_repository import LookupRecordRepository
from app.schemas.base import ApiResponse, error_response, success_response
from app.schemas.lookup import LookupListItem, PaginatedLookupListResponse

router = APIRouter(prefix="/api/lookups", tags=["lookups"])


@router.get(
    "",
    response_model=ApiResponse[PaginatedLookupListResponse],
    summary="List lookup records",
)
async def list_lookups(
    limit: int = Query(default=20),
    offset: int = Query(default=0),
    verified: bool | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get paginated lookup records with optional verification filter."""
    if limit < 1 or limit > 100:
        return error_response(
            type_uri="https://athena.example/errors/validation",
            title="Invalid Parameters",
            status=400,
            detail="limit must be between 1 and 100",
            instance="/api/lookups",
        )
    if offset < 0:
        return error_response(
            type_uri="https://athena.example/errors/validation",
            title="Invalid Parameters",
            status=400,
            detail="offset must be >= 0",
            instance="/api/lookups",
        )

    repo = LookupRecordRepository(session=db)

    records = await repo.get_all_with_hs_codes(
        limit=limit, offset=offset, verified_filter=verified
    )
    total = await repo.count_all(verified_filter=verified)

    items = [
        LookupListItem(
            id=r.id,
            query_text=r.query_text,
            query_language=r.query_language,
            matched_hs_code=r.matched_hs_code.code if r.matched_hs_code else None,
            matched_description_vn=(
                r.matched_hs_code.description_vn if r.matched_hs_code else None
            ),
            confidence_score=r.confidence_score,
            search_method=r.search_method,
            is_verified=r.is_verified,
            created_at=r.created_at.isoformat(),
        )
        for r in records
    ]

    response = PaginatedLookupListResponse(
        items=items, total=total, limit=limit, offset=offset
    )
    return success_response(response.model_dump())
