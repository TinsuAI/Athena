"""Favorite model for user bookmarked HS codes."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Favorite(Base):
    """User favorite HS code bookmark."""

    __tablename__ = "favorites"
    __table_args__ = (
        UniqueConstraint("user_id", "hs_code_id", name="uq_favorites_user_hs_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    hs_code_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("hs_codes.id"), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships for eager loading
    hs_code = relationship("HSCode", lazy="selectin")
