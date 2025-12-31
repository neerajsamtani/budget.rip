# server/models/sql_models.py
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import (
    DECIMAL,
    JSON,
    TIMESTAMP,
    Boolean,
    Column,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class BankAccount(Base):
    """
    Financial accounts from external sources (e.g., Stripe Financial Connections).

    BankAccount vs PaymentMethod:
    - BankAccount: The actual financial account (e.g., "Chase Checking 1234")
    - PaymentMethod: How a transaction was paid (derived from accounts + manual methods)
    - PaymentMethod.external_id soft-references BankAccount.id when type is bank/credit
    """

    __tablename__ = "bank_accounts"

    id = Column(String(255), primary_key=True)  # fca_xxx or account ID from source
    institution_name = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=False)
    last4 = Column(String(4), nullable=False)
    status = Column(String(50), nullable=False)
    can_relink = Column(Boolean, nullable=False, default=True)  # Whether inactive account can be relinked
    currency = Column(String(3), nullable=True)  # ISO 4217 currency code (e.g., 'usd', 'eur')
    latest_balance = Column(DECIMAL(12, 2), nullable=True)  # Most recent balance from Stripe in account currency
    balance_as_of = Column(TIMESTAMP(timezone=True), nullable=True)  # When Stripe calculated the balance
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class User(Base):
    __tablename__ = "users"

    id = Column(String(255), primary_key=True)  # user_xxx
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class Category(Base):
    __tablename__ = "categories"

    id = Column(String(255), primary_key=True)  # cat_xxx
    name = Column(String(100), nullable=False, unique=True)
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    events = relationship("Event", back_populates="category")


class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    id = Column(String(255), primary_key=True)  # pm_xxx
    name = Column(String(100), nullable=False, unique=True)
    type = Column(
        Enum("bank", "credit", "venmo", "splitwise", "cash", name="payment_method_type"),
        nullable=False,
    )
    external_id = Column(String(255), nullable=True)  # Primary/current external ID
    aliases = Column(JSON, nullable=True)  # List of historical external IDs (e.g., old fca_ IDs)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class Tag(Base):
    __tablename__ = "tags"

    id = Column(String(255), primary_key=True)  # tag_xxx
    name = Column(String(100), nullable=False, unique=True)
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (UniqueConstraint("source", "source_id", name="uq_transaction_source"),)

    id = Column(String(255), primary_key=True)  # txn_xxx
    source = Column(
        Enum("venmo", "splitwise", "stripe", "cash", "manual", name="transaction_source"),
        nullable=False,
    )
    source_id = Column(String(255), nullable=False)
    source_data = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False)  # JSONB for PostgreSQL, JSON for others
    transaction_date = Column(TIMESTAMP(timezone=True), nullable=False)
    imported_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC))
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC))


class LineItem(Base):
    __tablename__ = "line_items"

    id = Column(String(255), primary_key=True)  # li_xxx
    transaction_id = Column(String(255), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False)
    date = Column(TIMESTAMP(timezone=True), nullable=False)
    amount = Column(DECIMAL(12, 2), nullable=False)
    description = Column(Text, nullable=False)
    payment_method_id = Column(
        String(255),
        ForeignKey("payment_methods.id", ondelete="RESTRICT"),
        nullable=False,
    )
    responsible_party = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    transaction = relationship("Transaction")
    payment_method = relationship("PaymentMethod")
    events = relationship("Event", secondary="event_line_items", back_populates="line_items")


class Event(Base):
    __tablename__ = "events"

    id = Column(String(255), primary_key=True)  # evt_xxx
    date = Column(TIMESTAMP(timezone=True), nullable=False)
    description = Column(Text, nullable=False)
    category_id = Column(String(255), ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False)
    is_duplicate = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    category = relationship("Category", back_populates="events")
    line_items = relationship("LineItem", secondary="event_line_items", back_populates="events")
    tags = relationship("Tag", secondary="event_tags")

    @property
    def total_amount(self) -> Decimal:
        """Computed property - never stored in DB"""
        if not self.line_items:
            return Decimal("0.00")
        if self.is_duplicate:
            return self.line_items[0].amount
        return sum(li.amount for li in self.line_items)


class EventLineItem(Base):
    __tablename__ = "event_line_items"
    __table_args__ = (UniqueConstraint("event_id", "line_item_id", name="uq_event_line_item"),)

    id = Column(String(255), primary_key=True)  # eli_xxx
    event_id = Column(String(255), ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    line_item_id = Column(String(255), ForeignKey("line_items.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC))


class EventTag(Base):
    __tablename__ = "event_tags"
    __table_args__ = (UniqueConstraint("event_id", "tag_id", name="uq_event_tag"),)

    id = Column(String(255), primary_key=True)  # etag_xxx
    event_id = Column(String(255), ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    tag_id = Column(String(255), ForeignKey("tags.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC))


class EventHint(Base):
    """
    User-configurable rules for auto-filling event details.

    Each hint contains a CEL expression that is evaluated against line items.
    If the expression matches, the prefill_name and prefill_category are suggested.
    Hints are evaluated in display_order; first match wins.
    """

    __tablename__ = "event_hints"

    id = Column(String(255), primary_key=True)  # eh_xxx
    user_id = Column(String(255), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    cel_expression = Column(Text, nullable=False)
    prefill_name = Column(String(255), nullable=False)
    prefill_category_id = Column(String(255), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    display_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    user = relationship("User")
    prefill_category = relationship("Category")
