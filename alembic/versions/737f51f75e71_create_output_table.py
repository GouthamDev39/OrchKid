"""Create Output Table

Revision ID: 737f51f75e71
Revises: 48c828819990
Create Date: 2025-07-26 01:26:09.238895

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '737f51f75e71'
down_revision: Union[str, Sequence[str], None] = '48c828819990'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'output',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('stdout', sa.Text(), nullable=True),
        sa.Column('stderr', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('job_id', name='uq_job_id_output')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('output')
