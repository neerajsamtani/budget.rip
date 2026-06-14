"""add user_id to tags

Revision ID: c3d4e5f6a7b8
Revises: b1c2d3e4f5a6
Create Date: 2026-06-14 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "b1c2d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Step 1: Drop the old global unique constraint on name
    op.drop_constraint("tags_name_key", "tags", type_="unique")

    # Step 2: Add user_id column (nullable initially to handle existing data)
    op.add_column("tags", sa.Column("user_id", sa.String(255), nullable=True))

    # Step 3: Backfill user_id from the first (only) user so existing rows are valid
    connection = op.get_bind()
    result = connection.execute(sa.text("SELECT id FROM users LIMIT 1"))
    first_user = result.fetchone()

    if first_user:
        user_id = first_user[0]
        connection.execute(sa.text("UPDATE tags SET user_id = :user_id WHERE user_id IS NULL"), {"user_id": user_id})

    # Step 4: Make user_id NOT NULL and add foreign key
    op.alter_column("tags", "user_id", nullable=False)
    op.create_foreign_key("fk_tags_user_id", "tags", "users", ["user_id"], ["id"], ondelete="CASCADE")

    # Step 5: Create index on user_id
    op.create_index("ix_tags_user_id", "tags", ["user_id"])

    # Step 6: Create unique constraint on (user_id, name)
    op.create_unique_constraint("uq_user_tag_name", "tags", ["user_id", "name"])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the new unique constraint
    op.drop_constraint("uq_user_tag_name", "tags", type_="unique")

    # Drop the index
    op.drop_index("ix_tags_user_id", table_name="tags")

    # Drop the foreign key
    op.drop_constraint("fk_tags_user_id", "tags", type_="foreignkey")

    # Drop user_id column
    op.drop_column("tags", "user_id")

    # Re-add global unique constraint on name
    op.create_unique_constraint("tags_name_key", "tags", ["name"])
