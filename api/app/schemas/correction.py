"""Pydantic schemas for corrections API."""

from pydantic import BaseModel, Field


class CorrectionRequest(BaseModel):
    """Request body for submitting a correction."""

    lookup_id: int = Field(description="ID of the lookup record to correct")
    correct_hs_code_id: int = Field(description="ID of the correct HS code")
    notes: str | None = Field(
        default=None,
        max_length=200,
        description="Optional correction notes (max 200 characters)",
    )


class CorrectionResponse(BaseModel):
    """Response data for a submitted correction."""

    id: int = Field(description="Lookup record ID")
    query_text: str = Field(description="Original search query")
    matched_hs_code_id: int | None = Field(description="Originally matched HS code ID")
    correct_hs_code_id: int = Field(description="Corrected HS code ID")
    is_verified: bool = Field(description="Verification status")
    verified_at: str | None = Field(description="Verification timestamp (ISO format)")
    notes: str | None = Field(description="Correction notes")


class LookupRecordItem(BaseModel):
    """Lookup record with matched HS code details for display."""

    id: int = Field(description="Lookup record ID")
    query_text: str = Field(description="Original search query")
    query_language: str | None = Field(description="Detected query language")
    matched_hs_code_id: int | None = Field(description="Matched HS code ID")
    matched_hs_code: str | None = Field(description="Matched HS code string")
    matched_description_vn: str | None = Field(
        description="Vietnamese description of matched HS code"
    )
    matched_description_en: str | None = Field(
        description="English description of matched HS code"
    )
    confidence_score: float | None = Field(description="Search confidence score")
    search_method: str = Field(description="Search method used")
    created_at: str = Field(description="Record creation timestamp (ISO format)")


class PaginatedLookupResponse(BaseModel):
    """Paginated response for lookup records."""

    items: list[LookupRecordItem] = Field(description="List of lookup records")
    total: int = Field(description="Total number of unverified records")
    limit: int = Field(description="Page size")
    offset: int = Field(description="Page offset")
