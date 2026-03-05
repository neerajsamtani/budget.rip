"""initial sqlite schema - squashed from all previous postgresql migrations

Revision ID: 0001
Revises:
Create Date: 2026-03-05

Squashed migration representing the complete schema. All previous PostgreSQL
migrations have been consolidated into this single SQLite-compatible migration.
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column("first_name", sa.String(255), nullable=False),
        sa.Column("last_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True)),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "categories",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column("user_id", sa.String(255), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True)),
        sa.UniqueConstraint("user_id", "name", name="uq_user_category_name"),
    )
    op.create_index("ix_categories_user_id", "categories", ["user_id"])

    op.create_table(
        "payment_methods",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("type", sa.Enum("bank", "credit", "venmo", "splitwise", "cash", name="payment_method_type"), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("aliases", sa.JSON, nullable=True),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True)),
    )

    op.create_table(
        "tags",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True)),
    )

    op.create_table(
        "transactions",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column(
            "source",
            sa.Enum("venmo_api", "splitwise_api", "stripe_api", "manual", name="transaction_source"),
            nullable=False,
        ),
        sa.Column("source_id", sa.String(255), nullable=False),
        sa.Column("source_data", sa.JSON, nullable=False),
        sa.Column("transaction_date", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("imported_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True)),
        sa.UniqueConstraint("source", "source_id", name="uq_transaction_source"),
    )

    op.create_table(
        "line_items",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column("transaction_id", sa.String(255), sa.ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("amount", sa.DECIMAL(12, 2), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column(
            "payment_method_id",
            sa.String(255),
            sa.ForeignKey("payment_methods.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("responsible_party", sa.String(255), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True)),
        sa.UniqueConstraint("transaction_id", name="uq_line_item_transaction"),
    )
    op.create_index("ix_line_items_transaction_id", "line_items", ["transaction_id"])
    op.create_index("ix_line_items_payment_method_id", "line_items", ["payment_method_id"])

    op.create_table(
        "events",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column("date", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("category_id", sa.String(255), sa.ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("is_duplicate", sa.Boolean, default=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True)),
    )
    op.create_index("ix_events_category_id", "events", ["category_id"])

    op.create_table(
        "event_line_items",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column("event_id", sa.String(255), sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("line_item_id", sa.String(255), sa.ForeignKey("line_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True)),
        sa.UniqueConstraint("event_id", "line_item_id", name="uq_event_line_item"),
    )
    op.create_index("ix_event_line_items_event_id", "event_line_items", ["event_id"])
    op.create_index("ix_event_line_items_line_item_id", "event_line_items", ["line_item_id"])

    op.create_table(
        "event_tags",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column("event_id", sa.String(255), sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tag_id", sa.String(255), sa.ForeignKey("tags.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True)),
        sa.UniqueConstraint("event_id", "tag_id", name="uq_event_tag"),
    )

    op.create_table(
        "bank_accounts",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column("institution_name", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("last4", sa.String(4), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("can_relink", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("currency", sa.String(3), nullable=True),
        sa.Column("latest_balance", sa.DECIMAL(12, 2), nullable=True),
        sa.Column("balance_as_of", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True)),
    )

    op.create_table(
        "event_hints",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column("user_id", sa.String(255), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("cel_expression", sa.Text, nullable=False),
        sa.Column("prefill_name", sa.String(255), nullable=False),
        sa.Column("prefill_category_id", sa.String(255), sa.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("display_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True)),
    )


def downgrade() -> None:
    op.drop_table("event_hints")
    op.drop_table("bank_accounts")
    op.drop_table("event_tags")
    op.drop_table("event_line_items")
    op.drop_table("events")
    op.drop_table("line_items")
    op.drop_table("transactions")
    op.drop_table("tags")
    op.drop_table("payment_methods")
    op.drop_table("categories")
    op.drop_table("users")
