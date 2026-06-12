"""Unit tests for bulk_upsert_line_items deduplication logic."""

from datetime import UTC, datetime

from models.sql_models import Category, Event, EventLineItem, Transaction
from models.sql_models import LineItem as LineItemModel
from resources.line_item import LineItem
from utils.id_generator import generate_id
from utils.pg_bulk_ops import bulk_upsert_line_items


def _make_transaction(source_id, source="venmo_api"):
    return Transaction(
        id=generate_id("txn"),
        source=source,
        source_id=source_id,
        source_data={},
        transaction_date=datetime.now(UTC),
    )


class TestBulkUpsertLineItems:
    def _make_li(self, source_id, description="Test", amount=10.0):
        return LineItem(
            date=1700000000.0,
            responsible_party="Test Party",
            payment_method="Unknown",
            description=description,
            amount=amount,
            source_id=source_id,
        )

    def test_new_line_item_is_inserted(self, pg_session, flask_app):
        txn = _make_transaction("test_src_1")
        pg_session.add(txn)
        pg_session.flush()

        count = bulk_upsert_line_items(pg_session, [self._make_li("test_src_1")], source="venmo_api")
        pg_session.flush()

        assert count == 1
        result = (
            pg_session.query(LineItemModel)
            .join(Transaction, Transaction.id == LineItemModel.transaction_id)
            .filter(Transaction.source_id == "test_src_1")
            .first()
        )
        assert result is not None
        assert result.description == "Test"

    def test_duplicate_source_id_is_not_reinserted(self, pg_session, flask_app):
        txn = _make_transaction("test_src_2")
        pg_session.add(txn)
        pg_session.flush()

        li = self._make_li("test_src_2")
        bulk_upsert_line_items(pg_session, [li], source="venmo_api")
        pg_session.flush()

        count = bulk_upsert_line_items(pg_session, [li], source="venmo_api")
        pg_session.flush()

        assert count == 0
        rows = (
            pg_session.query(LineItemModel)
            .join(Transaction, Transaction.id == LineItemModel.transaction_id)
            .filter(Transaction.source_id == "test_src_2")
            .all()
        )
        assert len(rows) == 1

    def test_changed_line_item_is_updated(self, pg_session, flask_app):
        txn = _make_transaction("test_src_3")
        pg_session.add(txn)
        pg_session.flush()

        bulk_upsert_line_items(pg_session, [self._make_li("test_src_3", description="Old Description")], source="venmo_api")
        pg_session.flush()

        count = bulk_upsert_line_items(
            pg_session, [self._make_li("test_src_3", description="New Description")], source="venmo_api"
        )
        pg_session.flush()

        assert count == 1
        result = (
            pg_session.query(LineItemModel)
            .join(Transaction, Transaction.id == LineItemModel.transaction_id)
            .filter(Transaction.source_id == "test_src_3")
            .first()
        )
        assert result.description == "New Description"

    def test_evented_line_item_is_never_updated(self, pg_session, flask_app):
        txn = _make_transaction("test_src_4")
        pg_session.add(txn)
        pg_session.flush()

        bulk_upsert_line_items(
            pg_session, [self._make_li("test_src_4", description="Original Description")], source="venmo_api"
        )
        pg_session.flush()

        existing_li = (
            pg_session.query(LineItemModel)
            .join(Transaction, Transaction.id == LineItemModel.transaction_id)
            .filter(Transaction.source_id == "test_src_4")
            .first()
        )

        category = pg_session.query(Category).first()
        event = Event(
            id=generate_id("evt"),
            date=datetime.now(UTC),
            description="Test Event",
            category_id=category.id,
        )
        pg_session.add(event)
        pg_session.flush()

        eli = EventLineItem(id=generate_id("eli"), event_id=event.id, line_item_id=existing_li.id)
        pg_session.add(eli)
        pg_session.flush()

        bulk_upsert_line_items(
            pg_session, [self._make_li("test_src_4", description="Updated Description")], source="venmo_api"
        )
        pg_session.flush()

        pg_session.expire(existing_li)
        assert existing_li.description == "Original Description"

    def test_missing_transaction_is_skipped(self, pg_session, flask_app):
        count = bulk_upsert_line_items(pg_session, [self._make_li("test_src_5")], source="venmo_api")
        pg_session.flush()

        assert count == 0
        rows = (
            pg_session.query(LineItemModel)
            .join(Transaction, Transaction.id == LineItemModel.transaction_id)
            .filter(Transaction.source_id == "test_src_5")
            .all()
        )
        assert len(rows) == 0
