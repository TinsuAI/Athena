"""Base schemas for API envelope responses following RFC 7807."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiError(BaseModel):
    """RFC 7807 Problem Details error format."""

    type: str = Field(description="URI reference identifying the problem type")
    title: str = Field(description="Short human-readable summary")
    status: int = Field(description="HTTP status code")
    detail: str = Field(description="Human-readable explanation specific to this occurrence")
    instance: str = Field(description="URI reference identifying the specific occurrence")


class ApiResponse(BaseModel, Generic[T]):
    """Standard envelope response format for all API endpoints."""

    success: bool = Field(description="Whether the request was successful")
    data: T | None = Field(default=None, description="Response payload when successful")
    error: ApiError | None = Field(default=None, description="Error details when unsuccessful")


class HealthData(BaseModel):
    """Health check response data."""

    status: str = Field(default="healthy")
    database: bool = Field(default=False, description="Database connection status")
    redis: bool = Field(default=False, description="Redis connection status")


def success_response(data: Any) -> dict[str, Any]:
    """Create a successful API response."""
    return {"success": True, "data": data, "error": None}


def error_response(
    type_uri: str,
    title: str,
    status: int,
    detail: str,
    instance: str,
) -> dict[str, Any]:
    """Create an error API response following RFC 7807."""
    return {
        "success": False,
        "data": None,
        "error": {
            "type": type_uri,
            "title": title,
            "status": status,
            "detail": detail,
            "instance": instance,
        },
    }
