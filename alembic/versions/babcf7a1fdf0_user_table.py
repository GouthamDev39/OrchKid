"""User table

Revision ID: babcf7a1fdf0
Revises: 737f51f75e71
Create Date: 2025-07-27 03:17:30.999394

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'babcf7a1fdf0'
down_revision: Union[str, Sequence[str], None] = '737f51f75e71'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('runner', sa.String, unique=True, nullable=False),
        sa.Column('password', sa.String, nullable=False),  # Store hashed passwords
        sa.Column('is_superuser', sa.Boolean, default=False),  # For admin privileges
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()')),
        # is_active = Column(Boolean, default=True)  # To manage user status
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('users')

