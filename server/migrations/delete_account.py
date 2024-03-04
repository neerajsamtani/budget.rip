from pymongo import MongoClient
import stripe

# Config
DRY_RUN = True
account_id = ""
stripe.api_key = ""
mongo_host = ""

print(f"DRY RUN: {DRY_RUN}")

# Connect to MongoDB
client = MongoClient(host=mongo_host)
db = client.flask_db
accounts_collection = db.accounts
stripe_raw_transaction_collection = db.stripe_raw_transaction_data
line_items_collection = db.line_items
events_collection = db.events

# Get Account Object
account_query = {"id": account_id}
account = accounts_collection.find_one(account_query)
print(
    f"Fetching {account['id']} | {account['institution_name']} {account['display_name']} {account['last4']}",
    end="\n\n",
)

# Get Raw Transaction Objects and related line items
raw_transaction_query = {"account": account_id}
raw_transactions = stripe_raw_transaction_collection.find(raw_transaction_query)
for raw_transaction in raw_transactions:
    raw_transaction_id = raw_transaction["id"]
    print(f"Found raw transaction: {raw_transaction_id}")

    line_item_query = {"id": f"line_item_{raw_transaction_id}"}
    line_item = line_items_collection.find_one(line_item_query)
    line_item_id = line_item["id"]
    print(f"Found corresponding line item: {line_item_id}")

    # Ensure Line Item is not in any events
    print(f"Checking that {line_item_id} is not part of any events...")
    event_query = {"line_items": line_item_id}
    event = events_collection.find_one(event_query)
    if event is not None:
        print(f"{line_item_id} is part of {event['id']}. Not running Deletion Script.")
        exit()

    print(f"Deleting {raw_transaction['id']} | {raw_transaction['description']}")
    if not DRY_RUN:
        stripe_raw_transaction_collection.delete_one({"id": raw_transaction_id})

    print(f"Deleting {line_item['id']} | {line_item['description']}")
    if not DRY_RUN:
        line_items_collection.delete_one({"id": line_item_id})

    print()

# Disconnect from account
print(f"Disconnecting from Stripe Account {account_id}", end="\n\n")
if not DRY_RUN:
    stripe.financial_connections.Account.disconnect(account_id)

# Delete account object
print(f"Deleting Account From DB {account}", end="\n\n")
if not DRY_RUN:
    accounts_collection.delete_one(account_query)

print("Done!")
