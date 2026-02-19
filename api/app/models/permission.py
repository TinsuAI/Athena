"""Permission models for role-based and per-user permission management."""

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Permission(Base):
    """Predefined permission code."""

    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class RolePermission(Base):
    """Default permission assigned to a role."""

    __tablename__ = "role_permissions"
    __table_args__ = (UniqueConstraint("role", "permission_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    permission_code: Mapped[str] = mapped_column(
        String(50), ForeignKey("permissions.code"), nullable=False
    )


class UserPermissionOverride(Base):
    """Per-user permission grant or revocation (overrides role default)."""

    __tablename__ = "user_permission_overrides"
    __table_args__ = (UniqueConstraint("user_id", "permission_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    permission_code: Mapped[str] = mapped_column(
        String(50), ForeignKey("permissions.code"), nullable=False
    )
    granted: Mapped[bool] = mapped_column(Boolean, nullable=False)
