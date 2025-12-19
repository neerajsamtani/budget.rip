"""drop_mongo_id_columns

Revision ID: 224fee919c40
Revises: fb7a20ffd5fe
Create Date: 2025-12-19 10:20:52.462277

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '224fee919c40'
down_revision: Union[str, Sequence[str], None] = 'fb7a20ffd5fe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop mongo_id columns from all tables - no longer needed after MongoDB removal."""
    # Drop mongo_id from bank_accounts
    op.drop_index('ix_bank_accounts_mongo_id', table_name='bank_accounts')
    op.drop_column('bank_accounts', 'mongo_id')

    # Drop mongo_id from users
    op.drop_index('ix_users_mongo_id', table_name='users')
    op.drop_column('users', 'mongo_id')

    # Drop mongo_id from categories
    op.drop_index('ix_categories_mongo_id', table_name='categories')
    op.drop_column('categories', 'mongo_id')

    # Drop mongo_id from line_items
    op.drop_index('ix_line_items_mongo_id', table_name='line_items')
    op.drop_column('line_items', 'mongo_id')

    # Drop mongo_id from events
    op.drop_column('events', 'mongo_id')


def downgrade() -> None:
    """Restore mongo_id columns (for rollback purposes only)."""
    # Re-add mongo_id to events
    op.add_column('events', sa.Column('mongo_id', sa.String(255), nullable=True, unique=True))

    # Re-add mongo_id to line_items
    op.add_column('line_items', sa.Column('mongo_id', sa.String(255), nullable=True))
    op.create_index('ix_line_items_mongo_id', 'line_items', ['mongo_id'])

    # Re-add mongo_id to categories
    op.add_column('categories', sa.Column('mongo_id', sa.String(255), nullable=True))
    op.create_index('ix_categories_mongo_id', 'categories', ['mongo_id'])

    # Re-add mongo_id to users
    op.add_column('users', sa.Column('mongo_id', sa.String(255), nullable=True, unique=True))
    op.create_index('ix_users_mongo_id', 'users', ['mongo_id'])

    # Re-add mongo_id to bank_accounts
    op.add_column('bank_accounts', sa.Column('mongo_id', sa.String(255), nullable=True, unique=True))
    op.create_index('ix_bank_accounts_mongo_id', 'bank_accounts', ['mongo_id'])
