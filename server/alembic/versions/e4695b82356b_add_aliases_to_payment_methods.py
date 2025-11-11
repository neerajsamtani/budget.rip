"""add_aliases_to_payment_methods

Revision ID: e4695b82356b
Revises: e12f3d5e488a
Create Date: 2025-11-09 22:03:09.395900

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e4695b82356b"
down_revision: Union[str, Sequence[str], None] = "e12f3d5e488a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add aliases column to payment_methods to track historical external IDs."""
    op.add_column("payment_methods", sa.Column("aliases", sa.JSON(), nullable=True))


def downgrade() -> None:
    """Remove aliases column from payment_methods."""
    op.drop_column("payment_methods", "aliases")
