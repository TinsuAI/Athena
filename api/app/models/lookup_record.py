"""Knowledge base lookup record model for expert correction."""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.hs_code import HSCode


class LookupRecord(Base):
    """Knowledge base lookup record for expert correction.

    Stores every user lookup with fields for expert correction,
    enabling verified human classifications to enhance future search results.
    """

    __tablename__ = "lookup_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    query_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    query_language: Mapped[str | None] = mapped_column(String(5), nullable=True)
    matched_hs_code_id: Mapped[int | None] = mapped_column(
        ForeignKey("hs_codes.id"), nullable=True
    )
    correct_hs_code_id: Mapped[int | None] = mapped_column(
        ForeignKey("hs_codes.id"), nullable=True
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    verified_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    search_method: Mapped[str] = mapped_column(String(20), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    classification_data: Mapped[dict[str, str] | None] = mapped_column(JSONB, nullable=True)
    practical_notes: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    process_logs: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships (no back_populates since HSCode doesn't reference LookupRecord)
    matched_hs_code: Mapped["HSCode | None"] = relationship(
        "HSCode",
        foreign_keys=[matched_hs_code_id],
    )
    correct_hs_code: Mapped["HSCode | None"] = relationship(
        "HSCode",
        foreign_keys=[correct_hs_code_id],
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<LookupRecord(id={self.id}, query='{self.query_text[:30]}...', "
            f"verified={self.is_verified})>"
        )
