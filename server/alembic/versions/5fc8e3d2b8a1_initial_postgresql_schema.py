"""Initial PostgreSQL schema

Revision ID: 5fc8e3d2b8a1
Revises:
Create Date: 2025-10-21 20:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '5fc8e3d2b8a1'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create ENUM types first (PostgreSQL-specific)
    op.execute("CREATE TYPE payment_method_type AS ENUM ('bank', 'credit', 'venmo', 'splitwise', 'cash')")
    op.execute("CREATE TYPE transaction_source AS ENUM ('venmo', 'splitwise', 'stripe', 'cash', 'manual')")

    # Create categories table
    op.create_table('categories',
    sa.Column('id', sa.String(length=255), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('mongo_id', sa.String(length=24), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_categories_mongo_id'), 'categories', ['mongo_id'], unique=False)

    # Create parties table
    op.create_table('parties',
    sa.Column('id', sa.String(length=255), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('is_ignored', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )

    # Create payment_methods table
    op.create_table('payment_methods',
    sa.Column('id', sa.String(length=255), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('type', postgresql.ENUM('bank', 'credit', 'venmo', 'splitwise', 'cash', name='payment_method_type'), nullable=False),
    sa.Column('external_id', sa.String(length=255), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )

    # Create tags table
    op.create_table('tags',
    sa.Column('id', sa.String(length=255), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )

    # Create transactions table
    op.create_table('transactions',
    sa.Column('id', sa.String(length=255), nullable=False),
    sa.Column('source', postgresql.ENUM('venmo', 'splitwise', 'stripe', 'cash', 'manual', name='transaction_source'), nullable=False),
    sa.Column('source_id', sa.String(length=255), nullable=False),
    sa.Column('source_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('transaction_date', sa.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('imported_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('source', 'source_id', name='uq_transaction_source')
    )

    # Create events table
    op.create_table('events',
    sa.Column('id', sa.String(length=255), nullable=False),
    sa.Column('mongo_id', sa.String(length=24), nullable=True),
    sa.Column('date', sa.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('category_id', sa.String(length=255), nullable=False),
    sa.Column('is_duplicate', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_events_mongo_id'), 'events', ['mongo_id'], unique=False)

    # Create line_items table
    op.create_table('line_items',
    sa.Column('id', sa.String(length=255), nullable=False),
    sa.Column('transaction_id', sa.String(length=255), nullable=False),
    sa.Column('mongo_id', sa.String(length=24), nullable=True),
    sa.Column('date', sa.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('amount', sa.DECIMAL(precision=12, scale=2), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('payment_method_id', sa.String(length=255), nullable=False),
    sa.Column('party_id', sa.String(length=255), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['party_id'], ['parties.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['payment_method_id'], ['payment_methods.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_line_items_mongo_id'), 'line_items', ['mongo_id'], unique=False)

    # Create event_line_items table
    op.create_table('event_line_items',
    sa.Column('id', sa.String(length=255), nullable=False),
    sa.Column('event_id', sa.String(length=255), nullable=False),
    sa.Column('line_item_id', sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['line_item_id'], ['line_items.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('event_id', 'line_item_id', name='uq_event_line_item')
    )

    # Create event_tags table
    op.create_table('event_tags',
    sa.Column('id', sa.String(length=255), nullable=False),
    sa.Column('event_id', sa.String(length=255), nullable=False),
    sa.Column('tag_id', sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('event_id', 'tag_id', name='uq_event_tag')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('event_tags')
    op.drop_table('event_line_items')
    op.drop_index(op.f('ix_line_items_mongo_id'), table_name='line_items')
    op.drop_table('line_items')
    op.drop_index(op.f('ix_events_mongo_id'), table_name='events')
    op.drop_table('events')
    op.drop_table('transactions')
    op.drop_table('tags')
    op.drop_table('payment_methods')
    op.drop_table('parties')
    op.drop_index(op.f('ix_categories_mongo_id'), table_name='categories')
    op.drop_table('categories')

    # Drop ENUM types
    op.execute("DROP TYPE transaction_source")
    op.execute("DROP TYPE payment_method_type")
