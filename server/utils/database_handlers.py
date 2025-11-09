"""Handler registry pattern for MongoDB → PostgreSQL migration - routes reads based on READ_FROM_POSTGRESQL flag"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from bson import ObjectId


class DatabaseHandler(ABC):
    @abstractmethod
    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_by_id(self, id: Union[str, int, ObjectId]) -> Optional[Dict[str, Any]]:
        pass


class LineItemHandler(DatabaseHandler):

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        import dao

        if dao.READ_FROM_POSTGRESQL:
            return dao._pg_get_all_line_items(filters)

        cur_collection = dao.get_collection(dao.line_items_collection)
        return list(cur_collection.find(filters).sort("date", -1))

    def get_by_id(self, id: Union[str, int, ObjectId]) -> Optional[Dict[str, Any]]:
        import dao

        if dao.READ_FROM_POSTGRESQL:
            return dao._pg_get_line_item_by_id(str(id))

        cur_collection = dao.get_collection(dao.line_items_collection)
        return cur_collection.find_one({"_id": id})


class EventHandler(DatabaseHandler):

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        import dao

        if dao.READ_FROM_POSTGRESQL:
            return dao._pg_get_all_events(filters)

        cur_collection = dao.get_collection(dao.events_collection)
        return list(cur_collection.find(filters).sort("date", -1))

    def get_by_id(self, id: Union[str, int, ObjectId]) -> Optional[Dict[str, Any]]:
        import dao

        if dao.READ_FROM_POSTGRESQL:
            return dao._pg_get_event_by_id(str(id))

        cur_collection = dao.get_collection(dao.events_collection)
        return cur_collection.find_one({"_id": id})


class TransactionHandler(DatabaseHandler):

    def __init__(self, source: str):
        self.source = source

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        import dao

        if dao.READ_FROM_POSTGRESQL:
            return dao._pg_get_transactions(self.source, filters)

        # Get collection name from source
        collection_map = {
            "venmo": "venmo_raw_data",
            "splitwise": "splitwise_raw_data",
            "stripe": "stripe_raw_transaction_data",
            "cash": "cash_raw_data",
        }
        collection_name = collection_map.get(self.source)
        if not collection_name:
            return []

        cur_collection = dao.get_collection(collection_name)
        return list(cur_collection.find(filters).sort("date", -1))

    def get_by_id(self, id: Union[str, int, ObjectId]) -> Optional[Dict[str, Any]]:
        import dao

        collection_map = {
            "venmo": "venmo_raw_data",
            "splitwise": "splitwise_raw_data",
            "stripe": "stripe_raw_transaction_data",
            "cash": "cash_raw_data",
        }
        collection_name = collection_map.get(self.source)
        if not collection_name:
            return None

        cur_collection = dao.get_collection(collection_name)
        return cur_collection.find_one({"_id": id})


class BankAccountHandler(DatabaseHandler):

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        import dao

        if dao.READ_FROM_POSTGRESQL:
            return dao._pg_get_all_bank_accounts(filters)

        cur_collection = dao.get_collection(dao.bank_accounts_collection)
        return list(cur_collection.find(filters).sort("date", -1))

    def get_by_id(self, id: Union[str, int, ObjectId]) -> Optional[Dict[str, Any]]:
        import dao

        cur_collection = dao.get_collection(dao.bank_accounts_collection)
        return cur_collection.find_one({"_id": id})


class MongoDBHandler(DatabaseHandler):

    def __init__(self, collection_name: str):
        self.collection_name = collection_name

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        import dao

        # If trying to read from PostgreSQL but collection is not migrated, raise error
        if dao.READ_FROM_POSTGRESQL:
            raise NotImplementedError(
                f"Unknown collection '{self.collection_name}' - cannot read from PostgreSQL"
            )

        cur_collection = dao.get_collection(self.collection_name)
        return list(cur_collection.find(filters).sort("date", -1))

    def get_by_id(self, id: Union[str, int, ObjectId]) -> Optional[Dict[str, Any]]:
        import dao

        # If trying to read from PostgreSQL but collection is not migrated, raise error
        if dao.READ_FROM_POSTGRESQL:
            raise NotImplementedError(
                f"Unknown collection '{self.collection_name}' - cannot read from PostgreSQL"
            )

        cur_collection = dao.get_collection(self.collection_name)
        return cur_collection.find_one({"_id": id})


def get_collection_handler(collection_name: str) -> DatabaseHandler:
    """Registry pattern eliminates if/elif chains - add new collections to _COLLECTION_HANDLERS dict"""
    from dao import (
        bank_accounts_collection,
        cash_raw_data_collection,
        events_collection,
        line_items_collection,
        splitwise_raw_data_collection,
        stripe_raw_transaction_data_collection,
        users_collection,
        venmo_raw_data_collection,
    )

    # Test data always uses MongoDB (not migrated to PostgreSQL)
    class TestDataHandler(DatabaseHandler):

        def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
            import dao

            cur_collection = dao.get_collection("test_data")
            return list(cur_collection.find(filters).sort("date", -1))

        def get_by_id(self, id: Union[str, int, ObjectId]) -> Optional[Dict[str, Any]]:
            import dao

            cur_collection = dao.get_collection("test_data")
            return cur_collection.find_one({"_id": id})

    # Static handlers for common collections
    _COLLECTION_HANDLERS = {
        line_items_collection: LineItemHandler(),
        events_collection: EventHandler(),
        venmo_raw_data_collection: TransactionHandler("venmo"),
        splitwise_raw_data_collection: TransactionHandler("splitwise"),
        stripe_raw_transaction_data_collection: TransactionHandler("stripe"),
        cash_raw_data_collection: TransactionHandler("cash"),
        bank_accounts_collection: BankAccountHandler(),
        "test_data": TestDataHandler(),  # Test collection always uses MongoDB
    }

    # Special handling for users collection
    if collection_name == users_collection:
        raise NotImplementedError("Use get_user_by_email() instead of get_all_data() for users")

    # Return registered handler or fallback to MongoDB-only handler
    return _COLLECTION_HANDLERS.get(collection_name, MongoDBHandler(collection_name))
