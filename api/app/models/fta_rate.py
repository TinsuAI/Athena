"""FTA rate model for free trade agreement preferential rates."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import DECIMAL

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.hs_code import HSCode


class FTARate(Base):
    """Model for FTA preferential rates linked to HS codes."""

    __tablename__ = "fta_rates"

    id: Mapped[int] = mapped_column(primary_key=True)
    hs_code_id: Mapped[int] = mapped_column(
        ForeignKey("hs_codes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    agreement_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True
    )
    preferential_rate: Mapped[float] = mapped_column(DECIMAL(5, 2), nullable=False)
    conditions: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    hs_code: Mapped["HSCode"] = relationship(
        "HSCode",
        back_populates="fta_rates"
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<FTARate(agreement='{self.agreement_code}', rate={self.preferential_rate})>"
