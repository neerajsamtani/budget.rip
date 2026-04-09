from datetime import UTC, datetime

from dao import (
    create_notification,
    delete_transaction_by_source,
    get_unread_notifications,
    mark_notifications_read,
)
from models.database import SessionLocal
from models.sql_models import (
    Event,
    EventLineItem,
    LineItem,
    Notification,
    Transaction,
)


class TestDeleteTransactionBySource:
    def test_deletes_transaction_not_in_event(self, flask_app):
        """Transaction not assigned to any event is deleted without notification"""
        with flask_app.app_context():
            with SessionLocal.begin() as db:
                db.add(
                    Transaction(
                        id="txn_sw1",
                        source="splitwise_api",
                        source_id="123",
                        source_data={"description": "Dinner"},
                        transaction_date=datetime(2024, 1, 15, tzinfo=UTC),
                    )
                )
                db.add(
                    LineItem(
                        id="li_sw1",
                        transaction_id="txn_sw1",
                        date=datetime(2024, 1, 15, tzinfo=UTC),
                        amount=50.0,
                        description="Dinner",
                        payment_method_id="pm_splitwise",
                    )
                )

            result = delete_transaction_by_source("splitwise_api", "123", "user_id")

            assert result["deleted"] is True
            assert result["notified"] is False

            with SessionLocal.begin() as db:
                assert db.query(Transaction).filter(Transaction.id == "txn_sw1").first() is None
                assert db.query(LineItem).filter(LineItem.id == "li_sw1").first() is None

    def test_deletes_transaction_in_event_and_creates_notification(self, flask_app):
        """Transaction assigned to an event is deleted and a notification is created"""
        with flask_app.app_context():
            with SessionLocal.begin() as db:
                db.add(
                    Transaction(
                        id="txn_sw2",
                        source="splitwise_api",
                        source_id="456",
                        source_data={"description": "Groceries"},
                        transaction_date=datetime(2024, 1, 15, tzinfo=UTC),
                    )
                )
                db.add(
                    LineItem(
                        id="li_sw2",
                        transaction_id="txn_sw2",
                        date=datetime(2024, 1, 15, tzinfo=UTC),
                        amount=30.0,
                        description="Groceries",
                        payment_method_id="pm_splitwise",
                    )
                )
                db.add(
                    Event(
                        id="evt_test",
                        date=datetime(2024, 1, 15, tzinfo=UTC),
                        description="Weekly groceries",
                        category_id="cat_groceries",
                    )
                )
                db.flush()
                db.add(
                    EventLineItem(
                        id="eli_test",
                        event_id="evt_test",
                        line_item_id="li_sw2",
                    )
                )

            result = delete_transaction_by_source("splitwise_api", "456", "user_id")

            assert result["deleted"] is True
            assert result["notified"] is True

            # Transaction and line item should be gone
            with SessionLocal.begin() as db:
                assert db.query(Transaction).filter(Transaction.id == "txn_sw2").first() is None
                assert db.query(LineItem).filter(LineItem.id == "li_sw2").first() is None
                assert db.query(EventLineItem).filter(EventLineItem.id == "eli_test").first() is None

                # Notification should exist
                notification = db.query(Notification).first()
                assert notification is not None
                assert "Groceries" in notification.message
                assert "Weekly groceries" in notification.message
                assert notification.type == "warning"
                assert notification.user_id == "user_id"
                assert notification.event_id == "evt_test"

    def test_nonexistent_transaction_is_noop(self, flask_app):
        """Attempting to delete a nonexistent transaction returns deleted=False"""
        with flask_app.app_context():
            result = delete_transaction_by_source("splitwise_api", "nonexistent", "user_id")
            assert result["deleted"] is False
            assert result["notified"] is False


class TestNotificationCRUD:
    def test_create_and_get_unread_notifications(self, flask_app):
        """Notifications can be created and retrieved"""
        with flask_app.app_context():
            create_notification("user_id", "Test message", "warning")
            create_notification("user_id", "Info message", "info")

            notifications = get_unread_notifications("user_id")
            assert len(notifications) == 2
            messages = [n["message"] for n in notifications]
            assert "Test message" in messages
            assert "Info message" in messages
            # event_id should be None for generic notifications
            assert all(n["event_id"] is None for n in notifications)

    def test_mark_notifications_read(self, flask_app):
        """Marking notifications as read removes them from unread list"""
        with flask_app.app_context():
            create_notification("user_id", "To be read", "warning")

            unread = get_unread_notifications("user_id")
            assert len(unread) == 1

            mark_notifications_read([unread[0]["id"]])

            unread_after = get_unread_notifications("user_id")
            assert len(unread_after) == 0

    def test_create_notification_with_event_id(self, flask_app):
        """Notification can be created with an event_id link"""
        with flask_app.app_context():
            with SessionLocal.begin() as db:
                db.add(
                    Event(
                        id="evt_linked",
                        date=datetime(2024, 1, 15, tzinfo=UTC),
                        description="Trip dinner",
                        category_id="cat_groceries",
                    )
                )

            create_notification("user_id", "Linked notification", "warning", event_id="evt_linked")

            notifications = get_unread_notifications("user_id")
            assert len(notifications) == 1
            assert notifications[0]["event_id"] == "evt_linked"

    def test_unread_notifications_are_user_scoped(self, flask_app):
        """Notifications for different users are isolated"""
        with flask_app.app_context():
            # Create a second user
            from models.sql_models import User

            with SessionLocal.begin() as db:
                db.add(
                    User(
                        id="user_other",
                        first_name="Other",
                        last_name="User",
                        email="other@example.com",
                        password_hash="hash",
                    )
                )

            create_notification("user_id", "User 1 notification", "warning")
            create_notification("user_other", "User 2 notification", "warning")

            user1_notifs = get_unread_notifications("user_id")
            user2_notifs = get_unread_notifications("user_other")

            assert len(user1_notifs) == 1
            assert user1_notifs[0]["message"] == "User 1 notification"
            assert len(user2_notifs) == 1
            assert user2_notifs[0]["message"] == "User 2 notification"


class TestNotificationEndpoints:
    def test_get_notifications(self, flask_app, test_client, jwt_token):
        """GET /api/notifications returns unread notifications"""
        with flask_app.app_context():
            create_notification("user_id", "Endpoint test", "warning")

        response = test_client.get(
            "/api/notifications",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert response.status_code == 200
        data = response.get_json()["data"]
        assert len(data) == 1
        assert data[0]["message"] == "Endpoint test"

    def test_mark_read_endpoint(self, flask_app, test_client, jwt_token):
        """POST /api/notifications/mark-read marks notifications as read"""
        with flask_app.app_context():
            create_notification("user_id", "To dismiss", "warning")
            notifs = get_unread_notifications("user_id")
            notif_id = notifs[0]["id"]

        response = test_client.post(
            "/api/notifications/mark-read",
            json={"notification_ids": [notif_id]},
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert response.status_code == 200

        # Verify it's gone from unread
        with flask_app.app_context():
            assert len(get_unread_notifications("user_id")) == 0

    def test_mark_read_requires_notification_ids(self, test_client, jwt_token):
        """POST /api/notifications/mark-read requires notification_ids"""
        response = test_client.post(
            "/api/notifications/mark-read",
            json={},
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert response.status_code == 400

    def test_get_notifications_requires_auth(self, test_client):
        """GET /api/notifications requires authentication"""
        response = test_client.get("/api/notifications")
        assert response.status_code == 401


class TestSplitwiseDeletedExpenseHandling:
    def test_deleted_expense_cleans_up_local_transaction(self, flask_app, mocker):
        """When Splitwise returns a deleted expense that exists locally, it gets cleaned up"""
        with flask_app.app_context():
            # First, create a local transaction as if it was previously synced
            with SessionLocal.begin() as db:
                db.add(
                    Transaction(
                        id="txn_sw_del",
                        source="splitwise_api",
                        source_id="999",
                        source_data={"description": "Old dinner"},
                        transaction_date=datetime(2024, 1, 15, tzinfo=UTC),
                    )
                )
                db.add(
                    LineItem(
                        id="li_sw_del",
                        transaction_id="txn_sw_del",
                        date=datetime(2024, 1, 15, tzinfo=UTC),
                        amount=25.0,
                        description="Old dinner",
                        payment_method_id="pm_splitwise",
                    )
                )

            # Mock Splitwise returning this expense as deleted
            mock_deleted_expense = mocker.Mock()
            mock_deleted_expense.deleted_at = "2024-02-01T00:00:00Z"
            mock_deleted_expense.id = 999

            mock_active_expense = mocker.Mock()
            mock_active_expense.deleted_at = None
            mock_active_expense.id = 888

            mock_splitwise_client = mocker.patch("resources.splitwise.splitwise_client")
            mock_splitwise_client.getExpenses.return_value = [mock_active_expense, mock_deleted_expense]
            mocker.patch("resources.splitwise.bulk_upsert_transactions")
            # Mock get_jwt_identity to return user_id
            mocker.patch("resources.splitwise.get_jwt_identity", return_value="user_id")

            from resources.splitwise import refresh_splitwise

            refresh_splitwise()

            # Local transaction should be deleted
            with SessionLocal.begin() as db:
                assert db.query(Transaction).filter(Transaction.id == "txn_sw_del").first() is None
                assert db.query(LineItem).filter(LineItem.id == "li_sw_del").first() is None

    def test_deleted_expense_in_event_creates_notification(self, flask_app, mocker):
        """When a deleted expense's line item was in an event, a notification is created"""
        with flask_app.app_context():
            with SessionLocal.begin() as db:
                db.add(
                    Transaction(
                        id="txn_sw_evt",
                        source="splitwise_api",
                        source_id="777",
                        source_data={"description": "Trip dinner"},
                        transaction_date=datetime(2024, 1, 15, tzinfo=UTC),
                    )
                )
                db.add(
                    LineItem(
                        id="li_sw_evt",
                        transaction_id="txn_sw_evt",
                        date=datetime(2024, 1, 15, tzinfo=UTC),
                        amount=80.0,
                        description="Trip dinner",
                        payment_method_id="pm_splitwise",
                    )
                )
                db.add(
                    Event(
                        id="evt_trip",
                        date=datetime(2024, 1, 15, tzinfo=UTC),
                        description="Mexico trip",
                        category_id="cat_travel",
                    )
                )
                db.flush()
                db.add(
                    EventLineItem(
                        id="eli_trip",
                        event_id="evt_trip",
                        line_item_id="li_sw_evt",
                    )
                )

            mock_deleted_expense = mocker.Mock()
            mock_deleted_expense.deleted_at = "2024-02-01T00:00:00Z"
            mock_deleted_expense.id = 777

            mock_splitwise_client = mocker.patch("resources.splitwise.splitwise_client")
            mock_splitwise_client.getExpenses.return_value = [mock_deleted_expense]
            mocker.patch("resources.splitwise.bulk_upsert_transactions")
            mocker.patch("resources.splitwise.get_jwt_identity", return_value="user_id")

            from resources.splitwise import refresh_splitwise

            refresh_splitwise()

            # Transaction should be deleted
            with SessionLocal.begin() as db:
                assert db.query(Transaction).filter(Transaction.id == "txn_sw_evt").first() is None

                # Notification should exist
                notification = db.query(Notification).first()
                assert notification is not None
                assert "Trip dinner" in notification.message
                assert "Mexico trip" in notification.message
                assert notification.event_id == "evt_trip"
