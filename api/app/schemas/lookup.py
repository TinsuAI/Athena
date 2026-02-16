"""Schemas for lookup history list and detail responses."""

from typing import Any

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


class LookupDetailHSCode(BaseModel):
    """HS code details for lookup detail response."""

    code: str
    description_vn: str | None
    description_en: str | None
    duty_rate: str | None
    vat_rate: str | None


class LookupDetailResponse(BaseModel):
    """Full lookup record detail response."""

    id: int
    query_text: str
    query_language: str | None
    matched_hs_code: LookupDetailHSCode | None
    correct_hs_code: LookupDetailHSCode | None
    classification_data: dict[str, Any] | None
    practical_notes: list[str] | None
    process_logs: list[dict[str, Any]] | None
    nlm_raw_response: str | None = None
    confidence_score: float | None
    search_method: str
    is_verified: bool
    verified_at: str | None
    notes: str | None
    created_at: str
