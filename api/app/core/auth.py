"""JWT validation for NextAuth.js tokens on FastAPI side."""

from fastapi import HTTPException, Request
from fastapi_nextauth_jwt import NextAuthJWT

from app.core.config import get_settings

settings = get_settings()

JWT = NextAuthJWT(secret=settings.nextauth_secret)


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
