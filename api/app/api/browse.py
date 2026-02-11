"""Tariff browse API endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.base import ApiResponse, error_response, success_response
from app.schemas.browse import (
    BrowseChapterDetailResponse,
    BrowseChaptersResponse,
    BrowseSectionItem,
    PaginatedBrowseSearchResponse,
)
from app.services.browse_service import BrowseService

router = APIRouter(prefix="/api/browse", tags=["browse"])


@router.get(
    "/sections",
    response_model=ApiResponse[list[BrowseSectionItem]],
    summary="List all HS sections",
    description="Returns all HS sections ordered by section number with chapter counts.",
)
async def list_sections(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """List all HS sections with chapter counts."""
    service = BrowseService(db)
    sections = await service.list_sections()
    return success_response(sections)


@router.get(
    "/chapters",
    response_model=ApiResponse[BrowseChaptersResponse],
    summary="List chapters by section",
    description="Returns all chapters for a given section with heading and HS code counts.",
)
async def list_chapters(
    section_id: int = Query(..., description="Section ID to filter chapters"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """List chapters for a section with section notes."""
    service = BrowseService(db)
    result = await service.list_chapters(section_id)
    if result is None:
        return error_response(
            type_uri="https://athena.example/errors/not-found",
            title="Section Not Found",
            status=404,
            detail=f"Section with id {section_id} not found",
            instance=f"/api/browse/chapters?section_id={section_id}",
        )
    return success_response(result)


@router.get(
    "/chapters/{chapter_code}",
    response_model=ApiResponse[BrowseChapterDetailResponse],
    summary="Get full chapter detail",
    description="Returns full chapter hierarchy with all rate data.",
)
async def get_chapter_detail(
    chapter_code: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get full chapter detail with hierarchy and rates."""
    service = BrowseService(db)
    chapter = await service.get_chapter_detail(chapter_code)
    if chapter is None:
        return error_response(
            type_uri="https://athena.example/errors/not-found",
            title="Chapter Not Found",
            status=404,
            detail=f"Chapter '{chapter_code}' not found",
            instance=f"/api/browse/chapters/{chapter_code}",
        )
    return success_response(chapter)


@router.get(
    "/search",
    response_model=ApiResponse[PaginatedBrowseSearchResponse],
    summary="Search within tariff browser",
    description="Search HS codes by description or code prefix with optional chapter filter.",
)
async def search_browse(
    q: str = Query(..., min_length=1, max_length=200, description="Search query"),
    chapter: str | None = Query(default=None, description="Optional chapter code filter"),
    limit: int = Query(default=50, ge=1, le=200, description="Page size"),
    offset: int = Query(default=0, ge=0, description="Page offset"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Search HS codes within the tariff browser."""
    service = BrowseService(db)
    result = await service.search(q, chapter, limit, offset)
    return success_response(result)
