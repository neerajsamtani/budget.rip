import logging
from typing import Any, Dict, List, Optional, Union

from bson import ObjectId
from flask import current_app
from pymongo import UpdateOne
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import BulkWriteError
from sqlalchemy.orm import joinedload, subqueryload

from constants import READ_FROM_POSTGRESQL
from helpers import to_dict, to_dict_robust
from utils.dual_write import dual_write_operation

venmo_raw_data_collection: str = "venmo_raw_data"
splitwise_raw_data_collection: str = "splitwise_raw_data"
cash_raw_data_collection: str = "cash_raw_data"
stripe_raw_transaction_data_collection: str = "stripe_raw_transaction_data"
stripe_raw_account_data_collection: str = "stripe_raw_account_data"
line_items_collection: str = "line_items"
events_collection: str = "events"
bank_accounts_collection: str = "accounts"
users_collection: str = "users"
test_collection: str = "test_data"


def get_collection(cur_collection_str: str) -> Collection:
    # Access the MongoDB collection using current_app
    mongo: Any = current_app.config["MONGO"]
    # Use the configured database name, fallback to "flask_db" for backward compatibility
    db_name: str = current_app.config.get("MONGO_DB_NAME", "flask_db")
    client: Database = mongo.cx[db_name]
    return client[cur_collection_str]


def get_all_data(cur_collection_str: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    if READ_FROM_POSTGRESQL:
        if cur_collection_str == line_items_collection:
            return _pg_get_all_line_items(filters)
        elif cur_collection_str == events_collection:
            return _pg_get_all_events(filters)
        elif cur_collection_str in [
            venmo_raw_data_collection,
            splitwise_raw_data_collection,
            stripe_raw_transaction_data_collection,
            cash_raw_data_collection,
        ]:
            source_map = {
                venmo_raw_data_collection: "venmo",
                splitwise_raw_data_collection: "splitwise",
                stripe_raw_transaction_data_collection: "stripe",
                cash_raw_data_collection: "cash",
            }
            return _pg_get_transactions(source_map[cur_collection_str], filters)
        elif cur_collection_str == bank_accounts_collection:
            return _pg_get_all_bank_accounts(filters)
        elif cur_collection_str == users_collection:
            raise NotImplementedError("Use get_user_by_email() instead of get_all_data() for users")
        elif cur_collection_str == test_collection:
            # Fall back to MongoDB for test collections
            pass
        else:
            raise NotImplementedError(f"Unknown collection '{cur_collection_str}' - cannot read from PostgreSQL")

    cur_collection: Collection = get_collection(cur_collection_str)
    return list(cur_collection.find(filters).sort("date", -1))


def get_item_by_id(cur_collection_str: str, id: Union[str, int, ObjectId]) -> Optional[Dict[str, Any]]:
    if READ_FROM_POSTGRESQL:
        if cur_collection_str == line_items_collection:
            return _pg_get_line_item_by_id(str(id))
        elif cur_collection_str == events_collection:
            return _pg_get_event_by_id(str(id))
        else:
            # Fall back to MongoDB for unmigrated collections
            logging.debug(f"Collection '{cur_collection_str}' not migrated to PostgreSQL, reading from MongoDB")

    cur_collection: Collection = get_collection(cur_collection_str)
    return cur_collection.find_one({"_id": id})


def insert(cur_collection_str: str, item: Any) -> None:
    cur_collection: Collection = get_collection(cur_collection_str)
    item_dict: Dict[str, Any] = to_dict(item)
    if "id" in item_dict:
        item_dict["_id"] = item_dict["id"]
    cur_collection.insert_one(item_dict)


def delete_from_collection(cur_collection_str: str, id: Union[str, int]) -> None:
    cur_collection: Collection = get_collection(cur_collection_str)
    cur_collection.delete_one({"_id": id})


def remove_event_from_line_item(line_item_id: Union[str, int, ObjectId]) -> None:
    """
    Remove event_id from a line item by its ID.

    Args:
        line_item_id: The ID of the line item (can be string, int, or ObjectId)
    """

    def mongo_write():
        collection = get_collection(line_items_collection)
        # Try to unset event_id using the provided ID as-is
        result = collection.update_one({"_id": line_item_id}, {"$unset": {"event_id": ""}})
        if result.matched_count == 0:
            logging.warning(f"Could not find line item with ID {line_item_id} to remove event_id")

    def pg_write(db_session):
        from models.sql_models import EventLineItem, LineItem

        # Find the line item by mongo_id (the original MongoDB ID)
        line_item = db_session.query(LineItem).filter(LineItem.mongo_id == str(line_item_id)).first()
        if line_item:
            # Delete all EventLineItem junctions for this line item
            db_session.query(EventLineItem).filter(EventLineItem.line_item_id == line_item.id).delete()
        else:
            logging.info(f"Line item {line_item_id} not in PostgreSQL yet")

    # dual_write_operation handles transaction management (commit/rollback)
    dual_write_operation(
        mongo_write,
        pg_write,
        line_items_collection,
    )


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    if READ_FROM_POSTGRESQL:
        return _pg_get_user_by_email(email)
    cur_collection: Collection = get_collection(users_collection)
    return cur_collection.find_one({"email": {"$eq": email}})


def upsert(cur_collection_str: str, item: Any) -> None:
    item_dict: Dict[str, Any] = to_dict(item)
    upsert_with_id(cur_collection_str, item_dict, item_dict["id"])


def upsert_with_id(cur_collection_str: str, item: Dict[str, Any], id: Union[str, int, ObjectId]) -> None:
    """Upsert item to MongoDB and also to PostgreSQL for transaction collections (dual-write for tests)"""
    # MongoDB write
    cur_collection: Collection = get_collection(cur_collection_str)
    item["_id"] = item["id"]
    cur_collection.replace_one({"_id": id}, item, upsert=True)

    # PostgreSQL write (for transaction collections used in tests)
    if cur_collection_str in [
        venmo_raw_data_collection,
        splitwise_raw_data_collection,
        stripe_raw_transaction_data_collection,
        cash_raw_data_collection,
    ]:
        from models.database import SessionLocal
        from utils.pg_bulk_ops import bulk_upsert_transactions

        source_map = {
            venmo_raw_data_collection: "venmo",
            splitwise_raw_data_collection: "splitwise",
            stripe_raw_transaction_data_collection: "stripe",
            cash_raw_data_collection: "cash",
        }
        source = source_map[cur_collection_str]

        db_session = SessionLocal()
        try:
            bulk_upsert_transactions(db_session, [item], source=source)
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            # Re-raise the exception - don't swallow it!
            raise Exception(f"Failed to dual-write transaction {item.get('id')} to PostgreSQL: {e}") from e
        finally:
            db_session.close()

    elif cur_collection_str == events_collection:
        from models.database import SessionLocal
        from utils.pg_event_operations import upsert_event_to_postgresql

        db_session = SessionLocal()
        try:
            upsert_event_to_postgresql(item, db_session)
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            # Re-raise the exception - don't swallow it!
            raise Exception(f"Failed to dual-write event {item.get('id')} to PostgreSQL: {e}") from e
        finally:
            db_session.close()

    elif cur_collection_str == bank_accounts_collection:
        from models.database import SessionLocal
        from utils.pg_bulk_ops import bulk_upsert_bank_accounts

        db_session = SessionLocal()
        try:
            bulk_upsert_bank_accounts(db_session, [item])
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            # Re-raise the exception - don't swallow it!
            raise Exception(f"Failed to dual-write bank account {item.get('id')} to PostgreSQL: {e}") from e
        finally:
            db_session.close()


def bulk_upsert(cur_collection_str: str, items: List[Any]) -> None:
    """
    Bulk upsert multiple items for better performance.

    This function handles both insert (new items) and update (existing items) operations
    using MongoDB's UpdateOne with upsert=True, which is equivalent to the single upsert operation.

    Args:
        cur_collection_str: Collection name
        items: List of items to upsert
    """
    if not items:
        return

    cur_collection: Collection = get_collection(cur_collection_str)

    # Prepare bulk operations using PyMongo's UpdateOne class
    bulk_operations: List[UpdateOne] = []
    for item in items:
        try:
            # Convert item to dictionary using robust serialization
            item_dict: Dict[str, Any] = to_dict_robust(item)

            # Ensure _id field is set correctly
            if "id" in item_dict:
                item_dict["_id"] = item_dict["id"]
            elif hasattr(item, "id"):
                item_dict["_id"] = item.id
            elif hasattr(item, "_id"):
                item_dict["_id"] = item._id

            # Use PyMongo's UpdateOne class for proper bulk operations
            bulk_operations.append(UpdateOne({"_id": item_dict["_id"]}, {"$set": item_dict}, upsert=True))
        except Exception as e:
            logging.error(f"Error preparing item for bulk upsert: {e}")
            logging.error(f"Item type: {type(item)}")
            logging.error(f"Item: {item}")
            continue

    # Execute bulk operations
    if bulk_operations:
        try:
            result: Any = cur_collection.bulk_write(bulk_operations, ordered=False)
            logging.info(f"Bulk upsert completed: {result.upserted_count} inserted, {result.modified_count} updated")
        except Exception as e:
            logging.error(f"Error in bulk upsert: {e}")
            if isinstance(e, BulkWriteError):
                logging.error(f"BulkWriteError: {e.details}")
            # Fallback to individual upserts for better error isolation
            for item in items:
                try:
                    upsert(cur_collection_str, item)
                except Exception as individual_error:
                    logging.error(f"Error upserting individual item: {individual_error}")


def get_categorized_data() -> List[Dict[str, Any]]:
    """Group totalExpense by month, year, and category"""
    if READ_FROM_POSTGRESQL:
        return _pg_get_categorized_data()

    cur_collection: Collection = get_collection(events_collection)
    query_result: Any = cur_collection.aggregate(
        [
            {"$addFields": {"date": {"$toDate": {"$multiply": ["$date", 1000]}}}},
            {
                "$group": {
                    "_id": {
                        "year": {"$year": "$date"},
                        "month": {"$month": "$date"},
                        "category": "$category",
                    },
                    "totalExpense": {"$sum": "$amount"},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "year": "$_id.year",
                    "month": "$_id.month",
                    "category": "$_id.category",
                    "totalExpense": 1,
                }
            },
            {"$sort": {"year": 1, "month": 1, "category": 1}},
        ]
    )

    response: List[Dict[str, Any]] = []
    for document in query_result:
        response.append(dict(document))
    return response


# ============================================================================
# PostgreSQL Read Operations (Phase 5)
# ============================================================================


def _pg_serialize_line_item(li: Any) -> Dict[str, Any]:
    """Convert LineItem ORM to dict matching MongoDB format"""
    from datetime import timezone as tz

    mongo_id = li.mongo_id or li.id
    # Handle naive datetimes from SQLite by treating them as UTC
    if li.date and li.date.tzinfo is None:
        date_timestamp = li.date.replace(tzinfo=tz.utc).timestamp()
    else:
        date_timestamp = li.date.timestamp() if li.date else 0.0

    data = {
        "_id": mongo_id,
        "id": mongo_id,
        "date": date_timestamp,
        "payment_method": li.payment_method.name if li.payment_method else "Unknown",
        "description": li.description or "",
        "amount": float(li.amount or 0.0),
        "responsible_party": li.responsible_party,
        "notes": li.notes,
    }
    if li.events:
        data["event_id"] = li.events[0].mongo_id or li.events[0].id
    return data


def _pg_serialize_event(event: Any) -> Dict[str, Any]:
    """Convert Event ORM to dict matching MongoDB format"""
    from datetime import timezone as tz

    amount = float(event.total_amount) if event.total_amount else 0.0
    line_item_ids = [li.mongo_id or li.id for li in event.line_items]
    tag_names = [tag.name for tag in event.tags] if event.tags else []

    # Handle naive datetimes from SQLite by treating them as UTC
    if event.date and event.date.tzinfo is None:
        date_timestamp = event.date.replace(tzinfo=tz.utc).timestamp()
    else:
        date_timestamp = event.date.timestamp() if event.date else 0.0

    mongo_id = event.mongo_id or event.id
    return {
        "_id": mongo_id,
        "id": mongo_id,
        "date": date_timestamp,
        "name": event.description or "",
        "category": event.category.name if event.category else "Unknown",
        "amount": amount,
        "line_items": line_item_ids,
        "tags": tag_names,
        "is_duplicate_transaction": event.is_duplicate or False,
    }


def _pg_get_all_line_items(filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Get line items from PostgreSQL"""
    from models.database import SessionLocal
    from models.sql_models import Event, LineItem, PaymentMethod

    db_session = SessionLocal()
    try:
        query = db_session.query(LineItem).options(joinedload(LineItem.payment_method), joinedload(LineItem.events))

        if filters:
            # Handle _id: {$in: [...]} pattern (used in event creation)
            if "_id" in filters:
                id_filter = filters["_id"]
                if isinstance(id_filter, dict) and "$in" in id_filter:
                    ids = [str(id) for id in id_filter["$in"]]
                    # Try both mongo_id and PostgreSQL id
                    query = query.filter((LineItem.mongo_id.in_(ids)) | (LineItem.id.in_(ids)))

            if "payment_method" in filters and filters["payment_method"] not in [
                "All",
                None,
            ]:
                query = query.join(LineItem.payment_method).filter(PaymentMethod.name == filters["payment_method"])

            if "event_id" in filters:
                if isinstance(filters["event_id"], dict) and "$exists" in filters["event_id"]:
                    if not filters["event_id"]["$exists"]:
                        query = query.outerjoin(LineItem.events).filter(Event.id.is_(None))

        query = query.order_by(LineItem.date.desc())
        line_items = query.all()
        return [_pg_serialize_line_item(li) for li in line_items]
    finally:
        db_session.close()


def _pg_get_line_item_by_id(id: str) -> Optional[Dict[str, Any]]:
    """Get line item from PostgreSQL by PostgreSQL or MongoDB ID"""
    from models.database import SessionLocal
    from models.sql_models import LineItem

    db_session = SessionLocal()
    try:
        query = db_session.query(LineItem).options(joinedload(LineItem.payment_method), joinedload(LineItem.events))

        line_item = (
            query.filter(LineItem.id == id).first() if id.startswith("li_") else query.filter(LineItem.mongo_id == id).first()
        )

        return _pg_serialize_line_item(line_item) if line_item else None
    finally:
        db_session.close()


def _pg_get_all_events(filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Get events from PostgreSQL"""
    from datetime import datetime

    from models.database import SessionLocal
    from models.sql_models import Event, LineItem

    db_session = SessionLocal()
    try:
        # Use subqueryload for one-to-many relationships to avoid duplicate rows
        # joinedload is fine for many-to-one (category)
        query = db_session.query(Event).options(
            joinedload(Event.category),
            subqueryload(Event.line_items).joinedload(LineItem.payment_method),
            subqueryload(Event.tags),
        )

        if filters and "date" in filters:
            date_filter = filters["date"]
            if isinstance(date_filter, dict):
                from datetime import UTC

                if "$gte" in date_filter:
                    query = query.filter(Event.date >= datetime.fromtimestamp(date_filter["$gte"], UTC))
                if "$lte" in date_filter:
                    query = query.filter(Event.date <= datetime.fromtimestamp(date_filter["$lte"], UTC))

        events = query.all()
        return [_pg_serialize_event(event) for event in events]
    finally:
        db_session.close()


def _pg_get_event_by_id(id: str) -> Optional[Dict[str, Any]]:
    """Get event from PostgreSQL by PostgreSQL or MongoDB ID"""
    from models.database import SessionLocal
    from models.sql_models import Event, LineItem

    db_session = SessionLocal()
    try:
        query = db_session.query(Event).options(
            joinedload(Event.category),
            joinedload(Event.line_items).joinedload(LineItem.payment_method),
            joinedload(Event.tags),
        )

        # PostgreSQL event IDs look like "event_01K..." or "evt_xxx" (ULID or test IDs)
        # MongoDB event IDs look like "event_cash_..." or "event{hash}"
        # Check if it's a PostgreSQL ID by looking for patterns
        is_pg_id = (id.startswith("evt_") or id.startswith("event_0")) and len(id) >= 7

        event = query.filter(Event.id == id).first() if is_pg_id else query.filter(Event.mongo_id == id).first()

        return _pg_serialize_event(event) if event else None
    finally:
        db_session.close()


def _pg_get_line_items_for_event(event_id: str) -> List[Dict[str, Any]]:
    """Get line items for event from PostgreSQL"""
    from models.database import SessionLocal
    from models.sql_models import Event, EventLineItem, LineItem

    db_session = SessionLocal()
    try:
        pg_event = db_session.query(Event).filter((Event.id == event_id) | (Event.mongo_id == event_id)).first()

        if not pg_event:
            return []

        line_items = (
            db_session.query(LineItem)
            .join(EventLineItem, LineItem.id == EventLineItem.line_item_id)
            .filter(EventLineItem.event_id == pg_event.id)
            .options(joinedload(LineItem.payment_method), joinedload(LineItem.events))
            .all()
        )

        return [_pg_serialize_line_item(li) for li in line_items]
    finally:
        db_session.close()


def _pg_get_categorized_data() -> List[Dict[str, Any]]:
    """Get monthly breakdown from PostgreSQL"""
    from sqlalchemy import extract, func

    from models.database import SessionLocal
    from models.sql_models import Category, Event, LineItem

    db_session = SessionLocal()
    try:
        results = (
            db_session.query(
                extract("year", Event.date).label("year"),
                extract("month", Event.date).label("month"),
                Category.name.label("category"),
                func.sum(LineItem.amount).label("totalExpense"),
            )
            .join(Event.category)
            .join(Event.line_items)
            .group_by(extract("year", Event.date), extract("month", Event.date), Category.name)
            .order_by("year", "month", Category.name)
            .all()
        )

        return [
            {
                "year": int(row.year) if row.year else 0,
                "month": int(row.month) if row.month else 0,
                "category": row.category,
                "totalExpense": float(row.totalExpense) if row.totalExpense else 0.0,
            }
            for row in results
        ]
    finally:
        db_session.close()


def _pg_get_transactions(source: str, filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Get raw transactions from PostgreSQL by source (venmo, splitwise, stripe, cash)"""
    from models.database import SessionLocal
    from models.sql_models import Transaction

    db_session = SessionLocal()
    try:
        query = db_session.query(Transaction).filter(Transaction.source == source)

        # Apply filters if provided (though typically raw data reads don't use filters)
        if filters:
            # Could add date filters here if needed in the future
            pass

        query = query.order_by(Transaction.transaction_date.desc())
        transactions = query.all()

        # Return in MongoDB format: source_data with _id = source_id
        return [
            {
                "_id": txn.source_id,
                **txn.source_data,  # Unpack the JSONB data
            }
            for txn in transactions
        ]
    finally:
        db_session.close()


def _pg_get_all_bank_accounts(
    filters: Optional[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Get bank accounts from PostgreSQL"""
    from models.database import SessionLocal
    from models.sql_models import BankAccount

    db_session = SessionLocal()
    try:
        query = db_session.query(BankAccount)

        if filters and "status" in filters:
            query = query.filter(BankAccount.status == filters["status"])

        accounts = query.all()
        return [
            {
                "_id": acc.mongo_id or acc.id,
                "id": acc.id,
                "institution_name": acc.institution_name,
                "display_name": acc.display_name,
                "last4": acc.last4,
                "status": acc.status,
            }
            for acc in accounts
        ]
    finally:
        db_session.close()


def _pg_get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user from PostgreSQL by email"""
    from models.database import SessionLocal
    from models.sql_models import User

    db_session = SessionLocal()
    try:
        user = db_session.query(User).filter(User.email == email).first()
        if not user:
            return None
        return {
            "_id": user.mongo_id or user.id,
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "password_hash": user.password_hash,
        }
    finally:
        db_session.close()
