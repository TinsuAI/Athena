"""Add search_history table

Revision ID: add_search_history_table
Revises: add_favorites_table
Create Date: 2026-02-22

Creates search_history table for recording user search queries.
Includes FK to users and hs_codes, and index on user_id.
"""

from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision: str = "add_search_history_table"
down_revision: Union[str, None] = "add_favorites_table"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.create_table(
        "search_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("selected_hs_code_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["selected_hs_code_id"], ["hs_codes.id"]),
    )
    op.create_index("idx_search_history_user_id", "search_history", ["user_id"])


def downgrade() -> None:
    op.drop_index("idx_search_history_user_id", table_name="search_history")
    op.drop_table("search_history")
