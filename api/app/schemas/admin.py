"""Admin schemas for request/response validation."""

import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class RoleUpdateRequest(BaseModel):
    """Schema for updating a user's role."""

    role: str = Field(description="New role for the user")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate role is one of the allowed values."""
        if v not in ("user", "expert", "admin"):
            raise ValueError("Role must be 'user', 'expert', or 'admin'")
        return v


class AdminCreateUserRequest(BaseModel):
    """Schema for admin creating a new user."""

    email: str = Field(description="User email address")
    password: str = Field(min_length=8, description="Temporary password (min 8 characters)")
    role: str = Field(default="user", description="User role")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, v):
            raise ValueError("Please enter a valid email address")
        return v.lower().strip()

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate role is one of the allowed values."""
        if v not in ("user", "expert", "admin"):
            raise ValueError("Role must be 'user', 'expert', or 'admin'")
        return v


class AdminUpdateUserRequest(BaseModel):
    """Schema for admin updating a user's profile."""

    email: str | None = Field(default=None, description="New email address")
    role: str | None = Field(default=None, description="New role")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        """Validate email format if provided."""
        if v is None:
            return None
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, v):
            raise ValueError("Please enter a valid email address")
        return v.lower().strip()

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str | None) -> str | None:
        """Validate role is one of the allowed values if provided."""
        if v is None:
            return None
        if v not in ("user", "expert", "admin"):
            raise ValueError("Role must be 'user', 'expert', or 'admin'")
        return v


class UserStatusRequest(BaseModel):
    """Schema for toggling user active status."""

    is_active: bool = Field(description="Whether user is active")


class UserListItem(BaseModel):
    """Schema for a user item in the admin user list."""

    id: int
    email: str
    role: str
    is_active: bool
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


# --- Permission management schemas ---


class PermissionItem(BaseModel):
    """A single permission definition."""

    code: str
    name: str
    description: str | None = None


class RolePermissionsItem(BaseModel):
    """A role with its permission codes."""

    role: str
    permissions: list[str]


class RolePermissionsListResponse(BaseModel):
    """Response for listing all role permissions."""

    all_permissions: list[PermissionItem]
    roles: list[RolePermissionsItem]


class UpdateRolePermissionsRequest(BaseModel):
    """Request to update a role's permissions."""

    permissions: list[str]


class PermissionOverrideItem(BaseModel):
    """A single user permission override."""

    code: str
    granted: bool


class UserPermissionsResponse(BaseModel):
    """Response for a user's effective permissions."""

    user_id: int
    role: str
    role_permissions: list[str]
    overrides: list[PermissionOverrideItem]
    effective: list[str]


class UpdateUserPermissionsRequest(BaseModel):
    """Request to update a user's permission overrides."""

    overrides: list[PermissionOverrideItem]
