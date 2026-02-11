"""Add JSONB columns to lookup_records for classification data

Revision ID: add_jsonb_to_lookup_records
Revises: add_lookup_records
Create Date: 2026-02-10

Adds three nullable JSONB columns to persist full search analysis:
- classification_data: {"material": "...", "function": "..."}
- practical_notes: ["note1", "note2", ...]
- process_logs: [{"step": "...", "status": "...", "message": "...", ...}]
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "add_jsonb_to_lookup_records"
down_revision: Union[str, None] = "add_lookup_records"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("lookup_records", sa.Column("classification_data", JSONB, nullable=True))
    op.add_column("lookup_records", sa.Column("practical_notes", JSONB, nullable=True))
    op.add_column("lookup_records", sa.Column("process_logs", JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column("lookup_records", "process_logs")
    op.drop_column("lookup_records", "practical_notes")
    op.drop_column("lookup_records", "classification_data")
