"""Schemas for lookup history list responses."""

from pydantic import BaseModel


class LookupListItem(BaseModel):
    """Single lookup record in the list response."""

    id: int
    query_text: str
    query_language: str | None
    matched_hs_code: str | None
    matched_description_vn: str | None
    confidence_score: float | None
    search_method: str
    is_verified: bool
    created_at: str


class PaginatedLookupListResponse(BaseModel):
    """Paginated list of lookup records."""

    items: list[LookupListItem]
    total: int
    limit: int
    offset: int
