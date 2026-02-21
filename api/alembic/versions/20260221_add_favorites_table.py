"""Add favorites table

Revision ID: add_favorites_table
Revises: create_permission_tables
Create Date: 2026-02-21

Creates favorites table for user bookmarked HS codes.
Includes unique constraint on (user_id, hs_code_id) and index on user_id.
"""

from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision: str = "add_favorites_table"
down_revision: Union[str, None] = "create_permission_tables"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.create_table(
        "favorites",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("hs_code_id", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["hs_code_id"], ["hs_codes.id"]),
        sa.UniqueConstraint("user_id", "hs_code_id", name="uq_favorites_user_hs_code"),
    )
    op.create_index("idx_favorites_user_id", "favorites", ["user_id"])


def downgrade() -> None:
    op.drop_index("idx_favorites_user_id", table_name="favorites")
    op.drop_table("favorites")
