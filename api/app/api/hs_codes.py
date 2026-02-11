"""HS code API endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.base import ApiResponse, error_response, success_response
from app.schemas.hs_code import HSCodeAutocompleteItem, HSCodeSchema
from app.services.hs_code_service import HSCodeService

router = APIRouter(prefix="/api/hs-codes", tags=["hs-codes"])


@router.get(
    "/autocomplete",
    response_model=ApiResponse[list[HSCodeAutocompleteItem]],
    summary="Autocomplete HS codes",
    description="Search HS codes by code prefix or description substring for autocomplete.",
)
async def autocomplete_hs_codes(
    q: str = Query(default="", max_length=200, description="Search query"),
    limit: int = Query(default=10, ge=1, le=50, description="Maximum results"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Search HS codes for autocomplete by code prefix or description."""
    if not q.strip():
        return success_response([])

    service = HSCodeService(db)
    results = await service.autocomplete(q.strip(), limit=limit)

    items = [
        HSCodeAutocompleteItem.model_validate(r).model_dump() for r in results
    ]

    return success_response(items)


@router.get("/{code}", response_model=ApiResponse[HSCodeSchema])
async def get_hs_code(
    code: str,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get an HS code by its code with all FTA rates.

    Args:
        code: The 8-digit HS code
        db: Database session

    Returns:
        HS code with FTA rates in envelope format

    Raises:
        HTTPException: 404 if HS code not found
    """
    # Create service instance
    service = HSCodeService(db)

    # Validate code format
    is_valid, error_message = await service.validate_hs_code_format(code)
    if not is_valid:
        return error_response(
            type_uri="https://athena.example/errors/invalid-hs-code",
            title="Invalid HS Code Format",
            status=status.HTTP_400_BAD_REQUEST,
            detail=error_message or "Invalid HS code format",
            instance=f"/api/hs-codes/{code}"
        )

    # Get HS code from service
    hs_code = await service.get_hs_code_with_rates(code)

    if not hs_code:
        return error_response(
            type_uri="https://athena.example/errors/not-found",
            title="Not Found",
            status=status.HTTP_404_NOT_FOUND,
            detail=f"HS code '{code}' not found in database",
            instance=f"/api/hs-codes/{code}"
        )

    # Convert to Pydantic schema and return in envelope format
    # Note: No extra wrapper - direct schema in data field per architecture
    hs_code_schema = HSCodeSchema.model_validate(hs_code)

    return success_response(data=hs_code_schema.model_dump())
