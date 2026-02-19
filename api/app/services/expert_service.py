"""Expert service for correction approval workflow business logic."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lookup_record import LookupRecord
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.lookup_record_repository import LookupRecordRepository


class ExpertService:
    """Service for expert correction approval operations.

    Handles business logic for listing, approving, and rejecting
    pending corrections. All database operations are delegated to repositories.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.lookup_repo = LookupRecordRepository(session)
        self.audit_repo = AuditLogRepository(session)

    async def list_pending_corrections(
        self, page: int = 1, per_page: int = 20
    ) -> dict:
        """List pending corrections with pagination.

        Args:
            page: Page number (1-indexed).
            per_page: Items per page.

        Returns:
            Dict with items, total, page, per_page for response serialization.
        """
        offset = (page - 1) * per_page
        records = await self.lookup_repo.get_pending_corrections(
            limit=per_page, offset=offset
        )
        total = await self.lookup_repo.count_pending_corrections()

        items = []
        for record in records:
            items.append(
                {
                    "id": record.id,
                    "query_text": record.query_text,
                    "matched_hs_code": (
                        record.matched_hs_code.code
                        if record.matched_hs_code
                        else None
                    ),
                    "matched_description_vn": (
                        record.matched_hs_code.description_vn
                        if record.matched_hs_code
                        else None
                    ),
                    "matched_description_en": (
                        record.matched_hs_code.description_en
                        if record.matched_hs_code
                        else None
                    ),
                    "correct_hs_code": (
                        record.correct_hs_code.code
                        if record.correct_hs_code
                        else None
                    ),
                    "correct_description_vn": (
                        record.correct_hs_code.description_vn
                        if record.correct_hs_code
                        else None
                    ),
                    "correct_description_en": (
                        record.correct_hs_code.description_en
                        if record.correct_hs_code
                        else None
                    ),
                    "submitter_email": (
                        record.submitted_by_user.email
                        if record.submitted_by_user
                        else None
                    ),
                    "submitted_at": record.created_at.isoformat(),
                    "notes": record.notes,
                }
            )

        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    async def approve_correction(
        self, record_id: int, expert_user_id: int
    ) -> LookupRecord:
        """Approve a pending correction.

        Validates the record exists and is in 'pending' status,
        then approves it and creates an audit log entry.

        Args:
            record_id: ID of the lookup record to approve.
            expert_user_id: ID of the expert performing the approval.

        Returns:
            The updated LookupRecord.

        Raises:
            ValueError: If record not found or not in pending status.
        """
        record = await self.lookup_repo.find_by_id(record_id)
        if not record:
            raise ValueError("Record not found")
        if record.correction_status != "pending":
            raise ValueError("Only pending corrections can be approved")

        updated = await self.lookup_repo.approve_correction(
            record_id, expert_user_id
        )

        await self.audit_repo.create(
            admin_user_id=expert_user_id,
            action="correction_approved",
            target_user_id=None,
            details={
                "lookup_record_id": record_id,
                "correct_hs_code_id": record.correct_hs_code_id,
            },
        )

        return updated

    async def reject_correction(
        self, record_id: int, expert_user_id: int, reason: str
    ) -> LookupRecord:
        """Reject a pending correction.

        Validates the record exists and is in 'pending' status,
        then rejects it with the given reason and creates an audit log entry.

        Args:
            record_id: ID of the lookup record to reject.
            expert_user_id: ID of the expert performing the rejection.
            reason: Reason for rejecting the correction.

        Returns:
            The updated LookupRecord.

        Raises:
            ValueError: If record not found or not in pending status.
        """
        record = await self.lookup_repo.find_by_id(record_id)
        if not record:
            raise ValueError("Record not found")
        if record.correction_status != "pending":
            raise ValueError("Only pending corrections can be rejected")

        updated = await self.lookup_repo.reject_correction(record_id, reason)

        await self.audit_repo.create(
            admin_user_id=expert_user_id,
            action="correction_rejected",
            target_user_id=None,
            details={
                "lookup_record_id": record_id,
                "reason": reason,
            },
        )

        return updated
