"""Pydantic schemas for search history."""

from datetime import datetime

from pydantic import BaseModel, Field


class SearchHistoryCreate(BaseModel):
    """Input schema for recording a search."""

    query: str = Field(..., min_length=1, max_length=500, description="Search query text")
    selected_hs_code_id: int | None = Field(
        None, description="Matched HS code ID (null if no match)"
    )


class SearchHistoryResponse(BaseModel):
    """Output schema for a single search history entry."""

    id: int
    user_id: int
    query: str
    selected_hs_code_id: int | None = None
    selected_hs_code: str | None = Field(None, description="8-digit HS code string")
    selected_description_vn: str | None = Field(
        None, description="Vietnamese description"
    )
    created_at: datetime

    model_config = {"from_attributes": True}


class SearchHistoryListResponse(BaseModel):
    """Paginated list response for search history."""

    items: list[SearchHistoryResponse]
    total: int
