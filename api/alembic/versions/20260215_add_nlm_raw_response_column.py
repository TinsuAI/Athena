"""Add nlm_raw_response column to lookup_records

Revision ID: add_nlm_raw_response
Revises: add_audit_logs
Create Date: 2026-02-15

Adds nullable TEXT column to store full NotebookLM raw response.
"""

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "add_nlm_raw_response"
down_revision: Union[str, None] = "add_audit_logs"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.add_column(
        "lookup_records",
        sa.Column("nlm_raw_response", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("lookup_records", "nlm_raw_response")
