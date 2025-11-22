"""
Phase 5: Read Operation Cutover Tests

Tests that PostgreSQL read operations return the same data as MongoDB reads.
Verifies the READ_FROM_POSTGRESQL flag works correctly.

Test coverage:
- Line item read operations (all, by ID, with filters)
- Event read operations (all, by ID, with filters)
- Line items for event
- Analytics aggregation
- ID coexistence (both ID formats)
- Filter consistency
- Raw transaction reads (venmo, splitwise, stripe, cash)

NOTE: This test file uses the shared database setup from conftest.py.
The DATABASE_HOST and DATABASE_NAME env vars are set in conftest.py before any imports.
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from dao import (
    _pg_get_all_bank_accounts,
    _pg_get_all_events,
    _pg_get_all_line_items,
    _pg_get_categorized_data,
    _pg_get_event_by_id,
    _pg_get_line_item_by_id,
    _pg_get_line_items_for_event,
    _pg_get_transactions,
    _pg_get_user_by_email,
    _pg_get_user_by_id,
    bank_accounts_collection,
    events_collection,
    get_all_data,
    get_user_by_email,
    line_items_collection,
)
from models.sql_models import (
    BankAccount,
    Category,
    Event,
    EventLineItem,
    LineItem,
    PaymentMethod,
    Transaction,
    User,
)
from utils.id_generator import generate_id


@pytest.fixture(scope="function")
def sample_payment_methods(pg_session):
    """Create sample payment methods"""
    payment_methods = [
        PaymentMethod(id="pm_001", name="Credit Card", type="credit", is_active=True),
        PaymentMethod(id="pm_002", name="Debit Card", type="bank", is_active=True),
        PaymentMethod(id="pm_003", name="Venmo", type="venmo", is_active=True),
        PaymentMethod(id="pm_004", name="Cash", type="cash", is_active=True),
    ]

    for pm in payment_methods:
        pg_session.add(pm)

    pg_session.commit()
    return payment_methods


@pytest.fixture(scope="function")
def sample_categories(pg_session):
    """Create sample categories"""
    categories = [
        Category(id="cat_001", name="Dining", is_active=True),
        Category(id="cat_002", name="Groceries", is_active=True),
        Category(id="cat_003", name="Travel", is_active=True),
        Category(id="cat_004", name="Entertainment", is_active=True),
    ]

    for cat in categories:
        pg_session.add(cat)

    pg_session.commit()
    return categories


@pytest.fixture(scope="function")
def sample_transactions(pg_session):
    """Create sample transactions"""
    transactions = [
        Transaction(
            id="txn_001",
            source="venmo",
            source_id="venmo_123",
            source_data={"test": "data1"},
            transaction_date=datetime(2024, 1, 15, tzinfo=UTC),
        ),
        Transaction(
            id="txn_002",
            source="stripe",
            source_id="stripe_456",
            source_data={"test": "data2"},
            transaction_date=datetime(2024, 2, 20, tzinfo=UTC),
        ),
        Transaction(
            id="txn_003",
            source="cash",
            source_id="cash_789",
            source_data={"test": "data3"},
            transaction_date=datetime(2024, 3, 10, tzinfo=UTC),
        ),
    ]

    for txn in transactions:
        pg_session.add(txn)

    pg_session.commit()
    return transactions


class TestLineItemReads:
    """Test line item read operations"""

    def test_pg_get_all_line_items(self, pg_session, sample_payment_methods, sample_transactions):
        """Test getting all line items from PostgreSQL"""
        # Create line items
        line_items = [
            LineItem(
                id="li_001",
                mongo_id="507f1f77bcf86cd799439011",
                transaction_id="txn_001",
                payment_method_id="pm_001",
                date=datetime(2024, 1, 15, tzinfo=UTC),
                amount=Decimal("-25.50"),
                description="Dinner at restaurant",
                responsible_party="John",
                notes="Split with friends",
            ),
            LineItem(
                id="li_002",
                mongo_id="507f1f77bcf86cd799439012",
                transaction_id="txn_002",
                payment_method_id="pm_002",
                date=datetime(2024, 2, 20, tzinfo=UTC),
                amount=Decimal("-15.00"),
                description="Groceries",
                responsible_party="Jane",
            ),
            LineItem(
                id="li_003",
                mongo_id="507f1f77bcf86cd799439013",
                transaction_id="txn_003",
                payment_method_id="pm_003",
                date=datetime(2024, 3, 10, tzinfo=UTC),
                amount=Decimal("-50.00"),
                description="Hotel booking",
                responsible_party="John",
            ),
        ]

        for li in line_items:
            pg_session.add(li)
        pg_session.commit()

        # Test: Get all line items
        result = _pg_get_all_line_items({})

        assert len(result) == 3
        # id field returns mongo_id for MongoDB compatibility
        assert result[0]["id"] in [
            "507f1f77bcf86cd799439011",
            "507f1f77bcf86cd799439012",
            "507f1f77bcf86cd799439013",
        ]
        assert "_id" in result[0]
        assert "date" in result[0]
        assert "amount" in result[0]
        assert "payment_method" in result[0]

    def test_pg_get_line_item_by_id_postgresql_id(self, pg_session, sample_payment_methods, sample_transactions):
        """Test getting line item by PostgreSQL ID"""
        line_item = LineItem(
            id="li_001",
            mongo_id="507f1f77bcf86cd799439011",
            transaction_id="txn_001",
            payment_method_id="pm_001",
            date=datetime(2024, 1, 15, tzinfo=UTC),
            amount=Decimal("-25.50"),
            description="Test item",
        )
        pg_session.add(line_item)
        pg_session.commit()

        result = _pg_get_line_item_by_id("li_001")

        assert result is not None
        # id field returns mongo_id for MongoDB compatibility
        assert result["id"] == "507f1f77bcf86cd799439011"
        assert result["_id"] == "507f1f77bcf86cd799439011"

    def test_pg_get_line_item_by_id_mongodb_id(self, pg_session, sample_payment_methods, sample_transactions):
        """Test getting line item by MongoDB ID (ID coexistence)"""
        line_item = LineItem(
            id="li_001",
            mongo_id="507f1f77bcf86cd799439011",
            transaction_id="txn_001",
            payment_method_id="pm_001",
            date=datetime(2024, 1, 15, tzinfo=UTC),
            amount=Decimal("-25.50"),
            description="Test item",
        )
        pg_session.add(line_item)
        pg_session.commit()

        result = _pg_get_line_item_by_id("507f1f77bcf86cd799439011")

        assert result is not None
        # id field returns mongo_id for MongoDB compatibility
        assert result["id"] == "507f1f77bcf86cd799439011"
        assert result["_id"] == "507f1f77bcf86cd799439011"

    def test_pg_get_line_items_with_payment_method_filter(self, pg_session, sample_payment_methods, sample_transactions):
        """Test filtering line items by payment method"""
        line_items = [
            LineItem(
                id="li_001",
                transaction_id="txn_001",
                payment_method_id="pm_001",
                date=datetime(2024, 1, 15, tzinfo=UTC),
                amount=Decimal("-25.50"),
                description="Credit card purchase",
            ),
            LineItem(
                id="li_002",
                transaction_id="txn_002",
                payment_method_id="pm_002",
                date=datetime(2024, 2, 20, tzinfo=UTC),
                amount=Decimal("-15.00"),
                description="Debit card purchase",
            ),
        ]

        for li in line_items:
            pg_session.add(li)
        pg_session.commit()

        # Filter by Credit Card
        result = _pg_get_all_line_items({"payment_method": "Credit Card"})

        assert len(result) == 1
        assert result[0]["payment_method"] == "Credit Card"

    def test_pg_get_line_items_unassigned_filter(
        self, pg_session, sample_payment_methods, sample_transactions, sample_categories
    ):
        """Test filtering for unassigned line items (for review)"""
        # Create line items
        li1 = LineItem(
            id="li_001",
            transaction_id="txn_001",
            payment_method_id="pm_001",
            date=datetime(2024, 1, 15, tzinfo=UTC),
            amount=Decimal("-25.50"),
            description="Unassigned item",
        )
        li2 = LineItem(
            id="li_002",
            transaction_id="txn_002",
            payment_method_id="pm_002",
            date=datetime(2024, 2, 20, tzinfo=UTC),
            amount=Decimal("-15.00"),
            description="Assigned item",
        )

        pg_session.add(li1)
        pg_session.add(li2)
        pg_session.commit()

        # Create event and assign li2
        event = Event(
            id="evt_001",
            category_id="cat_001",
            date=datetime(2024, 2, 20, tzinfo=UTC),
            description="Test event",
        )
        pg_session.add(event)
        pg_session.commit()

        junction = EventLineItem(id=generate_id("eli"), event_id="evt_001", line_item_id="li_002")
        pg_session.add(junction)
        pg_session.commit()

        # Filter for unassigned line items
        result = _pg_get_all_line_items({"event_id": {"$exists": False}})

        assert len(result) == 1
        assert result[0]["id"] == "li_001"


class TestEventReads:
    """Test event read operations"""

    def test_pg_get_all_events(self, pg_session, sample_categories):
        """Test getting all events from PostgreSQL"""
        events = [
            Event(
                id="evt_001",
                mongo_id="507f1f77bcf86cd799439021",
                category_id="cat_001",
                date=datetime(2024, 1, 15, tzinfo=UTC),
                description="Dinner outing",
            ),
            Event(
                id="evt_002",
                mongo_id="507f1f77bcf86cd799439022",
                category_id="cat_002",
                date=datetime(2024, 2, 20, tzinfo=UTC),
                description="Weekly shopping",
            ),
        ]

        for evt in events:
            pg_session.add(evt)
        pg_session.commit()

        result = _pg_get_all_events({})

        assert len(result) == 2
        # Should return MongoDB IDs, not PostgreSQL IDs (for application transparency)
        assert result[0]["id"] in [
            "507f1f77bcf86cd799439021",
            "507f1f77bcf86cd799439022",
        ]
        assert result[0]["_id"] in [
            "507f1f77bcf86cd799439021",
            "507f1f77bcf86cd799439022",
        ]
        assert "category" in result[0]
        assert "amount" in result[0]

    def test_pg_get_event_by_id_postgresql_id(self, pg_session, sample_categories):
        """Test getting event by PostgreSQL ID"""
        event = Event(
            id="evt_001",
            mongo_id="507f1f77bcf86cd799439021",
            category_id="cat_001",
            date=datetime(2024, 1, 15, tzinfo=UTC),
            description="Test event",
        )
        pg_session.add(event)
        pg_session.commit()

        result = _pg_get_event_by_id("evt_001")

        assert result is not None
        # Should return MongoDB ID for both fields (application transparency)
        assert result["id"] == "507f1f77bcf86cd799439021"
        assert result["_id"] == "507f1f77bcf86cd799439021"

    def test_pg_get_event_by_id_mongodb_id(self, pg_session, sample_categories):
        """Test getting event by MongoDB ID (ID coexistence)"""
        event = Event(
            id="evt_001",
            mongo_id="507f1f77bcf86cd799439021",
            category_id="cat_001",
            date=datetime(2024, 1, 15, tzinfo=UTC),
            description="Test event",
        )
        pg_session.add(event)
        pg_session.commit()

        result = _pg_get_event_by_id("507f1f77bcf86cd799439021")

        assert result is not None
        # Should return MongoDB ID (application transparency)
        assert result["id"] == "507f1f77bcf86cd799439021"
        assert result["_id"] == "507f1f77bcf86cd799439021"
        assert result["category"] == "Dining"

    def test_pg_get_events_with_date_filter(self, pg_session, sample_categories):
        """Test filtering events by date range"""
        events = [
            Event(
                id="evt_001",
                category_id="cat_001",
                date=datetime(2024, 1, 15, tzinfo=UTC),
                description="January event",
            ),
            Event(
                id="evt_002",
                category_id="cat_002",
                date=datetime(2024, 6, 20, tzinfo=UTC),
                description="June event",
            ),
        ]

        for evt in events:
            pg_session.add(evt)
        pg_session.commit()

        # Filter for events in first half of year
        start_time = datetime(2024, 1, 1, tzinfo=UTC).timestamp()
        mid_time = datetime(2024, 6, 1, tzinfo=UTC).timestamp()

        result = _pg_get_all_events({"date": {"$gte": start_time, "$lte": mid_time}})

        assert len(result) == 1
        assert result[0]["id"] == "evt_001"


class TestEventLineItemRelationship:
    """Test event-line item relationship operations"""

    def test_pg_get_line_items_for_event(
        self,
        pg_session,
        sample_categories,
        sample_payment_methods,
        sample_transactions,
    ):
        """Test getting line items for a specific event"""
        # Create event
        event = Event(
            id="evt_001",
            category_id="cat_001",
            date=datetime(2024, 1, 15, tzinfo=UTC),
            description="Weekend trip",
        )
        pg_session.add(event)
        pg_session.commit()

        # Create line items
        line_items = [
            LineItem(
                id="li_001",
                transaction_id="txn_001",
                payment_method_id="pm_001",
                date=datetime(2024, 1, 15, tzinfo=UTC),
                amount=Decimal("-50.00"),
                description="Hotel",
            ),
            LineItem(
                id="li_002",
                transaction_id="txn_002",
                payment_method_id="pm_002",
                date=datetime(2024, 1, 15, tzinfo=UTC),
                amount=Decimal("-30.00"),
                description="Gas",
            ),
            LineItem(
                id="li_003",
                transaction_id="txn_003",
                payment_method_id="pm_003",
                date=datetime(2024, 2, 1, tzinfo=UTC),
                amount=Decimal("-20.00"),
                description="Unrelated item",
            ),
        ]

        for li in line_items:
            pg_session.add(li)
        pg_session.commit()

        # Link first two line items to event
        junctions = [
            EventLineItem(id=generate_id("eli"), event_id="evt_001", line_item_id="li_001"),
            EventLineItem(id=generate_id("eli"), event_id="evt_001", line_item_id="li_002"),
        ]
        for j in junctions:
            pg_session.add(j)
        pg_session.commit()

        # Test: Get line items for event
        result = _pg_get_line_items_for_event("evt_001")

        assert len(result) == 2
        assert result[0]["id"] in ["li_001", "li_002"]
        assert result[1]["id"] in ["li_001", "li_002"]


class TestAnalyticsAggregation:
    """Test analytics aggregation operations"""

    def test_pg_get_categorized_data(
        self,
        pg_session,
        sample_categories,
        sample_payment_methods,
        sample_transactions,
    ):
        """Test monthly breakdown aggregation"""
        # Create events with line items
        event1 = Event(
            id="evt_001",
            category_id="cat_001",  # Dining
            date=datetime(2024, 1, 15, tzinfo=UTC),
            description="Dinner",
        )
        event2 = Event(
            id="evt_002",
            category_id="cat_002",  # Groceries
            date=datetime(2024, 1, 20, tzinfo=UTC),
            description="Shopping",
        )
        event3 = Event(
            id="evt_003",
            category_id="cat_001",  # Dining
            date=datetime(2024, 2, 10, tzinfo=UTC),
            description="Lunch",
        )

        pg_session.add(event1)
        pg_session.add(event2)
        pg_session.add(event3)
        pg_session.commit()

        # Create line items
        line_items = [
            LineItem(
                id="li_001",
                transaction_id="txn_001",
                payment_method_id="pm_001",
                date=datetime(2024, 1, 15, tzinfo=UTC),
                amount=Decimal("-50.00"),
                description="Event 1 item",
            ),
            LineItem(
                id="li_002",
                transaction_id="txn_002",
                payment_method_id="pm_002",
                date=datetime(2024, 1, 20, tzinfo=UTC),
                amount=Decimal("-30.00"),
                description="Event 2 item",
            ),
            LineItem(
                id="li_003",
                transaction_id="txn_003",
                payment_method_id="pm_003",
                date=datetime(2024, 2, 10, tzinfo=UTC),
                amount=Decimal("-25.00"),
                description="Event 3 item",
            ),
        ]

        for li in line_items:
            pg_session.add(li)
        pg_session.commit()

        # Link line items to events
        junctions = [
            EventLineItem(id=generate_id("eli"), event_id="evt_001", line_item_id="li_001"),
            EventLineItem(id=generate_id("eli"), event_id="evt_002", line_item_id="li_002"),
            EventLineItem(id=generate_id("eli"), event_id="evt_003", line_item_id="li_003"),
        ]
        for j in junctions:
            pg_session.add(j)
        pg_session.commit()

        # Test: Get categorized data
        result = _pg_get_categorized_data()

        # Should have 3 groups: Jan-Dining, Jan-Groceries, Feb-Dining
        assert len(result) >= 2  # At least 2 categories

        # Find Dining category in January
        jan_dining = [r for r in result if r["year"] == 2024 and r["month"] == 1 and r["category"] == "Dining"]
        assert len(jan_dining) == 1
        assert abs(jan_dining[0]["totalExpense"] - (-50.00)) < 0.01


class TestIDCoexistence:
    """Test that both PostgreSQL and MongoDB IDs work"""

    def test_both_id_formats_work(self, pg_session, sample_payment_methods, sample_transactions):
        """Test that both ID formats can be used to retrieve records"""
        line_item = LineItem(
            id="li_001",
            mongo_id="507f1f77bcf86cd799439011",
            transaction_id="txn_001",
            payment_method_id="pm_001",
            date=datetime(2024, 1, 15, tzinfo=UTC),
            amount=Decimal("-25.50"),
            description="Test item",
        )
        pg_session.add(line_item)
        pg_session.commit()

        # Get by PostgreSQL ID
        result_pg_id = _pg_get_line_item_by_id("li_001")

        # Get by MongoDB ID
        result_mongo_id = _pg_get_line_item_by_id("507f1f77bcf86cd799439011")

        # Both should return the same data
        assert result_pg_id is not None
        assert result_mongo_id is not None
        assert result_pg_id["id"] == result_mongo_id["id"]
        assert result_pg_id["amount"] == result_mongo_id["amount"]


class TestRawTransactionReads:
    """Test reading raw transaction data from PostgreSQL"""

    def test_pg_get_venmo_transactions(self, pg_session):
        """Test reading Venmo transactions from PostgreSQL"""
        transactions = [
            Transaction(
                id="txn_001",
                source="venmo",
                source_id="venmo_123",
                transaction_date=datetime(2024, 1, 15, tzinfo=UTC),
                source_data={
                    "payment": {
                        "id": "venmo_123",
                        "amount": -25.50,
                        "note": "Coffee",
                        "date_created": "2024-01-15T10:00:00Z",
                    }
                },
            ),
            Transaction(
                id="txn_002",
                source="venmo",
                source_id="venmo_456",
                transaction_date=datetime(2024, 2, 10, tzinfo=UTC),
                source_data={
                    "payment": {
                        "id": "venmo_456",
                        "amount": -50.00,
                        "note": "Dinner",
                        "date_created": "2024-02-10T19:00:00Z",
                    }
                },
            ),
        ]

        for txn in transactions:
            pg_session.add(txn)
        pg_session.commit()

        result = _pg_get_transactions("venmo", None)

        assert len(result) == 2
        assert result[0]["_id"] in ["venmo_123", "venmo_456"]
        assert "payment" in result[0]

    def test_pg_get_splitwise_transactions(self, pg_session):
        """Test reading Splitwise transactions from PostgreSQL"""
        transaction = Transaction(
            id="txn_003",
            source="splitwise",
            source_id="splitwise_789",
            transaction_date=datetime(2024, 3, 5, tzinfo=UTC),
            source_data={
                "id": "splitwise_789",
                "cost": "100.00",
                "description": "Rent",
                "date": "2024-03-05T00:00:00Z",
            },
        )
        pg_session.add(transaction)
        pg_session.commit()

        result = _pg_get_transactions("splitwise", None)

        assert len(result) == 1
        assert result[0]["_id"] == "splitwise_789"
        assert result[0]["cost"] == "100.00"
        assert result[0]["description"] == "Rent"

    def test_pg_get_stripe_transactions(self, pg_session):
        """Test reading Stripe transactions from PostgreSQL"""
        transaction = Transaction(
            id="txn_004",
            source="stripe",
            source_id="stripe_ch_abc",
            transaction_date=datetime(2024, 4, 1, tzinfo=UTC),
            source_data={
                "id": "stripe_ch_abc",
                "amount": 2500,
                "currency": "usd",
                "description": "Subscription",
                "created": 1711929600,
            },
        )
        pg_session.add(transaction)
        pg_session.commit()

        result = _pg_get_transactions("stripe", None)

        assert len(result) == 1
        assert result[0]["_id"] == "stripe_ch_abc"
        assert result[0]["amount"] == 2500

    def test_pg_get_cash_transactions(self, pg_session):
        """Test reading cash transactions from PostgreSQL"""
        transaction = Transaction(
            id="txn_005",
            source="cash",
            source_id="cash_001",
            transaction_date=datetime(2024, 5, 1, tzinfo=UTC),
            source_data={
                "id": "cash_001",
                "amount": -20.00,
                "description": "Tip",
                "date": "2024-05-01",
            },
        )
        pg_session.add(transaction)
        pg_session.commit()

        result = _pg_get_transactions("cash", None)

        assert len(result) == 1
        assert result[0]["_id"] == "cash_001"
        assert result[0]["amount"] == -20.00

    def test_pg_get_transactions_ordered_by_date(self, pg_session):
        """Test that transactions are returned in descending date order"""
        transactions = [
            Transaction(
                id="txn_001",
                source="venmo",
                source_id="old_txn",
                transaction_date=datetime(2024, 1, 1, tzinfo=UTC),
                source_data={"id": "old_txn", "amount": -10},
            ),
            Transaction(
                id="txn_002",
                source="venmo",
                source_id="new_txn",
                transaction_date=datetime(2024, 12, 31, tzinfo=UTC),
                source_data={"id": "new_txn", "amount": -20},
            ),
            Transaction(
                id="txn_003",
                source="venmo",
                source_id="mid_txn",
                transaction_date=datetime(2024, 6, 15, tzinfo=UTC),
                source_data={"id": "mid_txn", "amount": -15},
            ),
        ]

        for txn in transactions:
            pg_session.add(txn)
        pg_session.commit()

        result = _pg_get_transactions("venmo", None)

        assert len(result) == 3
        assert result[0]["_id"] == "new_txn"
        assert result[1]["_id"] == "mid_txn"
        assert result[2]["_id"] == "old_txn"


class TestMongoDBIndependence:
    """Test that READ_FROM_POSTGRESQL=true doesn't require MongoDB"""

    def test_all_collection_types_route_to_postgresql(
        self,
        pg_session,
        sample_categories,
        sample_payment_methods,
        monkeypatch,
    ):
        """Test that all migrated collections read from PostgreSQL when flag is enabled"""
        # Set the flag
        monkeypatch.setattr("dao.READ_FROM_POSTGRESQL", True)

        # Create test transaction (not using sample_transactions to avoid constraint conflict)
        txn = Transaction(
            id="txn_test",
            source="venmo",
            source_id="venmo_test_123",
            transaction_date=datetime(2024, 1, 15, tzinfo=UTC),
            source_data={"id": "venmo_test_123", "amount": -25.50},
        )
        pg_session.add(txn)
        pg_session.commit()

        # Create test data
        line_item = LineItem(
            id="li_001",
            transaction_id="txn_test",
            payment_method_id="pm_001",
            date=datetime(2024, 1, 15, tzinfo=UTC),
            amount=Decimal("-25.50"),
            description="Test item",
        )
        pg_session.add(line_item)

        event = Event(
            id="evt_001",
            category_id="cat_001",
            date=datetime(2024, 1, 15, tzinfo=UTC),
            description="Test event",
        )
        pg_session.add(event)
        pg_session.commit()

        # Test line items collection
        result = get_all_data(line_items_collection, None)
        assert len(result) == 1
        assert result[0]["id"] == "li_001"

        # Test events collection
        result = get_all_data(events_collection, None)
        assert len(result) == 1
        assert result[0]["id"] == "evt_001"

        # Test raw data collections
        from dao import venmo_raw_data_collection

        result = get_all_data(venmo_raw_data_collection, None)
        assert len(result) == 1
        assert result[0]["_id"] == "venmo_test_123"

    def test_unknown_collections_raise_error(self, monkeypatch):
        """Test that unknown collections raise NotImplementedError"""
        monkeypatch.setattr("dao.READ_FROM_POSTGRESQL", True)

        with pytest.raises(NotImplementedError, match="Unknown collection.*cannot read from PostgreSQL"):
            get_all_data("unknown_collection", None)


class TestBankAccountReads:
    """Test PostgreSQL read operations for bank accounts"""

    def test_pg_get_all_bank_accounts(self, pg_session):
        """Test getting all bank accounts from PostgreSQL"""
        accounts = [
            BankAccount(
                id="fca_001",
                institution_name="Chase",
                display_name="Checking",
                last4="1234",
                status="active",
            ),
            BankAccount(
                id="fca_002",
                institution_name="BofA",
                display_name="Savings",
                last4="5678",
                status="active",
            ),
            BankAccount(
                id="fca_003",
                institution_name="Wells Fargo",
                display_name="Credit",
                last4="9012",
                status="inactive",
            ),
        ]

        for acc in accounts:
            pg_session.add(acc)
        pg_session.commit()

        # Get all accounts
        result = _pg_get_all_bank_accounts(None)
        assert len(result) == 3
        assert result[0]["id"] == "fca_001"
        assert result[0]["institution_name"] == "Chase"
        assert result[0]["display_name"] == "Checking"
        assert result[0]["last4"] == "1234"
        assert result[0]["status"] == "active"

    def test_pg_get_bank_accounts_with_status_filter(self, pg_session):
        """Test getting bank accounts with status filter"""
        accounts = [
            BankAccount(
                id="fca_001",
                institution_name="Chase",
                display_name="Checking",
                last4="1234",
                status="active",
            ),
            BankAccount(
                id="fca_002",
                institution_name="BofA",
                display_name="Savings",
                last4="5678",
                status="inactive",
            ),
        ]

        for acc in accounts:
            pg_session.add(acc)
        pg_session.commit()

        # Filter by status
        result = _pg_get_all_bank_accounts({"status": "active"})
        assert len(result) == 1
        assert result[0]["id"] == "fca_001"

    def test_get_all_data_routes_to_postgres(self, pg_session, monkeypatch):
        """Test that get_all_data routes bank_accounts to PostgreSQL"""
        monkeypatch.setattr("dao.READ_FROM_POSTGRESQL", True)

        account = BankAccount(
            id="fca_001",
            institution_name="Chase",
            display_name="Checking",
            last4="1234",
            status="active",
        )
        pg_session.add(account)
        pg_session.commit()

        result = get_all_data(bank_accounts_collection, None)
        assert len(result) == 1
        assert result[0]["id"] == "fca_001"


class TestUserReads:
    """Test PostgreSQL read operations for users"""

    def test_pg_get_user_by_email(self, pg_session):
        """Test getting user by email from PostgreSQL"""
        user = User(
            id="user_001",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            password_hash="hashed_password",
        )
        pg_session.add(user)
        pg_session.commit()

        result = _pg_get_user_by_email("john@example.com")
        assert result is not None
        assert result["id"] == "user_001"
        assert result["first_name"] == "John"
        assert result["last_name"] == "Doe"
        assert result["email"] == "john@example.com"
        assert result["password_hash"] == "hashed_password"

    def test_pg_get_user_by_email_not_found(self, pg_session):
        """Test getting non-existent user returns None"""
        result = _pg_get_user_by_email("nonexistent@example.com")
        assert result is None

    def test_get_user_by_email_routes_to_postgres(self, pg_session, monkeypatch):
        """Test that get_user_by_email routes to PostgreSQL"""
        monkeypatch.setattr("dao.READ_FROM_POSTGRESQL", True)

        user = User(
            id="user_001",
            first_name="Jane",
            last_name="Smith",
            email="jane@example.com",
            password_hash="hashed_password",
        )
        pg_session.add(user)
        pg_session.commit()

        result = get_user_by_email("jane@example.com")
        assert result is not None
        assert result["id"] == "user_001"
        assert result["email"] == "jane@example.com"

    def test_pg_get_user_by_id_postgresql_id(self, pg_session):
        """Test getting user by PostgreSQL ID"""
        user = User(
            id="user_001",
            mongo_id="507f1f77bcf86cd799439031",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            password_hash="hashed_password",
        )
        pg_session.add(user)
        pg_session.commit()

        result = _pg_get_user_by_id("user_001")

        assert result is not None
        # id field returns mongo_id for MongoDB compatibility
        assert result["id"] == "507f1f77bcf86cd799439031"
        assert result["_id"] == "507f1f77bcf86cd799439031"
        assert result["first_name"] == "John"
        assert result["last_name"] == "Doe"
        assert result["email"] == "john@example.com"

    def test_pg_get_user_by_id_mongodb_id(self, pg_session):
        """Test getting user by MongoDB ID (ID coexistence)"""
        user = User(
            id="user_001",
            mongo_id="507f1f77bcf86cd799439031",
            first_name="Jane",
            last_name="Smith",
            email="jane@example.com",
            password_hash="hashed_password",
        )
        pg_session.add(user)
        pg_session.commit()

        result = _pg_get_user_by_id("507f1f77bcf86cd799439031")

        assert result is not None
        # Should return MongoDB ID (application transparency)
        assert result["id"] == "507f1f77bcf86cd799439031"
        assert result["_id"] == "507f1f77bcf86cd799439031"
        assert result["first_name"] == "Jane"
        assert result["last_name"] == "Smith"
        assert result["email"] == "jane@example.com"

    def test_pg_get_user_by_id_not_found(self, pg_session):
        """Test getting non-existent user by ID returns None"""
        result = _pg_get_user_by_id("nonexistent_user_id")
        assert result is None

        result_mongo_id = _pg_get_user_by_id("507f1f77bcf86cd799439999")
        assert result_mongo_id is None
