"""Add HS hierarchy tables (sections, chapters, headings, subheadings)

Revision ID: add_hs_hierarchy
Revises: 5eae795c2eff
Create Date: 2026-01-28 00:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_hs_hierarchy'
down_revision: Union[str, None] = '5eae795c2eff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create hs_sections table
    op.create_table('hs_sections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('section_number', sa.Integer(), nullable=False),
        sa.Column('section_roman', sa.String(length=10), nullable=False),
        sa.Column('name_vn', sa.Text(), nullable=False),
        sa.Column('name_en', sa.Text(), nullable=True),
        sa.Column('notes_vn', sa.Text(), nullable=True),
        sa.Column('notes_en', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('section_number')
    )

    # Create hs_chapters table
    op.create_table('hs_chapters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('chapter_code', sa.String(length=2), nullable=False),
        sa.Column('section_id', sa.Integer(), nullable=False),
        sa.Column('name_vn', sa.Text(), nullable=False),
        sa.Column('name_en', sa.Text(), nullable=True),
        sa.Column('notes_vn', sa.Text(), nullable=True),
        sa.Column('notes_en', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['section_id'], ['hs_sections.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_hs_chapters_chapter_code'), 'hs_chapters', ['chapter_code'], unique=True)
    op.create_index(op.f('ix_hs_chapters_section_id'), 'hs_chapters', ['section_id'], unique=False)

    # Create hs_headings table
    op.create_table('hs_headings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('heading_code', sa.String(length=4), nullable=False),
        sa.Column('chapter_id', sa.Integer(), nullable=False),
        sa.Column('name_vn', sa.Text(), nullable=False),
        sa.Column('name_en', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['chapter_id'], ['hs_chapters.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_hs_headings_heading_code'), 'hs_headings', ['heading_code'], unique=True)
    op.create_index(op.f('ix_hs_headings_chapter_id'), 'hs_headings', ['chapter_id'], unique=False)

    # Create hs_subheadings table
    op.create_table('hs_subheadings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('subheading_code', sa.String(length=6), nullable=False),
        sa.Column('heading_id', sa.Integer(), nullable=False),
        sa.Column('name_vn', sa.Text(), nullable=False),
        sa.Column('name_en', sa.Text(), nullable=True),
        sa.Column('indent_level', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['heading_id'], ['hs_headings.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_hs_subheadings_subheading_code'), 'hs_subheadings', ['subheading_code'], unique=True)
    op.create_index(op.f('ix_hs_subheadings_heading_id'), 'hs_subheadings', ['heading_id'], unique=False)

    # Add new columns to hs_codes table
    op.add_column('hs_codes', sa.Column('subheading_id', sa.Integer(), nullable=True))
    op.add_column('hs_codes', sa.Column('indent_level', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_hs_codes_subheading_id'), 'hs_codes', ['subheading_id'], unique=False)
    op.create_foreign_key('fk_hs_codes_subheading_id', 'hs_codes', 'hs_subheadings', ['subheading_id'], ['id'])


def downgrade() -> None:
    # Remove foreign key and columns from hs_codes
    op.drop_constraint('fk_hs_codes_subheading_id', 'hs_codes', type_='foreignkey')
    op.drop_index(op.f('ix_hs_codes_subheading_id'), table_name='hs_codes')
    op.drop_column('hs_codes', 'indent_level')
    op.drop_column('hs_codes', 'subheading_id')

    # Drop hs_subheadings table
    op.drop_index(op.f('ix_hs_subheadings_heading_id'), table_name='hs_subheadings')
    op.drop_index(op.f('ix_hs_subheadings_subheading_code'), table_name='hs_subheadings')
    op.drop_table('hs_subheadings')

    # Drop hs_headings table
    op.drop_index(op.f('ix_hs_headings_chapter_id'), table_name='hs_headings')
    op.drop_index(op.f('ix_hs_headings_heading_code'), table_name='hs_headings')
    op.drop_table('hs_headings')

    # Drop hs_chapters table
    op.drop_index(op.f('ix_hs_chapters_section_id'), table_name='hs_chapters')
    op.drop_index(op.f('ix_hs_chapters_chapter_code'), table_name='hs_chapters')
    op.drop_table('hs_chapters')

    # Drop hs_sections table
    op.drop_table('hs_sections')
