"""add_interview_tables

Revision ID: 20f24813dff0
Revises: 31ba30360c92
Create Date: 2026-08-09 00:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20f24813dff0'
down_revision: Union[str, Sequence[str], None] = '31ba30360c92'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'interview_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('resume_id', sa.Integer(), nullable=False),
        sa.Column('target_role', sa.String(length=150), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'IN_PROGRESS', 'COMPLETED', 'ABANDONED', name='interview_session_status'), nullable=False),
        sa.Column('total_questions', sa.Integer(), nullable=False),
        sa.Column('current_index', sa.Integer(), nullable=False),
        sa.Column('overall_score', sa.Integer(), nullable=True),
        sa.Column('provider', sa.String(length=50), nullable=True),
        sa.Column('model', sa.String(length=100), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_interview_sessions_id'), 'interview_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_interview_sessions_user_id'), 'interview_sessions', ['user_id'], unique=False)
    op.create_index(op.f('ix_interview_sessions_resume_id'), 'interview_sessions', ['resume_id'], unique=False)

    op.create_table(
        'interview_questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('difficulty', sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['interview_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_interview_questions_id'), 'interview_questions', ['id'], unique=False)
    op.create_index(op.f('ix_interview_questions_session_id'), 'interview_questions', ['session_id'], unique=False)

    op.create_table(
        'interview_answers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('answer_text', sa.Text(), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('feedback', sa.Text(), nullable=False),
        sa.Column('strengths', sa.JSON(), nullable=False),
        sa.Column('improvements', sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['question_id'], ['interview_questions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('question_id'),
    )
    op.create_index(op.f('ix_interview_answers_id'), 'interview_answers', ['id'], unique=False)
    op.create_index(op.f('ix_interview_answers_question_id'), 'interview_answers', ['question_id'], unique=True)

    op.create_table(
        'interview_feedback',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('overall_score', sa.Integer(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('strengths', sa.JSON(), nullable=False),
        sa.Column('weaknesses', sa.JSON(), nullable=False),
        sa.Column('recommendation', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['interview_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id'),
    )
    op.create_index(op.f('ix_interview_feedback_id'), 'interview_feedback', ['id'], unique=False)
    op.create_index(op.f('ix_interview_feedback_session_id'), 'interview_feedback', ['session_id'], unique=True)

    op.create_table(
        'learning_roadmaps',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('items', sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['interview_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id'),
    )
    op.create_index(op.f('ix_learning_roadmaps_id'), 'learning_roadmaps', ['id'], unique=False)
    op.create_index(op.f('ix_learning_roadmaps_session_id'), 'learning_roadmaps', ['session_id'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_learning_roadmaps_session_id'), table_name='learning_roadmaps')
    op.drop_index(op.f('ix_learning_roadmaps_id'), table_name='learning_roadmaps')
    op.drop_table('learning_roadmaps')

    op.drop_index(op.f('ix_interview_feedback_session_id'), table_name='interview_feedback')
    op.drop_index(op.f('ix_interview_feedback_id'), table_name='interview_feedback')
    op.drop_table('interview_feedback')

    op.drop_index(op.f('ix_interview_answers_question_id'), table_name='interview_answers')
    op.drop_index(op.f('ix_interview_answers_id'), table_name='interview_answers')
    op.drop_table('interview_answers')

    op.drop_index(op.f('ix_interview_questions_session_id'), table_name='interview_questions')
    op.drop_index(op.f('ix_interview_questions_id'), table_name='interview_questions')
    op.drop_table('interview_questions')

    op.drop_index(op.f('ix_interview_sessions_resume_id'), table_name='interview_sessions')
    op.drop_index(op.f('ix_interview_sessions_user_id'), table_name='interview_sessions')
    op.drop_index(op.f('ix_interview_sessions_id'), table_name='interview_sessions')
    op.drop_table('interview_sessions')

    sa.Enum(name='interview_session_status').drop(op.get_bind(), checkfirst=True)
