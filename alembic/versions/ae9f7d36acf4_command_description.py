"""Command_Description

Revision ID: ae9f7d36acf4
Revises: 
Create Date: 2025-07-26 00:56:19.250086

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ae9f7d36acf4'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('jobs',
                  sa.Column('command_description', sa.String(), nullable=True)) 
    # Add any additional upgrade operations here, if needed


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('jobs', 'command_description')
