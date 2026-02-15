"""Authentication API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.schemas.base import error_response, success_response
from app.schemas.user import UserCreate, UserLogin
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])


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


@router.post("/login")
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Authenticate a user and return user data.

    Called by NextAuth.js authorize() callback to validate credentials.
    """
    service = AuthService(db)
    result = await service.authenticate_user(credentials.email, credentials.password)
    if result is None:
        return error_response(
            type_uri="https://athena.example/errors/authentication",
            title="Invalid Credentials",
            status=401,
            detail="Invalid email or password.",
            instance="/api/auth/login",
        )
    return success_response(result.model_dump(mode="json"))
