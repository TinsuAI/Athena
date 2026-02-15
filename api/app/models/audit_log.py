"""Audit log model for tracking admin actions."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class AuditLog(Base):
    """Audit log entry for admin actions (NFR-SEC5)."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    admin_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    target_user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships for eager loading (prevents N+1 queries)
    admin_user: Mapped["User"] = relationship(
        "User", foreign_keys=[admin_user_id], lazy="noload"
    )
    target_user: Mapped["User | None"] = relationship(
        "User", foreign_keys=[target_user_id], lazy="noload"
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<AuditLog(id={self.id}, action='{self.action}', admin_user_id={self.admin_user_id})>"
