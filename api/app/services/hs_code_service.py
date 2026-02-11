"""HS code business logic service."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hs_code import HSCode
from app.repositories.hs_code_repository import HSCodeRepository


class HSCodeService:
    """Service for HS code business logic."""

    def __init__(self, session: AsyncSession):
        """Initialize service with database session."""
        self.repository = HSCodeRepository(session)

    async def get_hs_code_with_rates(self, code: str) -> HSCode | None:
        """Get an HS code with all FTA rates.

        Args:
            code: The 8-digit HS code

        Returns:
            HS code with FTA rates, or None if not found
        """
        return await self.repository.get_with_fta_rates(code)

    async def validate_hs_code_format(self, code: str) -> tuple[bool, str | None]:
        """Validate HS code format.

        Args:
            code: The HS code to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(code) != 8:
            return False, f"HS code must be exactly 8 digits, got {len(code)} characters"

        if not code.isdigit():
            return False, "HS code must contain only digits"

        # Valid Vietnam HS codes start with 01-98 (not 00)
        chapter = code[:2]
        if chapter == "00":
            return False, "Invalid HS code: chapter code cannot be 00"

        return True, None

    async def get_total_count(self) -> int:
        """Get total number of HS codes in the system."""
        return await self.repository.count_all()

    async def autocomplete(
        self,
        query: str,
        limit: int = 10,
    ) -> list[HSCode]:
        """Search HS codes for autocomplete by code prefix or description.

        Args:
            query: Search query (code prefix or description substring)
            limit: Maximum number of results

        Returns:
            List of matching HS codes
        """
        return await self.repository.autocomplete(query=query, limit=limit)

    async def search_by_description(
        self,
        query: str,
        language: str = "both",
        limit: int = 20
    ) -> list[HSCode]:
        """Search HS codes by description.

        Args:
            query: Search query
            language: "vn", "en", or "both"
            limit: Maximum number of results

        Returns:
            List of matching HS codes
        """
        return await self.repository.search_by_description(
            query=query,
            language=language,
            limit=limit
        )
