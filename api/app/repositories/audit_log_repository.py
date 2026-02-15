"""Repository for audit log data access."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.audit_log import AuditLog


class AuditLogRepository:
    """Repository for audit_logs database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        admin_user_id: int,
        action: str,
        target_user_id: int | None = None,
        details: dict | None = None,
    ) -> AuditLog:
        """Create a new audit log entry."""
        entry = AuditLog(
            admin_user_id=admin_user_id,
            action=action,
            target_user_id=target_user_id,
            details=details,
        )
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def list_recent(self, limit: int = 50) -> list[AuditLog]:
        """Return recent audit log entries in descending order with eager-loaded users."""
        result = await self.session.execute(
            select(AuditLog)
            .options(
                selectinload(AuditLog.admin_user),
                selectinload(AuditLog.target_user),
            )
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
