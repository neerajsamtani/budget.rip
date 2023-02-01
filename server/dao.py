from typing import Collection, List, Dict
from pymongo import MongoClient
from bson.objectid import ObjectId
from pymongo.typings import _DocumentType
from constants import *
from line_item import LineItem
from helpers import to_dict
import mongomock

# TODO: Stop using mock dao
client = mongomock.MongoClient('localhost', 27017)
db = client.flask_db
venmo_raw_data_db = db.venmo_raw_data
splitwise_raw_data_db = db.splitwise_raw_data
cash_raw_data_db = db.cash_raw_data
stripe_raw_transaction_data_db = db.stripe_raw_transaction_data
stripe_raw_account_data_db = db.stripe_raw_account_data
line_items_db = db.line_items
events_db = db.events
accounts_db = db.accounts

def get_all_data(db: Collection, filters = None) -> List[_DocumentType]:
    print(filters)
    return list(db.find(filters).sort("date", -1))

def get_db_data(db: Collection, payment_method: Payment_Method) -> List[_DocumentType]:
    if payment_method == Payment_Method.ALL:
        # TODO: Make this events filter somewhere else. ALL should return all.
        cursor = db.find({ "event_id": { "$exists": False}}).sort("date", -1)
    elif payment_method == Payment_Method.VENMO:
        cursor =  db.find({"payment_method": "Venmo"}).sort("date", -1)
    elif payment_method == Payment_Method.SPLITWISE:
        cursor =  db.find({"payment_method": "Splitwise"}).sort("date", -1)
    elif payment_method == Payment_Method.STRIPE:
        cursor =  db.find({"payment_method": "Stripe"}).sort("date", -1)
    return list(cursor)

def get_line_items(line_item_ids: List[int]) -> List[LineItem]:
    result =  line_items_db.find({'_id': { "$in" : line_item_ids}}).sort("date", -1)
    return list(result)

# TODO: Clean up the requests to Mongo for get_event and get_line_item
# TODO: Add type hint for event

def get_event(event_id: int):
    result =  events_db.find({'_id': { "$eq" : event_id}})
    return list(result)[0]

def get_line_item(line_item_id: int) -> LineItem:
    result =  line_items_db.find({'_id': { "$eq" : line_item_id}})
    return list(result)[0]

def insert(db: Collection, item):
    item = to_dict(item)
    db.insert_one(item)

def delete_from_db(db: Collection, id: int):
    db.delete_one({"_id": id})

def remove_event_from_line_item(line_item_id: int):
    line_items_db.update_one({"_id": line_item_id}, { "$unset": { "event_id": ""} })

def upsert(db: Collection, item):
    item = to_dict(item)
    upsert_with_id(db, item, item["id"])

def upsert_with_id(db: Collection, item, id: int):
    item['_id'] =  item["id"]
    db.replace_one({'_id': id}, item, upsert=True)
