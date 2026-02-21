"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.browse import router as browse_router
from app.api.corrections import router as corrections_router
from app.api.favorites import router as favorites_router
from app.api.expert import router as expert_router
from app.api.history import router as history_router
from app.api.hs_codes import router as hs_codes_router
from app.api.lookups import router as lookups_router
from app.api.search import router as search_router
from app.core.config import get_settings
from app.core.database import engine
from app.core.rate_limiter import RateLimitMiddleware
from app.core.redis import check_redis_connection, redis_pool
from app.schemas.base import ApiResponse, HealthData, success_response

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    """Application lifespan handler for startup/shutdown."""
    # Startup
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    description="HS Code Lookup API with semantic search",
    version="0.1.0",
    lifespan=lifespan,
)

# Rate limiting middleware (NFR-SEC6: 100 req/min per user)
app.add_middleware(RateLimitMiddleware, redis_pool=redis_pool)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(admin_router)
app.include_router(auth_router)
app.include_router(browse_router)
app.include_router(corrections_router)
app.include_router(expert_router)
app.include_router(favorites_router)
app.include_router(history_router)
app.include_router(hs_codes_router)
app.include_router(lookups_router)
app.include_router(search_router)


@app.get("/health", response_model=ApiResponse[HealthData])
async def health_check() -> dict[str, Any]:
    """Health check endpoint returning service status."""
    # Check database connection
    db_healthy = False
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            db_healthy = True
    except Exception:
        pass

    # Check Redis connection
    redis_healthy = await check_redis_connection()

    health_data = HealthData(
        status="healthy",
        database=db_healthy,
        redis=redis_healthy,
    )

    return success_response(health_data.model_dump())
