"""add user_id to categories and remove is_active

Revision ID: e310f0f583d7
Revises: a2a7ce64dc79
Create Date: 2025-12-31 11:20:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e310f0f583d7"
down_revision: Union[str, Sequence[str], None] = "a2a7ce64dc79"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Step 1: Drop the old unique constraint on name
    op.drop_constraint("categories_name_key", "categories", type_="unique")

    # Step 2: Drop is_active column if it exists
    op.drop_column("categories", "is_active")

    # Step 3: Add user_id column (nullable initially to handle existing data)
    op.add_column("categories", sa.Column("user_id", sa.String(255), nullable=True))

    # Step 4: Get the first user ID and assign all existing categories to that user
    # This is a data migration for existing categories
    connection = op.get_bind()
    result = connection.execute(sa.text("SELECT id FROM users LIMIT 1"))
    first_user = result.fetchone()

    if first_user:
        user_id = first_user[0]
        connection.execute(sa.text("UPDATE categories SET user_id = :user_id WHERE user_id IS NULL"), {"user_id": user_id})

    # Step 5: Make user_id NOT NULL and add foreign key
    op.alter_column("categories", "user_id", nullable=False)
    op.create_foreign_key("fk_categories_user_id", "categories", "users", ["user_id"], ["id"], ondelete="CASCADE")

    # Step 6: Create index on user_id
    op.create_index("ix_categories_user_id", "categories", ["user_id"])

    # Step 7: Create unique constraint on (user_id, name)
    op.create_unique_constraint("uq_user_category_name", "categories", ["user_id", "name"])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the new unique constraint
    op.drop_constraint("uq_user_category_name", "categories", type_="unique")

    # Drop the index
    op.drop_index("ix_categories_user_id", table_name="categories")

    # Drop the foreign key
    op.drop_constraint("fk_categories_user_id", "categories", type_="foreignkey")

    # Drop user_id column
    op.drop_column("categories", "user_id")

    # Re-add is_active column
    op.add_column("categories", sa.Column("is_active", sa.Boolean(), nullable=True))

    # Re-add unique constraint on name
    op.create_unique_constraint("categories_name_key", "categories", ["name"])
