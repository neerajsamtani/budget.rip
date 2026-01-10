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
    """Upgrade: rename transaction sources and merge cash into manual.

    PostgreSQL requires new enum values to be committed before they can be used
    in the same transaction. To work around this, we:
    1. Create the new enum type with all desired values
    2. Convert the column to text temporarily
    3. Update the data values while it's text
    4. Convert to the new enum type
    5. Drop the old enum type
    6. Rename the new type
    """
    # Step 1: Create new enum type with all the values we want
    op.execute("""
        CREATE TYPE transaction_source_new AS ENUM (
            'venmo_api',
            'splitwise_api',
            'stripe_api',
            'manual'
        )
    """)

    # Step 2: Convert the source column to text temporarily
    op.execute("""
        ALTER TABLE transactions
        ALTER COLUMN source TYPE text
        USING source::text
    """)

    # Step 3: Update the data values while it's text
    op.execute("UPDATE transactions SET source = 'venmo_api' WHERE source = 'venmo'")
    op.execute("UPDATE transactions SET source = 'splitwise_api' WHERE source = 'splitwise'")
    op.execute("UPDATE transactions SET source = 'stripe_api' WHERE source = 'stripe'")
    op.execute("UPDATE transactions SET source = 'manual' WHERE source = 'cash'")

    # Step 4: Convert to the new enum type
    op.execute("""
        ALTER TABLE transactions
        ALTER COLUMN source TYPE transaction_source_new
        USING source::transaction_source_new
    """)

    # Step 5: Drop the old enum type
    op.execute("DROP TYPE transaction_source")

    # Step 6: Rename the new type to the original name
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

    # Convert the source column to text temporarily
    op.execute("""
        ALTER TABLE transactions
        ALTER COLUMN source TYPE text
        USING source::text
    """)

    # Migrate data back to old values
    op.execute("UPDATE transactions SET source = 'venmo' WHERE source = 'venmo_api'")
    op.execute("UPDATE transactions SET source = 'splitwise' WHERE source = 'splitwise_api'")
    op.execute("UPDATE transactions SET source = 'stripe' WHERE source = 'stripe_api'")
    op.execute("UPDATE transactions SET source = 'cash' WHERE source = 'manual'")

    # Convert to the old enum type
    op.execute("""
        ALTER TABLE transactions
        ALTER COLUMN source TYPE transaction_source_old
        USING source::transaction_source_old
    """)

    # Drop the new enum type
    op.execute("DROP TYPE transaction_source")

    # Rename the old type to the original name
    op.execute("ALTER TYPE transaction_source_old RENAME TO transaction_source")
