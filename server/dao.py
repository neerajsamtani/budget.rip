from typing import List

from flask import current_app

from helpers import to_dict

venmo_raw_data_collection = "venmo_raw_data"
splitwise_raw_data_collection = "splitwise_raw_data"
cash_raw_data_collection = "cash_raw_data"
stripe_raw_transaction_data_collection = "stripe_raw_transaction_data"
stripe_raw_account_data_collection = "stripe_raw_account_data"
line_items_collection = "line_items"
events_collection = "events"
bank_accounts_collection = "accounts"
users_collection = "users"


def get_collection(cur_collection_str: str):
    # Access the MongoDB collection using current_app
    mongo = current_app.config["MONGO"]
    return mongo.db[cur_collection_str]


def get_all_data(cur_collection_str: str, filters=None) -> List:
    cur_collection = get_collection(cur_collection_str)
    return list(cur_collection.find(filters).sort("date", -1))


def get_item_by_id(cur_collection_str: str, id):  # TODO: Return Type?
    cur_collection = get_collection(cur_collection_str)
    return cur_collection.find_one({"_id": id})


def insert(cur_collection_str: str, item):
    cur_collection = get_collection(cur_collection_str)
    item = to_dict(item)
    cur_collection.insert_one(item)


def delete_from_collection(cur_collection_str: str, id):
    cur_collection = get_collection(cur_collection_str)
    cur_collection.delete_one({"_id": id})


def remove_event_from_line_item(line_item_id: int):
    cur_collection = get_collection(line_items_collection)
    cur_collection.update_one({"_id": line_item_id}, {"$unset": {"event_id": ""}})


def get_user_by_email(email: str):
    cur_collection = get_collection(users_collection)
    return cur_collection.find_one({"email": {"$eq": email}})


def upsert(cur_collection_str: str, item):
    item = to_dict(item)
    upsert_with_id(cur_collection_str, item, item["id"])


def upsert_with_id(cur_collection_str: str, item, id):
    cur_collection = get_collection(cur_collection_str)
    item["_id"] = item["id"]
    cur_collection.replace_one({"_id": id}, item, upsert=True)


def get_categorized_data():
    """
    Group totalExpense by month, year, and category
    """
    cur_collection = get_collection(events_collection)
    query_result = cur_collection.aggregate(
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

    response = []
    for document in query_result:
        response.append(dict(document))
    return response
