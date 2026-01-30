"""HS Section model for tariff schedule sections."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.hs_chapter import HSChapter


class HSSection(Base):
    """Model for HS Sections (PHẦN).

    Sections are the top-level grouping in the Harmonized System.
    There are 21 sections (I-XXI) grouping chapters by broad product categories.

    Example: Section I - "ĐỘNG VẬT SỐNG; CÁC SẢN PHẨM TỪ ĐỘNG VẬT" (Live animals; Animal products)
    """

    __tablename__ = "hs_sections"

    id: Mapped[int] = mapped_column(primary_key=True)
    section_number: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    section_roman: Mapped[str] = mapped_column(String(10), nullable=False)  # I, II, III, etc.
    name_vn: Mapped[str] = mapped_column(Text, nullable=False)
    name_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes_vn: Mapped[str | None] = mapped_column(Text, nullable=True)  # Section notes (Chú giải)
    notes_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    chapters: Mapped[list["HSChapter"]] = relationship(
        "HSChapter",
        back_populates="section",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<HSSection(number={self.section_roman}, name='{self.name_vn[:30]}...')>"
