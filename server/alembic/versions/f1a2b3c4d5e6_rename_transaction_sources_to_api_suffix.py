"""rename transaction sources to api suffix and merge cash into manual

Revision ID: f1a2b3c4d5e6
Revises: e310f0f583d7
Create Date: 2025-01-08 10:00:00.000000

This migration:
1. Renames transaction source values: venmo→venmo_api, splitwise→splitwise_api, stripe→stripe_api
2. Migrates all 'cash' transactions to 'manual' source
3. Removes 'cash' from the transaction_source enum
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "e310f0f583d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade: rename transaction sources and merge cash into manual."""
    # PostgreSQL enum modification requires careful handling:
    # 1. Add new enum values
    # 2. Update existing data to use new values
    # 3. Remove old enum values (requires recreating the type)

    # Step 1: Add new enum values (venmo_api, splitwise_api, stripe_api)
    op.execute("ALTER TYPE transaction_source ADD VALUE IF NOT EXISTS 'venmo_api'")
    op.execute("ALTER TYPE transaction_source ADD VALUE IF NOT EXISTS 'splitwise_api'")
    op.execute("ALTER TYPE transaction_source ADD VALUE IF NOT EXISTS 'stripe_api'")

    # Step 2: Migrate existing data to new values
    # Note: cash → manual, venmo → venmo_api, etc.
    op.execute("UPDATE transactions SET source = 'venmo_api' WHERE source = 'venmo'")
    op.execute("UPDATE transactions SET source = 'splitwise_api' WHERE source = 'splitwise'")
    op.execute("UPDATE transactions SET source = 'stripe_api' WHERE source = 'stripe'")
    op.execute("UPDATE transactions SET source = 'manual' WHERE source = 'cash'")

    # Step 3: Recreate enum without old values
    # This is complex in PostgreSQL - we need to:
    # a) Create a new enum type with only the desired values
    # b) Alter the column to use the new type
    # c) Drop the old type
    # d) Rename the new type to the original name

    # Create new enum type with only the values we want
    op.execute("""
        CREATE TYPE transaction_source_new AS ENUM (
            'venmo_api',
            'splitwise_api',
            'stripe_api',
            'manual'
        )
    """)

    # Alter the column to use the new type
    op.execute("""
        ALTER TABLE transactions
        ALTER COLUMN source TYPE transaction_source_new
        USING source::text::transaction_source_new
    """)

    # Drop the old enum type
    op.execute("DROP TYPE transaction_source")

    # Rename the new type to the original name
    op.execute("ALTER TYPE transaction_source_new RENAME TO transaction_source")


def downgrade() -> None:
    """Downgrade: restore original transaction source names."""
    # Create old enum type with all original values
    op.execute("""
        CREATE TYPE transaction_source_old AS ENUM (
            'venmo',
            'splitwise',
            'stripe',
            'cash',
            'manual'
        )
    """)

    # Migrate data back to old values
    op.execute("UPDATE transactions SET source = 'venmo' WHERE source = 'venmo_api'")
    op.execute("UPDATE transactions SET source = 'splitwise' WHERE source = 'splitwise_api'")
    op.execute("UPDATE transactions SET source = 'stripe' WHERE source = 'stripe_api'")
    # Note: manual stays as manual (cash transactions that were migrated stay as manual)

    # Alter the column to use the old type
    op.execute("""
        ALTER TABLE transactions
        ALTER COLUMN source TYPE transaction_source_old
        USING source::text::transaction_source_old
    """)

    # Drop the new enum type
    op.execute("DROP TYPE transaction_source")

    # Rename the old type to the original name
    op.execute("ALTER TYPE transaction_source_old RENAME TO transaction_source")
