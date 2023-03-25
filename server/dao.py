from typing import Collection, List, Dict
from pymongo import MongoClient
from bson.objectid import ObjectId
from pymongo.typings import _DocumentType
from constants import *
from line_item import LineItem
from helpers import to_dict
import mongomock

# TODO: Stop using mock dao
# client = mongomock.MongoClient('localhost', 27017)
client = MongoClient('localhost', 27017)
db = client.flask_db
venmo_raw_data_db = db.venmo_raw_data
splitwise_raw_data_db = db.splitwise_raw_data
cash_raw_data_db = db.cash_raw_data
stripe_raw_transaction_data_db = db.stripe_raw_transaction_data
stripe_raw_account_data_db = db.stripe_raw_account_data
line_items_db = db.line_items
events_db = db.events
accounts_db = db.accounts

def get_all_data(cur_db: Collection, filters = None) -> List[_DocumentType]:
    return list(cur_db.find(filters).sort("date", -1))

def get_item_by_id(cur_db: Collection, id = int): # TODO: Return Type?
    return list(cur_db.find({'_id': { "$eq" : id}}))[0]

def insert(cur_db: Collection, item):
    item = to_dict(item)
    cur_db.insert_one(item)

def delete_from_db(cur_db: Collection, id: int):
    cur_db.delete_one({"_id": id})

def remove_event_from_line_item(line_item_id: int):
    line_items_db.update_one({"_id": line_item_id}, { "$unset": { "event_id": ""} })

def upsert(cur_db: Collection, item):
    item = to_dict(item)
    upsert_with_id(cur_db, item, item["id"])

def upsert_with_id(cur_db: Collection, item, id: int):
    item['_id'] =  item["id"]
    cur_db.replace_one({'_id': id}, item, upsert=True)

def get_categorized_data():
    """
    Group totalExpense by month, year, and category
    """
    query_result = events_db.aggregate([
        {
            '$addFields': {
                'date': {
                    '$toDate': {
                        '$multiply': [
                            '$date', 1000
                        ]
                    }
                }
            }
        }, {
            '$group': {
                '_id': {
                    'year': {
                        '$year': '$date'
                    }, 
                    'month': {
                        '$month': '$date'
                    }, 
                    'category': '$category'
                }, 
                'totalExpense': {
                    '$sum': '$amount'
                }
            }
        }, {
            '$project': {
                '_id': 0, 
                'year': '$_id.year', 
                'month': '$_id.month', 
                'category': '$_id.category', 
                'totalExpense': 1
            }
        }, {
            '$sort': {
                'year': 1, 
                'month': 1, 
                'category': 1
            }
        }
    ])

    response = []
    for document in query_result:
        response.append(dict(document))
    return response
