"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.hs_codes import router as hs_codes_router
from app.core.config import get_settings
from app.core.database import engine
from app.core.redis import check_redis_connection
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

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(hs_codes_router)


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
