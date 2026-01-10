"""add unique constraint on line_items transaction_id

Revision ID: fc917629c36e
Revises: f1a2b3c4d5e6
Create Date: 2026-01-10 10:38:29.400429

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "fc917629c36e"
down_revision: Union[str, Sequence[str], None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint("uq_line_item_transaction", "line_items", ["transaction_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uq_line_item_transaction", "line_items", type_="unique")
