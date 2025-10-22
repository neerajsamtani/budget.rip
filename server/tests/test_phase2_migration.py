"""
Comprehensive tests for Phase 2: Reference Data Migration

This test suite validates that reference data (categories, payment methods, parties, tags)
is correctly migrated from MongoDB to PostgreSQL with proper data integrity.
"""

import pytest
import sys
from datetime import datetime, UTC
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from decimal import Decimal

# Add server directory to path
sys.path.insert(0, '..')

from utils.id_generator import generate_id

# Create test-specific models that work with SQLite (no JSONB or PostgreSQL-specific types)
from sqlalchemy import Column, String, Boolean, TIMESTAMP
from sqlalchemy.orm import declarative_base

TestBase = declarative_base()

class Category(TestBase):
    __tablename__ = 'categories'
    id = Column(String(255), primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    mongo_id = Column(String(24), nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC))

class PaymentMethod(TestBase):
    __tablename__ = 'payment_methods'
    id = Column(String(255), primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    type = Column(String(20), nullable=False)  # Simplified for SQLite
    external_id = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC))

class Party(TestBase):
    __tablename__ = 'parties'
    id = Column(String(255), primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    is_ignored = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC))

class Tag(TestBase):
    __tablename__ = 'tags'
    id = Column(String(255), primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(UTC))


# Test database setup
@pytest.fixture(scope="function")
def test_db():
    """Create a fresh test database for each test."""
    # Use in-memory SQLite for tests
    engine = create_engine("sqlite:///:memory:", echo=False)

    # Enable foreign key constraints for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Create all tables
    TestBase.metadata.create_all(engine)

    # Create session
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestSessionLocal()

    yield session

    # Cleanup
    session.close()
    engine.dispose()


class TestCategoryMigration:
    """Tests for category migration."""

    def test_create_category(self, test_db):
        """Test creating a single category."""
        category = Category(
            id=generate_id("cat"),
            name="Groceries",
            is_active=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )
        test_db.add(category)
        test_db.commit()

        # Verify
        saved = test_db.query(Category).filter(Category.name == "Groceries").first()
        assert saved is not None
        assert saved.name == "Groceries"
        assert saved.is_active is True
        assert saved.id.startswith("cat_")

    def test_category_unique_name(self, test_db):
        """Test that category names must be unique."""
        # Create first category
        category1 = Category(
            id=generate_id("cat"),
            name="Dining",
            is_active=True
        )
        test_db.add(category1)
        test_db.commit()

        # Try to create duplicate
        category2 = Category(
            id=generate_id("cat"),
            name="Dining",
            is_active=True
        )
        test_db.add(category2)

        with pytest.raises(Exception):  # IntegrityError
            test_db.commit()

    def test_category_mongo_id(self, test_db):
        """Test that mongo_id is stored for coexistence."""
        category = Category(
            id=generate_id("cat"),
            name="Travel",
            mongo_id="507f1f77bcf86cd799439011",
            is_active=True
        )
        test_db.add(category)
        test_db.commit()

        # Verify
        saved = test_db.query(Category).filter(Category.name == "Travel").first()
        assert saved.mongo_id == "507f1f77bcf86cd799439011"

    def test_migrate_all_categories(self, test_db):
        """Test migrating all categories from constants."""
        from constants import CATEGORIES

        for cat_name in CATEGORIES:
            category = Category(
                id=generate_id("cat"),
                name=cat_name,
                is_active=True,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
            test_db.add(category)

        test_db.commit()

        # Verify count
        count = test_db.query(Category).count()
        assert count == len(CATEGORIES)

        # Verify all names exist
        for cat_name in CATEGORIES:
            exists = test_db.query(Category).filter(Category.name == cat_name).first()
            assert exists is not None, f"Category {cat_name} not found"


class TestPaymentMethodMigration:
    """Tests for payment method migration."""

    def test_create_payment_method(self, test_db):
        """Test creating a single payment method."""
        pm = PaymentMethod(
            id=generate_id("pm"),
            name="Chase Sapphire",
            type="credit",
            is_active=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )
        test_db.add(pm)
        test_db.commit()

        # Verify
        saved = test_db.query(PaymentMethod).filter(PaymentMethod.name == "Chase Sapphire").first()
        assert saved is not None
        assert saved.name == "Chase Sapphire"
        assert saved.type == "credit"
        assert saved.id.startswith("pm_")

    def test_payment_method_types(self, test_db):
        """Test all valid payment method types."""
        valid_types = ["bank", "credit", "venmo", "splitwise", "cash"]

        for i, pm_type in enumerate(valid_types):
            pm = PaymentMethod(
                id=generate_id("pm"),
                name=f"Test {pm_type.title()}",
                type=pm_type,
                is_active=True
            )
            test_db.add(pm)

        test_db.commit()

        # Verify all types were created
        count = test_db.query(PaymentMethod).count()
        assert count == len(valid_types)

    def test_payment_method_unique_name(self, test_db):
        """Test that payment method names must be unique."""
        # Create first payment method
        pm1 = PaymentMethod(
            id=generate_id("pm"),
            name="Venmo",
            type="venmo",
            is_active=True
        )
        test_db.add(pm1)
        test_db.commit()

        # Try to create duplicate
        pm2 = PaymentMethod(
            id=generate_id("pm"),
            name="Venmo",
            type="venmo",
            is_active=True
        )
        test_db.add(pm2)

        with pytest.raises(Exception):  # IntegrityError
            test_db.commit()

    def test_payment_method_external_id(self, test_db):
        """Test storing external ID for payment methods."""
        pm = PaymentMethod(
            id=generate_id("pm"),
            name="Stripe Payment",
            type="credit",
            external_id="stripe_pm_1234567890",
            is_active=True
        )
        test_db.add(pm)
        test_db.commit()

        # Verify
        saved = test_db.query(PaymentMethod).filter(PaymentMethod.name == "Stripe Payment").first()
        assert saved.external_id == "stripe_pm_1234567890"


class TestPartyMigration:
    """Tests for party migration."""

    def test_create_party(self, test_db):
        """Test creating a single party."""
        party = Party(
            id=generate_id("party"),
            name="Amazon",
            is_ignored=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )
        test_db.add(party)
        test_db.commit()

        # Verify
        saved = test_db.query(Party).filter(Party.name == "Amazon").first()
        assert saved is not None
        assert saved.name == "Amazon"
        assert saved.is_ignored is False
        assert saved.id.startswith("party_")

    def test_party_unique_name(self, test_db):
        """Test that party names must be unique."""
        # Create first party
        party1 = Party(
            id=generate_id("party"),
            name="Starbucks",
            is_ignored=False
        )
        test_db.add(party1)
        test_db.commit()

        # Try to create duplicate
        party2 = Party(
            id=generate_id("party"),
            name="Starbucks",
            is_ignored=False
        )
        test_db.add(party2)

        with pytest.raises(Exception):  # IntegrityError
            test_db.commit()

    def test_party_is_ignored_flag(self, test_db):
        """Test party is_ignored flag."""
        party = Party(
            id=generate_id("party"),
            name="Internal Transfer",
            is_ignored=True
        )
        test_db.add(party)
        test_db.commit()

        # Verify
        saved = test_db.query(Party).filter(Party.name == "Internal Transfer").first()
        assert saved.is_ignored is True

    def test_migrate_multiple_parties(self, test_db):
        """Test migrating multiple parties at once."""
        party_names = ["Amazon", "Whole Foods", "Target", "Uber", "Lyft"]

        for name in party_names:
            party = Party(
                id=generate_id("party"),
                name=name,
                is_ignored=False,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
            test_db.add(party)

        test_db.commit()

        # Verify count
        count = test_db.query(Party).count()
        assert count == len(party_names)

        # Verify all parties exist
        for name in party_names:
            exists = test_db.query(Party).filter(Party.name == name).first()
            assert exists is not None, f"Party {name} not found"


class TestTagMigration:
    """Tests for tag migration."""

    def test_create_tag(self, test_db):
        """Test creating a single tag."""
        tag = Tag(
            id=generate_id("tag"),
            name="vacation",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )
        test_db.add(tag)
        test_db.commit()

        # Verify
        saved = test_db.query(Tag).filter(Tag.name == "vacation").first()
        assert saved is not None
        assert saved.name == "vacation"
        assert saved.id.startswith("tag_")

    def test_tag_unique_name(self, test_db):
        """Test that tag names must be unique."""
        # Create first tag
        tag1 = Tag(
            id=generate_id("tag"),
            name="business",
            created_at=datetime.now(UTC)
        )
        test_db.add(tag1)
        test_db.commit()

        # Try to create duplicate
        tag2 = Tag(
            id=generate_id("tag"),
            name="business",
            created_at=datetime.now(UTC)
        )
        test_db.add(tag2)

        with pytest.raises(Exception):  # IntegrityError
            test_db.commit()

    def test_migrate_multiple_tags(self, test_db):
        """Test migrating multiple tags at once."""
        tag_names = ["vacation", "business", "medical", "emergency", "recurring"]

        for name in tag_names:
            tag = Tag(
                id=generate_id("tag"),
                name=name,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
            test_db.add(tag)

        test_db.commit()

        # Verify count
        count = test_db.query(Tag).count()
        assert count == len(tag_names)

        # Verify all tags exist
        for name in tag_names:
            exists = test_db.query(Tag).filter(Tag.name == name).first()
            assert exists is not None, f"Tag {name} not found"


class TestIDGeneration:
    """Tests for ID generation and format."""

    def test_category_id_format(self, test_db):
        """Test that category IDs have correct format."""
        category = Category(
            id=generate_id("cat"),
            name="Test Category",
            is_active=True
        )
        test_db.add(category)
        test_db.commit()

        # Verify ID format
        assert category.id.startswith("cat_")
        assert len(category.id) > 4  # Has ULID after prefix

    def test_payment_method_id_format(self, test_db):
        """Test that payment method IDs have correct format."""
        pm = PaymentMethod(
            id=generate_id("pm"),
            name="Test PM",
            type="credit",
            is_active=True
        )
        test_db.add(pm)
        test_db.commit()

        # Verify ID format
        assert pm.id.startswith("pm_")
        assert len(pm.id) > 3

    def test_party_id_format(self, test_db):
        """Test that party IDs have correct format."""
        party = Party(
            id=generate_id("party"),
            name="Test Party",
            is_ignored=False
        )
        test_db.add(party)
        test_db.commit()

        # Verify ID format
        assert party.id.startswith("party_")
        assert len(party.id) > 6

    def test_tag_id_format(self, test_db):
        """Test that tag IDs have correct format."""
        tag = Tag(
            id=generate_id("tag"),
            name="test"
        )
        test_db.add(tag)
        test_db.commit()

        # Verify ID format
        assert tag.id.startswith("tag_")
        assert len(tag.id) > 4

    def test_id_uniqueness(self, test_db):
        """Test that generated IDs are unique."""
        ids = set()

        # Generate 100 IDs
        for _ in range(100):
            new_id = generate_id("cat")
            assert new_id not in ids, "Duplicate ID generated!"
            ids.add(new_id)

        # All should be unique
        assert len(ids) == 100


class TestTimestamps:
    """Tests for timestamp handling."""

    def test_category_timestamps(self, test_db):
        """Test that category timestamps are set correctly."""
        # Use explicit timestamps to avoid timing issues
        test_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)

        category = Category(
            id=generate_id("cat"),
            name="Test",
            is_active=True,
            created_at=test_time,
            updated_at=test_time
        )
        test_db.add(category)
        test_db.commit()

        # Verify timestamps are stored correctly
        assert category.created_at is not None
        assert category.updated_at is not None
        # Verify timestamps are datetime objects
        assert isinstance(category.created_at, datetime)
        assert isinstance(category.updated_at, datetime)

    def test_payment_method_timestamps(self, test_db):
        """Test that payment method timestamps are set correctly."""
        # Use explicit timestamps to avoid timing issues
        test_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)

        pm = PaymentMethod(
            id=generate_id("pm"),
            name="Test",
            type="credit",
            is_active=True,
            created_at=test_time,
            updated_at=test_time
        )
        test_db.add(pm)
        test_db.commit()

        # Verify timestamps are stored correctly
        assert pm.created_at is not None
        assert pm.updated_at is not None
        # Verify timestamps are datetime objects
        assert isinstance(pm.created_at, datetime)
        assert isinstance(pm.updated_at, datetime)


class TestDataIntegrity:
    """Tests for overall data integrity."""

    def test_full_reference_data_migration(self, test_db):
        """Test migrating all reference data types together."""
        # Migrate categories
        from constants import CATEGORIES
        for cat_name in CATEGORIES:
            category = Category(
                id=generate_id("cat"),
                name=cat_name,
                is_active=True,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
            test_db.add(category)

        # Migrate payment methods
        payment_methods = [
            {"name": "Cash", "type": "cash"},
            {"name": "Venmo", "type": "venmo"},
            {"name": "Splitwise", "type": "splitwise"},
        ]
        for pm_data in payment_methods:
            pm = PaymentMethod(
                id=generate_id("pm"),
                name=pm_data["name"],
                type=pm_data["type"],
                is_active=True,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
            test_db.add(pm)

        # Migrate parties
        parties = ["Amazon", "Whole Foods", "Starbucks"]
        for party_name in parties:
            party = Party(
                id=generate_id("party"),
                name=party_name,
                is_ignored=False,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
            test_db.add(party)

        # Migrate tags
        tags = ["vacation", "business"]
        for tag_name in tags:
            tag = Tag(
                id=generate_id("tag"),
                name=tag_name,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
            test_db.add(tag)

        # Commit all at once
        test_db.commit()

        # Verify counts
        assert test_db.query(Category).count() == len(CATEGORIES)
        assert test_db.query(PaymentMethod).count() == len(payment_methods)
        assert test_db.query(Party).count() == len(parties)
        assert test_db.query(Tag).count() == len(tags)

    def test_no_duplicate_ids_across_types(self, test_db):
        """Test that IDs are unique even across different entity types."""
        # Create one of each type
        category = Category(id=generate_id("cat"), name="Cat1", is_active=True)
        pm = PaymentMethod(id=generate_id("pm"), name="PM1", type="credit", is_active=True)
        party = Party(id=generate_id("party"), name="Party1", is_ignored=False)
        tag = Tag(id=generate_id("tag"), name="Tag1")

        test_db.add_all([category, pm, party, tag])
        test_db.commit()

        # Collect all IDs
        all_ids = [category.id, pm.id, party.id, tag.id]

        # All should be unique
        assert len(all_ids) == len(set(all_ids))

        # All should have correct prefixes
        assert category.id.startswith("cat_")
        assert pm.id.startswith("pm_")
        assert party.id.startswith("party_")
        assert tag.id.startswith("tag_")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
