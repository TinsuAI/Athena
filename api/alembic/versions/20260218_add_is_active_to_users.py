"""Add is_active column to users table

Revision ID: add_is_active_to_users
Revises: add_nlm_raw_response
Create Date: 2026-02-18

Adds is_active boolean column (default True) to users table for account deactivation.
Existing users get is_active = true via server_default.
"""

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "add_is_active_to_users"
down_revision: Union[str, None] = "add_nlm_raw_response"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("users", "is_active")
