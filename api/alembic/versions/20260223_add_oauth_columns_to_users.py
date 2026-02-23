"""Add OAuth columns to users table

Revision ID: add_oauth_columns_to_users
Revises: add_search_history_table
Create Date: 2026-02-23

Makes password_hash nullable for OAuth users. Adds oauth_provider and oauth_id columns
with a partial unique index on (oauth_provider, oauth_id) WHERE both are NOT NULL.
"""

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "add_oauth_columns_to_users"
down_revision: Union[str, None] = "add_search_history_table"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    # Make password_hash nullable for OAuth users
    op.alter_column("users", "password_hash", existing_type=sa.String(255), nullable=True)

    # Add OAuth columns
    op.add_column("users", sa.Column("oauth_provider", sa.String(50), nullable=True))
    op.add_column("users", sa.Column("oauth_id", sa.String(255), nullable=True))

    # Add partial unique index on (oauth_provider, oauth_id)
    op.create_index(
        "ix_users_oauth",
        "users",
        ["oauth_provider", "oauth_id"],
        unique=True,
        postgresql_where=sa.text("oauth_provider IS NOT NULL AND oauth_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_users_oauth", table_name="users")
    op.drop_column("users", "oauth_id")
    op.drop_column("users", "oauth_provider")
    op.alter_column("users", "password_hash", existing_type=sa.String(255), nullable=False)
