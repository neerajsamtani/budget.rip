"""add event suggestions table

Revision ID: a7b8c9d0e1f2
Revises: d4e5f6a7b8c9
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "event_suggestions",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column("user_id", sa.String(255), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("line_item_id", sa.String(255), sa.ForeignKey("line_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_hint_id", sa.String(255), sa.ForeignKey("event_hints.id", ondelete="SET NULL"), nullable=True),
        sa.Column("suggested_name", sa.String(255), nullable=False),
        sa.Column("category_id", sa.String(255), sa.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("rejected_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint("user_id", "line_item_id", name="uq_event_suggestion_user_line_item"),
    )
    op.create_index("ix_event_suggestions_user_id", "event_suggestions", ["user_id"])
    op.create_index("ix_event_suggestions_line_item_id", "event_suggestions", ["line_item_id"])
    op.create_index(
        "ix_event_suggestions_user_pending",
        "event_suggestions",
        ["user_id", "rejected_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_event_suggestions_user_pending", table_name="event_suggestions")
    op.drop_index("ix_event_suggestions_line_item_id", table_name="event_suggestions")
    op.drop_index("ix_event_suggestions_user_id", table_name="event_suggestions")
    op.drop_table("event_suggestions")
