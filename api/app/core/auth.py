"""JWT validation for NextAuth.js tokens on FastAPI side."""

from fastapi import HTTPException, Request
from fastapi_nextauth_jwt import NextAuthJWT

from app.core.config import get_settings

settings = get_settings()

JWT = NextAuthJWT(secret=settings.nextauth_secret)


async def require_admin(request: Request) -> dict:
    """Require admin role for endpoint access.

    Calls get_current_user() first (handles 401),
    then checks role == "admin" (handles 403).
    """
    user = await get_current_user(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


async def get_current_user(request: Request) -> dict:
    """Extract user from NextAuth JWT cookie.

    Returns dict with id, email, role from the decoded JWT token.
    Raises 401 if token is missing or invalid.
    """
    try:
        token = JWT(request)
        return {
            "id": token.get("id"),
            "email": token.get("email"),
            "role": token.get("role"),
        }
    except Exception as e:
        # Log JWT validation errors for debugging
        import logging

        logging.getLogger(__name__).warning(f"JWT validation failed: {e}")
        raise HTTPException(status_code=401, detail="Not authenticated")


async def require_authenticated(request: Request) -> dict:
    """Require any authenticated user (user/expert/admin).

    Semantic alias for get_current_user -- use in route declarations for clarity.
    """
    return await get_current_user(request)


async def require_expert(request: Request) -> dict:
    """Require expert or admin role.

    Calls get_current_user() first (handles 401),
    then checks role in ("expert", "admin") (handles 403).
    """
    user = await get_current_user(request)
    if user.get("role") not in ("expert", "admin"):
        raise HTTPException(status_code=403, detail="Expert access required")
    return user


async def get_optional_user(request: Request) -> dict | None:
    """Return user if authenticated, None otherwise. Never raises."""
    try:
        return await get_current_user(request)
    except HTTPException:
        return None
