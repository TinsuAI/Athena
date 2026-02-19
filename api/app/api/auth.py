"""Authentication API endpoints."""

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.core.config import Settings, get_settings
from app.core.redis import get_redis
from app.schemas.base import error_response, success_response
from app.schemas.user import (
    PasswordResetConfirm,
    PasswordResetRequest,
    UserCreate,
    UserLogin,
)
from app.services.auth_service import AuthService, InactiveUserError

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Rate limit constants for forgot-password (3 requests per email per hour)
_RATE_LIMIT_MAX = 3
_RATE_LIMIT_WINDOW = 3600  # 1 hour in seconds


@router.post("/register")
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Register a new user account."""
    service = AuthService(db)
    result = await service.register_user(user_data)
    if result is None:
        return error_response(
            type_uri="https://athena.example/errors/validation",
            title="Email Already Registered",
            status=409,
            detail="An account with this email already exists. Please log in instead.",
            instance="/api/auth/register",
        )
    return success_response(result.model_dump(mode="json"))


async def _is_rate_limited(email: str, redis: Redis) -> bool:
    """Check if the email has exceeded the rate limit for password reset requests.

    Uses Redis for distributed rate limiting across multiple workers/processes.
    """
    key = f"reset_rate_limit:{email}"
    count = await redis.incr(key)

    if count == 1:
        # First request - set expiry
        await redis.expire(key, _RATE_LIMIT_WINDOW)

    return count > _RATE_LIMIT_MAX


@router.post("/login")
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Authenticate a user and return user data.

    Called by NextAuth.js authorize() callback to validate credentials.
    """
    service = AuthService(db)
    try:
        result = await service.authenticate_user(credentials.email, credentials.password)
    except InactiveUserError:
        return error_response(
            type_uri="https://athena.example/errors/account-deactivated",
            title="Account Deactivated",
            status=403,
            detail="Tai khoan da bi vo hieu hoa",
            instance="/api/auth/login",
        )
    if result is None:
        return error_response(
            type_uri="https://athena.example/errors/authentication",
            title="Invalid Credentials",
            status=401,
            detail="Invalid email or password.",
            instance="/api/auth/login",
        )
    return success_response(result.model_dump(mode="json"))


@router.post("/forgot-password")
async def forgot_password(
    data: PasswordResetRequest,
    db: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
    redis: Redis = Depends(get_redis),
) -> dict:
    """Request a password reset email.

    Always returns success regardless of whether the email exists (prevents enumeration).
    Rate limited to 3 requests per email per hour (distributed via Redis).
    """
    if await _is_rate_limited(data.email, redis):
        return error_response(
            type_uri="https://athena.example/errors/rate-limit",
            title="Too Many Requests",
            status=429,
            detail="Too many password reset requests. Please try again later.",
            instance="/api/auth/forgot-password",
        )

    service = AuthService(db, settings=settings)
    email_sent = await service.request_password_reset(data.email)

    if not email_sent:
        return error_response(
            type_uri="https://athena.example/errors/email-failure",
            title="Email Service Error",
            status=503,
            detail="Failed to send reset email. Please try again later.",
            instance="/api/auth/forgot-password",
        )

    # Always return success to prevent email enumeration
    return success_response(
        {"message": "If this email exists, a reset link has been sent"}
    )


@router.post("/reset-password")
async def reset_password(
    data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Reset a user's password using a valid reset token."""
    service = AuthService(db)
    result = await service.reset_password(data.token, data.password)

    if not result:
        return error_response(
            type_uri="https://athena.example/errors/invalid-token",
            title="Invalid or Expired Token",
            status=400,
            detail="This reset link has expired or is invalid. Please request a new one.",
            instance="/api/auth/reset-password",
        )

    return success_response({"message": "Password has been reset successfully"})
