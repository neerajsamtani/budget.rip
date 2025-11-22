"""Add integration_accounts table

Revision ID: a1b2c3d4e5f6
Revises: fb7a20ffd5fe
Create Date: 2025-11-22 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "fb7a20ffd5fe"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "integration_accounts",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column(
            "source",
            sa.Enum("venmo", "splitwise", name="integration_source"),
            nullable=False,
        ),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("last_refreshed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("integration_accounts")
    op.execute("DROP TYPE IF EXISTS integration_source")
