"""Create permission tables with seed data

Revision ID: create_permission_tables
Revises: add_correction_workflow_columns
Create Date: 2026-02-18

Creates permissions, role_permissions, and user_permission_overrides tables.
Seeds default permission codes and role-permission mappings.
"""

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "create_permission_tables"
down_revision: Union[str, None] = "add_correction_workflow_columns"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    # Create permissions table
    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    # Create role_permissions table
    op.create_table(
        "role_permissions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("permission_code", sa.String(50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["permission_code"], ["permissions.code"]),
        sa.UniqueConstraint("role", "permission_code"),
    )

    # Create user_permission_overrides table
    op.create_table(
        "user_permission_overrides",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("permission_code", sa.String(50), nullable=False),
        sa.Column("granted", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["permission_code"], ["permissions.code"]),
        sa.UniqueConstraint("user_id", "permission_code"),
    )

    # Seed default permissions
    op.execute(
        """
        INSERT INTO permissions (code, name, description) VALUES
        ('correction.submit', 'Gui chinh sua', 'Can submit corrections to lookup records'),
        ('correction.approve', 'Phe duyet chinh sua', 'Can approve or reject pending corrections'),
        ('user.manage', 'Quan ly nguoi dung', 'Can create, edit, deactivate users'),
        ('data.manage', 'Quan ly du lieu', 'Can upload and manage tariff data'),
        ('lookup.view_all', 'Xem tat ca tra cuu', 'Can view all lookup records, not just own')
        """
    )

    # Seed role_permissions: user role
    op.execute(
        """
        INSERT INTO role_permissions (role, permission_code) VALUES
        ('user', 'correction.submit')
        """
    )

    # Seed role_permissions: expert role
    op.execute(
        """
        INSERT INTO role_permissions (role, permission_code) VALUES
        ('expert', 'correction.submit'),
        ('expert', 'correction.approve'),
        ('expert', 'lookup.view_all')
        """
    )

    # Seed role_permissions: admin role (ALL permissions)
    op.execute(
        """
        INSERT INTO role_permissions (role, permission_code) VALUES
        ('admin', 'correction.submit'),
        ('admin', 'correction.approve'),
        ('admin', 'user.manage'),
        ('admin', 'data.manage'),
        ('admin', 'lookup.view_all')
        """
    )


def downgrade() -> None:
    op.drop_table("user_permission_overrides")
    op.drop_table("role_permissions")
    op.drop_table("permissions")
