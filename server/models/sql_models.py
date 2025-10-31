# server/models/sql_models.py
from sqlalchemy import Column, String, DECIMAL, TIMESTAMP, Text, Boolean, ForeignKey, Enum, UniqueConstraint, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime, UTC
from decimal import Decimal

Base = declarative_base()

# Note: No User model - this is a single-user application
# Authentication handled via environment config or hardcoded credentials

class Category(Base):
    __tablename__ = 'categories'

    id = Column(String(255), primary_key=True)  # cat_xxx
    name = Column(String(100), nullable=False, unique=True)
    mongo_id = Column(String(24), nullable=True, index=True)  # Original MongoDB _id
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Relationships
    events = relationship('Event', back_populates='category')


class PaymentMethod(Base):
    __tablename__ = 'payment_methods'

    id = Column(String(255), primary_key=True)  # pm_xxx
    name = Column(String(100), nullable=False, unique=True)
    type = Column(Enum('bank', 'credit', 'venmo', 'splitwise', 'cash', name='payment_method_type'), nullable=False)
    external_id = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class Party(Base):
    __tablename__ = 'parties'

    id = Column(String(255), primary_key=True)  # party_xxx
    name = Column(String(100), nullable=False, unique=True)
    is_ignored = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class Tag(Base):
    __tablename__ = 'tags'

    id = Column(String(255), primary_key=True)  # tag_xxx
    name = Column(String(100), nullable=False, unique=True)
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class Transaction(Base):
    __tablename__ = 'transactions'
    __table_args__ = (
        UniqueConstraint('source', 'source_id', name='uq_transaction_source'),
    )

    id = Column(String(255), primary_key=True)  # txn_xxx
    source = Column(Enum('venmo', 'splitwise', 'stripe', 'cash', 'manual', name='transaction_source'), nullable=False)
    source_id = Column(String(255), nullable=False)
    source_data = Column(JSON().with_variant(JSONB, 'postgresql'), nullable=False)  # JSONB for PostgreSQL, JSON for others
    transaction_date = Column(TIMESTAMP(timezone=True), nullable=False)
    imported_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC))
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC))


class LineItem(Base):
    __tablename__ = 'line_items'

    id = Column(String(255), primary_key=True)  # li_xxx
    transaction_id = Column(String(255), ForeignKey('transactions.id', ondelete='CASCADE'), nullable=False)
    mongo_id = Column(String(24), nullable=True, index=True)  # Original MongoDB _id
    date = Column(TIMESTAMP(timezone=True), nullable=False)
    amount = Column(DECIMAL(12, 2), nullable=False)
    description = Column(Text, nullable=False)
    payment_method_id = Column(String(255), ForeignKey('payment_methods.id', ondelete='RESTRICT'), nullable=False)
    party_id = Column(String(255), ForeignKey('parties.id', ondelete='SET NULL'), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Relationships
    transaction = relationship('Transaction')
    payment_method = relationship('PaymentMethod')
    party = relationship('Party')
    events = relationship('Event', secondary='event_line_items', back_populates='line_items')


class Event(Base):
    __tablename__ = 'events'

    id = Column(String(255), primary_key=True)  # evt_xxx
    mongo_id = Column(String(24), nullable=True, index=True)  # Original MongoDB _id
    date = Column(TIMESTAMP(timezone=True), nullable=False)
    description = Column(Text, nullable=False)
    category_id = Column(String(255), ForeignKey('categories.id', ondelete='RESTRICT'), nullable=False)
    is_duplicate = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Relationships
    category = relationship('Category', back_populates='events')
    line_items = relationship('LineItem', secondary='event_line_items', back_populates='events')
    tags = relationship('Tag', secondary='event_tags')

    @property
    def total_amount(self) -> Decimal:
        """Computed property - never stored in DB"""
        if not self.line_items:
            return Decimal('0.00')
        if self.is_duplicate:
            return self.line_items[0].amount
        return sum(li.amount for li in self.line_items)


class EventLineItem(Base):
    __tablename__ = 'event_line_items'
    __table_args__ = (
        UniqueConstraint('event_id', 'line_item_id', name='uq_event_line_item'),
    )

    id = Column(String(255), primary_key=True)  # eli_xxx
    event_id = Column(String(255), ForeignKey('events.id', ondelete='CASCADE'), nullable=False)
    line_item_id = Column(String(255), ForeignKey('line_items.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC))


class EventTag(Base):
    __tablename__ = 'event_tags'
    __table_args__ = (
        UniqueConstraint('event_id', 'tag_id', name='uq_event_tag'),
    )

    id = Column(String(255), primary_key=True)  # etag_xxx
    event_id = Column(String(255), ForeignKey('events.id', ondelete='CASCADE'), nullable=False)
    tag_id = Column(String(255), ForeignKey('tags.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC))
