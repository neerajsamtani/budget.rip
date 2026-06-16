"""add indexes for hot list queries

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-06-16 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index("ix_events_date", "events", ["date"])
    op.create_index("ix_line_items_date", "line_items", ["date"])
    op.create_index("ix_line_items_payment_method_date", "line_items", ["payment_method_id", "date"])
    op.create_index("ix_event_tags_event_id", "event_tags", ["event_id"])
    op.create_index("ix_event_tags_tag_id", "event_tags", ["tag_id"])
    op.create_index("ix_transactions_source_transaction_date", "transactions", ["source", "transaction_date"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_transactions_source_transaction_date", table_name="transactions")
    op.drop_index("ix_event_tags_tag_id", table_name="event_tags")
    op.drop_index("ix_event_tags_event_id", table_name="event_tags")
    op.drop_index("ix_line_items_payment_method_date", table_name="line_items")
    op.drop_index("ix_line_items_date", table_name="line_items")
    op.drop_index("ix_events_date", table_name="events")
