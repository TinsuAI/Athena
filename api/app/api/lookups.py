"""Lookups API for browsing lookup history."""

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.lookup_record_repository import LookupRecordRepository
from app.schemas.base import ApiResponse, error_response, success_response
from app.schemas.lookup import (
    LookupDetailHSCode,
    LookupDetailResponse,
    LookupListItem,
    PaginatedLookupListResponse,
)

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


@router.get(
    "/{lookup_id}",
    response_model=ApiResponse[LookupDetailResponse],
    summary="Get lookup record details",
)
async def get_lookup_detail(
    lookup_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get full details of a single lookup record."""
    repo = LookupRecordRepository(session=db)
    record = await repo.find_by_id_with_details(lookup_id)
    if record is None:
        return error_response(
            type_uri="https://athena.example/errors/not-found",
            title="Lookup Not Found",
            status=404,
            detail=f"No lookup record with id {lookup_id} exists.",
            instance=f"/api/lookups/{lookup_id}",
        )

    def _build_hs_code(hs: Any) -> dict[str, Any] | None:
        if hs is None:
            return None
        return LookupDetailHSCode(
            code=hs.code,
            description_vn=hs.description_vn,
            description_en=hs.description_en,
            duty_rate=str(hs.duty_rate) if hs.duty_rate is not None else None,
            vat_rate=str(hs.vat_rate) if hs.vat_rate is not None else None,
        ).model_dump()

    response = LookupDetailResponse(
        id=record.id,
        query_text=record.query_text,
        query_language=record.query_language,
        matched_hs_code=_build_hs_code(record.matched_hs_code),
        correct_hs_code=_build_hs_code(record.correct_hs_code),
        classification_data=record.classification_data,
        practical_notes=record.practical_notes,
        process_logs=record.process_logs,
        nlm_raw_response=record.nlm_raw_response,
        confidence_score=record.confidence_score,
        search_method=record.search_method,
        is_verified=record.is_verified,
        verified_at=record.verified_at.isoformat() if record.verified_at else None,
        notes=record.notes,
        correction_status=record.correction_status,
        submitted_by_user_id=record.submitted_by_user_id,
        created_at=record.created_at.isoformat(),
    )
    return success_response(response.model_dump())
