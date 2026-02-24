"""Add site_settings table

Revision ID: add_site_settings_table
Revises: add_oauth_columns_to_users
Create Date: 2026-02-23
"""
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "add_site_settings_table"
down_revision: Union[str, None] = "add_oauth_columns_to_users"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.create_table(
        "site_settings",
        sa.Column("key", sa.String(100), primary_key=True),
        sa.Column("value", sa.Text, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )
    # Seed the initial setting
    op.execute(
        "INSERT INTO site_settings (key, value, description) VALUES "
        "('search_requires_auth', 'true', 'Yêu cầu đăng nhập để sử dụng tính năng tìm kiếm')"
    )


def downgrade() -> None:
    op.drop_table("site_settings")
