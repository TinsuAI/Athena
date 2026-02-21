"""Expert API endpoints for correction approval workflow."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_permission
from app.core.database import get_db
from app.schemas.base import error_response, success_response
from app.schemas.expert import (
    ApproveResponse,
    RejectRequest,
    RejectResponse,
)
from app.services.expert_service import ExpertService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/expert", tags=["expert"])


@router.get("/corrections", response_model=None)
async def get_pending_corrections(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(require_permission("correction.approve")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """List pending corrections for expert review. Requires expert or admin role."""
    service = ExpertService(db)
    result = await service.list_pending_corrections(page=page, per_page=per_page)
    return success_response(result)


@router.get("/corrections/history", response_model=None)
async def get_correction_history(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(require_permission("correction.approve")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """List approved/rejected corrections for history view. Requires expert or admin role."""
    service = ExpertService(db)
    result = await service.list_correction_history(page=page, per_page=per_page)
    return success_response(result)


@router.post("/corrections/{record_id}/approve", response_model=None)
async def approve_correction(
    record_id: int,
    current_user: dict = Depends(require_permission("correction.approve")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Approve a pending correction. Requires expert or admin role."""
    service = ExpertService(db)

    try:
        updated = await service.approve_correction(
            record_id=record_id,
            expert_user_id=current_user["id"],
        )
    except ValueError as e:
        detail = str(e)
        if "not found" in detail.lower():
            return error_response(
                type_uri="https://athena.example/errors/not-found",
                title="Not Found",
                status=404,
                detail=detail,
                instance=f"/api/expert/corrections/{record_id}/approve",
            )
        return error_response(
            type_uri="https://athena.example/errors/validation",
            title="Bad Request",
            status=400,
            detail=detail,
            instance=f"/api/expert/corrections/{record_id}/approve",
        )

    response = ApproveResponse(
        id=updated.id,
        correction_status=updated.correction_status or "approved",
        is_verified=updated.is_verified,
        verified_at=(
            updated.verified_at.isoformat() if updated.verified_at else None
        ),
    )

    logger.info(
        "Correction approved",
        extra={"record_id": record_id, "expert_id": current_user["id"]},
    )

    return success_response(response.model_dump())


@router.post("/corrections/{record_id}/reject", response_model=None)
async def reject_correction(
    record_id: int,
    body: RejectRequest,
    current_user: dict = Depends(require_permission("correction.approve")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Reject a pending correction with a reason. Requires expert or admin role."""
    service = ExpertService(db)

    try:
        updated = await service.reject_correction(
            record_id=record_id,
            expert_user_id=current_user["id"],
            reason=body.reason,
        )
    except ValueError as e:
        detail = str(e)
        if "not found" in detail.lower():
            return error_response(
                type_uri="https://athena.example/errors/not-found",
                title="Not Found",
                status=404,
                detail=detail,
                instance=f"/api/expert/corrections/{record_id}/reject",
            )
        return error_response(
            type_uri="https://athena.example/errors/validation",
            title="Bad Request",
            status=400,
            detail=detail,
            instance=f"/api/expert/corrections/{record_id}/reject",
        )

    response = RejectResponse(
        id=updated.id,
        correction_status=updated.correction_status or "rejected",
        rejection_reason=updated.rejection_reason or body.reason,
    )

    logger.info(
        "Correction rejected",
        extra={"record_id": record_id, "expert_id": current_user["id"]},
    )

    return success_response(response.model_dump())
