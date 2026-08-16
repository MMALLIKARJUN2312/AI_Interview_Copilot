"""add_interview_rounds_and_coding

Revision ID: a1b2c3d4e5f6
Revises: 20f27109fd35
Create Date: 2026-08-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f38fc891149d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    round_type_enum = sa.Enum('DSA_CODING', 'MACHINE_CODING', 'GENERAL', name='interview_round_type')
    round_type_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        'interview_questions',
        sa.Column('round_type', round_type_enum, nullable=False, server_default='GENERAL'),
    )
    op.add_column('interview_questions', sa.Column('language', sa.String(length=20), nullable=True))
    op.add_column('interview_questions', sa.Column('starter_code', sa.Text(), nullable=True))
    op.add_column('interview_questions', sa.Column('examples', sa.Text(), nullable=True))
    op.add_column('interview_questions', sa.Column('constraints', sa.Text(), nullable=True))
    op.add_column('interview_questions', sa.Column('test_cases', sa.JSON(), nullable=True))

    op.add_column('interview_answers', sa.Column('language', sa.String(length=20), nullable=True))
    op.add_column('interview_answers', sa.Column('execution_results', sa.JSON(), nullable=True))
    op.add_column('interview_answers', sa.Column('passed_test_count', sa.Integer(), nullable=True))
    op.add_column('interview_answers', sa.Column('total_test_count', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('interview_answers', 'total_test_count')
    op.drop_column('interview_answers', 'passed_test_count')
    op.drop_column('interview_answers', 'execution_results')
    op.drop_column('interview_answers', 'language')

    op.drop_column('interview_questions', 'test_cases')
    op.drop_column('interview_questions', 'constraints')
    op.drop_column('interview_questions', 'examples')
    op.drop_column('interview_questions', 'starter_code')
    op.drop_column('interview_questions', 'language')
    op.drop_column('interview_questions', 'round_type')

    sa.Enum(name='interview_round_type').drop(op.get_bind(), checkfirst=True)
