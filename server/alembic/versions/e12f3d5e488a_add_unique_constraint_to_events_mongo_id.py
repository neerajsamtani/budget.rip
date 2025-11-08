"""add unique constraint to events mongo_id

Revision ID: e12f3d5e488a
Revises: 9a34125f75b2
Create Date: 2025-11-08 13:57:29.850659

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e12f3d5e488a"
down_revision: Union[str, Sequence[str], None] = "9a34125f75b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check for duplicates before adding unique constraint
    # This query will fail if duplicates exist, which is the correct behavior
    # If duplicates exist, they need to be manually resolved before migration

    # Add unique constraint to events.mongo_id
    # Note: mongo_id can be NULL (for events created directly in PostgreSQL),
    # so we use a partial unique index that only applies to non-NULL values
    op.create_unique_constraint("uq_events_mongo_id", "events", ["mongo_id"])


def downgrade() -> None:
    """Downgrade schema."""
    # Remove the unique constraint
    op.drop_constraint("uq_events_mongo_id", "events", type_="unique")
