"""Create hotsname/ussername column

Revision ID: 48c828819990
Revises: ae9f7d36acf4
Create Date: 2025-07-26 01:18:26.269699

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '48c828819990'
down_revision: Union[str, Sequence[str], None] = 'ae9f7d36acf4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('jobs',
                  sa.Column('hostname', sa.String(), nullable=True))
    op.add_column('jobs',
                  sa.Column('username', sa.String(), nullable=True))
    


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('jobs', 'hostname')
    op.drop_column('jobs', 'username')
