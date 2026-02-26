"""Knowledge base service for verified HS code lookups."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.lookup_record_repository import (
    LookupRecordRepository,
    compute_query_hash,
)


@dataclass
class KBLookupResult:
    """Result from knowledge base lookup."""

    hs_code_id: int
    confidence: int  # 0-100
    similarity_score: float  # 1.0 for exact, 0.85-1.0 for similar
    lookup_record_id: int
    verified_by_user_id: int | None
    verified_at: datetime | None
    match_type: str  # "exact" or "similar"


class KnowledgeBaseService:
    """Service for looking up verified HS codes from the knowledge base.

    Checks verified expert corrections before falling back to AI search.
    Priority: exact hash -> containment -> pg_trgm similar -> None (AI fallback).
    """

    def __init__(self, session: AsyncSession):
        self.repo = LookupRecordRepository(session)

    async def lookup(self, query: str) -> KBLookupResult | None:
        """Look up a query in the verified knowledge base.

        Args:
            query: User search query text

        Returns:
            KBLookupResult if verified match found, None otherwise
        """
        query_hash = compute_query_hash(query)

        # Step 1: Exact hash match (fastest, <5ms)
        exact = await self.repo.find_verified_exact(query_hash)
        if exact:
            return KBLookupResult(
                hs_code_id=exact.correct_hs_code_id,
                confidence=100,
                similarity_score=1.0,
                lookup_record_id=exact.id,
                verified_by_user_id=exact.verified_by_user_id,
                verified_at=exact.verified_at,
                match_type="exact",
            )

        # Step 2: Containment match — short query found within long KB description (<50ms)
        containment = await self.repo.find_verified_containment(query)
        if containment:
            record, conf_score = containment[0]
            return KBLookupResult(
                hs_code_id=record.correct_hs_code_id,
                confidence=int(conf_score * 100),
                similarity_score=conf_score,
                lookup_record_id=record.id,
                verified_by_user_id=record.verified_by_user_id,
                verified_at=record.verified_at,
                match_type="containment",
            )

        # Step 3: Similar text match (pg_trgm, <50ms)
        similar = await self.repo.find_verified_similar(query, threshold=0.85)
        if similar:
            record, sim_score = similar[0]
            return KBLookupResult(
                hs_code_id=record.correct_hs_code_id,
                confidence=int(sim_score * 100),
                similarity_score=sim_score,
                lookup_record_id=record.id,
                verified_by_user_id=record.verified_by_user_id,
                verified_at=record.verified_at,
                match_type="similar",
            )

        # Step 4: No match - caller should fall back to AI search
        return None
