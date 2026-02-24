"""Add customs_import_batches table

Revision ID: add_customs_import_batches_table
Revises: add_site_settings_table
Create Date: 2026-02-24
"""
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "add_customs_import_batches_table"
down_revision: Union[str, None] = "add_site_settings_table"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.create_table(
        "customs_import_batches",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("file_name", sa.String(500), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("imported_by_user_id", sa.Integer(), nullable=True),
        sa.Column("total_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_imported", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duplicates_skipped", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unmatched_codes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("errors_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["imported_by_user_id"], ["users.id"], name="fk_customs_import_batches_user"
        ),
    )
    op.create_index(
        "idx_customs_import_batches_user",
        "customs_import_batches",
        ["imported_by_user_id"],
    )


def downgrade() -> None:
    op.drop_index("idx_customs_import_batches_user", table_name="customs_import_batches")
    op.drop_table("customs_import_batches")
