"""add event suggestion provenance

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "b8c9d0e1f2a3"
down_revision: Union[str, Sequence[str], None] = "a7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # The server default backfills every existing row, including rejected ones and those whose hint was deleted.
    op.add_column(
        "event_suggestions",
        sa.Column("source", sa.String(64), nullable=False, server_default="event_hint"),
    )
    op.add_column(
        "event_suggestions",
        sa.Column("source_metadata", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("event_suggestions", "source_metadata")
    op.drop_column("event_suggestions", "source")
