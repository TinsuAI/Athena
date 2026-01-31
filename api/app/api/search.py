"""Search API endpoint for hybrid HS code search."""

import logging
import time
from typing import Any

import redis.asyncio as redis
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import get_redis
from app.schemas.base import ApiResponse, error_response, success_response
from app.schemas.search import (
    ClassificationSchema,
    SearchRequest,
    SearchResponseData,
)
from app.services.classification_analyzer import ClassificationAnalyzer
from app.services.search_cache import CachedSearchResult, SearchCacheService
from app.services.search_service import SearchService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["search"])


def _format_hs_code(code: str) -> str:
    """Format HS code with dots (e.g., 74182000 -> 7418.20.00)."""
    if len(code) == 8:
        return f"{code[:4]}.{code[4:6]}.{code[6:]}"
    return code


def _format_rate(rate: float) -> str:
    """Format rate as percentage string."""
    if rate == int(rate):
        return f"{int(rate)}%"
    return f"{rate}%"


@router.post(
    "/search",
    response_model=ApiResponse[SearchResponseData],
    summary="Search for HS codes",
    description="""
    Search for HS codes using product descriptions or exact codes.

    **Features:**
    - Supports Vietnamese, English, and Chinese (best effort) product descriptions
    - Hybrid search: vector similarity + fuzzy text + exact match
    - Returns classification analysis with material and function reasoning
    - Includes practical import notes and FTA optimization hints

    **Examples:**
    - Vietnamese: "Thanh treo khăn MITO, mã A2018ANE, bằng đồng mạ chrome"
    - English: "copper bathroom towel rack, chrome plated"
    - HS Code: "7418.20.00" or "74182000"
    """,
)
async def search_hs_codes(
    request: Request,
    body: SearchRequest,
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),  # type: ignore[type-arg]
) -> dict[str, Any]:
    """Search for HS codes with classification analysis.

    Args:
        request: FastAPI request (for logging)
        body: Search request with query
        db: Database session
        redis_client: Redis client for caching

    Returns:
        Best matching HS code with classification analysis
    """
    start_time = time.time()

    # Log search request (anonymized - NFR-M3)
    logger.info(
        "Search request",
        extra={
            "query_length": len(body.query),
            "limit": body.limit,
            "client_ip": request.client.host if request.client else "unknown",
        }
    )

    try:
        # Create services
        search_service = SearchService(session=db, redis_client=redis_client)
        cache_service = SearchCacheService(redis_client=redis_client)
        analyzer = ClassificationAnalyzer()

        # Check cache first
        cached_results = await cache_service.get(body.query)
        if cached_results:
            logger.info("Cache hit for search query")
            # Convert cached result to response (use first result)
            if cached_results:
                best_cached = cached_results[0]
                # We still need to generate classification analysis from query
                # Load HS code to get full object for analysis
                from app.models.hs_code import HSCode
                from sqlalchemy import select
                from sqlalchemy.orm import selectinload

                from app.models.hs_subheading import HSSubheading
                from app.models.hs_heading import HSHeading

                result = await db.execute(
                    select(HSCode)
                    .where(HSCode.code == best_cached.hs_code.replace(".", ""))
                    .options(
                        selectinload(HSCode.fta_rates),
                        selectinload(HSCode.subheading).selectinload(HSSubheading.heading).selectinload(HSHeading.chapter),
                    )
                )
                hs_code_obj = result.scalar_one_or_none()

                if hs_code_obj:
                    analysis = analyzer.analyze(body.query, hs_code_obj)

                    response_data = SearchResponseData(
                        hs_code=_format_hs_code(best_cached.hs_code),
                        description=best_cached.description_vn,
                        duty_rate=_format_rate(best_cached.duty_rate),
                        vat_rate=_format_rate(best_cached.vat_rate),
                        classification=ClassificationSchema(
                            material=analysis.material,
                            function=analysis.function,
                        ),
                        practical_notes=analysis.practical_notes,
                        confidence=best_cached.confidence,
                    )

                    duration = time.time() - start_time
                    logger.info(
                        "Search completed from cache",
                        extra={"duration_ms": int(duration * 1000)}
                    )
                    return success_response(response_data.model_dump())

        # Perform search
        results = await search_service.search(
            query=body.query,
            limit=body.limit,
        )

        # Log search duration
        duration = time.time() - start_time
        logger.info(
            "Search completed",
            extra={
                "duration_ms": int(duration * 1000),
                "results_count": len(results),
            }
        )

        # Handle no results
        if not results:
            return error_response(
                type_uri="https://athena.example/errors/no-results",
                title="No Results",
                status=status.HTTP_404_NOT_FOUND,
                detail="No matching HS code found. Try using more specific product details (material, function, industry)",
                instance="/api/search",
            )

        # Get best result
        best_result = results[0]

        # Cache the results for future queries
        cached_items = [
            CachedSearchResult(
                hs_code=r.hs_code,
                description_vn=r.description_vn,
                description_en=r.description_en,
                duty_rate=r.duty_rate,
                vat_rate=r.vat_rate,
                unit=r.unit,
                confidence=r.confidence,
                is_exact_match=r.is_exact_match,
            )
            for r in results
        ]
        await cache_service.set(body.query, cached_items)

        # Get full HS code object for classification analysis
        hs_code_obj = best_result.hs_code_full

        # Generate classification analysis
        analysis = analyzer.analyze(body.query, hs_code_obj)

        # Build response
        response_data = SearchResponseData(
            hs_code=_format_hs_code(best_result.hs_code),
            description=best_result.description_vn,
            duty_rate=_format_rate(best_result.duty_rate),
            vat_rate=_format_rate(best_result.vat_rate),
            classification=ClassificationSchema(
                material=analysis.material,
                function=analysis.function,
            ),
            practical_notes=analysis.practical_notes,
            confidence=best_result.confidence,
        )

        return success_response(response_data.model_dump())

    except ValueError as e:
        # Invalid input (empty query, etc.)
        return error_response(
            type_uri="https://athena.example/errors/invalid-input",
            title="Invalid Input",
            status=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
            instance="/api/search",
        )

    except Exception as e:
        logger.exception("Search error")
        return error_response(
            type_uri="https://athena.example/errors/internal-error",
            title="Internal Error",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your search",
            instance="/api/search",
        )
