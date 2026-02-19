"""Add correction workflow columns to lookup_records

Revision ID: add_correction_workflow_columns
Revises: add_is_active_to_users
Create Date: 2026-02-18

Adds submitted_by_user_id (FK to users.id), correction_status (varchar(20)),
and rejection_reason (text) to lookup_records for authenticated correction workflow.
Existing rows get NULL for all new columns (backward-compatible).
"""

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "add_correction_workflow_columns"
down_revision: Union[str, None] = "add_is_active_to_users"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.add_column(
        "lookup_records",
        sa.Column(
            "submitted_by_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
    )
    op.add_column(
        "lookup_records",
        sa.Column("correction_status", sa.String(20), nullable=True),
    )
    op.add_column(
        "lookup_records",
        sa.Column("rejection_reason", sa.Text(), nullable=True),
    )
    # Index for querying pending corrections (Story 5-3 will need this)
    op.create_index(
        "idx_lookup_records_correction_status",
        "lookup_records",
        ["correction_status"],
    )


def downgrade() -> None:
    op.drop_index(
        "idx_lookup_records_correction_status", table_name="lookup_records"
    )
    op.drop_column("lookup_records", "rejection_reason")
    op.drop_column("lookup_records", "correction_status")
    op.drop_column("lookup_records", "submitted_by_user_id")
