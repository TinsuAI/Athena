"""Repository for customs import batch queries and KB stats aggregation."""

from sqlalchemy import func, select, true
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customs_import_batch import CustomsImportBatch
from app.models.hs_chapter import HSChapter
from app.models.hs_code import HSCode
from app.models.hs_heading import HSHeading
from app.models.hs_subheading import HSSubheading
from app.models.lookup_record import LookupRecord
from app.models.user import User


class CustomsImportRepository:
    """Database queries for import history and knowledge base statistics."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_import_history(
        self, limit: int = 20, offset: int = 0
    ) -> tuple[list[dict], int]:
        """Return paginated import batch history with user email.

        Returns:
            Tuple of (list of batch dicts with imported_by_email, total count).
        """
        # Count total
        count_query = select(func.count(CustomsImportBatch.id))
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Fetch batches with user join
        query = (
            select(
                CustomsImportBatch.id,
                CustomsImportBatch.file_name,
                CustomsImportBatch.company_name,
                CustomsImportBatch.total_rows,
                CustomsImportBatch.records_imported,
                CustomsImportBatch.duplicates_skipped,
                CustomsImportBatch.unmatched_codes,
                CustomsImportBatch.errors_count,
                CustomsImportBatch.started_at,
                CustomsImportBatch.completed_at,
                User.email.label("imported_by_email"),
            )
            .outerjoin(User, CustomsImportBatch.imported_by_user_id == User.id)
            .order_by(CustomsImportBatch.started_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        rows = result.all()

        items = [
            {
                "id": row.id,
                "file_name": row.file_name,
                "company_name": row.company_name,
                "total_rows": row.total_rows,
                "records_imported": row.records_imported,
                "duplicates_skipped": row.duplicates_skipped,
                "unmatched_codes": row.unmatched_codes,
                "errors_count": row.errors_count,
                "started_at": row.started_at.isoformat() if row.started_at else None,
                "completed_at": row.completed_at.isoformat() if row.completed_at else None,
                "imported_by_email": row.imported_by_email,
            }
            for row in rows
        ]

        return items, total

    async def get_kb_stats(self) -> dict:
        """Return knowledge base quality statistics.

        Returns:
            Dict with total_verified, breakdown_by_method, and top_chapters.
        """
        # Total verified records
        total_query = select(func.count(LookupRecord.id)).where(
            LookupRecord.is_verified == true()
        )
        total_result = await self.session.execute(total_query)
        total_verified = total_result.scalar() or 0

        # Breakdown by search_method
        method_query = (
            select(
                LookupRecord.search_method,
                func.count(LookupRecord.id).label("count"),
            )
            .where(LookupRecord.is_verified == true())
            .group_by(LookupRecord.search_method)
        )
        method_result = await self.session.execute(method_query)
        breakdown_by_method = [
            {"search_method": row.search_method, "count": row.count}
            for row in method_result.all()
        ]

        # Top 10 chapters by KB coverage
        # Join through full hierarchy: lookup_records -> hs_codes -> subheadings -> headings -> chapters
        chapter_query = (
            select(
                HSChapter.chapter_code,
                HSChapter.name_vn,
                func.count(LookupRecord.id).label("record_count"),
            )
            .join(HSCode, LookupRecord.correct_hs_code_id == HSCode.id)
            .join(HSSubheading, HSCode.subheading_id == HSSubheading.id)
            .join(HSHeading, HSSubheading.heading_id == HSHeading.id)
            .join(HSChapter, HSHeading.chapter_id == HSChapter.id)
            .where(LookupRecord.is_verified == true())
            .group_by(HSChapter.chapter_code, HSChapter.name_vn)
            .order_by(func.count(LookupRecord.id).desc())
            .limit(10)
        )
        chapter_result = await self.session.execute(chapter_query)
        top_chapters = [
            {
                "chapter_code": row.chapter_code,
                "name_vn": row.name_vn,
                "record_count": row.record_count,
            }
            for row in chapter_result.all()
        ]

        return {
            "total_verified": total_verified,
            "breakdown_by_method": breakdown_by_method,
            "top_chapters": top_chapters,
        }

    async def get_recent_imports(self, limit: int = 5) -> list[dict]:
        """Return the most recent import batches for the dashboard.

        Returns:
            List of batch dicts with user email, ordered by most recent first.
        """
        query = (
            select(
                CustomsImportBatch.id,
                CustomsImportBatch.file_name,
                CustomsImportBatch.company_name,
                CustomsImportBatch.total_rows,
                CustomsImportBatch.records_imported,
                CustomsImportBatch.duplicates_skipped,
                CustomsImportBatch.unmatched_codes,
                CustomsImportBatch.errors_count,
                CustomsImportBatch.started_at,
                CustomsImportBatch.completed_at,
                User.email.label("imported_by_email"),
            )
            .outerjoin(User, CustomsImportBatch.imported_by_user_id == User.id)
            .order_by(CustomsImportBatch.started_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        rows = result.all()

        return [
            {
                "id": row.id,
                "file_name": row.file_name,
                "company_name": row.company_name,
                "total_rows": row.total_rows,
                "records_imported": row.records_imported,
                "duplicates_skipped": row.duplicates_skipped,
                "unmatched_codes": row.unmatched_codes,
                "errors_count": row.errors_count,
                "started_at": row.started_at.isoformat() if row.started_at else None,
                "completed_at": row.completed_at.isoformat() if row.completed_at else None,
                "imported_by_email": row.imported_by_email,
            }
            for row in rows
        ]
