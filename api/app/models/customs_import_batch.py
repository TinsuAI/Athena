"""Customs import batch model for tracking import operations."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class CustomsImportBatch(Base):
    """Tracks metadata for each customs data import operation.

    Records file name, user who triggered the import, row counts
    (imported, duplicates, unmatched, errors), and timing.
    """

    __tablename__ = "customs_import_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    imported_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_imported: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duplicates_skipped: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unmatched_codes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    errors_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    imported_by_user: Mapped["User | None"] = relationship(
        "User", foreign_keys=[imported_by_user_id]
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<CustomsImportBatch(id={self.id}, file='{self.file_name}', "
            f"imported={self.records_imported})>"
        )
