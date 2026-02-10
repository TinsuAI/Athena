"""Pydantic schemas for lookup record API responses."""

from datetime import datetime

from pydantic import BaseModel, Field


class LookupRecordResponse(BaseModel):
    """Schema for a single lookup record in API responses."""

    id: int
    query_text: str
    query_hash: str
    query_language: str | None = None
    matched_hs_code_id: int | None = None
    correct_hs_code_id: int | None = None
    is_verified: bool
    verified_by_user_id: int | None = None
    verified_at: datetime | None = None
    confidence_score: float | None = None
    search_method: str
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LookupRecordListResponse(BaseModel):
    """Schema for paginated list of lookup records."""

    items: list[LookupRecordResponse]
    total: int = Field(description="Total number of matching records")
    limit: int = Field(description="Page size")
    offset: int = Field(description="Current offset")
