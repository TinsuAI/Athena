"""Admin API endpoints for user management."""

from typing import Any

from fastapi import APIRouter, Depends, Query
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.core.auth import require_admin
from app.core.redis import get_redis
from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.admin import (
    AdminCreateUserRequest,
    AdminUpdateUserRequest,
    AuditLogResponse,
    RoleUpdateRequest,
    UserStatusRequest,
)
from app.schemas.base import error_response, success_response
from app.services.admin_service import AdminService

router = APIRouter(prefix="/api/admin", tags=["admin"])


async def _is_role_change_rate_limited(admin_user_id: int, redis: Redis) -> bool:  # type: ignore[type-arg]
    """Check if the admin has exceeded the rate limit for role change requests.

    Limit: 10 role changes per minute per admin (prevents abuse).
    Uses Redis for distributed rate limiting across multiple workers/processes.
    """
    key = f"role_change_rate_limit:{admin_user_id}"
    count = await redis.incr(key)

    if count == 1:
        # First request in this window - set 60 second expiry
        await redis.expire(key, 60)

    # Allow up to 10 role changes per minute
    return count > 10


@router.get("/users", response_model=None)
async def list_users(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    search: str = Query(default=""),
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """List all users with pagination and optional email search. Requires admin role."""
    service = AdminService(db)
    result = await service.list_users(page=page, per_page=per_page, search=search)
    return success_response(result)


@router.post("/users", response_model=None)
async def create_user(
    body: AdminCreateUserRequest,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Create a new user account. Requires admin role."""
    admin_id = current_user["id"]
    service = AdminService(db)
    result = await service.create_user(
        admin_user_id=admin_id,
        email=body.email,
        password=body.password,
        role=body.role,
    )

    if result is None:
        return error_response(
            type_uri="https://athena.example/errors/validation",
            title="Bad Request",
            status=400,
            detail="Email already exists",
            instance="/api/admin/users",
        )

    return success_response(result)


@router.patch("/users/{user_id}", response_model=None)
async def update_user(
    user_id: int,
    body: AdminUpdateUserRequest,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Update a user's email and/or role. Requires admin role."""
    admin_id = current_user["id"]
    service = AdminService(db)
    result = await service.update_user(
        admin_user_id=admin_id,
        target_user_id=user_id,
        email=body.email,
        role=body.role,
    )

    if result == "not_found":
        return error_response(
            type_uri="https://athena.example/errors/not-found",
            title="User Not Found",
            status=404,
            detail=f"No user with id {user_id} exists.",
            instance=f"/api/admin/users/{user_id}",
        )

    if result == "email_exists":
        return error_response(
            type_uri="https://athena.example/errors/validation",
            title="Bad Request",
            status=400,
            detail="Email already exists",
            instance=f"/api/admin/users/{user_id}",
        )

    return success_response(result)


@router.patch("/users/{user_id}/status", response_model=None)
async def toggle_user_status(
    user_id: int,
    body: UserStatusRequest,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Toggle a user's active status. Requires admin role."""
    admin_id = current_user["id"]
    service = AdminService(db)
    result = await service.toggle_user_status(
        admin_user_id=admin_id,
        target_user_id=user_id,
        is_active=body.is_active,
    )

    if result == "self_deactivation":
        return error_response(
            type_uri="https://athena.example/errors/validation",
            title="Bad Request",
            status=400,
            detail="Khong the vo hieu hoa tai khoan cua chinh minh",
            instance=f"/api/admin/users/{user_id}/status",
        )

    if result == "not_found":
        return error_response(
            type_uri="https://athena.example/errors/not-found",
            title="User Not Found",
            status=404,
            detail=f"No user with id {user_id} exists.",
            instance=f"/api/admin/users/{user_id}/status",
        )

    return success_response(result)


@router.patch("/users/{user_id}/role", response_model=None)
async def update_user_role(
    user_id: int,
    body: RoleUpdateRequest,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis),  # type: ignore[type-arg]
) -> dict[str, Any]:
    """Update a user's role. Requires admin role. Rate limited to 10 changes per minute."""
    admin_id = current_user["id"]

    # Rate limiting check
    if await _is_role_change_rate_limited(admin_id, redis):
        return error_response(
            type_uri="https://athena.example/errors/rate-limit",
            title="Too Many Requests",
            status=429,
            detail="Role change rate limit exceeded. Maximum 10 changes per minute.",
            instance=f"/api/admin/users/{user_id}/role",
        )

    service = AdminService(db)

    try:
        updated = await service.update_user_role(
            admin_user_id=admin_id,
            target_user_id=user_id,
            new_role=body.role,
        )
    except ValueError as e:
        return error_response(
            type_uri="https://athena.example/errors/validation",
            title="Bad Request",
            status=400,
            detail=str(e),
            instance=f"/api/admin/users/{user_id}/role",
        )

    if updated is None:
        return error_response(
            type_uri="https://athena.example/errors/not-found",
            title="User Not Found",
            status=404,
            detail=f"No user with id {user_id} exists.",
            instance=f"/api/admin/users/{user_id}/role",
        )

    return success_response(updated.model_dump(mode="json"))


@router.get("/audit-log", response_model=None)
async def list_audit_log(
    limit: int = Query(default=50, ge=1, le=200),
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """List recent audit log entries. Requires admin role."""
    audit_repo = AuditLogRepository(db)
    entries = await audit_repo.list_recent(limit=limit)

    # Use eager-loaded relationships (no N+1 queries)
    items = []
    for entry in entries:
        items.append(
            AuditLogResponse(
                id=entry.id,
                admin_email=entry.admin_user.email if entry.admin_user else None,
                action=entry.action,
                target_email=entry.target_user.email if entry.target_user else None,
                details=entry.details,
                created_at=entry.created_at,
            ).model_dump(mode="json")
        )

    return success_response(items)
