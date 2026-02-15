"""Add users table

Revision ID: add_users_table
Revises: expand_tariff_import
Create Date: 2026-02-15

Creates the users table for authentication with email unique constraint
and index, plus FK from lookup_records.verified_by_user_id to users.id.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "add_users_table"
down_revision: Union[str, None] = "expand_tariff_import"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="user"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Unique constraint and index on email
    op.create_unique_constraint("uq_users_email", "users", ["email"])
    op.create_index("ix_users_email", "users", ["email"])

    # Add FK constraint from lookup_records.verified_by_user_id to users.id
    op.create_foreign_key(
        "fk_lookup_records_verified_by_user_id",
        "lookup_records",
        "users",
        ["verified_by_user_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_lookup_records_verified_by_user_id",
        "lookup_records",
        type_="foreignkey",
    )
    op.drop_index("ix_users_email", table_name="users")
    op.drop_constraint("uq_users_email", "users", type_="uniqueconstraint")
    op.drop_table("users")
