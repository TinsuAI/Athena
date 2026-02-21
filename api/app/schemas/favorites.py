"""Pydantic schemas for favorites API."""

from datetime import datetime

from pydantic import BaseModel, Field


class FavoriteCreate(BaseModel):
    """Input schema for creating a favorite."""

    hs_code_id: int = Field(..., description="ID of the HS code to favorite")


class FavoriteUpdateNotes(BaseModel):
    """Input schema for updating favorite notes."""

    notes: str | None = Field(None, description="Personal notes (null or empty string clears)")


class FavoriteResponse(BaseModel):
    """Output schema for a single favorite."""

    id: int
    user_id: int
    hs_code_id: int
    hs_code: str = Field(description="8-digit HS code string")
    description_vn: str = Field(description="Vietnamese description")
    notes: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
