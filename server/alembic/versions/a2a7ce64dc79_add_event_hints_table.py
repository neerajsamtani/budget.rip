"""add_event_hints_table

Revision ID: a2a7ce64dc79
Revises: 224fee919c40
Create Date: 2025-12-29 16:48:34.781568

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a2a7ce64dc79"
down_revision: Union[str, Sequence[str], None] = "224fee919c40"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "event_hints",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column("user_id", sa.String(255), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("cel_expression", sa.Text(), nullable=False),
        sa.Column("prefill_name", sa.String(255), nullable=False),
        sa.Column("prefill_category_id", sa.String(255), sa.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("idx_event_hints_user_id", "event_hints", ["user_id"])
    op.create_index("idx_event_hints_user_order", "event_hints", ["user_id", "display_order"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("idx_event_hints_user_order", table_name="event_hints")
    op.drop_index("idx_event_hints_user_id", table_name="event_hints")
    op.drop_table("event_hints")
