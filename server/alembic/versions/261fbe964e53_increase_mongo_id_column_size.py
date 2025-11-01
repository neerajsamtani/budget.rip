"""increase_mongo_id_column_size

Revision ID: 261fbe964e53
Revises: 33c2fccb211e
Create Date: 2025-11-01 11:00:08.121206

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '261fbe964e53'
down_revision: Union[str, Sequence[str], None] = '33c2fccb211e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Increase mongo_id column size from VARCHAR(24) to VARCHAR(255)
    # This is needed because line item IDs are longer than 24 characters
    op.alter_column('line_items', 'mongo_id',
                    existing_type=sa.String(24),
                    type_=sa.String(255),
                    existing_nullable=True)

    op.alter_column('events', 'mongo_id',
                    existing_type=sa.String(24),
                    type_=sa.String(255),
                    existing_nullable=True)

    op.alter_column('categories', 'mongo_id',
                    existing_type=sa.String(24),
                    type_=sa.String(255),
                    existing_nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Revert mongo_id column size back to VARCHAR(24)
    op.alter_column('line_items', 'mongo_id',
                    existing_type=sa.String(255),
                    type_=sa.String(24),
                    existing_nullable=True)

    op.alter_column('events', 'mongo_id',
                    existing_type=sa.String(255),
                    type_=sa.String(24),
                    existing_nullable=True)

    op.alter_column('categories', 'mongo_id',
                    existing_type=sa.String(255),
                    type_=sa.String(24),
                    existing_nullable=True)
