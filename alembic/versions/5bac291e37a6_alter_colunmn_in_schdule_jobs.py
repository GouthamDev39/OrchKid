"""Alter colunmn in schdule jobs

Revision ID: 5bac291e37a6
Revises: babcf7a1fdf0
Create Date: 2025-07-30 22:57:27.689450

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5bac291e37a6'
down_revision: Union[str, Sequence[str], None] = 'babcf7a1fdf0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade():
    op.alter_column('schedule_jobs', 'last_run_at',
                    type_=sa.DateTime(timezone=False),
                    existing_nullable=True)
    op.alter_column('schedule_jobs', 'one_time_run',
                    type_=sa.DateTime(timezone=False),
                    existing_nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('schedule_jobs', 'last_run_at')
    op.drop_column('schedule_jobs', 'one_time_run')
