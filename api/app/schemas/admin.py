"""Admin schemas for request/response validation."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class RoleUpdateRequest(BaseModel):
    """Schema for updating a user's role."""

    role: str = Field(description="New role for the user")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate role is one of the allowed values."""
        if v not in ("user", "admin"):
            raise ValueError("Role must be 'user' or 'admin'")
        return v


class UserListItem(BaseModel):
    """Schema for a user item in the admin user list."""

    id: int
    email: str
    role: str
    created_at: datetime


class UserListResponse(BaseModel):
    """Schema for paginated user list response."""

    items: list[UserListItem]
    total: int
    page: int
    per_page: int
    pages: int


class AuditLogResponse(BaseModel):
    """Schema for an audit log entry response."""

    id: int
    admin_email: str | None
    action: str
    target_email: str | None
    details: dict | None
    created_at: datetime
