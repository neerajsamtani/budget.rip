"""add_can_relink_to_bank_accounts

Revision ID: 89d79c1aa775
Revises: e4695b82356b
Create Date: 2025-11-19 14:02:33.829257

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "89d79c1aa775"
down_revision: Union[str, Sequence[str], None] = "e4695b82356b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add can_relink column to bank_accounts table
    # Default to True for all existing accounts (assume they can be relinked)
    op.add_column("bank_accounts", sa.Column("can_relink", sa.Boolean(), nullable=False, server_default="true"))
    # Remove server default after column is created so future inserts use the model default
    op.alter_column("bank_accounts", "can_relink", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove can_relink column from bank_accounts table
    op.drop_column("bank_accounts", "can_relink")
