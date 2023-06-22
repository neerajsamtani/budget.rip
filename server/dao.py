from typing import Collection, List

import mongomock
from pymongo import MongoClient
from pymongo.typings import _DocumentType
from constants import MONGODB_URI

from helpers import to_dict

# TODO: Stop using mock dao
# client = mongomock.MongoClient(MONGODB_URI, 27017)
client = MongoClient(MONGODB_URI, 27017)
db = client.flask_db
venmo_raw_data_collection = db.venmo_raw_data
splitwise_raw_data_collection = db.splitwise_raw_data
cash_raw_data_collection = db.cash_raw_data
stripe_raw_transaction_data_collection = db.stripe_raw_transaction_data
stripe_raw_account_data_collection = db.stripe_raw_account_data
line_items_collection = db.line_items
events_collection = db.events
bank_accounts_collection = db.accounts


def get_all_data(cur_collection: Collection, filters=None) -> List[_DocumentType]:
    return list(cur_collection.find(filters).sort("date", -1))


def get_item_by_id(cur_collection: Collection, id=int):  # TODO: Return Type?
    return list(cur_collection.find({"_id": {"$eq": id}}))[0]


def insert(cur_collection: Collection, item):
    item = to_dict(item)
    cur_collection.insert_one(item)


def delete_from_collection(cur_collection: Collection, id: int):
    cur_collection.delete_one({"_id": id})


def remove_event_from_line_item(line_item_id: int):
    line_items_collection.update_one(
        {"_id": line_item_id}, {"$unset": {"event_id": ""}}
    )


def upsert(cur_collection: Collection, item):
    item = to_dict(item)
    upsert_with_id(cur_collection, item, item["id"])


def upsert_with_id(cur_collection: Collection, item, id: int):
    item["_id"] = item["id"]
    cur_collection.replace_one({"_id": id}, item, upsert=True)


def get_categorized_data():
    """
    Group totalExpense by month, year, and category
    """
    query_result = events_collection.aggregate(
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
