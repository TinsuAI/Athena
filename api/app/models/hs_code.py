"""HS code model for harmonized system codes and tariff data."""

from datetime import datetime
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import DECIMAL

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.data_version import DataVersion
    from app.models.fta_rate import FTARate
    from app.models.hs_subheading import HSSubheading


class HSCode(Base):
    """Model for HS codes (Mã hàng) - 8-digit national tariff lines.

    HS codes are the most detailed level of the tariff classification.
    They are 8-digit codes specific to Vietnam's national tariff schedule.

    Example: 01012100 - "- - Loại thuần chủng để nhân giống" (-- Pure-bred breeding animals)
    """

    __tablename__ = "hs_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(8), unique=True, nullable=False, index=True)
    subheading_id: Mapped[int | None] = mapped_column(
        ForeignKey("hs_subheadings.id"),
        nullable=True,  # Nullable during migration, should be required after
        index=True
    )
    description_vn: Mapped[str] = mapped_column(Text, nullable=False)
    description_en: Mapped[str] = mapped_column(Text, nullable=False)
    unit: Mapped[str | None] = mapped_column(Text, nullable=True)
    duty_rate: Mapped[float] = mapped_column(DECIMAL(5, 2), nullable=False)
    vat_rate: Mapped[float] = mapped_column(DECIMAL(5, 2), nullable=False)
    export_duty_rate: Mapped[str | None] = mapped_column(String, nullable=True)
    special_consumption_tax: Mapped[str | None] = mapped_column(String, nullable=True)
    environmental_tax: Mapped[str | None] = mapped_column(String, nullable=True)
    vat_reduction: Mapped[str | None] = mapped_column(String, nullable=True)
    policy_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    indent_level: Mapped[int | None] = mapped_column(Integer, default=0, nullable=True)  # Number of leading dashes
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(3072),
        nullable=True
    )
    data_version_id: Mapped[int] = mapped_column(
        ForeignKey("data_versions.id"),
        nullable=False,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    subheading: Mapped["HSSubheading | None"] = relationship(
        "HSSubheading",
        back_populates="hs_codes"
    )
    data_version: Mapped["DataVersion"] = relationship(
        "DataVersion",
        back_populates="hs_codes"
    )
    fta_rates: Mapped[list["FTARate"]] = relationship(
        "FTARate",
        back_populates="hs_code",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<HSCode(code='{self.code}', description_vn='{self.description_vn[:30]}...')>"
