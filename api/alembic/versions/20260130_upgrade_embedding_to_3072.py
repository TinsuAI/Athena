"""Upgrade embedding dimension from 1536 to 3072 for text-embedding-3-large

Revision ID: upgrade_embedding_3072
Revises: add_hs_hierarchy
Create Date: 2026-01-30 00:00:00.000000+00:00

This migration:
1. Drops the existing index on the embedding column (if exists)
2. Clears all existing embeddings (incompatible dimensions)
3. Alters the column to use 3072 dimensions
4. Recreates the IVFFlat index for vector similarity search
   (HNSW has a 2000-dim limit, IVFFlat supports larger dimensions)

Note: After running this migration, embeddings must be regenerated using:
    python -m app.scripts.generate_embeddings
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import pgvector.sqlalchemy


# revision identifiers, used by Alembic.
revision: str = 'upgrade_embedding_3072'
down_revision: Union[str, None] = 'add_hs_hierarchy'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop existing indexes if they exist
    op.execute('DROP INDEX IF EXISTS idx_hs_codes_embedding_hnsw')
    op.execute('DROP INDEX IF EXISTS idx_hs_codes_embedding_ivfflat')

    # Clear existing embeddings (they are 1536-dim, incompatible with 3072-dim)
    op.execute('UPDATE hs_codes SET embedding = NULL')

    # Alter column to use 3072 dimensions
    # pgvector requires dropping and recreating the column to change dimensions
    op.drop_column('hs_codes', 'embedding')
    op.add_column('hs_codes', sa.Column(
        'embedding',
        pgvector.sqlalchemy.vector.VECTOR(dim=3072),
        nullable=True
    ))

    # Note: IVFFlat index requires data to be present for training.
    # The index will be created after embeddings are generated.
    # Use: CREATE INDEX idx_hs_codes_embedding_ivfflat ON hs_codes
    #      USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);


def downgrade() -> None:
    # Drop the index
    op.execute('DROP INDEX IF EXISTS idx_hs_codes_embedding_ivfflat')
    op.execute('DROP INDEX IF EXISTS idx_hs_codes_embedding_hnsw')

    # Clear embeddings
    op.execute('UPDATE hs_codes SET embedding = NULL')

    # Revert to 1536 dimensions
    op.drop_column('hs_codes', 'embedding')
    op.add_column('hs_codes', sa.Column(
        'embedding',
        pgvector.sqlalchemy.vector.VECTOR(dim=1536),
        nullable=True
    ))

    # Recreate HNSW index with original dimensions (1536 is within limit)
    op.execute('''
        CREATE INDEX idx_hs_codes_embedding_hnsw
        ON hs_codes
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    ''')
