"""Initial migration creating jobs and certificates tables.

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-07 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create jobs table
    op.create_table(
        'jobs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('event_name', sa.String(length=255), nullable=False),
        sa.Column('event_date', sa.Date(), nullable=False),
        sa.Column('organization_name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.Enum('queued', 'processing', 'completed', 'completed_with_errors', 'failed', name='job_status_enum', native_enum=False), nullable=False),
        sa.Column('total_count', sa.Integer(), nullable=False),
        sa.Column('success_count', sa.Integer(), nullable=False),
        sa.Column('failure_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_jobs_id'), 'jobs', ['id'], unique=False)
    op.create_index(op.f('ix_jobs_status'), 'jobs', ['status'], unique=False)

    # 2. Create certificates table
    op.create_table(
        'certificates',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('job_id', sa.UUID(), nullable=False),
        sa.Column('recipient_name', sa.String(length=255), nullable=False),
        sa.Column('recipient_email', sa.String(length=255), nullable=False),
        sa.Column('status', sa.Enum('pending', 'processing', 'completed', 'failed', name='certificate_status_enum', native_enum=False), nullable=False),
        sa.Column('file_path', sa.String(length=512), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_certificates_id'), 'certificates', ['id'], unique=False)
    op.create_index(op.f('ix_certificates_job_id'), 'certificates', ['job_id'], unique=False)
    op.create_index(op.f('ix_certificates_status'), 'certificates', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_certificates_status'), table_name='certificates')
    op.drop_index(op.f('ix_certificates_job_id'), table_name='certificates')
    op.drop_index(op.f('ix_certificates_id'), table_name='certificates')
    op.drop_table('certificates')

    op.drop_index(op.f('ix_jobs_status'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_id'), table_name='jobs')
    op.drop_table('jobs')
