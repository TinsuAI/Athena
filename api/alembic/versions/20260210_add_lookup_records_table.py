"""Add lookup_records table for knowledge base

Revision ID: add_lookup_records
Revises: upgrade_embedding_3072
Create Date: 2026-02-10

Creates the lookup_records table that stores every user search lookup
with fields for expert correction, enabling a knowledge base for
verified human classifications.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "add_lookup_records"
down_revision: Union[str, None] = "upgrade_embedding_3072"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "lookup_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("query_hash", sa.String(64), nullable=False),
        sa.Column("query_language", sa.String(5), nullable=True),
        sa.Column(
            "matched_hs_code_id",
            sa.Integer(),
            sa.ForeignKey("hs_codes.id"),
            nullable=True,
        ),
        sa.Column(
            "correct_hs_code_id",
            sa.Integer(),
            sa.ForeignKey("hs_codes.id"),
            nullable=True,
        ),
        sa.Column(
            "is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("verified_by_user_id", sa.Integer(), nullable=True),
        sa.Column(
            "verified_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("search_method", sa.String(20), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Btree indexes per AC1
    op.create_index(
        "idx_lookup_records_query_hash", "lookup_records", ["query_hash"]
    )
    op.create_index(
        "idx_lookup_records_verified", "lookup_records", ["is_verified"]
    )

    # GIN trigram index for fuzzy text search (pg_trgm already enabled from Story 1-2)
    op.execute(
        "CREATE INDEX idx_lookup_records_query_trgm "
        "ON lookup_records USING gin(query_text gin_trgm_ops)"
    )

    # Additional index for ordering by created_at
    op.create_index(
        "idx_lookup_records_created_at",
        "lookup_records",
        [sa.text("created_at DESC")],
    )


def downgrade() -> None:
    op.drop_index("idx_lookup_records_created_at", table_name="lookup_records")
    op.execute("DROP INDEX IF EXISTS idx_lookup_records_query_trgm")
    op.drop_index("idx_lookup_records_verified", table_name="lookup_records")
    op.drop_index("idx_lookup_records_query_hash", table_name="lookup_records")
    op.drop_table("lookup_records")
