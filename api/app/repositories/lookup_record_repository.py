"""Repository for lookup record data access."""

import hashlib
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lookup_record import LookupRecord


def compute_query_hash(query_text: str) -> str:
    """Compute SHA-256 hash of normalized query text for deduplication."""
    normalized = query_text.strip().lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class LookupRecordRepository:
    """Repository for lookup_records database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, record: LookupRecord) -> LookupRecord:
        """Create a new lookup record."""
        self.session.add(record)
        await self.session.flush()
        return record

    async def find_by_query_hash(
        self, query_hash: str, within_hours: int = 24
    ) -> LookupRecord | None:
        """Find an existing lookup record by query hash within a time window."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=within_hours)
        result = await self.session.execute(
            select(LookupRecord)
            .where(
                LookupRecord.query_hash == query_hash,
                LookupRecord.created_at >= cutoff,
            )
            .order_by(LookupRecord.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_unverified(
        self, limit: int = 20, offset: int = 0
    ) -> list[LookupRecord]:
        """Get unverified lookup records, ordered by newest first."""
        result = await self.session.execute(
            select(LookupRecord)
            .where(LookupRecord.is_verified == False)  # noqa: E712
            .order_by(LookupRecord.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def count_unverified(self) -> int:
        """Count total unverified lookup records."""
        result = await self.session.execute(
            select(func.count(LookupRecord.id)).where(
                LookupRecord.is_verified == False  # noqa: E712
            )
        )
        return result.scalar_one()

    async def update(self, record: LookupRecord) -> LookupRecord:
        """Update an existing lookup record."""
        await self.session.flush()
        return record

    async def find_verified_exact(self, query_hash: str) -> LookupRecord | None:
        """Find a verified lookup record by exact query hash match.

        Returns the verified record with expert correction for exact hash match.
        """
        result = await self.session.execute(
            select(LookupRecord)
            .where(
                LookupRecord.query_hash == query_hash,
                LookupRecord.is_verified == True,  # noqa: E712
                LookupRecord.correct_hs_code_id.isnot(None),
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def find_verified_similar(
        self,
        query_text: str,
        threshold: float = 0.85,
        limit: int = 1,
    ) -> list[tuple[LookupRecord, float]]:
        """Find verified lookup records by pg_trgm text similarity.

        Returns list of (record, similarity_score) tuples ordered by similarity DESC.
        """
        similarity = func.similarity(LookupRecord.query_text, query_text)
        result = await self.session.execute(
            select(LookupRecord, similarity.label("similarity"))
            .where(
                LookupRecord.is_verified == True,  # noqa: E712
                LookupRecord.correct_hs_code_id.isnot(None),
                similarity >= threshold,
            )
            .order_by(similarity.desc())
            .limit(limit)
        )
        rows = result.all()
        return [(row.LookupRecord, row.similarity) for row in rows]

    async def touch_updated_at(self, record_id: int) -> None:
        """Update only the updated_at timestamp for deduplication."""
        await self.session.execute(
            update(LookupRecord)
            .where(LookupRecord.id == record_id)
            .values(updated_at=func.now())
        )
