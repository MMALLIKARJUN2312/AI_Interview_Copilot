"""add_resume_role_columns

Revision ID: 31ba30360c92
Revises: 20f27109fd35
Create Date: 2026-08-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '31ba30360c92'
down_revision: Union[str, Sequence[str], None] = '20f27109fd35'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('resumes', sa.Column('target_role', sa.String(length=150), nullable=True))
    op.add_column('resumes', sa.Column('job_description', sa.Text(), nullable=True))
    op.add_column('resumes', sa.Column('extracted_text', sa.Text(), nullable=True))

    # Backfill existing rows before enforcing NOT NULL.
    op.execute("UPDATE resumes SET target_role = 'unspecified' WHERE target_role IS NULL")

    op.alter_column('resumes', 'target_role', existing_type=sa.String(length=150), nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('resumes', 'extracted_text')
    op.drop_column('resumes', 'job_description')
    op.drop_column('resumes', 'target_role')
