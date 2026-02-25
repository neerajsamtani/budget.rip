"""add indexes on foreign key columns

Revision ID: b1c2d3e4f5a6
Revises: fc917629c36e
Create Date: 2026-02-25 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, Sequence[str], None] = "fc917629c36e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_line_items_transaction_id", "line_items", ["transaction_id"])
    op.create_index("ix_line_items_payment_method_id", "line_items", ["payment_method_id"])
    op.create_index("ix_events_category_id", "events", ["category_id"])
    op.create_index("ix_event_line_items_event_id", "event_line_items", ["event_id"])
    op.create_index("ix_event_line_items_line_item_id", "event_line_items", ["line_item_id"])


def downgrade() -> None:
    op.drop_index("ix_event_line_items_line_item_id", table_name="event_line_items")
    op.drop_index("ix_event_line_items_event_id", table_name="event_line_items")
    op.drop_index("ix_events_category_id", table_name="events")
    op.drop_index("ix_line_items_payment_method_id", table_name="line_items")
    op.drop_index("ix_line_items_transaction_id", table_name="line_items")
