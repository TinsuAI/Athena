"""User schemas for request/response validation."""

import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator


class UserCreate(BaseModel):
    """Schema for user registration request."""

    email: str = Field(description="User email address")
    password: str = Field(min_length=8, description="Password (min 8 characters)")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, v):
            raise ValueError("Please enter a valid email address")
        return v.lower().strip()


class UserResponse(BaseModel):
    """Schema for user data in API responses."""

    id: int
    email: str
    role: str
    created_at: datetime


class UserLogin(BaseModel):
    """Schema for user login request."""

    email: str = Field(description="User email address")
    password: str = Field(description="User password")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, v):
            raise ValueError("Please enter a valid email address")
        return v.lower().strip()


class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""

    email: str = Field(description="Email address for password reset")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, v):
            raise ValueError("Please enter a valid email address")
        return v.lower().strip()


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""

    token: str = Field(description="Password reset token from email")
    password: str = Field(min_length=8, description="New password (min 8 characters)")
    password_confirm: str = Field(description="Password confirmation")

    @model_validator(mode="after")
    def passwords_match(self) -> "PasswordResetConfirm":
        """Validate that password and password_confirm match."""
        if self.password != self.password_confirm:
            raise ValueError("Passwords do not match")
        return self
