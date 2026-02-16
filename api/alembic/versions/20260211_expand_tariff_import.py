"""Expand hs_codes and fta_rates for tariff browser data

Revision ID: expand_tariff_import
Revises: add_jsonb_to_lookup_records
Create Date: 2026-02-11

Adds to hs_codes: export_duty_rate, special_consumption_tax, environmental_tax, vat_reduction
Adds to fta_rates: rate_year, is_export, legal_document, effective_date
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "expand_tariff_import"
down_revision: Union[str, None] = "add_jsonb_to_lookup_records"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # hs_codes new columns
    op.add_column("hs_codes", sa.Column("export_duty_rate", sa.String(), nullable=True))
    op.add_column("hs_codes", sa.Column("special_consumption_tax", sa.String(), nullable=True))
    op.add_column("hs_codes", sa.Column("environmental_tax", sa.String(), nullable=True))
    op.add_column("hs_codes", sa.Column("vat_reduction", sa.String(), nullable=True))

    # fta_rates new columns
    op.add_column("fta_rates", sa.Column("rate_year", sa.Integer(), nullable=True))
    op.add_column(
        "fta_rates",
        sa.Column("is_export", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column("fta_rates", sa.Column("legal_document", sa.String(), nullable=True))
    op.add_column("fta_rates", sa.Column("effective_date", sa.String(), nullable=True))

    # Indexes for efficient filtering
    op.create_index("idx_fta_rates_is_export", "fta_rates", ["is_export"])
    op.create_index("idx_fta_rates_rate_year", "fta_rates", ["rate_year"])


def downgrade() -> None:
    op.drop_index("idx_fta_rates_rate_year")
    op.drop_index("idx_fta_rates_is_export")
    op.drop_column("fta_rates", "effective_date")
    op.drop_column("fta_rates", "legal_document")
    op.drop_column("fta_rates", "is_export")
    op.drop_column("fta_rates", "rate_year")
    op.drop_column("hs_codes", "vat_reduction")
    op.drop_column("hs_codes", "environmental_tax")
    op.drop_column("hs_codes", "special_consumption_tax")
    op.drop_column("hs_codes", "export_duty_rate")
