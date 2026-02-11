"""Corrections API for anonymous correction submissions."""

import logging
import time
from typing import Any

import redis.asyncio as redis
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rate_limiter import get_client_ip
from app.core.redis import get_redis
from app.models.hs_code import HSCode
from app.repositories.lookup_record_repository import LookupRecordRepository
from app.schemas.base import ApiResponse, error_response, success_response
from app.schemas.correction import (
    CorrectionRequest,
    CorrectionResponse,
    LookupRecordItem,
    PaginatedLookupResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/corrections", tags=["corrections"])

# Correction-specific rate limiting (separate from search 100 req/min)
CORRECTION_RATE_LIMIT = 10
CORRECTION_RATE_WINDOW = 3600  # 1 hour in seconds
CORRECTION_RATE_PREFIX = "correction_rate:"


async def check_correction_rate_limit(
    redis_client: "redis.Redis | None",
    client_ip: str,
) -> tuple[bool, int, int]:
    """Check IP-based rate limit for corrections (10/hour).

    Uses Redis sorted set sliding window pattern.

    Args:
        redis_client: Redis client
        client_ip: Client IP address

    Returns:
        Tuple of (allowed, remaining, reset_seconds)
    """
    if not redis_client:
        return True, CORRECTION_RATE_LIMIT, CORRECTION_RATE_WINDOW

    key = f"{CORRECTION_RATE_PREFIX}{client_ip}"
    current_time = int(time.time())
    window_start = current_time - CORRECTION_RATE_WINDOW

    try:
        async with redis_client.pipeline(transaction=True) as pipe:
            await pipe.zremrangebyscore(key, 0, window_start)
            await pipe.zcard(key)
            await pipe.zadd(key, {str(current_time): current_time})
            await pipe.expire(key, CORRECTION_RATE_WINDOW)
            results = await pipe.execute()

        current_count = results[1]

        if current_count >= CORRECTION_RATE_LIMIT:
            return False, 0, CORRECTION_RATE_WINDOW

        remaining = CORRECTION_RATE_LIMIT - current_count - 1
        return True, remaining, CORRECTION_RATE_WINDOW
    except Exception:
        # Fail open on Redis errors
        return True, CORRECTION_RATE_LIMIT, CORRECTION_RATE_WINDOW


@router.get(
    "/lookups",
    response_model=ApiResponse[PaginatedLookupResponse],
    summary="Get unverified lookup records",
    description="Returns paginated list of unverified lookup records with matched HS code details.",
)
async def get_unverified_lookups(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get paginated unverified lookup records with HS code details."""
    repo = LookupRecordRepository(session=db)

    records = await repo.get_unverified_with_hs_codes(limit=limit, offset=offset)
    total = await repo.count_unverified()

    items = []
    for record in records:
        items.append(
            LookupRecordItem(
                id=record.id,
                query_text=record.query_text,
                query_language=record.query_language,
                matched_hs_code_id=record.matched_hs_code_id,
                matched_hs_code=(
                    record.matched_hs_code.code if record.matched_hs_code else None
                ),
                matched_description_vn=(
                    record.matched_hs_code.description_vn
                    if record.matched_hs_code
                    else None
                ),
                matched_description_en=(
                    record.matched_hs_code.description_en
                    if record.matched_hs_code
                    else None
                ),
                confidence_score=record.confidence_score,
                search_method=record.search_method,
                created_at=record.created_at.isoformat(),
            )
        )

    response = PaginatedLookupResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )

    return success_response(response.model_dump())


@router.post(
    "",
    response_model=ApiResponse[CorrectionResponse],
    summary="Submit a correction",
    description="Submit an anonymous correction for a lookup record. Rate limited to 10/hour per IP.",
)
async def submit_correction(
    request: Request,
    body: CorrectionRequest,
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),  # type: ignore[type-arg]
) -> dict[str, Any]:
    """Submit a correction for a lookup record (anonymous, rate-limited)."""
    # Check correction-specific rate limit (10/hour per IP)
    client_ip = get_client_ip(request)
    allowed, remaining, reset = await check_correction_rate_limit(
        redis_client, client_ip
    )

    if not allowed:
        return error_response(
            type_uri="https://athena.example/errors/rate-limit-exceeded",
            title="Too Many Requests",
            status=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit reached - please try again later",
            instance="/api/corrections",
        )

    repo = LookupRecordRepository(session=db)

    # Validate lookup_id exists
    record = await repo.find_by_id(body.lookup_id)
    if not record:
        return error_response(
            type_uri="https://athena.example/errors/not-found",
            title="Not Found",
            status=status.HTTP_404_NOT_FOUND,
            detail=f"Lookup record {body.lookup_id} not found",
            instance="/api/corrections",
        )

    # Validate correct_hs_code_id exists
    hs_result = await db.execute(
        select(HSCode).where(HSCode.id == body.correct_hs_code_id)
    )
    hs_code = hs_result.scalar_one_or_none()
    if not hs_code:
        return error_response(
            type_uri="https://athena.example/errors/invalid-hs-code",
            title="Bad Request",
            status=status.HTTP_400_BAD_REQUEST,
            detail=f"HS code with id {body.correct_hs_code_id} not found",
            instance="/api/corrections",
        )

    # Validate correction is not duplicate (same as matched)
    if record.matched_hs_code_id and body.correct_hs_code_id == record.matched_hs_code_id:
        return error_response(
            type_uri="https://athena.example/errors/duplicate-correction",
            title="Bad Request",
            status=status.HTTP_400_BAD_REQUEST,
            detail="The suggested HS code is the same as the current match. Please select a different code.",
            instance="/api/corrections",
        )

    # Check if record already has a verified correction
    if record.is_verified and record.correct_hs_code_id:
        return error_response(
            type_uri="https://athena.example/errors/already-corrected",
            title="Conflict",
            status=status.HTTP_409_CONFLICT,
            detail=f"This lookup has already been corrected (HS code ID: {record.correct_hs_code_id}). Multiple corrections are not allowed.",
            instance="/api/corrections",
        )

    # Apply correction (sets is_verified=true, verified_at=now(), notes)
    updated_record = await repo.apply_correction(
        record_id=body.lookup_id,
        correct_hs_code_id=body.correct_hs_code_id,
        notes=body.notes,
    )

    response = CorrectionResponse(
        id=updated_record.id,
        query_text=updated_record.query_text,
        matched_hs_code_id=updated_record.matched_hs_code_id,
        correct_hs_code_id=updated_record.correct_hs_code_id,
        is_verified=updated_record.is_verified,
        verified_at=(
            updated_record.verified_at.isoformat()
            if updated_record.verified_at
            else None
        ),
        notes=updated_record.notes,
    )

    logger.info(
        "Correction submitted",
        extra={
            "lookup_id": body.lookup_id,
            "correct_hs_code_id": body.correct_hs_code_id,
            "client_ip": client_ip,
        },
    )

    return success_response(response.model_dump())
