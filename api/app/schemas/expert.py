"""Pydantic schemas for expert correction approval API endpoints."""

from pydantic import BaseModel, Field


class PendingCorrectionItem(BaseModel):
    """A single pending correction item for expert review."""

    id: int
    query_text: str
    matched_hs_code: str | None = None
    matched_description_vn: str | None = None
    matched_description_en: str | None = None
    correct_hs_code: str | None = None
    correct_description_vn: str | None = None
    correct_description_en: str | None = None
    submitter_email: str | None = None
    submitted_at: str  # created_at ISO format
    notes: str | None = None


class PaginatedPendingCorrectionsResponse(BaseModel):
    """Paginated response for pending corrections list."""

    items: list[PendingCorrectionItem]
    total: int
    page: int
    per_page: int


class RejectRequest(BaseModel):
    """Request body for rejecting a correction."""

    reason: str = Field(
        min_length=1, max_length=500, description="Reason for rejecting the correction"
    )


class ApproveResponse(BaseModel):
    """Response after approving a correction."""

    id: int
    correction_status: str
    is_verified: bool
    verified_at: str | None = None


class RejectResponse(BaseModel):
    """Response after rejecting a correction."""

    id: int
    correction_status: str
    rejection_reason: str
