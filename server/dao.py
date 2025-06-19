from typing import Any, Dict, List, Optional, Union

from flask import current_app
from pymongo import UpdateOne
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import BulkWriteError

from helpers import to_dict, to_dict_robust

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
    print(f"client: {client}")
    return client[cur_collection_str]


def get_all_data(
    cur_collection_str: str, filters: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    cur_collection: Collection = get_collection(cur_collection_str)
    return list(cur_collection.find(filters).sort("date", -1))


def get_item_by_id(
    cur_collection_str: str, id: Union[str, int]
) -> Optional[Dict[str, Any]]:
    cur_collection: Collection = get_collection(cur_collection_str)
    return cur_collection.find_one({"_id": id})


def insert(cur_collection_str: str, item: Any) -> None:
    cur_collection: Collection = get_collection(cur_collection_str)
    item_dict: Dict[str, Any] = to_dict(item)
    cur_collection.insert_one(item_dict)


def delete_from_collection(cur_collection_str: str, id: Union[str, int]) -> None:
    cur_collection: Collection = get_collection(cur_collection_str)
    cur_collection.delete_one({"_id": id})


def remove_event_from_line_item(line_item_id: int) -> None:
    cur_collection: Collection = get_collection(line_items_collection)
    cur_collection.update_one({"_id": line_item_id}, {"$unset": {"event_id": ""}})


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    cur_collection: Collection = get_collection(users_collection)
    return cur_collection.find_one({"email": {"$eq": email}})


def upsert(cur_collection_str: str, item: Any) -> None:
    item_dict: Dict[str, Any] = to_dict(item)
    upsert_with_id(cur_collection_str, item_dict, item_dict["id"])


def upsert_with_id(
    cur_collection_str: str, item: Dict[str, Any], id: Union[str, int]
) -> None:
    cur_collection: Collection = get_collection(cur_collection_str)
    item["_id"] = item["id"]
    cur_collection.replace_one({"_id": id}, item, upsert=True)


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
            bulk_operations.append(
                UpdateOne({"_id": item_dict["_id"]}, {"$set": item_dict}, upsert=True)
            )
        except Exception as e:
            print(f"Error preparing item for bulk upsert: {e}")
            print(f"Item type: {type(item)}")
            print(f"Item: {item}")
            continue

    # Execute bulk operations
    if bulk_operations:
        try:
            result: Any = cur_collection.bulk_write(bulk_operations, ordered=False)
            print(
                f"Bulk upsert completed: {result.upserted_count} inserted, {result.modified_count} updated"
            )
        except Exception as e:
            print(f"Error in bulk upsert: {e}")
            if isinstance(e, BulkWriteError):
                print(f"BulkWriteError: {e.details}")
            # Fallback to individual upserts for better error isolation
            for item in items:
                try:
                    upsert(cur_collection_str, item)
                except Exception as individual_error:
                    print(f"Error upserting individual item: {individual_error}")


def get_categorized_data() -> List[Dict[str, Any]]:
    """
    Group totalExpense by month, year, and category
    """
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
