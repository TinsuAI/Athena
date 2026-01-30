"""HS Subheading model for tariff schedule subheadings (6-digit codes)."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.hs_code import HSCode
    from app.models.hs_heading import HSHeading


class HSSubheading(Base):
    """Model for HS Subheadings (Phân nhóm) - 6-digit codes.

    Subheadings are 6-digit groupings within headings.
    This level represents the international HS subheading standard.

    Example: 010121 - "- - Loại thuần chủng để nhân giống" (-- Pure-bred breeding animals)
    """

    __tablename__ = "hs_subheadings"

    id: Mapped[int] = mapped_column(primary_key=True)
    subheading_code: Mapped[str] = mapped_column(String(6), nullable=False, unique=True, index=True)
    heading_id: Mapped[int] = mapped_column(
        ForeignKey("hs_headings.id"),
        nullable=False,
        index=True
    )
    name_vn: Mapped[str] = mapped_column(Text, nullable=False)
    name_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    indent_level: Mapped[int | None] = mapped_column(default=0, nullable=True)  # Number of leading dashes
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    heading: Mapped["HSHeading"] = relationship(
        "HSHeading",
        back_populates="subheadings"
    )
    hs_codes: Mapped[list["HSCode"]] = relationship(
        "HSCode",
        back_populates="subheading",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<HSSubheading(code='{self.subheading_code}', name='{self.name_vn[:30]}...')>"
