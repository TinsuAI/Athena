"""HS Heading model for tariff schedule headings (4-digit codes)."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.hs_chapter import HSChapter
    from app.models.hs_subheading import HSSubheading


class HSHeading(Base):
    """Model for HS Headings (Nhóm) - 4-digit codes.

    Headings are 4-digit groupings within chapters.
    They represent the international HS standard level.

    Example: 0101 - "Ngựa, lừa, la sống" (Live horses, asses, mules)
    """

    __tablename__ = "hs_headings"

    id: Mapped[int] = mapped_column(primary_key=True)
    heading_code: Mapped[str] = mapped_column(String(4), nullable=False, unique=True, index=True)
    chapter_id: Mapped[int] = mapped_column(
        ForeignKey("hs_chapters.id"),
        nullable=False,
        index=True
    )
    name_vn: Mapped[str] = mapped_column(Text, nullable=False)
    name_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    chapter: Mapped["HSChapter"] = relationship(
        "HSChapter",
        back_populates="headings"
    )
    subheadings: Mapped[list["HSSubheading"]] = relationship(
        "HSSubheading",
        back_populates="heading",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<HSHeading(code='{self.heading_code}', name='{self.name_vn[:30]}...')>"
