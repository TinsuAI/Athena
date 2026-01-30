"""HS Chapter model for tariff schedule chapters."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.hs_heading import HSHeading
    from app.models.hs_section import HSSection


class HSChapter(Base):
    """Model for HS Chapters (Chương).

    Chapters are 2-digit groupings within sections.
    There are 97 chapters (01-97) plus special provisions (98-99).

    Example: Chapter 01 - "Động vật sống" (Live animals)
    """

    __tablename__ = "hs_chapters"

    id: Mapped[int] = mapped_column(primary_key=True)
    chapter_code: Mapped[str] = mapped_column(String(2), nullable=False, unique=True, index=True)
    section_id: Mapped[int] = mapped_column(
        ForeignKey("hs_sections.id"),
        nullable=False,
        index=True
    )
    name_vn: Mapped[str] = mapped_column(Text, nullable=False)
    name_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes_vn: Mapped[str | None] = mapped_column(Text, nullable=True)  # Chapter notes (Chú giải)
    notes_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    section: Mapped["HSSection"] = relationship(
        "HSSection",
        back_populates="chapters"
    )
    headings: Mapped[list["HSHeading"]] = relationship(
        "HSHeading",
        back_populates="chapter",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<HSChapter(code='{self.chapter_code}', name='{self.name_vn[:30]}...')>"
